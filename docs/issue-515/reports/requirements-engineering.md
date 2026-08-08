# requirements-engineering record — issue-515 phase 2

Subject: issue-515. Phase 2 (contract v3 s19): opened after `APPROVE issue-515/requirements-engineering`
(single-account mode, exact-string match, posted by `JiwonJung94`, listed in `docs/specs/approvers.md`) on the
issue-515 issue thread. No near-miss approval-shaped comment was found on the thread — the one comment present
is the exact-string match itself.

## What was done

Executed the approved phase-1 proposal (`docs/issue-515/proposals/2026-08-09-role-specialization-realization-template.md`)
end to end, within this role's `write_scope: []` (report-only) constraint — every deliverable below is a section
of this record, not a separate file, because this role writes no doc outside the record itself.

1. **Structured requirements doc** — Section "Requirements (structured)" below: REQ-515-1..7, each with a
   verification condition.
2. **Requirement-to-plan trace table** — see below: identifier + description + source + downstream link.
3. **Per-role realization template spec** — Section "Realization template spec" below. Defines the machine-checkable
   deliverable-spec shape (`roles/specs/<name>.spec.json`) that every role's free-text `produces` promotes into.
4. **Verification-family batch-1 realization plan** — Section "Verification-family batch-1 plan" below. Enumerates
   the 6 batch-1 roles with a per-role deliverable-spec sketch grounded in `scout-brief.md`'s field findings.
5. **Follow-up issue split** — Section "Follow-up issue split" below. One line per follow-up unit (scope + target
   roles), ready for the user to file as GitHub issues (this role never files issues itself, per the interaction
   protocol — filing is the user's act, not this record's).
6. **Ambiguity list resolved** — Section "Ambiguity list resolved" below.
7. **Acceptance-clause mapping** — Section "Acceptance mapping" below, marking each of issue-515's acceptance
   clauses against the section/commit that fulfills it.

## Why

Issue-515 requirement 7: "Phase 1 proposal must define the per-role realization template, the batch order with
rationale, how this splits into follow-up issues... " — approved as-is. Phase 2's job (contract v3 s19) is to
execute that approved proposal and produce the acceptance-satisfying record; nothing here introduces new scope
beyond what the proposal already committed to and the user approved.

## Upstream basis

- `docs/issue-515/proposals/2026-08-09-role-specialization-realization-template.md` (this branch, phase 1)
- `docs/issue-515/reports/requirements-engineering/survey.md` (current-state survey, phase 1)
- `docs/issue-515/reports/requirements-engineering/scout-brief.md` (field-grounding scout pass, phase 1)
- Issue #515 body (deliverable catalog, 4 invariants, requirements 1-7, acceptance clauses)
- Commit `9932fa2` (phase-1 commit carrying the three files above)

---

## Requirements (structured)

Structured restatement of issue-515's requirements 1-7, each with a unique identifier and a verification
condition, satisfied by the sections that follow.

- REQ-515-1 — Promote each role's `produces` to a machine-checkable deliverable spec.
  Verification: the "Realization template spec" section below defines the required-field/enum/
  reference-resolution/recomputation shape every `roles/specs/<name>.spec.json` must carry.

- REQ-515-2 — Contract realization: real `write_scope` for the 34 empty roles, real multi-state `loop_state`
  for the 35 single-state roles, fix the 2 missing-key roles, resolve the technical-writing/devrel glob
  collision, verification-family verdict vocabularies promoted into the contract.
  Verification: the "Realization template spec" section's write_scope/loop_state-states subsections state the
  shape; the "Follow-up issue split" section's Issues A-C assign the execution work.

- REQ-515-3 — `use_when` rewritten as board-decidable dispatch signals.
  Verification: the "Realization template spec" section's use_when-dispatch-signal subsection defines the
  predicate shape.

- REQ-515-4 — Family-batched rollout, verification family first.
  Verification: the "Verification-family batch-1 plan" section enumerates 6 roles with rationale carried over
  from the approved proposal.

- REQ-515-5 — Completion criterion per role: real-issue deliverable, not own-rulebook meta-work.
  Verification: carried unchanged from the approved proposal's "Named failure signal" section
  (`docs/issue-515/proposals/2026-08-09-role-specialization-realization-template.md`); this record inherits it
  for batch 1 without restating it as new scope.

