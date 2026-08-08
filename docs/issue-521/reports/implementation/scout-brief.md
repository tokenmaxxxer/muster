# Scout brief — issue-521 (batch-1 verification-family spec realization)

Mode: single foreground research agent (Agent tool, one dispatch, result consumed same turn — batched-sequential,
not the 4-angle parallel sweep). Stages used: 1. This is a targeted addendum to #515's own
`docs/issue-515/reports/requirements-engineering/scout-brief.md`, which already field-confirmed EARL 1.0, OWASP
ASVS, Bugmon, and IV&V/DO-178C traceability for this same 6-role batch. This pass closes the two gaps #515 left
open: WCAG-EM/ACT (named in issue-521 requirement 2 but not in #515's sweep) and ISO/IEC/IEEE 29119-3 (named in
issue-521 requirement 2; #515 only reached Bugmon for `defect-verification`) — plus resolves #515's stated open
finding on Threat Dragon's per-threat field list.

## Findings (must-bes)

- **WCAG-EM 2.0** (W3C, https://www.w3.org/TR/wcag-em/): defines 5 evaluation steps (define scope → explore
  target → select sample → evaluate sample → report findings); the report step's required fields are evaluator
  identity, scope, conformance target, accessibility-support baseline, explored technologies, and per-sample
  outcomes.
- **ACT Rules Format** (W3C, https://www.w3.org/TR/act-rules-format/): each rule requires `applicability` +
  one or more `expectation`s, and defines its own outcome vocabulary — `inapplicable | passed | failed |
  cantTell | untested` — a 5-value superset of EARL 1.0's 4-value `result` enum (EARL lacks `untested`). The
  spec explicitly states ACT outcomes "can be expressed using the outcome property of EARL 1.0 Schema" —
  compatibility, not identity. **Decision this brief makes**: `accessibility`'s `result` field uses the ACT
  5-value enum (superset), not EARL's 4-value one, since ACT is the accessibility-specific profile and issue-521
  names WCAG-EM/EARL/ACT together.
- **ISO/IEC/IEEE 29119-3 Incident Report** (clause 7.12, Annex A.2.15 — full text mirror consulted at
  https://wildart.github.io/MISG5020/standards/ISO-IEC-IEEE-29119-3.pdf since iso.org is paywalled): defines
  timing information, originator, context, description of the incident, originator's severity assessment,
  originator's priority assessment, risk, and status. No standalone "steps to reproduce" field — that content
  lives inside "description"/"context." This confirms #515's finding that `defect-verification`'s
  `reproduced|not-reproduced` + free-text `repro_steps` (no closed vocabulary — 29119-3 doesn't define one
  either) is the right shape; 29119-3 additionally grounds adding `severity` and `status` as fields, matching
  the issue text's named `ISO 29119-3/Bugmon`.
- **OWASP Threat Dragon schema**, resolved (previously #515's open finding — the docs page returned HTTP 403 in
  this pass too, but the model file itself fetched cleanly at
  https://raw.githubusercontent.com/OWASP/threat-dragon/main/ThreatDragonModels/demo-threat-model.json): a
  per-threat object carries `status`, `severity`, `title`, `type` (STRIDE category), `description`, `mitigation`
  as real, present fields — not an authored guess. This closes #515's open finding: `severity`/`status`/
  `mitigation` are lifted from the schema, not borrowed from CVSS as previously assumed.

## Performance axes

Same three as #515 (verdict is a closed enum; every verdict cites evidence inline; recomputable from raw
evidence) — unchanged, since this pass only fills two field-level gaps within the same batch, not a new family.

## Adopt / skip

- **Adopt**: ACT's 5-value outcome enum for `accessibility` (supersedes reusing EARL's 4-value enum verbatim);
  29119-3's severity/status/context shape for `defect-verification`; Threat Dragon's confirmed
  status/severity/title/type/description/mitigation field set for `security-threat-model` (replacing the
  CVSS-borrow assumption).
- **Skip**: writing a bespoke enforcement engine per role for `recomputation` — the same worst-case-across-
  verdicts rule (already adopted from EARL/ACT semantics) covers execution-observation, conformance-review,
  and accessibility; defect-verification and security-threat-model get a one-line role-specific recomputation
  rule instead of a shared one, since their verdict shapes differ (repro-based vs. STRIDE-per-threat).

## Gap line

Before this pass: `accessibility` and `defect-verification` had no field-level standard confirmed (only WCAG/
Bugmon named in prose); `security-threat-model`'s per-threat fields were an unconfirmed CVSS-borrow assumption.
After this pass: all 6 roles have a confirmed, sourced field list. Nothing remains unconfirmed.

## Sources

```
https://www.w3.org/TR/wcag-em/
https://www.w3.org/TR/act-rules-format/
https://wildart.github.io/MISG5020/standards/ISO-IEC-IEEE-29119-3.pdf
https://www.iso.org/standard/56737.html
https://raw.githubusercontent.com/OWASP/threat-dragon/main/ThreatDragonModels/demo-threat-model.json
```

(Carried over from #515's own scout-brief for the remaining 4 roles: `https://www.w3.org/TR/EARL10-Schema/`,
`https://owasp.org/www-project-threat-dragon/docs-2/schema/`, `https://softwaremill.com/implementing-owasp-asvs/`,
`https://github.com/MozillaSecurity/bugmon/blob/master/README.md`, DO-178C/IV&V traceability sources — see
`docs/issue-515/reports/requirements-engineering/scout-brief.md`.)
