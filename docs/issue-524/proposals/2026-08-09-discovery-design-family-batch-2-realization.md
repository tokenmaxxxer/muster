---
status: proposed
files:
  - roles/specs/product-discovery.spec.json
  - roles/specs/user-discovery.spec.json
  - roles/specs/requirements-engineering.spec.json
  - roles/specs/interaction-design.spec.json
  - roles/product-discovery.json
  - roles/user-discovery.json
  - roles/requirements-engineering.json
  - roles/interaction-design.json
  - gates/test_role_spec_shape_batch2.py
  - docs/issue-524/reports/requirements-engineering.md
---

## Request

Issue #524 (follow-up D of #515, batch-2): realize the 4 discovery/design-family role specs
(product-discovery, user-discovery, requirements-engineering, interaction-design) against the #515 realization
template — required-field lists, closed enums, reference-resolution rules, recomputation rules, real
`write_scope`, 4-bucket `loop_state`, board-decidable `use_when` — each grounded independently in the
discipline's canonical artifact form (Cagan Opportunity Assessment + pre-registered decision rules, Torres
interview snapshots + saturation, EARS + ISO/IEC/IEEE 29148 RTM, NN/g wireflows), sources cited, per this
proposal's own scout-brief (`docs/issue-524/reports/requirements-engineering/scout-brief.md`) rather than
templated from #521's verification-family shape by analogy. The issue-524 thread comment additionally scopes
realization to **both** this repo's contracts/specs and each target role's own `<role>-rulebook` repo — this
proposal's "Rulebook-side alignment plan" section covers that half.

## Constraints

- Minimal-required-fields-first, same as #521 — a role's `required_fields` list expands only where the
  scout-brief found evidence a field is needed, never speculatively.
- No invented enums: every closed vocabulary in the 4 specs must trace to a `Sources:` entry in
  `scout-brief.md`. Two fields (product-discovery's `confidence_level`, requirements-engineering's `status`)
  have a confirmed absence of a citable closed enum in the scouted sources and stay typed `string`, not a
  fabricated enum dressed as a citation.
- Reuse #521's generic infrastructure unchanged: `docs/specs/role-spec-template.schema.json` (already
  role-agnostic) and `gates/role_spec_shape.py` (already takes any spec dict) need no edits. A new
  `gates/test_role_spec_shape_batch2.py` mirrors `gates/test_role_spec_shape.py`'s structure with its own
  `BATCH2_ROLES` tuple, rather than editing the batch-1 test file, so each batch's own test intent stays
  legible (same reasoning #521 itself gives for not inventing new dependencies where an existing pattern
  already fits).
- Enforcement mechanism stays the existing `on-the-record/hooks/role-spec-reference-guard.sh` (already generic,
  no change needed) — never a new bespoke hook, never GitHub Actions, matching #521's own out-of-scope note.
- `docs/issue-524/reports/requirements-engineering.md` (this role's own record, phase-2 output per this
  session's role-handoff contract) is listed in the write set for completeness of the frozen scope, not written
  this turn — this proposal, the survey, and the scout-brief are the only phase-1 writes.
- Rulebook-repo work (the 4 `<role>-rulebook` repos) is out of this proposal's write set entirely — this
  session has no write access to those repos from here. The alignment plan below is a plan the user executes as
  separate sessions against each rulebook's own board, not something this PR's write set can carry.

## Rationale

**Four independently-scouted domain groundings, vs. copying #521's EARL-style 4-field shape across all four
roles by analogy.** Rejected templating from #521: the issue text itself requires each domain scouted
independently (Cagan/Torres/EARS-RTM/NN-g named explicitly, not "reuse the verification-family shape"), and the
scout pass confirms the four domains are structurally different enough that forcing one shared shape would lose
real information — Cagan's opportunity-assessment fields are prose-heavy strategic questions (not a per-claim
verdict record like EARL), Torres's snapshot is a semi-structured narrative artifact with a evidence-count
threshold rather than a closed result enum, EARS is a regex-checkable grammar constraint on the requirement
*statement itself* (not a separate metadata record), and NN/g's wireflow is graph-shaped (states + transitions)
rather than flat-record-shaped like every batch-1 role. The shared template
(`role-spec-template.schema.json`'s `required_fields`/`reference_resolution`/`recomputation`/`write_scope`/
`loop_state`/`use_when` shape) still applies uniformly — what differs, correctly, is each role's *content*
inside that shape.

