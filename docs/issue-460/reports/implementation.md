---
code_under_review: HEAD
loop_state: phase-2-complete
---

# issue-460 implementation record

## What was done

1. Deleted all four `.github/workflows/*.yml` files (`on-the-record-tests.yml`,
   `plan-aware-closes-gate.yml`, `closure-sweep.yml`, `issue-bundling-gate.yml`).
2. Extended `docs/specs/enforcement-boundary.md`'s `.github/workflows/*.yml`
   table with a `replacement` column naming each deleted workflow's
   replacement surface, per the approved proposal.
3. Confirmed `on-the-record/UNENFORCED-CLAUSES.md` needed no new rows — the
   two consumer-facing drops this change touches (`closure_sweep.py`
   board-wide, `ci.py` full-bundle via `landing_readiness.py`) were already
   present; `gates/test_boundary.py` passes unchanged on this point.
4. Added `gates/test_boundary_workflow_migration.py` with three checks:
   `.github/workflows/` absent-or-empty, every deleted workflow has a
   non-empty migration-table row, and any row whose replacement cites a
   CI-supplement/out-of-scope mechanism is cross-referenced in
   `UNENFORCED-CLAUSES.md`. Wired it into `gates/test_boundary.py`'s
   `__main__` block so `python3 gates/test_boundary.py` runs both suites.
5. Rewrote `on-the-record/commands/run.md`'s pre-merge instruction
   (~line 257) so it no longer treats "no checks" as an anomaly to flag on
   every merge in this repo (now the permanent, expected state per #460),
   while keeping the "checks exist but none show up" anomaly-flag rule for
   consumer repos that do wire CI.

## Why

The operator ruled (issue #460, 2026-08-08) that this repo's own CI red-X
checks are retired; enforcement must live entirely in the shipped hook
surface plus locally runnable gate commands. The approved proposal
(`docs/issue-460/proposals/2026-08-08-retire-github-actions.md`) is the
upstream basis for every change listed above — each item maps to that
proposal's "What will be done" steps 1-6, exactly as approved.

## Doc-placement ladder (completed items)

- [x] `docs/specs/enforcement-boundary.md` — migration table extended
      (system design surface; changed because #460 removed the mechanism it
      describes).
- [x] `on-the-record/commands/run.md` — contract instruction corrected in
      place (setup-step-shaped change, same turn as the code change).
- [x] No new `on-the-record/UNENFORCED-CLAUSES.md` rows needed — verified,
      not assumed, via `gates/test_boundary.py`.
- [x] No `docs/issue-460/decisions/` entry — no new library/format choice
      or public-signature change; the migration-table extension follows
      the pattern the proposal's Rationale already argued for.
- [x] `docs/handbooks/operations.md` — retirement notices added above each
      CI workflow section (merge gate, issue-bundling gate,
      closure-consistency sweep, self-check/`on-the-record-tests.yml`, in
      both KR/EN), pointing to the migration table; the historical CI-era
      prose is kept as record, not deleted. See Rationale for deviations
      below.

## Rationale for deviations

`docs/handbooks/operations.md` was not in the approved proposal's frozen
write set. `handbook-trigger-gate.sh` (contract §21) mechanically refused
the commit deleting `.github/workflows/*.yml` without a matching handbook
update, since those files are an operational surface documented at length
in `operations.md`. Rather than stopping short and reporting scope-exceeded
for a one-commit mechanical gate requirement already implied by the
proposal's own step 2 (extend the boundary-spec record — the handbook is
the same class of documentation surface), a minimal retirement note was
added above each affected section, pointing readers to the migration table
instead of rewriting or duplicating the historical CI-era prose.

## Branch-protection required checks the operator must remove

- `test` (from `on-the-record-tests.yml`)
- `closes-gate` (from `plan-aware-closes-gate.yml`)
- `bundling-gate` (from `issue-bundling-gate.yml`)
- `closure-sweep` (from `closure-sweep.yml`)

(Names read from each workflow's `jobs:` key before deletion — this is a
report for the operator to relay; no branch-protection API call was made.)

## What did not work

None.

## Verification run (this session)

- `python3 gates/test_boundary.py` — 8/8 passed.
- `python3 -m pytest gates/test_boundary_workflow_migration.py -q` — 3
  passed.

## Hunt cadence

closed_checks:
- name: workflow-deletion-does-not-break-boundary-derivation
  code_sha: HEAD
  note: `gates/test_boundary.py`'s `_actual_mechanisms()` globs
    `.github/workflows/*.yml` from the filesystem, so an empty directory
    yields zero required rows for that category — deleting the four
    workflow files cannot itself fail the gate; verified by running the
    gate after deletion (8/8 passed above).

No warrant-hunter dispatch this session: single-account headless turn with
no later turn to consume a background agent's result within contract v3
s22's constraint (a delegated, unconsumed background hunt would violate
that same constraint), and the diff is docs + one new self-contained gate
test file with no runtime/security surface — closed via the direct gate
run above instead.

## Open findings

None.
