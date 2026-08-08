# Scout brief — commercial/risk family (10 roles)

Mode: parallel Agent-tool fan-out, 1 stage (sweep only; saturation reached).

Must-bes:
- sales: MEDDPICC — Metrics, Economic Buyer, Decision Criteria, Decision Process,
  Paper Process, Identify Pain, Champion, Competition.
- marketing: April Dunford's positioning framework — competitive alternatives,
  unique attributes, value/themes, target market, market category.
- partnerships-bd: ISO 44001:2017 Collaborative Business Relationship Management —
  relationship management plan across an eight-stage lifecycle, governance/exit
  strategy.
- risk-management: NIST SP 800-161r1 (C-SCRM) — risk register entries (description,
  likelihood, impact, treatment, owner); NIST IR 8286 lineage cited by secondary
  sources but not independently fetched this pass (flagged as an assumption pending
  a direct nist.gov confirmation at delivery time).
- finance-unit-economics: no single primary-source standards body found (gap, stated
  as assumption) — de facto convention: SaaS unit-economics metric set (CAC, LTV,
  LTV:CAC ratio, CAC payback, Rule-of-40), popularized by Bessemer's Cloud reports;
  worth a direct bvp.com fetch before finalizing.
- growth-analytics: AARRR "Pirate Metrics" (Dave McClure) + North Star Metric —
  metrics per funnel stage, one designated North Star Metric; original McClure
  source not independently fetched (assumption, flagged).
- legal-compliance: GDPR Article 35(7) DPIA — systematic processing description,
  necessity/proportionality assessment, risk assessment, mitigation measures.
- market-analysis: Porter's Five Forces (HBR) — assessed across new entrants,
  supplier power, buyer power, substitutes, rivalry.
- pr-communications: AMEC Integrated Evaluation Framework (Barcelona Principles) —
  chain of objectives/inputs/activities/outputs/outtakes/outcomes/impact across
  paid/earned/shared/owned channels.
- pricing: Van Westendorp Price Sensitivity Meter — four price-perception questions
  plotted to an acceptable price corridor.

Performance axes: qualification checklist (MEDDPICC) vs. narrative canvas (Dunford
positioning) vs. numeric metric ratio (LTV:CAC, AARRR, Van Westendorp) — same
required_fields type-mix pattern seen in the other two families.

Adopt: MEDDPICC's and Porter's closed enumerable structure (checklist fields,
five-force assessment) directly as required_fields. Skip: asserting a closed enum
for finance-unit-economics/growth-analytics where the source is convention, not a
ratified standard — stay `string`/`ref` typed pending stronger sourcing.

Segment fit: revenue/risk-facing roles, distinct from both build and ops/knowledge —
justifies the third family boundary the issue itself proposes.

Gap line: finance-unit-economics, growth-analytics, and (partly) risk-management's
NIST IR 8286 lineage are the weakest-sourced roles across the family — flagged so
the delivery batch that includes them runs one more deepening pass before authoring
`source_standard` fields, rather than asserting these citations as confirmed here.

Sources:
```
https://meddicc.com/meddpicc-sales-methodology-and-process
https://www.aprildunford.com/books
https://www.kathirvel.com/guide-april-dunford-positioning-framework/
https://www.iso.org/standard/72798.html
https://www.iso.org/standard/72799.html
https://csrc.nist.gov/pubs/sp/800/161/r1/upd1/final
https://www.dualentry.com/blog/saas-unit-economics
https://www.productcompass.pm/p/aarrr-pirate-metrics
https://gdpr.eu/data-protection-impact-assessment-template/
https://hbr.org/2008/01/the-five-competitive-forces-that-shape-strategy
https://amecorg.com/amecframework/
https://en.wikipedia.org/wiki/Van_Westendorp's_Price_Sensitivity_Meter
```
