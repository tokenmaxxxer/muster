# Current-state survey — issue-524 (discovery/design-family batch-2)

Subject: issue-524. Phase-1 survey (contract v3 s19 rigor floor), run before the scout sweep per
scout-directive's survey-first order.

## Target roles, current `roles/<name>.json` state

| role | write_scope | loop_state (flat) | spec file | notes |
|---|---|---|---|---|
| `product-discovery` | `[]` (no `report_only` tag) | `["measuring"]` | none | `use_when`/`produces` are prose, not board-decidable predicate / typed fields |
| `user-discovery` | `[]` (no `report_only` tag) | `["landed"]` | none | same gaps |
| `requirements-engineering` | `[]` (no `report_only` tag) | `["landed"]` | none | this role's own record — same gaps |
| `interaction-design` | `[]` (no `report_only` tag) | `["reviewed"]` | none | `repo` field present but missing the `marketplace`-adjacent `path`... actually has no `path` key at all (only `product-discovery`/`user-discovery`/`requirements-engineering` have `path`); flagged below |

All 4 match the batch-1-before-realization pattern exactly: empty `write_scope` with no `report_only` flag,
single-value flat `loop_state` array, prose `use_when`, prose `produces` (no `required_fields` typing). None
has a sibling `roles/specs/<name>.spec.json`.

**Additional gap found in `interaction-design.json` not present in the other 3**: missing top-level `"path"`
key (present in all of `product-discovery`/`user-discovery`/`requirements-engineering`/every batch-1 role) —
a shape drift the batch-1 realization pass didn't have to handle. Batch-2's phase-2 edit must add it
(`"path": "$TOKENMAXXXER_RULEBOOKS/interaction-design-rulebook"`, matching the naming convention every other
role file uses) since leaving it out would be an unexplained inconsistency, not a decision.

## Reusable infrastructure from issue-521 (batch-1, commit `782a81d`)

- `docs/specs/role-spec-template.schema.json` — the shared shape (`role`, `source_standard`, `required_fields`,
  `reference_resolution`, `recomputation`, `write_scope`, `report_only`, `loop_state` 4-bucket,
  `use_when.board_condition`). Generic, not batch-1-specific — batch-2 specs instantiate the same shape,
  no schema change needed.
- `gates/role_spec_shape.py` — hand-rolled shape checker, also generic (takes any spec dict). No change needed.
- `gates/test_role_spec_shape.py` — **batch-1-specific**: hardcodes `BATCH1_ROLES` tuple of the 6 verification
  roles and asserts only those 6 spec files exist/validate. Batch-2 needs its own test module (mirroring this
  file's structure with a `BATCH2_ROLES` tuple) rather than editing this one, so batch-1's own test intent
  stays legible and future batches keep following the same per-batch-test-file convention.
- `on-the-record/hooks/role-spec-reference-guard.sh` + `hooks.json` wiring — already generic (checks any
  `ref`/`ref[]` field in any role's record against the repo), needs no change for batch-2's specs to be
  enforced once they exist.

## Issue-515's own follow-up split (docs/issue-515/reports/requirements-engineering.md, "Follow-up issue split")

Issue-515 pre-named this exact batch as "Issue D — scope: batch-2 phase-1 proposal (discovery/design family,
EARS+RTM and Cagan/Torres formats), scouted independently before templating; target roles: product-discovery,
user-discovery, requirements-engineering, interaction-design." Issue #524 is that Issue D, filed by the user.
This confirms the target-role list and the two named methodology anchors (EARS+RTM, Cagan/Torres) — NN/g
wireflows for `interaction-design` is new territory issue-515 didn't scope out, since #515's own survey did not
cover the design family in the same depth as it did for discovery.

## What issue-524's comment adds beyond #515/#521's realization scope

The issue-524 thread comment (JiwonJung94) adds a requirement neither #515 nor #521 carried: realization spans
**both** this repo's contracts/specs and each target role's own rulebook repo
(`<role>-rulebook`, per the `repo`/`path` fields surveyed above). #521 (batch-1) only ever touched this repo
(`on-the-record`) — it never opened work in `execution-observation-rulebook` etc. Batch-2's phase-1 proposal
must therefore add a section #521's proposal didn't need: a rulebook-side alignment plan, listing which
methodology docs/hooks/gates change in each of the 4 rulebook repos, and stating that this executes as
separate sessions/PRs against each rulebook's own board (this role has no write access to those repos from
here — the plan is a plan, not an execution).
