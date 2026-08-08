---
code_under_review: HEAD
loop_state: awaiting-verify
---

## What was done

Built `docs/issue-492/proposals/2026-08-08-implement-reconciliation-step.md`
verbatim (approved proposal, step 2 of issue-492):

- `reconcile(expected: dict, observed: dict) -> list[dict]` in `spawn.py`,
  placed right after `fail_closed_downgrade` (near `session_end_verdict`).
  Pure function, no I/O. Divergence rules, in order: `session_verdict ==
  "crashed"` → `respawn`; `session_verdict == "stalled"` → `resume-watch`;
  `expects_pr` true, `pr_number is None`, `session_verdict != "in-progress"`
  → `respawn`; `session_verdict is None` with a non-`None` `loop_state`
  (inconsistent input) → `manual-review`; `session_verdict` a value outside
  the known set (`normal`/`crashed`/`stalled`/`in-progress`) → `manual-review`;
  otherwise empty list (clean).
- `_build_expected(entry)` and `_build_observed(root, entry)` helpers wiring
  a roster entry into `reconcile()`'s input shape, reusing
  `session_end_verdict`, `_pr_open_or_merged_for_branch`, `board`, and
  `_is_new_commit` — no new `gh` calls.
- `roster_register()` call site (`spawn.py`, inside `_spawn_one`): added
  `"expects_pr": issue is not None` to the entry dict.
- CLI verb `spawn.py reconcile [--issue N]` (new `roster_reconcile()`
  function, dispatched in `main()` alongside the `watchdog` branch, no
  `require_board`/`require_no_repo_config`/`require_doctor` guards —
  mirrors `watchdog`'s dispatch, not `drive`'s). Prints one line per
  divergence; exit code is the divergence count (0 = clean).
- `roster_watchdog()`: inside its existing per-entry loop, calls
  `reconcile()` once per scanned entry, prints divergences, folds the
  count into `anomaly_count`. No new poller — rides the existing tick.
- `drive(cwd, unattended, limit)`: replaced the unconditional no-op with
  reading the roster, calling `reconcile()` per entry, and printing each
  divergence with its `next_action`. Still returns 0 unconditionally and
  never spawns or picks a role — the #120 "drive never auto-picks" contract
  is preserved by construction (no code path calls `spawn_cmd`/`_spawn_one`
  from `drive()`).
- Tests in `test_spawn.py` (`Reconcile` class): unit tests for each
  divergence rule (crashed→respawn, stalled→resume-watch, expects_pr+no
  PR+not-in-progress→respawn, expects_pr+no PR+in-progress→clean,
  clean/empty case, inconsistent-input→manual-review), plus the two
  fixture tests reproducing the issue's own acceptance checks: SIGKILL
  (`session_end_verdict` with `alive_fn` returning `False` and no
  session-end event → `crashed` → `reconcile()` → `respawn`, not silence)
  and vanish-without-push (`expects_pr=True`, `pr_number=None`,
  `session_verdict="crashed"` → `reconcile()` names the divergence with
  `next_action=respawn`).
- `gates/test_boundary.py`: one manifest row per delivered piece
  (`reconcile()`, the `reconcile` CLI verb, the `drive()` edit) via
  `_ISSUE_492_RECONCILE_CITATIONS` + `t_issue_492_reconcile_pieces_present`,
  following the existing citations-dict + presence-check pattern already
  used by `_ISSUE_467_BATCH_A_CITATIONS`/`_ISSUE_467_BATCH_C_CITATIONS` in
  that file.

## Why

Per the approved proposal's Rationale: the ADR (#493) already closed the
"where does divergence detection live" and "no second poller" questions;
the one implementation-level choice left open — where in `drive()` the
reconciled state gets consumed — is resolved as print-then-stop (not
auto-respawn), preserving issue #120's "drive never picks a role" contract
while satisfying the ADR's explicit `drive()` write-surface requirement.

## Upstream / basis

`docs/issue-492/proposals/2026-08-08-implement-reconciliation-step.md`
(approved proposal, verbatim spec for this step); ADR
`docs/issue-492/decisions/2026-08-08-reconciliation-step-for-supervision.md`;
survey `docs/issue-492/reports/implementation/survey.md` (exact line
numbers and existing-function inventory used to wire `_build_expected`/
`_build_observed`).

## What did not work

None.

## Rationale for deviations

One deviation from the letter of the task's stated write-set: it named
`test/test_spawn.py`, but the repo's real, sole test file for `spawn.py`
is `test_spawn.py` at repo root — confirmed via `git log -- test_spawn.py`,
which shows every prior phase-2 delivery (issue-488, issue-466, etc.)
editing that exact path, and via `git log --all -- 'test/test_spawn.py'`,
which returns nothing: that path has never existed in this repo's history.
`test/` (the directory) holds a different, smaller, unrelated set of files
(`test/test_portability_audit_table.py`, `test/test_silent_failure_repros.py`,
a shell script) — not a plausible sibling location for `spawn.py` coverage.
Tests for `reconcile()` were added to `test_spawn.py` instead, in the same
`Reconcile` `unittest.TestCase` class, following every existing convention
this proposal asked to match (fixture patterns from `SessionEndVerdict`,
imports, class layout). No other write-set element was touched outside
what the proposal named.

## Next steps

Execution-observation instrumentation (issue-492's step 3, separate role,
out of scope here) — or a verify pass on this implementation per contract
v3 s19's phase-2 flow, whichever the orchestrator schedules first.

## Resolution path

None open.

## Open findings

None.
