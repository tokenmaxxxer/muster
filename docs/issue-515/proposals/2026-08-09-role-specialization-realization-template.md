---
status: proposed
files:
  - docs/issue-515/reports/requirements-engineering/survey.md
  - docs/issue-515/reports/requirements-engineering/scout-brief.md
  - docs/issue-515/proposals/2026-08-09-role-specialization-realization-template.md
---

# Proposal — per-role realization template + verification-family batch 1 (issue-515, phase 1)

## Request (paraphrased)

Issue-515 asks for phase 1 only: define a per-role realization template that turns each of the 43 roles' free-text `produces` into a machine-checkable deliverable spec, realize `write_scope`/`loop_state`/`use_when` per role against that template, order the rollout family-by-family (verification first), and split the program into follow-up issues — proposal only, no `roles/*.json` edits in this PR.

## Constraints

- Phase-1 output only: this proposal + its survey/scout-brief. No `roles/*.json` edits, no hook code, no role rulebook edits — those are phase-2/follow-up-issue work.
- Grounded in the deliverable catalog issue-515 already names (MADR, Spectral/oasdiff/dbt-contract, Kayenta, IV&V, Bugmon, STRIDE/Threat Dragon, WCAG-EM/EARL, DPIA, Cagan, EARS+RTM, Torres, Dunford, SRE postmortems, ITIL, KCS, Diataxis, MEDDPICC, SRM, NIST 8286) — adopt existing formats, don't invent (issue-515 invariant 3).
- Enforcement target is hooks running in plugin-installed sessions on arbitrary target repos — never GitHub Actions, never marketplace-repo-anchored paths.
- Minimal-required-fields-first, expand only on evidence (issue-515 requirement 7).

## What will be done

### 1. The per-role realization template

Every role's `roles/<name>.json` gains a sibling deliverable-spec file, `roles/specs/<name>.spec.json`, with this shape (JSON Schema-flavored, not a full JSON Schema document — kept minimal per the evidence-expansion constraint):

```json
{
  "role": "<name>",
  "source_standard": "<the existing format this borrows from, e.g. EARL 1.0 / STRIDE / IV&V RTM / MADR — 'none' only if scout genuinely found nothing>",
  "required_fields": [
    {"name": "...", "type": "string|enum|ref|ref[]", "enum": ["..."], "required": true}
  ],
  "reference_resolution": {
    "rule": "every field of type ref/ref[] must resolve to an existing repo path, commit sha, or line-anchored citation",
    "checked_by": "hook: <hook filename>"
  },
  "recomputation": {
    "rule": "how the overall verdict is derived from the individual required_fields — never asserted standalone",
    "checked_by": "hook: <hook filename>"
  },
  "write_scope": ["<real globs, or [] with a 'report-only' tag if the role is genuinely report-only>"],
  "loop_state": {
    "progress": ["..."],
    "terminal": ["..."],
    "refusal": ["..."],
    "error": ["..."]
  },
  "use_when": {
    "board_condition": "a mechanically checkable predicate over issue text / board state, e.g. 'issue has label:needs-repro AND a comment disputes execution-observation's verdict' — not a Korean sentence a human interprets"
  }
}
```

Design rationale per field:

