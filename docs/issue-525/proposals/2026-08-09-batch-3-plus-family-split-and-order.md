---
status: proposed
files:
  - docs/issue-525/reports/implementation/survey.md
  - docs/issue-525/reports/implementation/scout-brief-build.md
  - docs/issue-525/reports/implementation/scout-brief-ops-knowledge.md
  - docs/issue-525/reports/implementation/scout-brief-commercial-risk.md
  - docs/issue-525/proposals/2026-08-09-batch-3-plus-family-split-and-order.md
---

## Request

Issue #525 (follow-up E of #515, batch-3+): propose a family split and delivery
order for the 33 still-unrealized role specs, with per-family scouting and cited
sources per role (no templating from memory), plus the rulebook-side alignment
plan the issue-525 thread comment requires. Per the invoking instruction this
session was given, this is a **phase-1, proposal-only** turn — stop after opening
this PR; no `roles/specs/*.spec.json` files are authored here.

## Constraints

- Same #515 template, minimal-required-fields-first, no-invented-enum rules as
  #521 (batch-1) and #524 (batch-2).
- Shared infrastructure (`docs/specs/role-spec-template.schema.json`,
  `gates/role_spec_shape.py`, `on-the-record/hooks/role-spec-reference-guard.sh`)
  stays unchanged — already generic across roles, confirmed by survey.
- Each delivery batch gets its own `gates/test_role_spec_shape_batch<N>.py`, never
  editing an earlier batch's test file (batch-2's own precedent).
- Rulebook-repo work is out of this session's write access — the alignment plan
  below is a plan for the user to execute as separate sessions, not something
  this or any delivery PR's write set can carry directly.
- Every family/role assignment below traces to a scout-brief `Sources:` entry;
  where scouting could not confirm a primary source (data-modeling, devrel,
  finance-unit-economics, growth-analytics, part of risk-management), the brief
  states that explicitly as a gap, not a fabricated citation.

## Rationale

**Three families split further into two-sized sub-batches per family, vs. one
single 33-role PR.** Rejected a single mega-batch: batch-1 realized 6 roles and
batch-2 realized 4 in one PR each; scaling that same per-role authoring depth
(required_fields + reference_resolution + recomputation + loop_state + use_when,
each independently grounded) to all 33 roles in one PR would produce a
non-reviewable diff and defeats the point of PR-sized human review batch-2's own
proposal already reasoned about. Sub-batches of four to five roles keep each
delivery PR at the same reviewable size as the two that already landed.

**Family boundaries drawn by deliverable segment (engineering-artifact vs.
ops/knowledge-lifecycle vs. revenue/risk-facing), vs. drawing boundaries strictly
around the four named lineages per family and leaving the other 21 roles
unassigned.** Rejected leaving the remaining roles unsorted: the issue text names
the four lineages per family as "highlights," and leaving 21 of 33 roles without a
family would just relocate the family-split decision into each delivery PR
instead of answering it here. The three scout-briefs confirm the segment
boundary holds — each family's roles cluster on a distinct axis (build: artifact
format machine-checkability; ops/knowledge: point-in-time capture or structural
classification; commercial/risk: qualification checklist or numeric ratio) that
would blur if e.g. `risk-management` sat in ops/knowledge instead of
commercial/risk.

**Named-lineage roles as each family's first sub-batch, vs. delivering families
in a different internal order.** Rejected mixing lineage and non-lineage roles
within the first sub-batch of each family: the four roles the issue text
explicitly names per family (architecture/api-design/data-engineering/
data-modeling; incident-response/capacity-planning/knowledge-management/
technical-writing; sales/marketing/partnerships-bd/risk-management) are also each
family's best-sourced roles per the scout-briefs — sequencing them first means the
weakest-sourced roles (data-modeling, devrel, finance-unit-economics,
growth-analytics) land in later sub-batches, after a stronger source is found for
each, rather than shipping a weakly-cited spec early to hit a round batch size.

**Rulebook-side alignment recorded as a plan section here, vs. deferring it to
each delivery PR.** Rejected per-delivery-PR alignment sections: the issue-525
comment asks this phase-1 proposal specifically to carry the plan, and stating it
once at the family level (methodology-doc/hook/gate categories per family) avoids
each of eight delivery PRs re-deriving the same category list — each delivery PR's
own alignment section then only needs the per-role specifics, not the shape.

## What will be done