**`string`, not an invented enum, for `product-discovery.confidence_level` and
`requirements-engineering.status`.** Rejected inventing a plausible-looking enum for either: the scout-brief
explicitly could not confirm a Cagan/Bland-attributed confidence scale or a 29148-attributed status vocabulary
in any fetched primary or reputable secondary source (practitioner tool conventions like ReqView's
draft/approved/verified exist, but are conventions, not the standard's own text) — the no-invented-enum
constraint (carried over from #521's ACT-vs-EARL precedent, where #521 only added a value once a primary
source confirmed it) means these stay `string` fields pending a future pass that can confirm an actual source,
not silently filled in now.

**UML `state | choice | terminal` as the closed node-type enum for `interaction-design`, vs. leaving node type
untyped free text.** NN/g's own wireflow article deliberately avoids prescribing abstract flowchart symbols
(branching is shown via multiple hotspots on one screen, not a diamond) — but a machine-checkable spec still
needs a closed vocabulary for the state-graph shape check (reference-resolution needs to know what a
"terminal" node is to check a flow has one). UML state-machine notation is the closest confirmed closed
vocabulary in the scouted sources (uml-diagrams.org, en.wikipedia.org/wiki/UML_state_machine) that a wireflow
can be losslessly expressed in without contradicting NN/g's own screen-embedded-hotspot practice — the enum
constrains the graph's *structural* type, not the screen's visual design, so it doesn't force NN/g's
avoided-diamond notation onto the actual deliverable.

**Guest et al./Hennink et al. run-length saturation rule, vs. a fixed magic-number interview count.** Rejected
a fixed count (e.g. "10 interviews"): Torres's own practice has no numeric stop rule (continuous discovery has
no phase boundary), and the qualitative-methods literature's own contribution is precisely that saturation is a
*rate* condition (a run of consecutive interviews adding zero new themes), not a fixed total — baking in a
magic number would misrepresent the cited methodology as prescribing something it explicitly frames as
sample-dependent.

## What will be done

