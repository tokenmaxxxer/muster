files:
- spawn.py
- test_spawn.py
- docs/issue-327/decisions/watchdog-exit-code.md

## Request

Deadlock, idle waiting, and unnecessary work are user-facing defects and
today nothing treats them as a defect: existing checks only ever ask
whether output was correct, never whether it was worth the wait. The
issue asks for a name and a measurement for this before any deeper fix,
with acceptance naming an executable artifact that fails on regression
(per #310).

## Constraints

- Must not duplicate the existing detection logic. `spawn.py` already
  names and computes idle waiting (`session_end_verdict`'s `stalled`),
  unnecessary work (`classify`'s `silent-failure`, `watchdog_check_one`'s
  `no-commits-late`), and deadlock-shaped blocking
  (`watchdog_check_one`'s `denied-tool-calls` and
  `background-delegation-phrasing`) — see survey.md. The fix must consume
  these, not re-derive them.
- `roster_watchdog`'s `auto_respawn=True` behavior (crashed-only
  respawn/cap-comment) must be unchanged — this proposal only changes the
  return value, never the side effects the function already performs.
- `watchdog_check_one` must stay observe-only per its docstring contract
  (issue #90 phase-2): it still must not fix, kill, or touch the sessions
  it inspects. Only the caller's exit code changes.
- The change must be visible to a caller that only reads the process exit
  code (the orchestrator's periodic `spawn.py watchdog` invocation, or a
  CI job) without requiring stdout parsing.

## Rationale

**Considered: build a new idle/deadlock detector with per-step-kind
tolerance thresholds**, matching the issue's own framing ("what is a
tolerable wait for each kind of step"). Rejected for this proposal: the
issue itself defers this — it asks for a name and measurement "before it
can have a fix," and per-step-kind tolerance calibration is an open
question the issue does not answer (no step taxonomy or tolerance table
exists anywhere in the repo to build from). Inventing thresholds now
would be guessing at a design the operator hasn't specified, and would
make this proposal's write set balloon past a single reviewable unit.
This proposal instead wires the coarser, already-named, already-computed
binary signal (anomaly / no anomaly, at the existing per-signal
thresholds) to something that fails — which is itself a complete,
independently valuable step, and does not foreclose a later per-kind
calibration proposal built on top of it.

**Considered: add a brand-new `gates/` CI-style script that re-reads
`runs/roster.json` and re-implements the four anomaly signals.** Rejected:
`watchdog_check_one` already implements and unit-tests all four signals;
a second implementation in `gates/` would drift from it the same way
#140→#147 drifted (per #330's own example) and would need to be kept in
sync with `WATCHDOG_SILENCE_MIN`/`WATCHDOG_DENIAL_THRESHOLD`/
`WATCHDOG_NO_COMMIT_MIN` by hand. Changing `roster_watchdog`'s return
value is a one-line-of-behavior change directly on the existing,
tested detector.

## What will be done

- Change `roster_watchdog()` (`spawn.py:1542`) to return the count of
  roster entries that produced at least one anomaly (0 when the scan is
  clean, unchanged from today), instead of unconditionally returning 0.
  `auto_respawn` behavior and all printed output stay exactly as they
  are today — only the return value changes.
- Because `roster_watchdog`'s return value is passed straight through as
  the `spawn.py watchdog` CLI's process exit code (`spawn.py:2438`), this
  makes "an idle-waiting, deadlock-shaped, or unnecessary-work session was
  found" a non-zero exit code — an executable artifact a CI job or the
  orchestrator's periodic call can fail on, per #310's acceptance bar.
- Add `test_spawn.py` coverage: `roster_watchdog()` returns 0 on a roster
  with no anomalies (already covered by
  `test_roster_watchdog_reports_no_anomaly_on_empty_roster`, extend with a
  non-empty, anomaly-free roster case), and returns a non-zero count when
  at least one live entry trips a `watchdog_check_one` signal (log-silence
  case, reusing the fixture shape from
  `test_unmatched_alive_stale_log_is_stalled`).
- Record the public-signature change (`roster_watchdog`'s return value now
  carries meaning it did not carry before) in
  `docs/issue-327/decisions/watchdog-exit-code.md`, per the doctrine
  ladder for a changed public signature.

## Out of scope

- Per-step-kind idle/wait tolerance calibration (deferred by the issue
  itself — see Rationale).
- Any change to `watchdog_check_one`'s four signals, their thresholds, or
  what counts as an anomaly — this proposal changes only what the caller
  does with an anomaly that already exists.
- Wiring `spawn.py watchdog` into an actual CI job or a specific
  orchestrator retry/alert policy on non-zero exit — that consumption
  decision belongs to whoever operates the schedule, and is a policy
  choice outside a single issue's write set.
- `#325`'s gap (issues that never spawn a session at all) and `#326`'s
  gap (interrupted work hiding instead of prompting resumption) — both
  are different failure points from an existing session idling or
  spinning, per the survey's boundary check.

## How you'll know it worked

- `python3 test_spawn.py` passes, including the two new/extended cases:
  a clean roster still returns 0, and a roster containing a `stalled`
  (log-silence) entry returns non-zero from `roster_watchdog()`.
- Running `spawn.py watchdog` against a roster with a known stale-log
  entry exits non-zero (`echo $?` after the call); against a clean
  roster it exits 0 — this is the executable artifact that fails on
  regression: reverting the return-value change makes the non-zero-exit
  test fail.
