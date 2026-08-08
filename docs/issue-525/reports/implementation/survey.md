# Survey — issue #525 (batch-3+ realization of remaining 33 roles)

## Current state (verified 2026-08-09)

- `roles/specs/*.spec.json`: 10 files exist (batch-1's 6 verification-family roles +
  batch-2's 4 discovery/design-family roles). `roles/*.json`: 43 files total.
- Remaining unrealized: 43 - 10 = 33 roles. Listed by reading `roles/*.json` minus
  `roles/specs/*.spec.json` stems:
  api-design, architecture, brand-design, capacity-planning, content-design,
  customer-support, data-engineering, data-modeling, devrel, finance-unit-economics,
  growth-analytics, implementation, incident-response, issue-retrospective,
  knowledge-management, legal-compliance, localization, market-analysis, marketing,
  ml-engineering, observability, partnerships-bd, performance-engineering,
  pr-communications, pricing, refactoring-legacy, release-engineering,
  risk-management, sales, technical-feasibility, technical-writing, test-authoring,
  ux-engineering. (33 names, confirmed by count.)
- Shared infrastructure already generic and reusable unchanged (same conclusion
  batch-2's survey reached): `docs/specs/role-spec-template.schema.json`,
  `gates/role_spec_shape.py`, `on-the-record/hooks/role-spec-reference-guard.sh`.
  `gates/role_spec_shape.py` takes any spec dict — no per-batch edit needed.
  `gates/test_role_spec_shape.py` (batch-1) and `gates/test_role_spec_shape_batch2.py`
  (batch-2) each own a `BATCH<N>_ROLES` tuple — batch-3+ continues that pattern
  (one test file per batch, never editing an earlier batch's file), per batch-2's own
  proposal accumulation note.

## Issue #525 requirements re-read

- Propose a family split for the 33 roles: build (MADR/Spectral/oasdiff/dbt-contract),
  ops/knowledge (SRE/ITIL/KCS/Diataxis), commercial/risk (MEDDPICC/Dunford/SRM/
  NIST 8286) — these lineage-per-family groups are named as **highlights**, not the
  full 33-role membership; the issue leaves the rest of the family assignment and the
  batch order to this proposal ("order not pre-committed").
- Per-family scouting required, sources cited per role, "no templating from memory" —
  i.e. each of the 33 roles needs its own scouted grounding, not batch-2's shape
  copied by analogy.
- Same #515 template / minimal-fields rules as batches A/D (i.e. #521, #524).
- May split delivery into multiple PRs.
- Issue-525 thread comment: realization also spans each role's own
  `<role>-rulebook` repo (methodology docs, hooks, gates) — the phase-1 proposal
  must include a rulebook-side alignment plan, executed as separate sessions against
  each rulebook's own board.

## Write-set projection

This session is phase-1 only ("Proposal only — stop after opening the phase-1 PR").
The write set for this PR is therefore the phase-1 documents themselves — this
survey, three per-family scout briefs, and the proposal — not any
`roles/specs/*.spec.json` file. Actual spec authoring for each sub-batch is deferred
to follow-up delivery PRs the proposal enumerates, the same relationship #515 itself
had to the batches that separately realized it.

## Gap this proposal must close

`roles/*.json` for these 33 roles: confirmed (by #515's own original survey) to
mostly carry empty `write_scope` and single-state `loop_state: ["landed"]` — the
same defect #521/#524 fixed for the 10 already-realized roles. No new defect class
found beyond what #515's original survey already documented for the full 43.

## Skip-condition check (scout-directive)

Neither skip condition applies: this is not a pure bugfix, and the spec leaves
substantial open design decisions (which standard grounds each of 33 roles, how to
batch them, what the rulebook-side plan says). Scouting is mandatory and was run —
see the three scout-briefs in this same directory.