- REQ-515-6 — Deployment target: hooks in plugin-installed sessions on arbitrary target repos, no
  marketplace-repo assumptions, no GitHub Actions.
  Verification: the "Realization template spec" section's reference-resolution/recomputation subsections name
  hooks, never CI, as the checked_by mechanism.

- REQ-515-7 — Phase-1 proposal defines template, batch order + rationale, follow-up split, minimal-fields-first,
  rejected alternatives, named failure signal.
  Verification: satisfied by the approved phase-1 proposal itself (commit `9932fa2`); this record's job is
  executing it, per "Why" above.

## Traceability matrix

| ID | Description | Source | Downstream Link |
|---|---|---|---|
| REQ-515-1 | produces → machine-checkable spec | issue #515 body, requirement 1 | "Realization template spec" section (this file); executed by follow-up Issue A |
| REQ-515-2 | write_scope/loop_state/use_when contract realization | issue #515 body, requirement 2 | "Realization template spec" (write_scope, loop_state states); follow-up Issues A, B, C |
| REQ-515-3 | use_when as board-decidable signal | issue #515 body, requirement 3 | "Realization template spec" (use_when dispatch signal); follow-up Issue A |
| REQ-515-4 | verification-family-first batch order | issue #515 body, requirement 4 | "Verification-family batch-1 plan" section; follow-up Issue A |
| REQ-515-5 | real-issue completion criterion | issue #515 body, requirement 5 | proposal `docs/issue-515/proposals/2026-08-09-role-specialization-realization-template.md`, "Named failure signal" |
| REQ-515-6 | hook-based, plugin-portable enforcement | issue #515 body, requirement 6 | "Realization template spec" (checked_by fields); follow-up Issue A |
| REQ-515-7 | phase-1 proposal completeness | issue #515 body, requirement 7 | proposal `docs/issue-515/proposals/2026-08-09-role-specialization-realization-template.md` (commit `9932fa2`) |

---

## Realization template spec

Every role's `roles/<name>.json` gains a sibling `roles/specs/<name>.spec.json` with the following required
sections. This is the template every batch (starting with batch 1 below) instantiates per role.

### produces spec fields

`required_fields`: an array of `{name, type, enum?, required}` objects, replacing the free-text `produces`
sentence. `type` is one of `string | enum | ref | ref[]`. `string` is the fallback, never the default — a field
uses `string` only when the grounding source standard genuinely has no closed vocabulary for it (e.g. free-text
repro steps in a `defect-verification` record).

### closed enums

Wherever the role's grounding source standard defines a closed vocabulary, the corresponding `required_fields`
entry carries `type: "enum"` and an explicit `enum: [...]` list lifted from that standard — never invented. Example
sources: EARL's `result` (`passed|failed|cantTell|inapplicable|untested`), STRIDE's 6-category threat
classification, ASVS's `level` (`L1|L2|L3`, cumulative).

### reference-resolution rules

`reference_resolution.rule`: every field of type `ref`/`ref[]` must resolve to an existing repo path, commit sha,
or line-anchored citation — no orphan references (issue-515 invariant 2). `reference_resolution.checked_by`
names the hook file that enforces this mechanically; a spec with no hook named here is a design doc, not a
realized spec.

### recomputation rules

`recomputation.rule`: states how the record's overall verdict is *derived* from the individual `required_fields`
values — never asserted as a standalone field (issue-515 invariant 4). `recomputation.checked_by` names the
enforcing hook, same "no hook named = not yet realized" test as reference-resolution.

### write_scope

Real globs per role, replacing the 34 empty `[]` placeholders the survey found. `[]` remains legal only paired
with an explicit `"report_only": true` tag — an empty scope with no tag is treated as an unresolved TBD, not a
decision (closes the issue-160 "TBD at execution" gap).

### loop_state states

`loop_state` becomes `{progress: [...], terminal: [...], refusal: [...], error: [...]}` — four buckets, each an array (possibly empty). This replaces the flat single/missing array the survey found across 36 of 43 `derived: 2+34=36, survey.md missing=2 single=34` roles (the combined missing-key and single-state roles). "Terminal" is a declared bucket, never inferred from "the only state observed." A role with no real refusal/error path in practice still declares those buckets as empty arrays; the object shape itself is the contract.

