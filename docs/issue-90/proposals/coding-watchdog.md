# Issue #90 phase-1 proposal: mid-run watchdog for live role sessions

Status: proposal, phase 1 of 2. Awaits approval before any write-set work
starts, per role-handoff contract v3 s19. Built on the two survey docs in
this same directory tree:
`docs/issue-90/reports/coding/orchestrate-surfaces.md` and
`docs/issue-90/reports/coding/runtime-distribution.md`.

## Request

Issue #90 asks for a watchdog that checks on role sessions *while they are
still running* inside the orchestrator, not just after they exit. Issue-89
(merged as PR #91) already added post-exit fail-closed verification —
`classify()` / `fail_closed_downgrade()` in `spawn.py` decide, once a
session's process has exited, whether its result should be trusted (e.g.
downgrading a claimed success to failed if there is no new commit on the
branch). That is the "did it actually finish honestly" half. Issue #90 is
the other half: "is it still alive and behaving, right now, before it
exits." A stuck, silently-failing, or rule-violating session can run for
hours before issue-89's checks ever get a chance to fire, because those
checks only run at `proc.wait()` return. The watchdog closes that gap by
polling observable state during the run and surfacing anomalies early,
without waiting for exit.

Structured heartbeats (a session self-reporting progress via a typed
convention) are explicitly out of scope for this issue and are referenced
here only as a noted future follow-up — the watchdog operates entirely on
signals that already exist today, per the surfaces survey.

## Constraints

The watchdog must be **observe-only**: it may read the live log, the
workspace/worktree, the ledger, and git state, but it must not modify the
role session's own process, its prompt, or its working tree. It does not
send input to the child process and does not touch anything the role
session itself owns while running. This is a deliberate scope line: the
issue asks for detection, not intervention (see Out of scope).

All thresholds proposed below are grounded in
`docs/issue-90/reports/coding/runtime-distribution.md`, which measured
session runtime using a git commit-timestamp clustering fallback because
the authoritative source was unreachable in this workspace: `runs/` is
gitignored by design, and the one populated `runs/ledger.jsonl` found on
this host (`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/ledger.jsonl`)
was denied by the sandbox permission layer for both `Read` and `Bash`
access during that survey. The fallback numbers this proposal relies on:

- median session span ≈ 0 min (majority of sessions are single-commit
  bursts — the visible span is zero even though wall-clock time before
  that commit was nontrivial)
- p90 ≈ 142.6 min
- max ≈ 222.3 min (a 16-commit burst)
- normal in-session inter-commit gap ceiling ≈ 51 min; the break to 80+ min
  gaps marks cross-session idle time, not in-session silence

These are stated as an order-of-magnitude floor, not a precise SLA, and the
runtime-distribution doc itself recommends re-deriving them from
`duration_s` once `runs/ledger.jsonl` is actually reachable. Phase 2 should
treat the thresholds below as provisional pending that re-derivation.

## Anomaly-signal list

Following the prior-art shape named in the issue and reused in the surfaces
survey — systemd `WatchdogSec`, CI no-output stall timeouts, k8s liveness
probes — this is a **multi-signal, per-signal-threshold** design, not one
global timer. Each signal has an asymmetric cost: a missed detection just
delays discovery of a problem that issue-89's post-exit check would likely
also catch eventually, while a false positive interrupts or worries a
reviewer about a session that was fine. Thresholds below are biased toward
fewer false positives, per the runtime-distribution doc's own reasoning.

1. **Log silence.** Detection surface: `<workspace>.session.log` /
   `runs/last-session.log` (path derivation in
   `orchestrate-surfaces.md` "Live log file" section, `spawn.py:1729-1730`);
   every stream-json line is flushed on arrival
   (`spawn.py:1750-1752`), so `mtime` is a true "last event emitted" signal,
   not a buffering artifact. Check: `now - mtime(log_path) > 90 min`.
   Justification: the runtime-distribution doc's in-session gap ceiling is
   ~51 min, and its own recommended threshold derivation
   (`51 + (142.6 - 51) * 0.4 ≈ 88 min`, rounded to 90) sits above that
   ceiling but below the p90 full-session time (142.6 min), so it should not
   fire on a slow-but-alive session while still catching genuinely stuck
   ones before the tail of the distribution.