- `source_standard` is mandatory and forces the minimal-invention rule to be checked at authoring time, not trusted to memory.
- `required_fields` uses closed `enum` wherever the source standard has one (EARL's `result`, STRIDE's threat category, ASVS's `level`) — free-text `string` is the fallback, not the default.
- `reference_resolution` and `recomputation` each name the hook that checks them — a spec with no hook listed is not yet realized, it's still a design doc. This makes "realized" mechanically distinguishable from "designed."
- `write_scope` realization keeps `[]` legal but requires an explicit `report-only` tag alongside it, so an empty scope is a stated decision, not an unresolved TBD (closes the issue-160 "TBD at execution" gap the survey found).
- `loop_state` becomes an object with 4 buckets instead of a flat array, so "terminal" is explicit rather than inferred from "the only state present." A role with no real refusal/error path in practice still declares empty arrays for those buckets — the object shape itself is the contract, not just its non-empty entries.
- `use_when.board_condition` is the board-decidability requirement (issue-515 req 3): written so a hook (or the orchestrator) can evaluate it against issue labels/comments/state without an LLM re-reading Korean prose to decide fit.

### 2. Family batch order

Batch 1 (this issue's immediate follow-up): **verification family** — `execution-observation`, `conformance-review`, `defect-verification`, `security-threat-model`, `accessibility`, `secure-coding`.

Rationale (per issue-515 req 4 and the scout-brief field grounding):
- Most-dispatched family already, per issue-515's own framing — realizing it first gives the orchestrator its highest-traffic path to a REAL completion criterion soonest.
- Shortest distance to a machine-checkable spec: every one of the six roles maps to a standard with a closed verdict enum already confirmed in the scout pass (EARL's 4-value result, ASVS levels, STRIDE's category enum, defect-verification's existing reproduced/not-reproduced). No batch-1 role requires inventing a new vocabulary from scratch.
- Downstream roles depend on verification-family verdicts being trustworthy (e.g. `defect-verification`'s hand-off assumes `execution-observation`/`conformance-review` verdicts are real) — realizing the family that everything else cites first reduces rework risk in later batches.

Batch 2 (follow-up): discovery/design family (`product-discovery`, `user-discovery`, `requirements-engineering`, `interaction-design`) — EARS+RTM and Cagan/Torres formats already named in issue-515's catalog, next-shortest path.

Batch 3+ (follow-up, order TBD per-batch in that batch's own phase-1 proposal): build family (MADR/Spectral/oasdiff/dbt-contract), ops/knowledge family (SRE/ITIL/KCS/Diataxis), commercial/risk family (MEDDPICC/SRM/NIST 8286). Not sequenced further here — each batch gets its own scouted phase-1 proposal, per this same template, rather than pre-committing an order this proposal has not scouted evidence for.

### 3. Split into follow-up issues

- **Issue A (batch 1 execution)**: realize the 6 verification-family roles' `roles/specs/*.spec.json` + author the reference-resolution/recomputation hooks + realize their `write_scope`/`loop_state`/`use_when`. One issue, one PR per role-family batch (not per role) — six roles share enough structural overlap (all verdict-shaped, all citing evidence) that splitting further would fragment a single reviewable design.
- **Issue B**: fix the 2 missing-`loop_state`-key roles (`issue-retrospective`, `release-engineering`) — mechanical, no design decision, can land independently and immediately rather than waiting on any family batch.
- **Issue C**: resolve the `technical-writing`/`devrel` write-scope glob collision the issue names — independent of the family-batch sequencing, narrow enough to be its own issue.
- **Issue D+ per remaining batch**: one phase-1-proposal issue per batch (2, 3, ...), each scouting that batch's own deliverable catalog before templating, per the same process this proposal used.

### 4. Minimal-required-fields-first, evidence-based expansion

Batch-1 specs start with only the fields the source standard requires at its own minimum tier (EARL's 4 required fields, not its full vocabulary; ASVS Level 1 only, not L1-L3 simultaneously). Expansion to more fields/higher tiers happens only when a real dispatched role's record is rejected by conformance-review or a hunter finding for being too coarse to be checkable — not speculatively upfront. This mirrors issue-515's own explicit tradeoff acknowledgment.

### 5. Rejected alternatives

- **One universal deliverable schema for all 43 roles.** Rejected: the scout pass confirms each role family maps to a different real-world standard (EARL vs. IV&V vs. MADR); forcing one shape would either over-fit verification-family roles onto commercial-family roles or dilute the closed-enum benefit that makes EARL/STRIDE/ASVS checkable in the first place.
- **GitHub Actions-based enforcement.** Rejected per issue-515 req 6 — this system must work in plugin-installed sessions on arbitrary target repos with no CI assumption; hooks are the only surface that holds in that deployment shape.
- **Realizing all 43 roles in one PR.** Rejected: issue-515 itself calls this a multi-round program; one PR touching 43 roles' specs simultaneously is unreviewable and makes the verification-family-first ordering meaningless (everything lands at once regardless of order).
- **Keeping `write_scope: []` silently for report-only roles (no explicit tag).** Rejected: indistinguishable from an unresolved TBD, which is exactly the state issue-160 already left behind and issue-515 is trying to close.

### 6. Named failure signal

If, after batch 1 lands and a verification-family role is dispatched on a real issue, its record still passes `record-claim-guard.sh`-equivalent checks (or the new reference-resolution/recomputation hooks) while a human reviewer can point to a specific claim in it that isn't actually backed by cited evidence — the hooks are checking shape, not substance, and the realization has produced a more convincing shell rather than a real deliverable. That is the signal to stop expanding batch coverage and go back to tightening batch 1's recomputation rules before touching batch 2.

## Out of scope (this PR)

- Any `roles/*.json` edit.
- Any hook implementation.
- Any batch-2+ family's field grounding (deferred to that batch's own phase-1 proposal).
- `docs/specs/record-fields-terminal-states.json` authoring — a phase-2, per-role call once loop_state buckets are actually realized.

## How you'll know it worked

- This proposal, its survey, and its scout-brief are committed and pushed on `issue-515/requirements-engineering`, and a PR is open against `main`.
- Issue-515's phase-1 approval gate (an `APPROVE issue-515/requirements-engineering` comment, per contract v3 s19) is what authorizes phase 2 (writing `docs/issue-515/reports/requirements-engineering.md` and opening the follow-up issues named above) — not part of this PR's own success criterion.
