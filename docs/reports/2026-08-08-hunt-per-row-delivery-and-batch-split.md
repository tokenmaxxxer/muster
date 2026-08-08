
## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — the proposal names `gates/test_boundary.py` as the "new" disposition-table check to build, but that exact path already exists as a live, unrelated, currently-passing gate for issue-441's enforcement-boundary spec; landing the proposal as specified silently collides with/overwrites it.
Kind: design-error
Seed: docs/issue-467/proposals/2026-08-08-per-row-delivery-and-batch-split.md (rows for #362, #390 name `gates/test_boundary.py` as the new disposition-table check; "Out of scope" and closing paragraph repeat the same path as the not-yet-built deliverable, "built once, in whichever batch lands first")
cap_seconds: 120
tier: default
diff_stat_lines: 187
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:02:00Z

### Reproduce
```
$ ls gates/test_boundary.py
gates/test_boundary.py
$ python3 gates/test_boundary.py
ok - t_a_new_unrecorded_module_is_caught
ok - t_all_gates_modules_recorded
ok - t_gate_porting_rows_are_ported_or_justified
ok - t_run_md_references_unenforced_clauses
ok - t_spec_records_the_operator_boundary_decision
ok - t_unenforced_clauses_file_matches_spec_exactly
ok - t_ci_supplement_or_out_of_scope_rows_are_cross_referenced
ok - t_every_deleted_workflow_has_migration_row
ok - t_workflows_dir_absent_or_empty
9/9 passed
$ grep -n "gates/test_boundary.py" docs/issue-467/proposals/2026-08-08-per-row-delivery-and-batch-split.md
```
`gates/test_boundary.py`'s docstring: "issue-441 — 계약/집행 경계 게이트: `docs/specs/enforcement-boundary.md` 가 `gates/*.py`, ... 를 전부 덮는지 도출해서 검사한다" — this is issue-441's boundary-coverage gate, not a 13-row #N-tag disposition table.

### Expected
The proposal should name a path that does not already exist for an unrelated purpose (e.g. `gates/test_disposition_table.py`), or explicitly state how the new disposition-table check coexists with (is added as new functions inside, alongside the existing #441 checks, in) the current `gates/test_boundary.py` without displacing `t_all_gates_modules_recorded` and its siblings. As written, "built once, in whichever batch lands first" gives the first implementer no instruction not to clobber the existing file, and no reviewer signal distinguishes "extended #441's file" from "silently replaced it."

## before-landing — docs-only, no before-landing dispatch

proposal: docs/issue-467/proposals/2026-08-08-per-row-delivery-and-batch-split.md

Phase-2 landing's write set (`git diff --stat` against the proposal-time
base) is entirely under `docs/` — the ADR
(`docs/issue-467/decisions/2026-08-08-per-row-delivery-and-batch-split.md`),
the architecture report
(`docs/issue-467/reports/architecture.md`), and this proposal's own
status/scouting-wording/what-did-not-work updates. Per the docs-only
fast path, the before-landing hunter dispatch is skipped.
