# Current-state survey — issue-523

## The collision

`roles/technical-writing.json` and `roles/devrel.json` both declare
`"write_scope": ["docs/**"]` — identical sets. The only distinguishing text
lives in Korean prose fields (`decides`, `use_when`), which
`scripts/check-write-set-conflicts.sh` and any board-level dispatch logic
never reads. If both roles are spawned on one issue, their `files:` claims
under `docs/**` are indistinguishable at the mechanical layer.

- technical-writing: `decides` = "독자가 알아야 할 것을 어떻게 구조화할지"
  (how to structure what the reader needs to know); `produces` = "doc
  outline, draft, target-reader note". General external-public
  documentation authoring.
- devrel: `decides` = "외부 개발자가 이 표면을 채택할 수 있는가" (can an
  external developer adopt this surface); `produces` = "onboarding doc,
  sample code, adoption-friction list". Developer-adoption-specific
  surfaces: onboarding, sample code framing, friction points.

## Prior art in this repo: how other roles already narrow `write_scope`

`roles/*.json` write_scope survey (43 roles, `python3` read of every file):

- 34 roles: `[]` (report-only, no declared write surface)
- `roles/architecture.json`: `["docs/issue-<n>/decisions/**"]`
- `roles/incident-response.json`: `["docs/issue-<n>/postmortems/**"]`
- `roles/knowledge-management.json`: `["docs/patterns/**"]`
- `roles/data-modeling.json`, `roles/implementation.json`,
  `roles/refactoring-legacy.json`: `src/**` (+ `test/**` where applicable)
- `roles/test-authoring.json`: `["test/**"]`
- `roles/technical-writing.json`, `roles/devrel.json`: both `["docs/**"]`
  (the collision)

Precedent is clear: roles that write docs narrow to a **dedicated
subdirectory under `docs/`**, not the full `docs/**` tree. `technical-writing`
and `devrel` are the only two roles that still claim the entire tree.

## Doctrine ladder constraint (contract v3, output-layout clause)

> Under docs/ exist only the six standing buckets (_assets, decisions,
> handbooks, proposals, reports, specs) and per-issue trees docs/issue-<n>/
> holding those same six buckets.

`roles/knowledge-management.json`'s `docs/patterns/**` already sits outside
this six-bucket list — a pre-existing exception, not something #523 is
scoped to fix (issue #523 requirement 2: "No role merge or removal —
differentiation only"). It does establish, however, that a role-dedicated
subdirectory outside the six buckets is an accepted pattern in this repo
when the role's own methodology needs one.

## Rulebook methodology grounding available in-repo

The two roles' actual rulebooks (`tokenmaxxxer/technical-writing-rulebook`,
`tokenmaxxxer/devrel-rulebook`) live in external marketplace repos not
checked out in this sandbox — `roles/*.json`'s `path` fields point at
`$TOKENMAXXXER_RULEBOOKS/...`, unavailable here, and the sandbox's allowed
network hosts do not include those marketplace repos. The grounding
available for this proposal is therefore each role's own `decides` /
`use_when` / `produces` fields (the contract-level summary of that
methodology already realized into JSON, per `docs/issue-515`'s
realization-template work) plus the write_scope precedent above. This is
sufficient to separate "structuring what a reader needs to know" (general
authoring) from "can a developer adopt this surface" (onboarding/adoption
artifacts) into two disjoint glob families — it does not require reading
the rulebooks' full prose methodology, since the distinguishing qualifier
issue #523 asks for is already stated in each role's `decides` field.

## Write surface this proposal will touch

- `roles/technical-writing.json` — narrow `write_scope`
- `roles/devrel.json` — narrow `write_scope`

No test file covers `roles/*.json` write_scope values directly beyond the
two acceptance checks named in issue #523 (`python3 -c "..."` set-inequality
check, `scripts/check-write-set-conflicts.sh`) — both are pre-existing and
require no new test file.