1. Author 4 `roles/specs/<name>.spec.json` files instantiating `role-spec-template.schema.json`'s shape with
   the scout-brief's confirmed fields:
   - **product-discovery**: `required_fields` = Cagan's 10 opportunity-assessment questions (`problem_statement`,
     `target_market`, `market_size_rationale`, `competitive_alternatives`, `differentiator`,
     `timing_rationale`, `go_to_market_plan`, `success_metric`, `critical_success_factors`,
     `recommendation` enum `go|no-go`) plus the lean-startup rigor layer (`hypothesis_statement`,
     `fail_condition`, `time_box`, `decision_rule`, `confidence_level` type `string`, `evidence_log` type
     `ref[]`). `source_standard`: "Cagan/SVPG Opportunity Assessment + lean-startup pre-registered decision
     rules (Startup Commons / Kromatic / Startup Project)". Verdict enum
     `validated|invalidated|inconclusive` (roadmap.one convention, flagged as not Cagan-attributed in the
     field's own description).
   - **user-discovery**: `required_fields` = `interview_snapshot` (`ref`, one per interview), `quote` (`string`),
     `opportunity_tag` enum `need|pain|desire` (Torres's triad), `snapshot_refs` (`ref[]`, >=1 required per
     opportunity per Torres's evidence-count rule), `saturation_run_length` (`string`, cites Guest et
     al./Hennink et al. — kept as a stated parameter, not a fixed number, per the rationale above),
     `verdict` enum `pain-confirmed|not-confirmed` (this role's own pre-existing vocabulary, spec's
     `source_standard` field states plainly this is an extension beyond Torres's native need/pain/desire
     triad, not a direct citation). `source_standard`: "Teresa Torres interview snapshots
     (producttalk.org) + Guest/Bunce/Johnson 2006 and Hennink/Kaiser/Weber 2020 saturation run-length
     (extension beyond Torres's own confirmed/not-confirmed vocabulary, stated explicitly)".
   - **requirements-engineering**: `required_fields` = `statement` (`string`, must match one of the EARS
     patterns — `reference_resolution.rule` states the regex-checkable grammar constraint since EARS
     compliance is a property of the statement text itself, not a separate field), `ears_pattern` enum
     `ubiquitous|event-driven|state-driven|optional-feature|unwanted-behaviour|complex`, `source` (`ref`,
     backward traceability), `verification_method` enum `Inspection|Analysis|Demonstration|Test` (29148,
     shared lineage with this repo's own batch-1 IV&V-derived enum), `downstream_link` (`ref`, forward
     traceability), `status` (`string`, no citable closed enum confirmed — see rationale). `source_standard`:
     "EARS (Mavin et al., IEEE RE'09) + ISO/IEC/IEEE 29148 bidirectional traceability".
   - **interaction-design**: `required_fields` = `state_name` (`string`), `entry_trigger` (`string`),
     `screen_ref` (`ref`), `node_type` enum `state|choice|terminal` (UML state-machine notation), `feedback`
     (`string`), `transitions` (`ref[]`, each resolving to another state's `state_name` — reference-resolution
     rule), `edge_case_variant` (`string`, required per NN/g's error-state-beyond-happy-path must-be).
     `source_standard`: "NN/g wireflows (nngroup.com/articles/wireflows) + UML state-machine notation
     (uml-diagrams.org) for the closed node-type enum NN/g itself leaves unspecified".
2. Update each `roles/<name>.json`: `write_scope: []` paired with `report_only: true` (all 4 roles' existing
   `produces` fields are record-only, matching batch-1's own report-only pattern for the roles that had no
   real external write surface); `loop_state` expanded to the 4-bucket shape per role (e.g.
   `product-discovery`: `progress: ["measuring"], terminal: ["validated", "invalidated"], refusal:
   ["hypothesis-not-falsifiable"], error: ["evidence-log-unreadable"]`); `use_when` rewritten as a
   `board_condition` predicate string; `interaction-design.json` additionally gains the missing `"path"` key
   (survey.md finding) to match every other role file's shape.
3. Author `gates/test_role_spec_shape_batch2.py` (pytest, `BATCH2_ROLES` tuple of the 4 roles above, same
   three test functions as `gates/test_role_spec_shape.py`: files-exist, shape-check-passes, role-field-matches-
   filename) — satisfies acceptance clause 1 without editing the batch-1 test file.
4. Verify acceptance clauses locally before opening the PR: `python3 -m pytest gates/ -q -k "spec"` exits 0
   (covering both `BATCH1_ROLES` and `BATCH2_ROLES`); for each of the 4 roles,
   `python3 -c "import json;d=json.load(open('roles/<name>.json'));assert d['write_scope'] is not None and
   set(d['record_fields']['loop_state']) == {'progress','terminal','refusal','error'}"` — using the
   set-equality form #521's own warrant-hunter finding corrected the literal `len(...)>=3` check to, not the
   weaker form; `grep -c "use_when" roles/specs/*.spec.json` covers all 8 spec files (4 batch-1 + 4 batch-2)
   with one `use_when` object each.

## Accumulation

This batch repeats batch-1's per-role file shape (one `roles/specs/<name>.spec.json` + one matching one-line
edit to `roles/<name>.json` + one shared batch-scoped pytest file) across 4 roles, same as #521 did across 6.
If a batch-3+ (build family, ops/knowledge family, commercial/risk family, issue-515's Issue E) repeats this
same shape again, the accumulation is: one more `gates/test_role_spec_shape_batchN.py` per batch (never edits
to an earlier batch's test file — each batch's own intent stays legible, matching this proposal's own
constraint) plus N more `roles/specs/*.spec.json` files, all validated by the same unmodified
`gates/role_spec_shape.py` and `docs/specs/role-spec-template.schema.json` shared infrastructure. No new
shared helper is warranted yet: `gates/role_spec_shape.py` already takes any spec dict (batch-agnostic), and
each batch's own `BATCH<N>_ROLES` tuple is 3-6 lines, not an accumulating inline `subprocess`/`gh` pattern. If
a 4th batch's test file becomes near-identical boilerplate to batch-1/2/3's, that is the trigger to factor a
shared `roles/specs/*.spec.json` glob-based test (one file replacing all `BATCH<N>` files) — not before, since
three data points don't yet justify the abstraction and batch-2 (this proposal) is only the second.

## Rulebook-side alignment plan (per issue-524's scope comment)

Realization is only complete when each target role's own `<role>-rulebook` repo's methodology docs, hooks, and
gates are updated to match the new spec shape — this repo's `roles/<name>.json`/`roles/specs/<name>.spec.json`
files are the *contract*, not the enforcement inside each rulebook's own session. This proposal cannot execute
that half (no write access to those repos from this session) — it states the plan the user carries into
separate sessions against each rulebook's own board:

- **product-discovery-rulebook**: add a methodology doc naming the 10-question Cagan Opportunity Assessment
  frame plus the pre-registered fail-condition/decision-rule/time-box triple as the record's required shape;
  a hook enforcing `fail_condition`/`decision_rule` are populated *before* `evidence_log` gains entries (the
  pre-registration order this proposal's rationale section treats as load-bearing); a gate checking
  `recommendation` is one of `go|no-go`, never asserted without the 10 fields present.
- **user-discovery-rulebook**: a methodology doc defining the per-interview snapshot artifact shape
  (`quote`/`opportunity_tag`/`snapshot_refs`) and the saturation run-length rule; a hook checking each
  opportunity claim resolves to `>=1` `snapshot_refs` entry (Torres's evidence-count rule); a gate computing
  saturation from the run-length parameter rather than accepting an asserted "saturated" verdict.
- **requirements-engineering-rulebook**: a methodology doc naming the 6 EARS patterns with their grammar; a
  hook (or CI-adjacent target-repo gate, per this repo's hooks-not-CI enforcement convention) that regex-checks
  each `statement` against the declared `ears_pattern`'s template; a gate checking `verification_method` is
  populated before `status` can move past its initial value (bidirectional-traceability-before-status-change,
  mirroring 29148's own ordering).
- **interaction-design-rulebook**: a methodology doc defining the wireflow's state/transition record shape and
  the UML node-type enum; a hook checking every `transitions` entry resolves to a real `state_name` elsewhere
  in the same record (graph reference-resolution, this role's version of the orphan-reference check every
  other realized role already has); a gate requiring at least one `terminal` node type per flow and at least
  one populated `edge_case_variant` per flow (NN/g's error-state must-be).

This plan itself is not this PR's deliverable — it is the section the issue-524 comment asked this proposal to
carry, so the user has a concrete per-repo task list to execute as the batch's second half.

## Out of scope

- Executing the rulebook-side alignment plan above — four separate sessions against four separate rulebook
  repos' own boards, per the interaction protocol (this role never files issues, never opens sessions in
  another repo from here).
- Bespoke recomputation-enforcement hooks per role — same TBD-follow-up posture #521 took for the verification
  family; each of the 4 specs' `recomputation.checked_by` states `"TBD (follow-up)"` with the same reasoning.
- Editing `docs/specs/role-spec-template.schema.json`, `gates/role_spec_shape.py`, or
  `on-the-record/hooks/role-spec-reference-guard.sh` — all three are already generic across roles; batch-2 adds
  data files against the existing shape, not a shape or enforcement-mechanism change.
- Batch-3+ (build family, ops/knowledge family, commercial/risk family) — issue-515's Issue E, not this issue.

## How you'll know it worked

- `python3 -m pytest gates/ -q -k "spec"` exits 0, including `gates/test_role_spec_shape_batch2.py` loading and
  validating all 4 `roles/specs/*.spec.json` batch-2 files against the shared shape.
- For each of the 4 roles: `write_scope` is non-null and `set(loop_state.keys()) ==
  {'progress','terminal','refusal','error'}` (set-equality form, per #521's own warrant-hunter-corrected
  reading of the acceptance clause).
- All 8 `roles/specs/*.spec.json` files (4 batch-1 + 4 batch-2) carry exactly one `use_when` object each, each
  `board_condition` a predicate over board/issue state, reviewed at PR review as the stated human-check
  provenance (acceptance clause 3's own provenance note).
- The "Rulebook-side alignment plan" section above is present and lists all 4 target rulebooks by name with
  concrete doc/hook/gate items — reviewed as this PR's answer to the issue-524 thread comment's scope
  clarification.

**Warrant-hunter finding acknowledged**
(`docs/reports/2026-08-09-hunt-discovery-design-family-batch-2-realization.md`, after-proposal, stance 0):
`gates/role_spec_shape.py` checks presence/type/non-emptiness only — a spec file filled with placeholder
values (`"enum": ["TODO"]`, `"source_standard": "bogus-role"`) passes the shape check with exit 0. This is not
a batch-2-specific defect: it is the same shape-vs-content boundary issue-521's own acceptance clauses already
name explicitly ("provenance: executed-unit for schema/grep checks; spec substance is human PR review") and
issue-524's acceptance clauses repeat verbatim. The gate was never meant to certify citation authenticity —
phase 2's per-role `source_standard`/enum content is reviewed by a human against `scout-brief.md`'s `Sources:`
list at PR review, not by `pytest`. No gate change proposed here; flagged so review knows the shape check's
scope going in, same as batch-1's own posture.