Family split (33 roles total, verified against the survey's role list):

**Build family** (12 roles — api-design, architecture, data-engineering,
data-modeling, technical-feasibility, ml-engineering, refactoring-legacy,
performance-engineering, release-engineering, test-authoring, observability,
implementation), grounded in `scout-brief-build.md`:
- batch-3 (4): api-design, architecture, data-engineering, data-modeling — the
  issue's named lineage (Spectral/MADR/dbt-contract; data-modeling's own source
  still open per the brief's gap note, resolved before that PR authors its spec).
- batch-4a (4): technical-feasibility, ml-engineering, refactoring-legacy,
  performance-engineering.
- batch-4b (4): release-engineering, test-authoring, observability, implementation.

**Ops/knowledge family** (11 roles — incident-response, capacity-planning,
knowledge-management, technical-writing, issue-retrospective, devrel,
customer-support, content-design, brand-design, localization, ux-engineering),
grounded in `scout-brief-ops-knowledge.md`:
- batch-5 (4): incident-response, capacity-planning, knowledge-management,
  technical-writing — the issue's named lineage (SRE/ITIL/KCS/Diataxis).
- batch-6a (4): issue-retrospective, devrel, customer-support, content-design.
- batch-6b (3): brand-design, localization, ux-engineering.

**Commercial/risk family** (10 roles — sales, marketing, partnerships-bd,
risk-management, finance-unit-economics, growth-analytics, legal-compliance,
market-analysis, pr-communications, pricing), grounded in
`scout-brief-commercial-risk.md`:
- batch-7 (4): sales, marketing, partnerships-bd, risk-management — the issue's
  named lineage (MEDDPICC/Dunford/SRM-equivalent as ISO 44001/NIST 8286).
- batch-8a (3): finance-unit-economics, growth-analytics, pricing.
- batch-8b (3): legal-compliance, market-analysis, pr-communications.

Total: 8 delivery sub-batches (4+4+4 build, 4+4+3 ops/knowledge, 4+3+3
commercial/risk), each a separate PR mirroring batch-2's own per-role file shape:
one `roles/specs/<name>.spec.json` + a matching edit to `roles/<name>.json`
(write_scope/report_only, 4-bucket loop_state, use_when board_condition) + one
`gates/test_role_spec_shape_batch<N>.py`, each sub-batch re-scoping its own brief
before authoring (per the scout-directive's re-scout trigger — a new sub-batch
starting is a new decision point, not covered by this phase-1 pass alone).

## Rulebook-side alignment plan (per issue-525's scope comment)

Realization is only complete when each of the 33 target roles' own
`<role>-rulebook` repo (methodology docs, hooks, gates) is updated to match its
new spec shape — this repo's contract files are the contract, not the
enforcement inside each rulebook's own session. Per family, the alignment
category each `<role>-rulebook` needs:

- **Build family**: a methodology doc naming the role's canonical
  standard/format (MADR/Spectral/dbt-contract/Model-Cards/Fowler-catalog/SLO/
  Keep-a-Changelog/IEEE-829/OpenTelemetry/Conventional-Commits, per role); a hook
  enforcing the standard's own required-section presence before the record can
  move past its initial loop_state; a gate checking machine-parseable fields
  (Spectral rule shape, Conventional Commits header grammar, OpenTelemetry
  attribute names) against the standard's own grammar, not just presence.
- **Ops/knowledge family**: a methodology doc naming the role's canonical
  practice (SRE postmortem/ITIL capacity/KCS Solve-loop/Diataxis
  quadrant/blameless-retro/DevRel-metrics/HDI-CSAT/GOV.UK-content-design/
  DTCG-tokens/CLDR-locale, per role); a hook enforcing capture-at-point-of-
  resolution ordering for knowledge-management (KCS's own invariant) and
  quadrant-exclusivity for technical-writing (a Diataxis document belongs to
  exactly one quadrant); a gate checking DTCG token JSON validity for
  brand-design/ux-engineering's shared format.
- **Commercial/risk family**: a methodology doc naming the role's canonical
  framework (MEDDPICC/Dunford-positioning/ISO-44001/NIST-800-161/SaaS-unit-
  economics/AARRR/GDPR-DPIA/Porter-five-forces/AMEC/Van-Westendorp, per role); a
  hook enforcing MEDDPICC's eight-field checklist completeness before a sales
  record reaches a terminal loop_state; a gate checking DPIA records cite the
  GDPR Article 35(7) required elements and risk-management records populate a
  treatment/owner pair per registered risk (NIST-lineage completeness).

Each of the 8 delivery PRs above states its own roles' rulebook items at the
per-role level (the category list here is the shared shape); rulebook-repo
execution itself happens as separate sessions against each `<role>-rulebook`'s
own board, per the interaction protocol (this role never files issues or opens
sessions in another repo from here).

## Out of scope

- Authoring any `roles/specs/*.spec.json` file — this phase-1 session stops
  after this proposal, per its own invoking instruction. The 8 sub-batches above
  are each a separate follow-up delivery PR.
- Executing the rulebook-side alignment plan — 33 separate rulebook sessions
  across 33 repos, each against its own board.
- Editing `docs/specs/role-spec-template.schema.json`, `gates/role_spec_shape.py`,
  or `on-the-record/hooks/role-spec-reference-guard.sh` — confirmed generic,
  unchanged by this or prior batches.
- Resolving the three flagged sourcing gaps (data-modeling's canonical standard,
  devrel's convergent-practice-only status, finance-unit-economics/growth-
  analytics' convention-not-standard status) — each is deferred to a one-stage
  re-scout at the start of the delivery sub-batch that includes that role, per
  the scout-directive's re-scout trigger, not resolved speculatively here.

## How you'll know it worked

- This PR's diff is exactly the 5 files in the frontmatter's `files:` list.
- All three `Sources:` lists in the scout-briefs are non-empty and every
  named standard/framework in "What will be done" traces to one of them.
- The family split accounts for all 33 roles named in the survey with no
  omission and no duplicate — `grep -o` for each role name across the three
  scout-briefs' must-bes sections returns exactly one match per role.
- The 8-sub-batch enumeration under "What will be done" is reviewed at PR review
  as this proposal's answer to "order not pre-committed" and "may split delivery
  into multiple PRs."
- The "Rulebook-side alignment plan" section is present and lists all three
  families' methodology-doc/hook/gate categories, reviewed as this PR's answer to
  the issue-525 thread comment's scope clarification.
