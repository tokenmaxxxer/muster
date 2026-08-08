# Scout brief — build family (12 roles)

Mode: parallel Agent-tool fan-out, 1 stage (sweep only; saturation reached — each
role's canonical source converged on first pass, no deepening needed).

Must-bes (per role, chosen canonical standard, 1-2 mandated attributes):
- api-design: Spectral ruleset (`given`/`then` rule shape) + OpenAPI schema conformance.
- architecture: MADR (context/problem, decision drivers, considered options, outcome).
- data-engineering: dbt model contracts (`columns[].name`+`data_type`, `constraints`).
- data-modeling: no independently-verified distinct primary source found this pass
  (gap, stated as assumption) — candidate Kimball dimensional-modeling conventions or
  the Data Contract Specification (bitol.io), not fetched; flagged for the delivery
  PR's own scout pass rather than asserted here.
- technical-feasibility: ADR-style spike record (goal, timebox, findings, decision).
- ml-engineering: Model Cards (Mitchell et al. 2019) — sections incl. intended use,
  training/eval data, ethical considerations.
- refactoring-legacy: Fowler's Refactoring Catalog (name, motivation, mechanics, example).
- performance-engineering: Google SRE SLO/error-budget (SLI, SLO target, error budget).
- release-engineering: Keep a Changelog (Added/Changed/Deprecated/Removed/Fixed/Security).
- test-authoring: IEEE 829's test case specification format (ID, items, input/output
  spec, environment).
- observability: OpenTelemetry semantic conventions (span/metric attribute naming).
- implementation: Conventional Commits v1.0.0 (`<type>[scope]: <desc>`, `BREAKING CHANGE:`).

Performance axes across the family: machine-parseable grammar (Spectral rules,
Conventional Commits header) vs. narrative-with-required-sections (MADR, Model Cards,
Fowler catalog) — this splits `required_fields` type choice (string vs. enum/ref) per
role, not one shape for the whole family.

Adopt: cite the standard's own required-section list verbatim as `required_fields`.
Skip: don't invent a closed enum where the standard's field is prose (matches #524's
no-invented-enum precedent).

Segment fit: these are all engineering-artifact roles — same segment as batch-1 and
batch-2's verification/discovery roles, template shape applies unchanged.

Gap line: current `roles/*.json` for all these roles already have empty `write_scope`
+ single-state `loop_state` (the #515-documented defect); none pre-meet any must-be.

Sources:
- https://adr.github.io/madr/
- https://stoplight.io/open-source/spectral
- https://docs.getdbt.com/docs/collaborate/govern/model-contracts
- https://adr.github.io/
- https://arxiv.org/pdf/1810.03993
- https://refactoring.com/catalog/
- https://sre.google/workbook/error-budget-policy/
- https://sre.google/workbook/implementing-slos/
- https://keepachangelog.com/
- https://www.stickyminds.com/article/software-test-case-specification-ieee-829-1998-format-template
- https://opentelemetry.io/docs/specs/semconv/
- https://www.conventionalcommits.org/en/v1.0.0/
