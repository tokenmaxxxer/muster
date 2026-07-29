# Product record — issue-54: structural-context reporting

Status: finalized (phase 2). Approved via `APPROVE issue-54/product` on PR #55.

loop_state: landed
upstream: docs/issue-54/proposals/requirements.md (phase-1 proposal, approved as-is via `APPROVE issue-54/product` on PR #55)

## What was done

Finalized the phase-1 proposal into this binding product record: the flow/stage/next reporting
schema, its compactness rules, batched-decision composition, and the 9-point acceptance-criteria
checklist, all reproduced below as the authoritative version. No changes were made to the proposal
content at approval — the approver accepted it as written, so this record's role is to promote that
proposal from draft to binding record, not to re-decide anything.

## Decision

Adopt the requirements proposed in `docs/issue-54/proposals/requirements.md` as-is, no revisions
requested at approval. This record is the authoritative deliverable for issue #54's product stage;
the proposal and survey remain as supporting phase-1 material.

## Requirements summary (binding)

### 1. Schema

Every orchestrator report about an item carries three additive fields, alongside the existing
issue-34 minimum item list and issue-44 role-classification line where still live in the same turn:

- **flow** — issue number + ≤8-word restatement of the user's original ask (short-form
  issue-number-only on repeat mention within a turn, per compactness rule 2).
- **stage** — one of exactly six fixed values: `proposal` / `approval` / `implementation` /
  `verification` / `merge` / `close`.
- **next** — one short clause per decision branch actually open (at minimum: proceed vs.
  stop/rework), never forecasting beyond the immediately next stage.

All three are computed at report time from already-existing state (the GitHub issue, the
PR/proposal under discussion, `docs/issue-<n>/reports/<role>.md` and its `loop_state` where
present) — no new stored artifact.

### 2. Compactness rules

One line per field; `flow` full restatement only on first mention per flow per turn (issue-number
only thereafter); `stage` is single-word fixed vocabulary; `next` capped at two short branch
clauses; the three fields sit as a compact prefix, not a new prose section.

### 3. Batched-decision composition

Group by **flow first**, one header per flow. Under each flow header, one line per item:
`stage → item-specific next`. A shared `next` is permitted only within a flow+stage group when
branch outcomes are identical across items; otherwise state `next` per item. Different flows are
never merged under one header even if they share a stage.

### 4. Acceptance criteria (binding on the coding-stage `run.md` edit)

1. Every step-5 report includes a `flow` reference identifying the owning original request.
2. Every such report includes a `stage` value from the fixed six-value vocabulary, matching the
   item's actual position.
3. Every such report includes a `next` clause per open decision branch, capped at the immediately
   next stage.
4. The three fields are structurally distinguishable from, not interleaved into, the issue-34
   what/why/what-changed/how-verified fields.
5. The three fields never duplicate the issue-44 role-classification line.
6. Multi-item turns group by flow first, with shared `next` only within an identical-outcome
   flow+stage group — no default to per-item full `flow` restatement.
7. No criterion implies a new stored artifact; all three fields are computed at report time from
   state the orchestrator already reads.
8. Compactness caps (≤8-word flow restatement on first mention, issue-number-only on repeat within
   a turn, one word for stage, ≤2 branch clauses for next) are stated as explicit limits in the
   edited text.
9. The edit integrates into existing step 5 (and step 6 for `next`'s branch outcomes) rather than
   introducing a new, separately-numbered loop step.

### 5. Constraint compliance

- **Issue-34**: content-explanation obligation (what/why/what-changed/how-verified) stands
  unchanged; the new fields are additive and must not restate it.
- **Issue-44**: role-classification line stands unchanged; `stage` is a distinct lifecycle axis,
  not a re-ask of "which role."
- **Issue-43's read-only-view condition**: satisfied — `flow`, `stage`, and `next` are all sourced
  by reading existing state (issue title/body, `loop_state` in `docs/issue-<n>/reports/<role>.md`,
  the fixed stage sequence and step-6 relay mechanics) at report time; no new file, board, queue,
  or persisted schema is introduced or implied.

## Scope for the coding stage

A separate coding-stage issue applies these requirements as an edit to
`orchestrate/commands/run.md`, integrated into loop step 5 (and step 6 for `next`). That edit is
conformant if and only if it satisfies all nine acceptance criteria in section 4 above.

## Next steps (backlog)

1. File/route the coding-stage issue that edits `orchestrate/commands/run.md` per this record's
   acceptance criteria (owner: next `coding` role session on a fresh `issue-<n>/coding` branch;
   this record itself files no issue, per contract — the user files it).
2. When that coding-stage PR is opened, its own record should cite this file
   (`docs/issue-54/reports/product.md`) as `upstream:` and be checked against all nine acceptance
   criteria in section 4 before merge.

## Open findings

None. The approved proposal required no revision; no unresolved product-side question remains for
the coding stage to carry forward beyond implementing the specified schema.

## References

- Proposal (full detail): `docs/issue-54/proposals/requirements.md`
- Survey: `docs/issue-54/reports/product/survey.md`
- Approval: PR #55, `APPROVE issue-54/product` comment
