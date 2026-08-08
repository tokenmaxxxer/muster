---
code_under_review:
  - gates/approval_request_shape.py
  - gates/open_work.py
  - gates/test_approval_request_shape.py
  - gates/test_open_work.py
  - gates/test_boundary.py
  - on-the-record/commands/run.md
  - docs/specs/enforcement-boundary.md
  - on-the-record/UNENFORCED-CLAUSES.md
loop_state: landed
---

# issue-472 phase 2 — Batch B delivery record

upstream: docs/issue-472/proposals/2026-08-08-batch-b-proposal-content-shape-gates.md

## Summary of work

Delivered issue-467 ADR Batch B per the approved proposal:

- `gates/approval_request_shape.py` (new): `missing_approval_clauses(text)`
  — pure-function port of `on-the-record/hooks/stop-gate.sh`'s inline
  clause-detection regexes (#318). `has_generator_section(proposal_text)`
  — presence-only check for a `## Generator`/`## 생성자` heading (#363);
  docstring states plainly it does not verify content.
- `gates/open_work.py` (new): `build_open_work_query(keyword)` — builds
  `gh issue list`/`gh pr list --search` parameters for a constraint
  keyword, no network call inside the function (#379).
- `gates/test_approval_request_shape.py`, `gates/test_open_work.py`
  (new): red-green tests for both modules, all passing.
- `gates/test_boundary.py`: added `318`, `363`, `379` to
  `_ISSUE_467_BATCH_A_CITATIONS`, pointing at the two new test files.
  Batch A's `{362, 390, 412}` entries left untouched (verified by diff:
  only additions to the dict). `t_class_b_disposition_rows_cited` stays
  green.
- `on-the-record/commands/run.md`: added a contract section for
  #318/#363/#379 mirroring Batch A's #362/#390/#412 section shape.
- `docs/specs/enforcement-boundary.md` +
  `on-the-record/UNENFORCED-CLAUSES.md`: the pre-existing
  `t_all_gates_modules_recorded` / `t_unenforced_clauses_file_matches_
  spec_exactly` checks (issue-441/#452, not part of this batch's own
  acceptance) required the two new `gates/*.py` modules to carry a
  recorded verdict row once they existed on disk. Added
  `approval_request_shape.py` (verdict: `contract` — testable extraction
  of already-hook-enforced #318 logic, plus presence-only #363 check
  instructed via `run.md`) and `open_work.py` (verdict: `contract,
  CI-supplement` — query construction only, the actual lookup runs
  manually per `run.md`; mirrored into `UNENFORCED-CLAUSES.md` per its
  own exact-match invariant). These are docs/ writes, allowed regardless
  of the frozen write set (warrant directive's docs/ exception); no code
  outside the proposal's write set was touched.

All new/modified gates suites run green:
`python3 gates/test_approval_request_shape.py` (8/8),
`python3 gates/test_open_work.py` (5/5),
`python3 gates/test_boundary.py` (11/11, up from 8/8 pre-change).

## Why

Per the approved phase-1 proposal: issue #472 asks for deployed-surface
enforcement (run.md contract text + named check) for three issue-467 ADR
Class-B rows, landing after Batch A.

## What did not work

None.

## Rationale for deviations

Two docs/ files outside the proposal's stated `files:` write set
(`docs/specs/enforcement-boundary.md`, `on-the-record/UNENFORCED-CLAUSES.md`)
were edited. This is not a scope-exceeded stop: both are pre-existing,
already-shipped invariants (`gates/test_boundary.py::t_all_gates_modules_
recorded` from issue #441, `t_unenforced_clauses_file_matches_spec_exactly`
from issue #452) that fire on any new `gates/*.py` module regardless of
which issue adds it, and the warrant directive treats `docs/` as always
writable. No code file outside the frozen write set was touched.

## Open findings

None. Before-landing warrant hunt (stance: assume this change and another
plugin's rule cancel each other — find the pair) returned NO FINDING;
see docs/reports/2026-08-08-hunt-issue-472-batch-b.md. A pre-existing,
unrelated finding from the after-proposal hunt (Batch A's citation dict
has no mechanical protection against silent deletion/repointing) is
noted there — this delivery did not touch Batch A's `{362, 390, 412}`
entries, so it does not block this record.

## closed_checks

- gates/test_approval_request_shape.py: 8/8 passed (code_under_review: see frontmatter)
- gates/test_open_work.py: 5/5 passed (code_under_review: see frontmatter)
- gates/test_boundary.py: 11/11 passed (code_under_review: see frontmatter)

## Next steps

None — phase 2 delivery complete, PR #482 to be updated and left for
human review/merge.

## Resolution path

No open findings.