2. **Background-delegation phrasing.** Detection surface: same live log,
   content-scanned (not stat'd) for stream-json `text`/`tool_use` blocks
   matching patterns like `run_in_background`, "백그라운드", "delegate",
   "background worker" (`orchestrate-surfaces.md` "Signals visible today,"
   second bullet). No structured field exists for this — it is a
   string/regex match over the same transcript already tailed for silence.
   Concretely relevant because the task prompt itself already warns against
   this behavior for issue-scoped spawns (`spawn.py:1683-1686`); the
   watchdog signal exists to catch a session that ignores that warning.
   Threshold: any match triggers an immediate anomaly report (not
   time-windowed) — this is a content match, not a rate.

3. **Denied tool calls.** Detection surface: per-event `permission_denial`
   -shaped lines inline in the live log's stream-json transcript
   (`orchestrate-surfaces.md` "Denied tool calls," per-event granularity).
   Note the aggregate count used by post-exit `classify()`
   (`result.get("permission_denials")`, `spawn.py:1002`, `1806`) is
   populated only on the final `result` event and is **not** available
   mid-run — the watchdog's in-flight count is a parallel, approximate tally
   over the same log, not a call into the exit-time aggregate. Threshold:
   repeated denials in a short window (proposed: 3+ denial-shaped lines
   within any 10-minute scan window) flags an anomaly, since headless mode
   cannot answer a permission prompt and a session stuck retrying denied
   calls will not self-resolve.

4. **No commits late in the run.** Detection surface: `git -C <workspace>
   rev-list --count <before_head>..HEAD` against the workspace path from the
   roster's `work` field, mirroring the `ensure_pushed` ahead-check pattern
   (`spawn.py:1628`) and reusing `before_head` already captured at
   `spawn.py:1718` before the child starts
   (`orchestrate-surfaces.md`, "No commits late in the run"). `elapsed_minutes`
   is already computed identically by `roster_ps()`
   (`(int(time.time()) - e["ts"]) // 60`, `spawn.py:1076`), so the watchdog
   reuses that formula rather than inventing a new one. Threshold: flag when
   `elapsed_minutes > 0.5 * p90_completion` (≈71 min, half of 142.6) **and**
   commit count since `before_head` is zero. The half-p90 fraction is chosen
   because the majority regime is single-commit-and-done in well under that
   window (median span ≈ 0 min), so a session past the halfway point of the
   90th-percentile session with literally no commits is already an outlier
   worth surfacing, not yet worth treating as certainly stuck.

5. **PID liveness vs. hung-on-prompt ambiguity (supporting signal, not a
   standalone trigger).** The surfaces survey flags that `_alive(pid)`
   (`spawn.py:1046-1051`) only confirms the OS pid exists via signal-0 and
   cannot distinguish "actively working" from "hung waiting on a permission
   prompt that will never be answered in headless mode"
   (`orchestrate-surfaces.md`, Gaps section, last bullet). This is why signal
   1 (log silence) and signal 3 (denied calls) are both needed: a hung
   session on a denied prompt will show as PID-alive with a growing denial
   count and then log silence once it gives up retrying — the two signals
   together disambiguate what PID-alive alone cannot.

**Check interval: 10-15 minutes.** Derived in
`runtime-distribution.md` as `min(48.8, 142.6) / 3 ≈ 16 min`, rounded down
for margin — a fraction of both the long-session median (48.8 min) and a
third of the p90 completion time (142.6 min), and comfortably below the
observed median inter-output gap during active sessions (22.5 min), so a
watchdog polling at this cadence should typically see at least one
commit/log-write between checks during a healthy long session without
polling tightly enough to trip on normal short silent stretches between
commits.

## What will be done (phase 2)

Proposed frozen write set, pending approval:

- **`spawn.py`** (same file as the existing post-exit checks, per
  `orchestrate-surfaces.md`'s survey showing the watchdog's ingredients —
  `roster_ps()`, `_alive()`, `before_head`, `ledger_write()` — all already
  live there): add a watchdog check function or a small sibling module
  (e.g. `watchdog.py` next to `spawn.py`) that implements the four signals
  above against the roster (`runs/active.json`) entries, callable either as
  a new `spawn.py watchdog` subcommand alongside the existing `spawn.py ps`,
  or as a periodic call the orchestrator issues itself between other
  actions. Exact shape (subcommand vs. importable function vs. background
  poller) is a phase-2 design decision, not fixed here.
- **`on-the-record/commands/run.md`**: update the procedure text (the same
  file that already tells the orchestrator to check `spawn.py ps` instead of
  trusting "background task memory," `run.md:221-223`) to instruct the
  orchestrator to invoke the watchdog check at the 10-15 minute cadence
  while a role session is running, and how to react to each anomaly class
  (report only — see Out of scope).
- **`test_spawn.py`**: add watchdog unit tests following this repo's
  existing convention of testing `spawn.py` logic directly from a top-level
  `test_spawn.py` (confirmed present at repo root alongside `test_gates.py`
  and `tests/run-orchestrate-tests.sh`) — at minimum a fixture with a stale
  log `mtime` to exercise the silence signal, a fixture log containing
  delegation phrasing, a fixture with synthetic denial lines, and a fixture
  workspace with `before_head` == current `HEAD` past the no-commit
  threshold.
- **`docs/issue-90/reports/coding.md`**: record phase-2 completion (what was
  built, what tests ran, any deviation from this proposal).

## Out of scope

- **Structured heartbeats.** Named explicitly out of scope in the issue;
  referenced here only as a future follow-up that would replace some
  regex/mtime heuristics (signals 1 and 2 above) with a typed field, per the
  Gaps section of `orchestrate-surfaces.md`.
- **Killing or restarting sessions.** The watchdog reports anomalies; it
  does not intervene. Nothing in the issue text asks for automatic
  kill/restart, and doing so would violate the observe-only constraint
  above — an anomaly report is a prompt for the orchestrator (or a human) to
  decide what to do, not an automatic action.
- **Post-exit verification.** Already covered by issue-89/PR-91
  (`classify()`, `fail_closed_downgrade()`). This proposal only concerns
  signals available *before* a session exits; it does not change or
  duplicate the exit-time logic.

## How we'll know it worked

- A simulated stalled-log fixture (a log file whose `mtime` is set > 90 min
  in the past against a still-`RUNNING`-per-`_alive()` roster entry) reliably
  triggers the silence signal in the watchdog's own test suite
  (`test_spawn.py`).
- Fixtures for the other three signals (delegation phrasing in a log,
  synthetic repeated denial lines, a workspace with zero commits past the
  half-p90 threshold) each independently trigger their respective signal and
  no others, confirming the signals are per-condition rather than one
  conflated check.
- In an actual live orchestrator run against a real spawned session, at
  least one anomaly class (most easily log silence, since it requires no
  session misbehavior to test — just a paused session) is observed and
  reported by the watchdog *before* the session exits, not only recoverable
  after the fact from the log — i.e., the check genuinely runs mid-flight,
  not just as a post-hoc log replay.
