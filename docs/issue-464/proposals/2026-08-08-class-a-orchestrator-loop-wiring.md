---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - on-the-record/UNENFORCED-CLAUSES.md
  - docs/specs/enforcement-boundary.md
  - gates/test_boundary.py
  - docs/issue-464/reports/implementation.md
---

## Request

issue-464 step 2 (implementation), scoped to the ADR's follow-up item 1
(class A only, per the operator's step-2 instruction that class-B rows are
separate follow-up issues): wire `gates/closure_sweep.classify()` and
`gates/spawn_coverage.find_uncovered()` into the `spawn.py:roster_watchdog()`
tick (closing #369/#383/#325's board-state-unreachable justification),
update `on-the-record/UNENFORCED-CLAUSES.md` and
`docs/specs/enforcement-boundary.md`'s verdicts for those three rows, and
tighten `gates/test_boundary.py`'s `t_gate_porting_rows_are_ported_or_justified`
per the hunt finding already recorded in the ADR's proposal (it currently
accepts any non-empty row text as "justified").

## Constraints

- Per the ADR (`docs/issue-464/decisions/2026-08-08-board-state-into-orchestrator-loop.md`):
  only #369/#383/#325 are reversed; #312/#388/#407 stay re-confirmed drops
  and are not touched by this session's code changes.
- `roster_watchdog` stays observe-only (spawn.py:1636-1637 contract): the
  new sweep call reports anomalies the same way existing ones do
  (print + counted into `anomaly_count`), never auto-closes or auto-fixes
  anything.
- The sweep must run even on a tick with an empty live roster — survey
  found `roster_watchdog`'s early return (spawn.py:1652-1654) would
  otherwise skip a board-wide check exactly when a stale board is likely to
  go unnoticed longest.
- `find_violations()`/`find_uncovered()` make real `gh` calls; tests must
  not depend on network access — mock at the same boundary
  `closure_sweep.py`'s/`spawn_coverage.py`'s own test suites already mock
  at (survey: no existing test currently exercises this from
  `roster_watchdog`, so these are new tests, not edits to existing ones).
- `gates/test_boundary.py`'s tightened check must still pass for all 16
  `GATE_PORTING_ISSUES` rows, not just the three this session rewrites —
  the other 13 rows' existing verdict text must already fall into one of
  the vocabulary buckets the tightened check accepts, or the check itself
  is broken for rows this session does not touch.

## Rationale

Considered calling `gates/closure_sweep.classify()` directly from
`roster_watchdog`, matching the ADR's own follow-up wording ("wire
`gates/closure_sweep.classify()` ... into the watchdog tick"). Rejected in
favor of calling `gates/closure_sweep.find_violations()` instead:
`classify()` is a per-subject pure judgment that takes already-resolved
issue/PR state as arguments; to feed it, `roster_watchdog` would have to
re-walk `spawn.board()` and re-issue the same `gh issue view`/`gh pr view`
calls `find_violations()` already makes internally. Calling
`find_violations()` reuses that existing board-walk-plus-classify pipeline
(including its `skips` list for unresolvable subjects) instead of
duplicating it inside `spawn.py`; `classify()` remains the pure unit
`find_violations()` and its own tests already build on, unchanged.

## What will be done

1. In `spawn.py:roster_watchdog()`, before the empty-roster early return,
   call `closure_sweep.find_violations(root)` and
   `spawn_coverage.find_uncovered(open_issues, board, now)` (with the `gh
   issue list` fetch `spawn_coverage._list_open_issues()` already wraps),
   print any violations/uncovered issues the same way existing anomaly
   output is printed, and fold their count into the return value
   (`anomaly_count`) so `spawn.py watchdog`'s exit code reflects board-wide
   findings alongside per-session ones. `gh`-call failure (skips list
   non-empty, or `_list_open_issues` returning `None`) is reported, not
   silently treated as "clean."
2. Add tests to `test_spawn.py` covering: violations found -> reported and
   counted; uncovered issues found -> reported and counted; both clean ->
   unchanged behavior; `gh`-failure paths reported rather than swallowed.
   Mock the `gh`-calling functions (`find_violations`,
   `_list_open_issues`) rather than shelling out.
3. Rewrite `on-the-record/UNENFORCED-CLAUSES.md` rows for #369, #383, #325
   to cite the `roster_watchdog` mechanism instead of "out of scope."
4. Rewrite `docs/specs/enforcement-boundary.md`'s `closure_sweep.py` and
   `spawn_coverage.py` board-wide-case rows (and the `closure-sweep.yml`
   row) to describe the orchestrator-tick call site; leave the general
   2026-08-07-ruling prose (lines 25-26, 91, 104) in place but add a
   pointer to this ADR for the narrowed #369/#383/#325 rows, since the
   ADR explicitly does not reverse #312/#388/#407.
5. Tighten `gates/test_boundary.py`'s `t_gate_porting_rows_are_ported_or_justified`
   to check the located row's verdict text against a named vocabulary
   (mechanism citation naming `roster_watchdog`, `out of scope — operator
   decision`, or another disposition keyword already in use in
   `UNENFORCED-CLAUSES.md`) instead of accepting any non-empty
   `| #n | ... |` row.
6. Write the phase-2 record (`docs/issue-464/reports/implementation.md`),
   after Approve, per contract v3 s19.

## Out of scope

- All class-B (#444 audit) rows and their dispositions — separate
  follow-up issues per the operator's step-2 instruction.
- #312/#388/#407 — re-confirmed drops per the ADR, not touched.
- Any change to `roster_watchdog`'s `auto_respawn` behavior or its
  per-session anomaly signals (signals 1-4) — this proposal only adds the
  board-wide sweep call.
- Filing the follow-up issues the ADR lists for class-B/other class-A
  rows — operator's task per the ADR.

## How you'll know it worked

- `python3 test_spawn.py` passes, including the new
  closure/coverage-sweep tests.
- `python3 gates/test_boundary.py` passes, including the tightened
  `t_gate_porting_rows_are_ported_or_justified` (still green for all 16
  `GATE_PORTING_ISSUES`, not just the three rewritten here).
- `on-the-record/UNENFORCED-CLAUSES.md` and
  `docs/specs/enforcement-boundary.md` no longer describe #369/#383/#325's
  board-wide case as out of scope; both cite the `roster_watchdog`
  mechanism.
- `spawn.py watchdog`'s exit code is non-zero when a closure/coverage
  violation exists even with an empty live roster.

## What did not work

(none yet — phase 2 not started)
