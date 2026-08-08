---
proposal: docs/issue-464/proposals/2026-08-08-class-a-orchestrator-loop-wiring.md
---

# Hunt record — class-a-orchestrator-loop-wiring

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: NO FINDING
Seed: docs/issue-464/proposals/2026-08-08-class-a-orchestrator-loop-wiring.md (frozen write set: spawn.py, test_spawn.py, on-the-record/UNENFORCED-CLAUSES.md, docs/specs/enforcement-boundary.md, gates/test_boundary.py, docs/issue-464/reports/implementation.md)
cap_seconds: 120
tier: default
diff_stat_lines: ~270 (docs-only, phase-1 proposal)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:18:00Z

Checked and ruled out (each reproduced, not just reasoned about):

- Circular import spawn.py <-> gates/closure_sweep.py/gates/spawn_coverage.py
  (both do top-level `import spawn`). Reproduced by copying spawn.py plus
  all gates/*.py into a scratch dir, injecting a top-level
  `import closure_sweep; import spawn_coverage` into the copied spawn.py,
  and running `python3 -c "import spawn"` — it succeeds (`closure_sweep.spawn
  is spawn` True) because neither module touches the other's attributes at
  import time, only inside function bodies. No new import-order file needed.
- `gates/test_boundary_workflow_migration.py` (not in the write set) reads
  `docs/specs/enforcement-boundary.md`'s `closure-sweep.yml` migration row
  and cross-checks `on-the-record/UNENFORCED-CLAUSES.md`. Ran
  `python3 gates/test_boundary_workflow_migration.py` (3/3 pass) and traced
  `t_ci_supplement_or_out_of_scope_rows_are_cross_referenced`: it only
  asserts when the row's verdict/replacement text contains "CI-supplement"
  or "out of scope"; the proposal's planned rewrite of that row (dropping
  "out of scope — operator decision") makes the check a no-op for that row,
  not a failure. No edit to this file is required.
- No `.github/workflows/*.yml` exists at all (issue-460 retired them) —
  `find .github -iname '*.yml'` returns nothing — so no CI config needs
  touching.
- `docs/specs/reconciled-index.md` (hash-index gate `gates/spec_index.py`)
  does not index `UNENFORCED-CLAUSES.md` or `enforcement-boundary.md`
  (grep for both names returns nothing) — no hash to regenerate outside the
  listed files.
- No test file besides `test_spawn.py` references `roster_watchdog`
  (grepped `test*.py`, `tests/*.py`, `gates/test_*.py`); no
  `gates/test_spawn_coverage.py` exists at all currently, so there is no
  pre-existing sibling suite this proposal silently leaves stale.
- Other `gates/*.py` importing `spawn` (`flows.py`, `ci.py`,
  `test_closure_sweep.py`, `test_closes_gate_ci.py`) do not reference
  `roster_watchdog`, `find_violations`, or `find_uncovered`, so they are
  unaffected by the new call site.

I did find that `gates/test_boundary.py`'s existing
`t_unenforced_clauses_file_matches_spec_exactly` (equal-set check between
`enforcement-boundary.md` verdicts and `UNENFORCED-CLAUSES.md` mechanism
rows) will likely break once `enforcement-boundary.md`'s `closure_sweep.py`/
`spawn_coverage.py` mechanism rows (lines 40/43) drop "out of scope —
operator decision" per item 4, because the proposal's item 3 only rewrites
the *issue-number* rows (#369/#383/#325) in `UNENFORCED-CLAUSES.md`, not the
*mechanism-name* rows (lines 15/17) that mirror those same verdicts. But
both files on both sides of that mismatch (`gates/test_boundary.py`,
`on-the-record/UNENFORCED-CLAUSES.md`, `docs/specs/enforcement-boundary.md`)
are already in the frozen write set — this is an incomplete edit plan
inside listed files, not a path outside the write set, so it does not
satisfy this stance's bar.
