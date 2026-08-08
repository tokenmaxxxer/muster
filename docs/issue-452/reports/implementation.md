---
code_under_review:
  - on-the-record/UNENFORCED-CLAUSES.md
  - on-the-record/commands/run.md
  - gates/test_boundary.py
  - docs/specs/enforcement-boundary.md
loop_state: phase-2-complete
---

# Implementation record — issue-452

Phase 2, per approved proposal
`docs/issue-452/proposals/2026-08-08-ship-unenforced-clause-list.md`.

## What was done

- Added `on-the-record/UNENFORCED-CLAUSES.md`: derived extract of the
  `contract, CI-supplement` / `out of scope — operator decision` rows
  in `docs/specs/enforcement-boundary.md`.
- Referenced it from `on-the-record/commands/run.md`.
- Added two `gates/test_boundary.py` cases: exact-set match between
  the shipped list and the spec rows; reference-string presence check
  in `run.md`.
- Noted in `docs/specs/enforcement-boundary.md` that the shipped list
  is the derived, gate-checked extract.

## Why / upstream basis

Follow-up from issue #441's execution-observation verdict (criterion
4 not discharged): a consumer project could not read, zero-install,
which contract clauses are not mechanically enforced for it. Approved
phase-1 proposal above authorizes this delivery.

## What did not work

None.

## Doc placement

- New env var/config key/dep/migration: none — no placement needed.
- Library-or-format choice, changed public signature/wire format: none
  new beyond what the proposal's Rationale already recorded.
- Benchmark/investigation numbers: none.

## Hunt

- Hunter was dispatched at phase-1 end (see
  `docs/reports/2026-08-08-hunt-ship-unenforced-clause-list.md`) — one
  finding, addressed in the proposal (subset-match corrected to
  exact-set match). No before-landing hunt run in this turn (headless
  single-shot session; contract v3 s22 takes priority over waiting on
  a second background dispatch this turn).

## Open findings

None outstanding.

## Next steps

- `python3 gates/test_boundary.py` run and confirmed passing (5/5).
- Commit, push, and let the open PR #455 pick up phase-2 delivery.

## Resolution path

N/A — no open findings to resolve.
