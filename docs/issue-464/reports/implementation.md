---
code_under_review: HEAD
loop_state: phase-2-complete
---

# issue-464 implementation record

Phase 2 of proposal `docs/issue-464/proposals/2026-08-08-class-a-orchestrator-loop-wiring.md`,
approved via `APPROVE issue-464/implementation` (single-account mode,
issue comment).

## What was done

1. `spawn.py`: added `_board_wide_sweep(root)`, called from
   `roster_watchdog()` before the empty-roster early return. It lazily
   imports `gates/closure_sweep.py` and `gates/spawn_coverage.py` (avoids
   the module-load-time circular import both have with `spawn`), calls
   `closure_sweep.find_violations(root)` and
   `spawn_coverage.find_uncovered(open_issues, board(root), now)`, prints
   violations/uncovered issues/`gh`-failures the same way existing
   watchdog anomalies print, and folds the count into
   `roster_watchdog()`'s return value (`anomaly_count`). Runs even when
   the live roster is empty.
2. `test_spawn.py`: patched the three pre-existing `roster_watchdog` tests
   to mock `spawn._board_wide_sweep` (isolates roster-only behavior from
   the new board-wide call, no real `gh`). Added 6 new tests: sweep count
   folds into `roster_watchdog`'s return; `_board_wide_sweep` reports/counts
   closure violations, uncovered issues, a clean sweep, and `gh`-failure
   paths (mocked via `sys.modules` patch of `closure_sweep`/`spawn_coverage`,
   matching the boundary those modules' own suites already mock at).
3. `on-the-record/UNENFORCED-CLAUSES.md`: rewrote the #369/#383/#325 rows
   to cite the `roster_watchdog` mechanism; removed the
   `closure_sweep.py`/`spawn_coverage.py` rows from the top (#452
   spec-verdict-extract) table, since their verdict is no longer
   CI-supplement/out-of-scope in the spec.
4. `docs/specs/enforcement-boundary.md`: added a `contract,
   orchestrator-loop` verdict value; retargeted the `closure_sweep.py`/
   `spawn_coverage.py`/`closure-sweep.yml` board-wide rows to it, with a
   pointer back to the issue-464 ADR; left the 2026-08-07 ruling prose
   (lines 25-28, still covering #312/#388/#407) in place and added a
   narrowing note.
5. `gates/test_boundary.py`: tightened
   `t_gate_porting_rows_are_ported_or_justified` to require the matched
   row (or its section heading) to cite one of a named disposition
   vocabulary (`roster_watchdog`, `operator decision`, `Justified`,
   `Deferred`, `CI-supplement`, `n/a (infrastructure)`) instead of
   accepting any non-empty `| #n | ... |` row.

## Why

Per the approved proposal: wire `closure_sweep.find_violations()` and
`spawn_coverage.find_uncovered()` into `spawn.py:roster_watchdog()` so the
class-A board-state-unreachable justification for #369/#383/#325 is
reversed with a real orchestrator-loop mechanism, per the ADR
(`docs/issue-464/decisions/2026-08-08-board-state-into-orchestrator-loop.md`).
`find_violations()` (not `classify()` directly) is called because it
already owns the board-walk-plus-classify pipeline `roster_watchdog` would
otherwise have to duplicate (proposal Rationale).

## Open findings

None open. Resolved during this session:

- resolved_findings: before-landing warrant-hunter (stance 0, bypassable
  gate) found `t_gate_porting_rows_are_ported_or_justified`'s row+heading
  vocabulary check let a filler row pass by matching its section heading
  (`### Justified ...`) alone, regardless of the row's own text — repro:
  replace #407's row text with meaningless filler while leaving it under
  the `Justified` heading, gate still passed. Fixed in `gates/test_boundary.py`:
  dropped the heading fallback and the generic `Justified`/`Deferred`
  vocabulary entries; check now requires the row's own text to cite one
  of a row-specific vocabulary (`roster_watchdog`, `operator decision`,
  `CI-supplement`, `n/a (infrastructure)`, `contract-guard.sh`,
  `not a blocking check`, `nothing to port`, `issue-comment history`) —
  each already present verbatim in the corresponding row's real
  disposition text. Re-verified: `gates/test_boundary.py` 9/9 still
  passes for all 16 `GATE_PORTING_ISSUES`; the #407 filler-repro now
  fails the check as expected.

## Next steps

None — this delivery is scoped to class-A item 1 (#369/#383/#325) only;
class-B rows and #312/#388/#407 are out of scope per the ADR and are
separate follow-up issues (operator's task).

## Resolution path

N/A — no open findings.

## What did not work

None — no attempted approach was undone or replaced during this build.

## Completed items (doc-placement ladder)

- `docs/specs/enforcement-boundary.md` updated (system-design change:
  new `contract, orchestrator-loop` verdict value + retargeted rows).
- `on-the-record/UNENFORCED-CLAUSES.md` updated (derived extract kept in
  sync, verified by `gates/test_boundary.py`'s
  `t_unenforced_clauses_file_matches_spec_exactly`).
- No new env var / dependency / migration introduced by this delivery.

## Test runs

- `python3 test_spawn.py` — 268 tests, OK (includes the 6 new
  `_board_wide_sweep`/`roster_watchdog` tests).
- `python3 gates/test_boundary.py` — 9/9 passed, including the tightened
  `t_gate_porting_rows_are_ported_or_justified` (still green for all 16
  `GATE_PORTING_ISSUES`) and `t_unenforced_clauses_file_matches_spec_exactly`.