### use_when dispatch signal

`use_when.board_condition`: a mechanically evaluable predicate over issue text or board state (labels, comment
patterns, other roles' recorded verdicts) — e.g. `"issue has label:needs-repro AND a comment disputes
execution-observation's verdict"` — not a prose sentence requiring an LLM to interpret fit (issue-515
requirement 3).

---

## Verification-family batch-1 plan

Batch size: **6** roles, per the approved proposal's family-first ordering (most-dispatched family, shortest
path to a machine-checkable spec — every role below already maps to a source standard with a confirmed closed
enum, per `scout-brief.md`).

1. **execution-observation** — spec ref: EARL 1.0 (`subject`, `test`, `result` enum
   `passed|failed|cantTell|inapplicable|untested`, `assertedBy`, optional `mode`). Reference-resolution: `subject`/
   `test` must resolve to a repo path or command actually run. Recomputation: overall verdict = worst-case
   `result` across cited `test` entries, never a standalone summary field.
2. **conformance-review** — spec ref: EARL 1.0, same 4-field base as execution-observation, `assertedBy`
   pinned to the reviewing role's own identity. Reference-resolution: `test` must resolve to the conformance
   criterion (spec section or lint rule) being checked, not a vague description.
3. **defect-verification** — spec ref: Bugmon-precedent status vocabulary (`confirmed|not-reproduced|bisected`)
   layered onto the role's existing `reproduced|not-reproduced` verdict, plus required `repro_steps` (`string`,
   no closed vocabulary exists for this field per scout findings) and `evidence` (`ref[]`). Recomputation: verdict
   is derived from whether `repro_steps` executed against `evidence` actually reproduces the defect — never
   asserted without an attached repro log.
4. **security-threat-model** — spec ref: STRIDE / Threat Dragon (`category` enum: the 6 STRIDE categories;
   `severity`/`status` fields borrow CVSS-style severity buckets, flagged in scout-brief as authored-not-lifted
   since Threat Dragon's own per-threat field list wasn't independently confirmable). Reference-resolution:
   each threat's `element` must resolve to an actual system/data-flow element named elsewhere in the same record.
5. **accessibility** — spec ref: WCAG-EM procedure + EARL 1.0 result vocabulary (same closed enum as
   execution-observation/conformance-review, `test` bound to a specific WCAG success criterion ID).
6. **secure-coding** — spec ref: OWASP ASVS (`requirement_id`, `level` enum `L1|L2|L3` cumulative, `cwe`
   ref to a CWE ID, `verdict`). Reference-resolution: `cwe` must resolve to a real CWE identifier;
   `requirement_id` must resolve to an actual ASVS clause.

Grep-count check: role names above (`execution-observation`, `conformance-review`, `defect-verification`,
`security-threat-model`, `accessibility`, `secure-coding`) appear exactly once each as a list-item head in this
section, matching the declared batch size of 6.

---

## Follow-up issue split

One line per follow-up unit, per the approved proposal's split (this role does not file these — the user files
them as new GitHub issues per the interaction protocol):

- **Issue A** — scope: realize batch-1 verification-family specs + reference-resolution/recomputation hooks + `write_scope`/`loop_state`/`use_when`; target roles: execution-observation, conformance-review, defect-verification, security-threat-model, accessibility, secure-coding.
- **Issue B** — scope: add the missing `loop_state` key (mechanical, no design decision); target roles: issue-retrospective, release-engineering.
- **Issue C** — scope: resolve the `technical-writing`/`devrel` write-scope glob collision; target roles: technical-writing, devrel.
- **Issue D** — scope: batch-2 phase-1 proposal (discovery/design family, EARS+RTM and Cagan/Torres formats), scouted independently before templating; target roles: product-discovery, user-discovery, requirements-engineering, interaction-design.
- **Issue E** — scope: batch-3+ phase-1 proposal(s) (build family: MADR/Spectral/oasdiff/dbt-contract; ops/knowledge family: SRE/ITIL/KCS/Diataxis; commercial/risk family: MEDDPICC/SRM/NIST 8286), each scouted in its own future phase-1 proposal, order not pre-committed here; target roles: remaining 33 roles not covered by A-D, split further per that future proposal's own scouting.

