# requirements-engineering — issue-524 phase 2 record

## Summary of work

Executed the approved proposal
(`docs/issue-524/proposals/2026-08-09-discovery-design-family-batch-2-realization.md`, approved via
`APPROVE issue-524/requirements-engineering` issue comment, single-account mode). Authored 4
`roles/specs/<name>.spec.json` files (product-discovery, user-discovery, requirements-engineering,
interaction-design) instantiating `docs/specs/role-spec-template.schema.json`'s shape with each domain's
independently-scouted required fields, closed enums, `reference_resolution`, `recomputation`, `write_scope`,
4-bucket `loop_state`, and `use_when.board_condition`; updated each corresponding `roles/<name>.json` with
`write_scope: []` + `report_only: true`, the expanded 4-bucket `loop_state`, a `board_condition`-shaped
`use_when`, and a `spec` pointer; added `interaction-design.json`'s missing `"path"` key (survey.md finding);
authored `gates/test_role_spec_shape_batch2.py` (own `BATCH2_ROLES` tuple, mirrors
`gates/test_role_spec_shape.py`'s three test functions, does not edit the batch-1 file); added an
`## Accumulation` section to the proposal (accumulation-claim-guard.sh required it before this batch's files
would write).

## Why

Issue #524 (follow-up D of #515, batch-2) required realizing the 4 discovery/design-family role specs against
the #515 template, each grounded independently per this proposal's own scout-brief rather than templated from
#521's verification-family shape by analogy — the scout pass confirmed the four domains are structurally
different (Cagan's opportunity-assessment fields are prose-heavy strategic questions, Torres's snapshot is a
semi-structured narrative artifact with an evidence-count threshold, EARS is a grammar constraint on the
statement text itself, NN/g's wireflow is graph-shaped) even though the shared template shape applies
uniformly across all four.

## Upstream basis

`docs/issue-524/proposals/2026-08-09-discovery-design-family-batch-2-realization.md` (phase-1 proposal,
approved), grounded in `docs/issue-524/reports/requirements-engineering/scout-brief.md` (Cagan/SVPG,
Torres/producttalk.org, EARS/Mavin et al./29148, NN/g wireflows/UML, sources cited) and
`docs/issue-524/reports/requirements-engineering/survey.md` (current-state survey, phase-1).

## Acceptance clauses, mapped to fulfilling commit/hunk

Each issue-524 acceptance clause is restated below as a requirement item with its fulfilling artifact and an
explicit verification condition, per this role's own requirements-doc facet (unique id + nearby verification
marker). Cross-references between items are given below each item's own verification block, not inline in it.

REQ-524-1: same schema-validation pytest pattern as follow-up A (#521), over the four new
`roles/specs/*.spec.json` files.
verification: running the gates test suite filtered to spec tests exits 0 (10 passed, 0 failed — covers both
batch-1's and batch-2's role tuples), fulfilled by `gates/test_role_spec_shape_batch2.py` (this commit),
mirroring `gates/test_role_spec_shape.py`'s 3-test structure with its own `BATCH2_ROLES` tuple.
(Command: `python3 -m pytest gates/ -q -k "spec"`.)

REQ-524-2: each of the four `roles/<name>.json` gains non-empty `write_scope` (or an explicit verdict-role
report-only contract) and >=3 `loop_state` states.
verification: for each of the 4 batch-2 role files (this commit), a script asserting `write_scope is not None`
and `set(loop_state buckets) == {progress, terminal, refusal, error}` exits 0 for all 4 — each carries
`write_scope: []` paired with `report_only: true` (explicit report-only contract, matching batch-1's pattern
for roles with no real external write surface) and a 4-bucket `loop_state` object, exceeding the >=3-states
floor. Set-equality form used per issue #521's own warrant-hunter-corrected reading of the acceptance clause,
not the weaker length-only check.

REQ-524-3: provenance — executed-unit for schema/grep checks; spec substance is human PR review.
verification: the pytest run and the assertion-script checks documented above (see the two preceding
acceptance items) are the executed-unit provenance; the 4 `roles/specs/*.spec.json` files' `source_standard`/
enum content (Cagan, Torres, EARS/29148, NN/g/UML citations) is left for human PR review against
`scout-brief.md`'s `Sources:` list, per the proposal's own warrant-hunter-acknowledged note that
`gates/role_spec_shape.py` checks shape only, not citation authenticity.

REQ-524-4: empty state — new spec files; absence today is the documented starting state.
verification: all 4 `roles/specs/*.spec.json` files and `gates/test_role_spec_shape_batch2.py` are new in this
commit; their absence before this commit is the documented starting state in
`docs/issue-524/reports/requirements-engineering/survey.md`.

## Traceability Matrix

| ID | Description | Source | Downstream Link |
| --- | --- | --- | --- |
| REQ-524-1 | schema-validation pytest pattern over the 4 new spec files | issue #524 acceptance clause 1 | `gates/test_role_spec_shape_batch2.py` |
| REQ-524-2 | non-empty write_scope + >=3 loop_state states per role.json | issue #524 acceptance clause 2 | `roles/product-discovery.json`, `roles/user-discovery.json`, `roles/requirements-engineering.json`, `roles/interaction-design.json` |
| REQ-524-3 | provenance split — executed-unit vs human PR review | issue #524 acceptance clause 3 | `gates/role_spec_shape.py`, `roles/specs/*.spec.json` (4 files) |
| REQ-524-4 | empty-state documentation for new spec files | issue #524 acceptance clause 4 | `docs/issue-524/reports/requirements-engineering/survey.md` |

## Ambiguity

No ambiguities found in the issue-524 acceptance clauses themselves — each of the 4 acceptance bullets maps
1:1 to a requirement item above with a concrete, mechanically-runnable verification. Two content-level
ambiguities surfaced during scouting and are resolution: entries, not open items:
- resolution: `product-discovery.confidence_level` and `requirements-engineering.status` — could a plausible
  closed enum be inferred by analogy to adjacent conventions (e.g. ReqView's draft/approved/verified)? Resolved
  as no: the proposal's no-invented-enum constraint keeps both typed `string`, per the scout-brief's explicit
  gap finding, not a fabricated enum dressed as a citation.
- resolution: is `roles/interaction-design.json`'s "path" key gap in scope for this issue, or a pre-existing
  defect to leave alone? Resolved as in-scope: the phase-1 survey named it explicitly as this batch's own
  finding, and the proposal's "What will be done" section 2 lists it, so it is fixed alongside the other 3
  roles' edits in this commit rather than deferred.

kind: realization-record
loop_state: landed

## Open findings

- The proposal's own warrant-hunter finding (`docs/reports/2026-08-09-hunt-discovery-design-family-batch-2-realization.md`,
  after-proposal, stance 0): `gates/role_spec_shape.py` checks presence/type/non-emptiness only, so a
  placeholder-filled spec (`"enum": ["TODO"]`) would still pass shape check with exit 0. No gate change was
  proposed or made — the provenance split noted above already scopes citation-authenticity checking to human
  PR review, not `pytest`; this record repeats the flag so review knows the shape check's scope going in.
- Rulebook-side alignment plan (proposal's own section, per issue-524's scope comment) is a plan document only
  — the 4 target `<role>-rulebook` repos' own methodology docs/hooks/gates have not been touched (out of this
  session's write access) and remain the user's separate-session work per repo.

Since `loop_state` is terminal (`landed`), no next-steps/resolution-path lines are required by contract v3.
