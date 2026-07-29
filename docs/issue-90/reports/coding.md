# Issue #90 — Coding Record

loop_state: phase2-complete

code_under_review: e65353f

## Upstream basis

- Issue #90 (mid-run watchdog for live role sessions).
- Phase-1 proposal: `docs/issue-90/proposals/coding-watchdog.md`.
- Phase-1 surveys: `docs/issue-90/reports/coding/orchestrate-surfaces.md`,
  `docs/issue-90/reports/coding/runtime-distribution.md`.
- Approval: PR #92 phase-1 proposal, confirmed approved per role-handoff
  contract v3 s19 before phase-2 write-set work started.

## Why

Execute the approved proposal: give the orchestrator an observe-only way
to check on a role session while it is still running, not only after it
exits (issue-89/PR-91 already covers the post-exit half).

## What was done

In `spawn.py`:

- Added `watchdog_check_one(key, entry, now=None, state=None)`, a pure-ish
  function that reads (never writes to) a roster entry's live log and
  workspace git state and returns a list of anomaly strings. Implements
  all four signals from the proposal:
  1. Log silence: `now - mtime(log_path) > WATCHDOG_SILENCE_MIN` (90 min).
  2. Background-delegation phrasing: regex match
     (`run_in_background|백그라운드|delegate|background worker`) over
     newly-appended log content only.
  3. Denied tool calls: regex match (`permission_denial|denied`) counted
     over newly-appended log content; fires at `WATCHDOG_DENIAL_THRESHOLD`
     (3) or more in one scan.
  4. No commits late in run: `elapsed_minutes > WATCHDOG_NO_COMMIT_MIN`
     (71, half the p90 completion time from the runtime-distribution doc)
     and `git rev-list --count <before_head>..HEAD` == 0.
- Added `roster_watchdog()` — the `spawn.py watchdog` subcommand — which
  scans every alive roster entry once, prints per-session anomaly reports
  or "정상", and persists scan offsets to `runs/watchdog_state.json` (a
  gitignored `runs/` file, same convention as `ledger.jsonl`) so repeated
  polls don't re-count log content already scanned.
- `roster_register()` now also stores `before_head` (the pre-spawn HEAD
  already captured for the post-exit check) in each roster entry so signal
  4 has the git-state baseline it needs, without duplicating the capture.
- Wired the `watchdog` subcommand into `main()` alongside the existing
  `ps`/`kill`/`clean` subcommands.

In `on-the-record/commands/run.md`: added an instruction (next to the
existing `spawn.py ps` guidance) telling the orchestrator to run
`spawn.py watchdog` every 10-15 minutes while a role session is live, and
to report — not act on — any anomaly it surfaces.

In `test_spawn.py`: added a `Watchdog` test class covering each signal
firing and not-firing, the offset-based dedup behavior (a denial count
already reported in one scan isn't re-reported on the next scan of the
same log content), and a `roster_watchdog()` smoke test on an empty
roster.

## What did not work

- First denial-detection regex attempt
  (`r'"permission_denial|permission_denials|denied'`) required a leading
  literal `"` before `permission_denial` and a trailing `s` for the plural
  form, so it silently failed to match a plain `permission_denial` line in
  the fixture log (caught by the corresponding test failing on first run,
  not by inspection). Replaced with `r"permission_denial|denied"`, which
  matches both the exact-field name and free-text "denied" mentions in the
  log content. No production code shipped in the broken state — the test
  suite caught it before commit.

## Open findings

None raised against this work.

## Next steps

None — proposal scope executed in full: `spawn.py`, `on-the-record/commands/run.md`,
`test_spawn.py`, and this record are exactly the frozen write set named in
the phase-1 proposal. `.env.example` was not touched — the proposal
introduces no new environment variables.

## Open-finding resolution path

No open findings currently block progress. Should a reviewer raise a
blocking finding, it will be addressed and logged here as
resolved_findings before further commits, per the coding-progress gate.

## resolved_findings

(none)

## Phase-1 hunt findings folded in

The phase-1 coding session's warrant-hunter ran a hunt
("after-proposal — stance: grounding errors") against the three phase-1
docs before this record existed, and left its finding uncommitted at
`docs/reports/2026-07-29-hunt-coding-watchdog.md`. That file is now
removed as a stray untracked file; its one check is folded into
`closed_checks` below (see the `hunt-coding-watchdog phase-1` entry) —
its `code_under_review` is left as the phase-1 proposal commit (5558814),
the sha it was actually run against, not this phase-2 sha, since it never
touched the phase-2 code.

## Phase-2 pre-completion warrant hunt

`coding:warrant-hunter` ran against `e65353f` (this phase-2 sha) and
returned one finding: `watchdog_state.json`'s per-key byte offset is
never invalidated across a respawn of the same `issue/role`, while the
live log file at that same deterministic path is truncated
(`open(log_path, "w", ...)` in the spawn loop) on respawn. Since the new
session's log starts shorter than the stale offset, `watchdog_check_one`
would seek past the entire new log and read nothing, silently disabling
signals 2 (background-delegation phrasing) and 3 (denied tool calls)
for the new session until its log content regrew past the old offset.

Fixed in `spawn.py`'s `watchdog_check_one`: before seeking, compare the
log file's current size to the stored offset; if the log is shorter than
the offset (truncated/rotated since the last scan), read from 0 instead
of the stale offset. Added
`test_stale_offset_survives_log_truncation_on_respawn` to
`test_spawn.Watchdog` reproducing the respawn-truncation sequence
(denial fires pre-truncation, log is truncated to simulate respawn,
denial must fire again on the very next scan) — it failed against the
pre-fix code and passes after the fix.

## closed_checks

closed_checks:
  - check: hunt-coding-watchdog phase-1 — after-proposal grounding-errors
      stance (spawn.py:line citations, threshold arithmetic in
      orchestrate-surfaces.md / runtime-distribution.md / coding-watchdog.md)
    code_sha: 5558814
    result: NO FINDING — every spawn.py line citation and every arithmetic
      derivation (median/p90/interval/silence-threshold/signal-4-threshold)
      checked and matched exactly; folded in from
      docs/reports/2026-07-29-hunt-coding-watchdog.md (now removed as a
      stray file, content preserved here)
  - check: python3 -m unittest test_spawn -v
    code_sha: e65353f
    result: pass — 81 tests, 0 failures (includes 10 new Watchdog tests)
  - check: python3 -m unittest test_spawn.Watchdog -v
    code_sha: e65353f
    result: pass — 10/10 (silence fire/no-fire, delegation fire/no-fire,
      denial fire/no-fire, offset-dedup, no-commits-late fire/no-fire,
      empty-roster smoke)
  - check: coding:warrant-hunter phase-2 pre-completion hunt
    code_sha: e65353f
    result: FINDING (fixed) — stale watchdog_state.json offset survives
      log truncation on respawn, silently disabling signals 2/3 for the
      new session; fixed by resetting the read offset to 0 when the log
      is shorter than the stored offset, covered by
      test_stale_offset_survives_log_truncation_on_respawn
  - check: python3 -m unittest test_spawn -v (post-fix)
    code_sha: e65353f (fix commit)
    result: pass — 82 tests, 0 failures (includes the new truncation
      test)
