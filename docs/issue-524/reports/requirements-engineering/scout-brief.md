# Scout brief — issue-524 (discovery/design-family batch-2)

Mode: parallel sweep, 4 angles, genuinely concurrent (4 `general-purpose` subagents dispatched in one message,
each with WebSearch/WebFetch, foreground-consumed same turn per contract v3 s22). Stages used: 1 (sweep only —
judge point 1 found no exemplar mismatches and no cross-angle overlap needing reconciliation, since the 4
angles target disjoint standards for disjoint roles; judge point 2 saturation call: another round would not
change any build decision — each angle already returned a primary-source-grounded must-be set plus an explicit
list of what could NOT be confirmed from primary text, which is itself the actionable signal — so stopped at 1
stage, well under the 5-stage/3min budget).

Angles: (1) Cagan Opportunity Assessment + lean-startup decision rules → `product-discovery`; (2) Torres
interview snapshots + saturation → `user-discovery`; (3) EARS + ISO/IEC/IEEE 29148 RTM → `requirements-engineering`;
(4) NN/g wireflows → `interaction-design`.

## Findings (must-bes) per role

### product-discovery — Cagan Opportunity Assessment (SVPG) + lean-startup hypothesis rigor

- Cagan's Opportunity Assessment (svpg.com) 10-question set: problem statement, target market, market-size
  rationale, competitive alternatives, differentiator, timing rationale, go-to-market plan, success
  metric/revenue model, critical success factors, explicit go/no-go recommendation.
- Layered hypothesis-testing rigor (Startup Commons, Kromatic, Startup Project): hypothesis statement, metric,
  pre-registered fail condition/threshold (must be fixed before data, or the hypothesis isn't falsifiable),
  time-box, decision rule (what action each outcome triggers), evidence log.
- Verdict vocabulary: `validated / invalidated / inconclusive` recurs across discovery-metrics sources
  (roadmap.one) — **not** attributable to Cagan/SVPG directly; adopted as the domain's de facto verdict enum
  since no more-authoritative closed vocabulary was found.
- **Gap, explicitly flagged, not invented around**: no citable Cagan/Bland numeric "confidence level" scale
  exists in the fetched sources. `confidence level` stays a free-text/string field in the spec, not a
  fabricated enum — this is the proposal's own no-invented-enum constraint (carried over from #521) in action.

### user-discovery — Torres interview snapshots + saturation (producttalk.org) + Guest et al./Hennink et al.

- Torres's interview snapshot (producttalk.org/interview-snapshot): one snapshot per interview, containing a
  direct quote, an experience-map/timeline of the story, and opportunities tagged by category. Torres's own
  taxonomy for that tag is **need / pain / desire** (recurring triad across her writing and the
  opportunity-solution-tree glossary) — not a "confirmed/not-confirmed" binary; that binary is this repo's own
  role's pre-existing `produces` field ("pain-confirmed|not-confirmed verdict"), which the scout confirms is an
  extension beyond Torres's native vocabulary, not a mis-citation to fix.
- Opportunity evidence threshold: Torres requires at least one or two snapshots backing an opportunity before
  it's placed on the tree — a minimum-evidence-count rule, machine-checkable as "opportunity referenced by
  >=1 snapshot ref".
- Saturation: Torres gives no numeric stop rule (her practice is continuous, not phase-bounded). The
  machine-checkable rule comes from qualitative-methods literature instead: Guest, Bunce & Johnson 2006 ("How
  Many Interviews Are Enough?") — saturation = no new themes across a run of interviews; Hennink, Kaiser & Weber
  2020 (PLOS ONE) formalizes this as a **run-length** parameter (a short run of consecutive interviews) against
  a **new-information threshold** (a low or zero percentage of new tags). Adopted rule: "saturation reached at
  interview N if the following run of consecutive interviews adds zero new opportunity tags — run length and
  threshold configurable per the cited papers, defaulting to the stricter zero-new-tags reading."

### requirements-engineering — EARS (Mavin et al., RE'09) + ISO/IEC/IEEE 29148 RTM

- EARS's template patterns, exact grammar (Mavin et al., IEEE RE'09; qracorp.com summary):
  Ubiquitous `THE <system> SHALL <response>`; Event-driven `WHEN <trigger>, THE <system> SHALL <response>`;
  State-driven `WHILE <precondition>, THE <system> SHALL <response>`; Optional-feature
  `WHERE <feature>, THE <system> SHALL <response>`; Unwanted-behaviour `IF <trigger>, THEN THE <system> SHALL
  <response>`; Complex (chained combination of the above).
- ISO/IEC/IEEE 29148: requires bidirectional traceability — backward (requirement → stakeholder-need source)
  and forward (requirement → verification method → downstream test/design artifact). Verification method is a
  closed enum shared with DO-178C's lineage (already used by this repo's own batch-1 verification-family work
  by way of IV&V, per `docs/issue-515/reports/requirements-engineering/scout-brief.md`):
  `Inspection | Analysis | Demonstration | Test`.
- **Gap, explicitly flagged**: no single verbatim RTM column list or a `draft/approved/verified`-style status
  enum could be confirmed against 29148's primary text from open sources (practitioner tools like ReqView
  render columns consistently, but that's convention, not quoted standard). Requirement `status` stays a
  free-text/string field, not an invented enum.