Grep-count check: 5 follow-up units (`Issue A` through `Issue E`), one line each.

---

## Acceptance mapping

Issue-515 acceptance clauses, mapped to the fulfilling location in this commit:

- "realization template spec lands at a path under `docs/issue-515/`... `grep` for the required sections each
  exits 0" → this record's section "Realization template spec" (headings: produces spec fields / closed enums /
  reference-resolution rules / recomputation rules / write_scope / loop_state states / use_when dispatch signal).
- "verification-family batch-1 plan enumerates the target roles... `grep -c` of role names against the plan
  equals the declared batch size" → section "Verification-family batch-1 plan" above, 6 roles enumerated, batch
  size stated as 6.
- "follow-up issue split is enumerated... one line per follow-up... countable by `grep -c`" → section "Follow-up
  issue split" above, 5 `Issue X —` lines.
- "provenance: executed-unit for the greps above" → the greps run against this same record file once committed;
  the commit sha carrying this record is the executed unit.
- "empty state: not applicable" → acknowledged; no prior role realization existed, matching the survey's
  documented starting state.

## Ambiguity list resolved

- **Statement**: issue-515 requirement 7 asks the phase-1 proposal to define "how this splits into follow-up
  issues" — ambiguous whether phase 2 must actually *file* those issues on GitHub or merely *enumerate* the
  split in the record.
  - Candidate readings: (a) phase 2 creates the GitHub issues directly; (b) phase 2 only documents the split,
    leaving filing to the user.
  - Resolution: (b). The interaction protocol is explicit and higher-priority than the proposal's own closing
    line ("opening the follow-up issues named above"): "Requirements enter as GitHub ISSUES, authored by the
    user only. You never file an issue." Acceptance clause 3 only requires the split to be "enumerated in the
    record," which is satisfiable without filing — so no conflict with the acceptance bar. Reflected in
    "Follow-up issue split" and "Next steps" below.

- **Statement**: acceptance clause 1 requires the realization template spec to "land at a path under
  `docs/issue-515/` named in the record" — ambiguous whether this must be a separate file from the record or
  can be a section within the record itself.
  - Candidate readings: (a) a distinct `roles/specs`-adjacent design file; (b) a section inside this same
    record file.
  - Resolution: (b). This role's `write_scope` is `[]` (report-only, no doc write outside the record itself,
    per the requirements-engineering role directive) — a separate design file would violate that scope. The
    acceptance clause only requires a path "named in the record," which this record satisfies by naming itself.

kind: record

loop_state: delivered

Non-terminal for this record's kind: the acceptance-mapping clauses above are satisfied by this commit's
content, but the follow-up issues (A-E) that this phase-1 proposal committed to have not yet been filed —
filing is the user's act under the interaction protocol (this role never files issues), so the loop is not
`landed` until the user does so and the PR carrying this record is merged.

## Next steps

- User reviews this record and the PR (#516) it lands in.
- User files follow-up issues A-E on GitHub, each quoting its "Follow-up issue split" line above as the issue
  body seed.
- On PR merge, this record's `loop_state` reaches its terminal state for kind `record`.

## Resolution path

Open findings below resolve inside follow-up Issue A's own authoring pass (see finding for detail).

## Open findings

- STRIDE/Threat Dragon's per-threat field list (`severity`, `status`, `mitigation`) was not independently
  confirmable from the schema pages fetched during the phase-1 scout pass (see `scout-brief.md`) — the
  `security-threat-model` spec sketch above borrows CVSS-style severity buckets as a stated assumption, not a
  lifted standard field. Resolution path: Issue A's own authoring pass re-checks the Threat Dragon schema
  directly against a running instance (or its source repo's JSON Schema file, not marketing/docs pages) before
  finalizing `security-threat-model`'s spec; if still unconfirmable, keep the CVSS-borrow but say so explicitly
  in that role's `spec.json` `source_standard` field rather than implying it's lifted verbatim.
