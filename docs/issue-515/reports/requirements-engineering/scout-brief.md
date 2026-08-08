# Scout brief — issue-515 (verification-family deliverable specs)

Mode: single background research agent (Agent tool, one dispatch, foreground-consumed same turn — batched-sequential fallback, not the 4-angle parallel sweep, because the target set is 5 named reference standards to confirm, not an open search space needing multiple independent angles). Stages used: 1.

Issue-515's own body already ran a broader in-conversation research pass naming the full deliverable catalog across all families; this pass narrows to field-level confirmation for the verification family only (execution-observation, conformance-review, defect-verification, security-threat-model, accessibility, secure-coding), since that's the batch-1 family this proposal commits to (see proposal.md).

## Findings (must-bes — what a real spec of this kind requires)

- **IV&V / DO-178C traceability matrix**: Requirement ID (structured prefix), Design Assurance Level, isDerived flag, Verification Method (Analysis/Demonstration/Inspection/Test), linked Test Case ID, Test Result. Maps directly to `requirements-engineering`'s traceability matrix and to a `conformance-review` per-claim record.
- **EARL 1.0** (W3C standard, directly liftable): `subject`, `test`, `result` (closed enum: passed/failed/cantTell/inapplicable/untested), `assertedBy`, optional `mode` (automatic/manual/semi-automatic). This is the tightest fit for `execution-observation` and `conformance-review` — 4 required fields, one closed enum, already standardized.
- **OWASP ASVS**: requirement ID, Level tag (L1-L3, cumulative), CWE mapping (bidirectional), verdict — fits `secure-coding`.
- **STRIDE / Threat Dragon**: title, diagramType, per-element cells; STRIDE's 6-category enum is the closed enum for `security-threat-model`'s finding classification. Per-threat field list (severity/status/mitigation) not independently confirmed from the schema pages fetched — gap, not blocker: STRIDE's category enum alone is enough to close the required-enum half of the spec; severity/status can borrow CVSS-style severity buckets already common practice, flagged for phase-2 authoring rather than invented here.
- **Bugmon** (closest real bug-repro-bot precedent for `defect-verification`): status tags on a ticket (`confirmed`/`verified`/`bisected`), reads the original report for repro env, auto-attempts reproduction. No formal JSON schema found — the closest available answer is a controlled-vocabulary status tag, not a structured record; `defect-verification`'s existing `reproduced|not-reproduced` verdict already matches this shape, so the realization work is adding the *evidence* and *repro steps* required fields around that verdict, not inventing a new verdict vocabulary.

## Performance axes (what strong instances compete on)

1. Verdict is a closed enum, never free text (EARL, ASVS, defect-verification's existing reproduced/not-reproduced).
2. Every verdict cites its evidence inline (EARL's `assertedBy`, IV&V's linked Test Case ID) — never an unlinked assertion.
3. Recomputable from raw evidence, not merely stated (this is issue-515's invariant 4, and it's what separates EARL from a plain checklist).

## Adopt / skip

- **Adopt**: EARL's 4-field shape (subject/test/result/assertedBy) as the base pattern for every verification-family role's per-claim record; STRIDE's closed threat-category enum; IV&V's requirement-ID-to-test-case link as the traceability-matrix reference-resolution rule.
- **Skip**: inventing a bespoke JSON schema from scratch for any of the six roles — every one has a real standard within reach; skip only where genuinely no standard exists (none found in this batch).

## Gap line

Current state (see `survey.md`) has zero required fields, zero closed enums, and zero reference-resolution rules for any of the six verification-family roles. The field, per role: enum vocab straight from source standard (EARL result / STRIDE category / ASVS level), required-field list per role's existing `produces` prose (already itemized, just not typed), reference-resolution rule = every cited claim/finding must resolve to an actual line/commit/file in the repo (mirrors IV&V's Test-Case-ID link and this repo's own `record-claim-guard.sh` orphan-path check).

## Sources

```
https://www.parasoft.com/learning-center/do-178c/requirements-traceability/
https://rtmify.io/standards/do-178c
https://www.faa.gov/sites/faa.gov/files/2022-02/VVSPT-E5-GDE-017_VRTM_V3.0.pdf
https://owasp.org/www-project-threat-dragon/docs-2/schema/
https://github.com/OWASP/threat-dragon/blob/main/ThreatDragonModels/demo-threat-model.json
https://www.threatdragon.com/docs/development/schema.html
https://www.w3.org/TR/EARL10-Schema/
https://softwaremill.com/implementing-owasp-asvs/
https://www.securecodinghub.com/blog/owasp-asvs-developers-complete-guide
https://github.com/MozillaSecurity/bugmon/blob/master/README.md
https://hacks.mozilla.org/2021/01/analyzing-bugzilla-testcases-with-bugmon/
```