### interaction-design — NN/g wireflows

- NN/g's wireflow (nngroup.com/articles/wireflows): per-screen low-fidelity mockup + explicit hotspot markup
  (the clickable target driving the next transition) + on-screen feedback (confirmation, error, state change
  shown in the mockup, not as separate annotation text) + directed transition arrows between screens. NN/g
  explicitly scopes wireflows to few-screen, dynamic-state apps — not static multi-page sites (skip pattern).
- NN/g does **not** publish a closed vocabulary for decision/branching nodes — branching is shown via multiple
  hotspots leaving one screen, not an abstract diamond. The closed-vocabulary fallback for a machine-checkable
  spec's node-type field is UML state-machine notation (uml-diagrams.org / ISO 5807 lineage): `state | choice |
  terminal`, each transition carrying a trigger/guard label.
- Must-bes per state: name, entry trigger, screen/content ref, feedback shown, at least one outgoing
  transition, an edge-case/error variant. Must-bes per transition: source, target, trigger/hotspot, guard
  condition if branching.

## Performance axes (cross-role)

1. Every verdict/decision is derived from a pre-registered rule fixed before evidence, never asserted
   post-hoc (product-discovery's fail-condition, user-discovery's saturation run-length, requirements-
   engineering's verification-method-before-status, interaction-design's error-state-before-happy-path-only).
2. Every claim/state cites its evidence inline, never an unlinked assertion (Cagan's evidence log, Torres's
   snapshot-per-opportunity link, 29148's requirement-to-test-case link, NN/g's hotspot-to-transition link) —
   the same invariant issue-515's scout-brief found across the verification family, now confirmed independently
   across the discovery/design family too.
3. Gaps are stated as gaps (free-text field), never filled with an invented enum dressed as a citation — this
   recurred across most of the angles (product-discovery confidence level, requirements-engineering status,
   and partially user-discovery's confirmed/not-confirmed extension) and is carried forward as this batch's
   no-invented-enum discipline, same as #521's.

## Adopt / skip

- **Adopt**: Cagan's question frame for `product-discovery.required_fields`; lean-startup's pre-registered
  fail-condition/decision-rule/time-box triple; Torres's need/pain/desire tag enum + snapshot-evidence-count
  rule; Guest/Hennink run-length saturation rule; EARS's pattern taxonomy as a regex-checkable requirement
  shape; 29148's verification-method enum; NN/g's screen+hotspot+feedback triple; UML's state/choice/terminal
  enum as the interaction-design node-type fallback.
- **Skip**: inventing a Cagan-attributed confidence-level scale; inventing a 29148-attributed status enum;
  treating Torres's need/pain/desire as if it already contains a confirmed/not-confirmed binary; forcing
  NN/g wireflow format onto static multi-page flows (interaction-design's spec notes this as a documented
  non-goal, not silently ignored).

## Gap line

Current state (survey.md): zero required fields, zero closed enums, zero reference-resolution rules for all
discovery/design-family roles — same starting point batch-1 had. Per role, the field this batch supplies:
Cagan's fields plus lean-startup's rigor fields (product-discovery); Torres's snapshot triple plus
need/pain/desire enum plus saturation rule (user-discovery); EARS's pattern grammar plus 29148's
verification-method enum (requirements-engineering); NN/g's screen/transition fields plus UML's node-type enum
(interaction-design). Two domains (product-discovery's confidence level, requirements-engineering's status)
have a confirmed absence of a citable closed enum — resolved as `string`, not invented, matching the schema's
own "string is the fallback, never speculative" rule.

## Sources

```
https://www.svpg.com/assessing-product-opportunities/
https://www.svpg.com/lean-canvas-vs-opportunity-assessment/
https://www.svpg.com/tag/opportunity-assessment/
https://itsadeliverything.com/opportunity-assessment-10-questions-to-evaluate-proposed-features-and-projects
https://caroli.org/en/10-questions-decide-worth-pursue-given-opportunity/
https://www.startupcommons.org/lean-startup-experiment-template.html
https://kromatic.com/blog/templates-suck-heres-our-lean-startup-template/
https://startupproject.org/guides/lean-startup/
https://roadmap.one/blog/posts/blog9-3-measuring-discovery-success/
https://www.producttalk.org/interview-snapshot/
https://www.producttalk.org/opportunity-solution-trees/
https://www.producttalk.org/glossary-discovery-opportunity-solution-tree/
https://journals.sagepub.com/doi/10.1177/1525822x05279903
https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0232076
https://en.wikipedia.org/wiki/Easy_Approach_to_Requirements_Syntax
https://ieeexplore.ieee.org/document/5328509/
https://www.iaria.org/conferences2013/filesICCGI13/ICCGI_2013_Tutorial_Terzakis.pdf
https://qracorp.com/guides_checklists/the-easy-approach-to-requirements-syntax-ears/
https://www.reqview.com/blog/requirements-traceability-matrix/
https://www.modernanalyst.com/Careers/InterviewQuestions/tabid/128/ID/1168/What-are-the-four-fundamental-methods-of-requirement-verification.aspx
https://www.nngroup.com/articles/wireflows/
https://www.nngroup.com/videos/wireflows-101/
https://www.uml-diagrams.org/state-machine-diagrams.html
https://en.wikipedia.org/wiki/UML_state_machine
```
