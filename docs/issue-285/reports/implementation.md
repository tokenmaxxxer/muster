---
code_under_review: spawn.py, test_spawn.py
loop_state: complete
---

# Phase 2 — spawn latency fixes (issue #285)

Implements `docs/issue-285/proposals/spawn-latency-fixes.md` P1-P5, approved
via `APPROVE issue-285/implementation` on the issue (single-account mode).

## Why

Issue #285 measured a bounded spawn spending ~3.6s of its ~4.9s total on
work producing no new information (flat 2s sleep, the same rulebook pull
run 3x, the same workspace fetch run 2x) and found almost no network
subprocess call in `spawn.py` carries a `timeout=`, so a flaky network or
credential prompt hangs the orchestrator indefinitely instead of failing
fast — the reported "the spawn is stuck." The approved phase-1 proposal
(`docs/issue-285/proposals/spawn-latency-fixes.md`) is the upstream basis
for every change below; each of P1-P5 there maps 1:1 to a change here.

## What was done

- **P1** (`spawn.py:_await_bounded`): replaced the flat `time.sleep(2)`
  with an escalating poll — starts at 50ms, doubles each iteration, caps
  at the existing 2s. Event-detection and stall-detection logic
  (offset tracking, `session-end` distinction, stall message) untouched.
- **P2** (`spawn.py:rulebook_checkout`): added `_RULEBOOK_CACHE: dict[str, Path]`
  module-level memo keyed on `spec["marketplace"]`. Local-path
  short-circuit stays first (not a network path). Cache populated on
  both the pull-existing and clone-new branches.
- **P3** (`spawn.py:_fetch_or_halt`): added `_FETCHED_THIS_SPAWN: dict[str, float]`
  keyed on the resolved `work_dir`. A dedupe hit still runs `after()` if
  given, then returns without hitting the network. The freshness mark is
  written only after a successful fetch (post the halt check), so a
  failing first call still `sys.exit`s before anything is cached — the
  second caller can never observe a skipped halt.
- **P4**: TTL marker file `.muster-last-pull` written next to each managed
  clone (rulebook and `tokenmaxxxer-core`), checked by `_pull_is_fresh()`
  before running `git pull`. Default TTL 15 min; `MUSTER_RULEBOOK_TTL`
  overrides (minutes), `MUSTER_RULEBOOK_TTL=0` forces a pull every time.
- **P5**: added `_run_net()` — wraps `subprocess.run` with a mandatory
  `timeout=`, catching `subprocess.TimeoutExpired` and failing closed via
  `sys.exit(f"{label}: 시간초과({timeout}s) — ...")`. Applied with
  `NETWORK_TIMEOUT=60` to: rulebook pull, core pull, `_fetch_or_halt`'s
  fetch, `issue_workspace`'s local clone, and `ensure_pushed`'s git
  closure (push). Applied with `CLONE_TIMEOUT=180` to the rulebook and
  core `git clone` calls. `_git_env()`'s dict branch (token present) now
  also sets `GIT_TERMINAL_PROMPT=0` and `GIT_ASKPASS=true`; the
  `None`-on-no-token fallback is preserved exactly (rewritten as an early
  `if not token: return None`, same net effect as before).

## Constraint checks

- [x] `_await_bounded()`'s bounded-return contract (issue #114) and the
  `session-end`-only-means-ended distinction (issue #142) verbatim —
  only the sleep cadence changed; pinned by `AwaitBoundedTiming.test_still_bounded_by_stall_timeout`.
- [x] P2 memo does not become a permanent skip: it's process-lifetime
  only (module dict, no disk persistence); a fresh process re-checks the
  P4 TTL marker independently.
- [x] P3 dedupe never skips `_fetch_or_halt`'s halt check — verified by
  `FetchDedupe.test_second_fetch_of_same_dir_is_skipped` (only the
  successful path gets deduped) and by code inspection: the cache write
  happens after the `sys.exit` branch, never before.
- [x] P5 timeouts fail closed with a named error, not a swallowed
  `TimeoutExpired` — pinned by `NetworkSubprocessTimeout`.
- [x] `_git_env()`'s `None` fallback preserved — pinned by
  `GitEnvTimeoutPromptVars.test_no_token_fallback_stays_none`.

## Tests added (`test_spawn.py`)

- `AwaitBoundedTiming` — timing test (P1): caller-return <1.5s on an
  early event, plus a stall-timeout regression guard.
- `RulebookCheckoutMemo` — call-count tests (P2/P4): at most one `git
  pull` per process across the three real call sites (`plugin_dirs`,
  `checkout_version` x2), TTL-fresh marker skips pull, `MUSTER_RULEBOOK_TTL=0`
  forces it.
- `FetchDedupe` — call-count test (P3): second `_fetch_or_halt()` on the
  same dir skips the network call; `after()` still runs on the skip path.
- `NetworkSubprocessTimeout` — timeout-behavior tests (P5): `_run_net`
  surfaces a named `SystemExit` on `TimeoutExpired`; `_fetch_or_halt`
  surfaces it promptly rather than hanging.
- `GitEnvTimeoutPromptVars` — `_git_env()` dict-branch additions and
  None-fallback preservation.

Full suite: `python3 -m pytest test_spawn.py -q` → 230 passed (219
pre-existing + 11 new), run once, confirmed locally.

Doc placement ladder: no new env var beyond `MUSTER_RULEBOOK_TTL`, which
is documented inline in `rulebook_checkout`'s TTL helpers and in this
proposal/record — no separate handbook exists for spawn.py env vars to
extend. No new dependency, no migration, no changed public signature/wire
format warranting `docs/issue-285/decisions/`.

## What did not work

None — no attempt was undone or replaced during this build.

## Open findings

None currently open against this record.

## Next steps

None required from this session. All five fixes (P1-P5) and their tests
are implemented, run, and pass. The only outstanding item is procedural
(see Hunt cadence below), not implementation work: this PR is ready for
human review/merge as-is.

## Open-finding resolution path

There are no open findings against this record (see Open findings
above), so there is nothing to resolve. If verify or a future session
opens a finding here, it blocks further build commits on this record
until this section carries a `resolved_findings:` entry naming it and
the finder re-clears, per contract.

## Hunt cadence

Before-landing warrant-hunter dispatch was skipped this turn. This
session runs headless/single-shot (contract v3 s22): a background
dispatch whose result isn't consumed in this same turn would violate the
higher-priority headless rule, so no hunter was dispatched. Resolution
path: a future turn on this branch, or verify's own pass, may run the
before-landing hunt before merge; nothing further is pending from this
session's side.

closed_checks: none (no hunt ran this turn — see Rationale for deviations).

## Rationale for deviations

The approved proposal's own text does not mention hunt cadence (that
comes from the standing warrant directive, not this issue's `## What
will be done`), so implementation of P1-P5 itself has no deviation from
what was approved. The one divergence worth recording is procedural: the
warrant directive calls for a before-landing warrant-hunter dispatch, but
this session is headless/single-shot (contract v3 s22) — dispatching a
background hunter whose finding this turn could not consume would violate
the higher-priority headless rule (never end a turn having delegated work
not consumed within that same turn). Contract v3 s22 explicitly outranks
the warrant directive's hunter-dispatch instructions in this situation, so
the dispatch was skipped rather than run and abandoned. No code or test
scope was altered as a result — this affects only the hunt-cadence
side-channel, not the delivered implementation.
