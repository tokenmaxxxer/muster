# Proposal: issue-35 — review of the merged MUSTER_ROLE_MODEL strip fix

## Spec audited against
Issue #35 text (verbatim fix instruction), not the coding proposal or
report prose.

## code_under_review
`36d75c5c5dfe5f91d176ba59cac8bc3de48ccc20` (PR #47, merged to `main` at
`7f30bf0`).

## Requirement list (from docs/issue-35/reports/review/survey.md)
- R1: strip `MUSTER_ROLE_MODEL` before the truthiness check in `spawn_cmd`
- R2: whitespace-only value behaves like unset (no `--model` in argv)
- R3: empty/unset behavior unchanged (non-regression)
- R4: test added next to existing `SpawnCmd` cases

## closed_checks: cite vs re-derive
- The coding report's single closed_checks entry bundles `spawn_cmd` and
  `--dry-run` together and only asserts the behavior half. Will re-derive
  R1–R4 independently from the diff and by running the test suite myself
  rather than citing it.

## What will be done (phase 2, pending human Approve)
- Read `spawn.py` at the two touched sites (spawn_cmd ~1241, `--dry-run`
  branch ~1377) and `test_spawn.py`'s new/changed tests directly against
  R1–R4.
- Run `python3 -m pytest test_spawn.py -q` to independently confirm the
  42/42 claim rather than trust the coding report's number.
- Assign one verdict per requirement (Present/Surface/Absent/
  Incorrect/Unverifiable) with file:line evidence.
- Flag the unrequested `--dry-run`/`_dry_run_output` site as
  out-of-issue-scope addition (not a defect — note it as observed scope
  beyond R1–R4, addressed to no one, informational).
- Write `docs/issue-35/reports/review.md` as first act of phase 2 with
  loop_state updated at each transition.

## Out of scope
- Judging code style/quality beyond the four requirements.
- Any fix or suggested patch — findings are addressed to the owning role
  only.

## How it will be verified
- Running the existing test suite myself (`python3 -m pytest test_spawn.py -q`).
- Direct line-level inspection of `spawn.py` diff hunks for R1–R3.
