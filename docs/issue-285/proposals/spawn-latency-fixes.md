files:
- spawn.py
- test_spawn.py
- docs/issue-285/reports/implementation.md

## Request

A bounded spawn spends ~3.6s of its ~4.9s total on work that produces no
new information: a flat `time.sleep(2)` polling wait for a session-start
event that typically lands in milliseconds, the same `rulebook_checkout()`
git pull run three separate times per spawn, and the same workspace `git
fetch` run twice seconds apart. On top of that, almost none of the
orchestrator's own network subprocess calls carry a `timeout=`, so a flaky
network or a credential prompt on an unattended run — rather than failing
fast with a named error — hangs the orchestrator indefinitely; this is what
gets reported as "the spawn is stuck." Fix all five: escalating poll instead
of flat sleep (P1), per-process memoization of `rulebook_checkout` (P2),
dedupe the double workspace fetch (P3), a short TTL on the rulebook/core
freshness pulls (P4), and timeouts plus `GIT_TERMINAL_PROMPT=0`/
`GIT_ASKPASS=true` on every network subprocess call the orchestrator itself
makes (P5).

## Constraints

- No behavior change to the bounded-return contract in `_await_bounded()`
  (issue #114): it must still return on the first new `events.jsonl` line
  OR on stall, whichever comes first, without ever blocking past the stall
  timeout. Only the poll cadence changes.
- No behavior change to the "session-end only means the session actually
  ended" distinction (issue #142) inside `_await_bounded()` — the `ev["type"]
  != "session-end"` branch and its message must be preserved verbatim.
- P2's memoization must not defeat the reason `rulebook_checkout()` exists:
  it still has to detect a genuinely stale checkout when the freshness
  window (P4) has expired — memoization only prevents redundant re-pulls
  *within a single already-fresh process run*, it must not become a
  permanent skip.
- P3's dedupe must not weaken `_fetch_or_halt`'s fail-closed contract
  (`spawn.py:2559-2577`): if the shared fetch failed, both
  `issue_workspace()` and `checkout_issue_branch()` must still observe the
  halt — a flag that skips the second fetch must not also skip the check.
- P5's timeouts must fail closed with a named, actionable error (matching
  the existing `sys.exit(f"...: fetch 실패 — ...")` shape at
  `spawn.py:2577`), not swallow `subprocess.TimeoutExpired` silently.
- `_git_env()`'s existing `None`-on-no-token fallback (so a real
  `subprocess.run` inherits the parent env and doesn't stomp
  ssh-agent/osxkeychain auth) must be preserved when adding
  `GIT_TERMINAL_PROMPT`/`GIT_ASKPASS` — those two additions belong in the
  dict-branch, not forced into the `None` branch.

## Rationale

**P1 — escalating poll vs. file-watching (inotify/watchdog).** Considered
switching `_await_bounded()`'s loop to an OS-level file-watcher
(`inotify` on Linux via a library like `watchdog`) so the loop wakes
exactly when `events.jsonl` changes instead of polling at all. Rejected:
it's a new external dependency (violates the "no new external
dependencies" house preference re-affirmed on this repo, see Out of
scope) to shave a poll interval that's already small once escalated, on a
loop that already has to poll `log_path.stat().st_size` every iteration
for stall detection regardless of how the event-file wait is implemented —
so file-watching would only remove half the polling, not all of it, at the
cost of a new dependency and cross-platform fallback code (inotify doesn't
exist on macOS/BSD without `kqueue` alternatives, which the repo's dev
machine notes elsewhere is a real platform it runs on). An escalating poll
(e.g. 50ms, backing off toward the existing 2s ceiling) gets the measured
win — median 3.739s actual sits within milliseconds of session-start being
written, so a sub-100ms wake beats the flat 2s wait by ~1.9s — without
touching the loop's dependency-free, single-process shape.

**P2/P4 — one in-process memo dict vs. one combined memo+TTL store.**
Considered folding P2 and P4 into a single mechanism (e.g. a disk-persisted
"last pulled at T" record that both processes and calls consult). Rejected
as the sole mechanism: P2's problem is *within one spawn's process* —
`plugin_dirs()` (`spawn.py:2875`), `checkout_version()`'s print
(`spawn.py:2887`), and the ledger entry (`spawn.py:3221`) all resolve the
same marketplace's checkout independently in the same `python3 spawn.py`
invocation, so a disk round-trip on every call (stat a marker file, parse a
timestamp) is needless I/O for a fact the process already knows from its
own first call this run. P4's problem is *across successive spawns* — a
fresh process 30 seconds after the last one has no memory of the first
process's pull, so only a disk-persisted marker (next to the clone, e.g.
`<clone-dir>/.muster-last-pull`) can tell it "you don't need to hit the
network again." The two layers solve different scopes (in-process
call-count vs. cross-process wall-clock) and neither subsumes the other:
an in-process-only memo does nothing for the common case of many spawns in
a short session (still one network pull per spawn — P4's actual target),
and a disk-only TTL still forces every one of P2's three call sites in a
single process to independently stat and parse the marker file instead of
reading a plain dict once. Both stay: `rulebook_checkout()` checks the
in-process dict first (keyed on `spec["marketplace"]`, mirroring
`_GH_TOKEN_CACHE`'s pattern at `spawn.py:2508-2534`); on a miss it checks
the on-disk TTL marker before deciding whether to actually invoke `git
pull`.

**P3 — dedupe via flag vs. always keeping two independent fetches.**
Considered leaving `issue_workspace()` and `checkout_issue_branch()`
fully independent (current state) on the theory that decoupling makes each
function's contract simpler to reason about in isolation. Rejected: this
is precisely the issue's confirmed measurement — `checkout_issue_branch()`
(`spawn.py:2667`) unconditionally re-fetches the same `cwd` that
`issue_workspace()` (`spawn.py:2622`/`2625`/`2651`) just fetched seconds
earlier, and the issue's own note ("reuse is currently near-worthless as
an optimization") shows the current independence is not actually buying
safety, only doubling the network cost with zero freshness benefit given
how close together the two calls run in the same `_spawn_one()` flow.

**P5 — timeouts as a blanket sweep vs. case-by-case tuning.** Considered
tuning each subprocess call's timeout individually by call site.
Rejected in favor of two fixed tiers (60s for pull/fetch/push, 180s for
`git clone`) matching the one precedent already in the file
(`spawn.py:2199`'s existing `timeout=180`, presumably a clone-shaped call)
— per-call tuning would require load-testing every remote's actual clone
size, which is not knowable statically and not worth the design time
against the acceptance bar of "fails within 60s with a named error"
rather than "fails at the theoretically optimal time."

## What will be done

- **P1** — `_await_bounded()` (`spawn.py:1875-1918`): replace the fixed
  `time.sleep(2)` at `spawn.py:1918` with an escalating interval (e.g.
  start at 50ms, multiply up, cap at the current 2s) so the loop still
  bounds CPU usage on a long stall but wakes almost immediately for the
  common case where `session-start` lands within tens of milliseconds of
  `Popen`. The event-detection and stall-detection logic (lines
  1890-1917) are otherwise untouched.
- **P2** — add a module-level `dict[str, Path]` cache next to
  `_GH_TOKEN_CACHE` (`spawn.py:2508`), keyed on `spec["marketplace"]`.
  `rulebook_checkout()` (`spawn.py:177-210`) checks the cache first (after
  the local-install-path short-circuit at `spawn.py:192-194`, which stays
  first since it's not a network path); on a cache miss it runs today's
  logic (pull-if-exists at `spawn.py:200-203`, or clone at
  `spawn.py:204-210`) and populates the cache with the resolved `Path`
  before returning. This collapses the 3 calls confirmed at
  `spawn.py:2875` (`plugin_dirs`), `spawn.py:2887` (`checkout_version`,
  via its print statement), and `spawn.py:3221` (ledger entry) down to at
  most 1 pull per process per marketplace.
- **P3** — thread a freshness signal from `issue_workspace()`
  (`spawn.py:2580-2654`) to `checkout_issue_branch()`
  (`spawn.py:2657-2683`): the simplest option consistent with these two
  functions' existing independent-return-value shape is a small
  per-workspace freshness stamp (module-level dict keyed on the resolved
  workspace path, storing `time.monotonic()` of the last successful
  fetch) that `_fetch_or_halt()` (`spawn.py:2559-2577`) itself checks and
  updates — so any caller that goes through `_fetch_or_halt` for the same
  `work_dir` within the same spawn skips the actual `git fetch` but still
  gets the same fail-closed guarantee (nothing to fail closed on if it
  didn't refetch) that the first fetch already established for that path.
- **P4** — TTL marker file next to each managed clone (rulebook:
  `ROOT/runs/rulebooks/<marketplace>/.muster-last-pull`; core:
  `ROOT/runs/rulebooks/tokenmaxxxer-core/.muster-last-pull`), read/written
  around the pulls at `spawn.py:201` and `spawn.py:2054`. Default TTL 15
  minutes; skip the `git pull` (log why, still return the existing dir)
  if the marker's timestamp is inside the window. `MUSTER_RULEBOOK_TTL`
  env var overrides the window in minutes; `MUSTER_RULEBOOK_TTL=0` forces
  a pull every time (today's behavior), for anyone who needs same-minute
  freshness.
- **P5** — add `timeout=60` to the network subprocess calls at
  `spawn.py:201` (rulebook pull), `spawn.py:2054` (core pull),
  `spawn.py:2572` (`_fetch_or_halt`'s fetch), and `spawn.py:2710`
  (`ensure_pushed`'s push); add `timeout=180` to the clone calls at
  `spawn.py:206` (rulebook clone), `spawn.py:2060-2062` (core clone), and
  `spawn.py:2628` (`issue_workspace`'s new-clone). Each `subprocess.run`
  call gains a `try/except subprocess.TimeoutExpired` (or an inline
  check) that produces a `sys.exit(f"...: 시간초과(Ns) — ...")`-shaped
  named error matching the existing fail-closed message style at
  `spawn.py:2577`, rather than letting `TimeoutExpired` propagate as an
  unhandled traceback. Also update `_git_env()` (`spawn.py:2537-2556`) to
  add `"GIT_TERMINAL_PROMPT": "0"` and `"GIT_ASKPASS": "true"` into the
  returned dict (the token-present branch only — the `None`-fallback
  branch for "no token resolved" stays `None` per the Constraints
  section), so the orchestrator's own fetch/push calls through
  `_git_env()` can't block on a credential prompt the way
  `spawn.py:2287`'s session-env-only `GIT_TERMINAL_PROMPT=0` currently
  fails to prevent.

## Out of scope

- No change to `--stall-timeout`'s default (5.0 min,
  `spawn.py:2326`-adjacent) or to `WATCHDOG_SILENCE_MIN`/
  `WATCHDOG_NO_COMMIT_MIN` (`spawn.py:1381-1382`) beyond what P1-P5
  require — the issue's "fix direction" section floats lowering the stall
  default to ~90s as a follow-on idea, but that is a separate behavior
  change (affects what counts as "stuck" for a live session, not spawn
  startup latency) and is not part of this issue's acceptance criteria.
- No restructuring of `ensure_rulebook`'s double `claude -p` invocation
  (noted in the issue as a related but separate cost on first-ever role
  spawn) — out of scope for this latency pass on the git/sleep/timeout
  paths.
- No new external dependencies (rules out `watchdog`/`inotify`-based
  file-watching for P1, see Rationale).
- No change to `_await_bounded`'s bounded-return contract shape (issue
  #114) or its session-end-vs-spawn-returned distinction (issue #142) —
  only the sleep cadence changes.
- No change to how `issue_workspace()` decides between reuse-src,
  reuse-work-dir, and new-clone (`spawn.py:2620-2654`) — P3 only removes
  the redundant *second* fetch after whichever of those three paths
  already fetched.

## How you'll know it worked

- **Timing test** (P1): a warm-spawn timing test in `test_spawn.py`
  asserting caller-return <=1.5s and first-model-token <=1.5s (measured
  from process start, mirroring the issue's own `t=0.000`/`t=1.733`
  instrumentation), using a stub for the actual `claude` session process
  so the test doesn't depend on a real model call.
- **Call-count tests** (P2/P3): a test asserting `rulebook_checkout()`'s
  underlying `git pull`/`git clone` subprocess is invoked at most once per
  process for a given `spec["marketplace"]` across the three real call
  paths (`plugin_dirs`, `checkout_version`, ledger-entry construction) —
  following the existing stub-executable-plus-call-count-file pattern
  already used at `test_spawn.py:1343-1364`. A parallel test asserting
  the workspace's `git fetch` is invoked at most once per spawn across
  `issue_workspace()` + `checkout_issue_branch()`.
- **Timeout behavior test** (P5): a test that points a network subprocess
  call at an address that will not respond (or stubs `subprocess.run` to
  raise `TimeoutExpired`) and asserts the call surfaces a named,
  recognizable error within the configured timeout bound (<=60s) rather
  than hanging or raising an unhandled traceback.
- Phase 2's `docs/issue-285/reports/implementation.md` records which of
  these tests were added, their pass/fail state, and any acceptance-bar
  deviation discovered during implementation.
