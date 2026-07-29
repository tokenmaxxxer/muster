# Coding record — issue-54: structural-context reporting

code_under_review: orchestrate/commands/run.md
loop_state: landed

upstream: docs/issue-54/reports/product.md (PR #55), docs/issue-54/reports/ux-design.md (PR #56),
docs/issue-54/proposals/coding.md (approved via PR #57, `APPROVE issue-54/coding`)

## Why

Per-item orchestrator reports left the user to reconstruct context each time (which flow, which
stage, what's next) — confirmed live when the user had to ask "what was #48 again?". Product (PR
#55) and ux-design (PR #56) fixed the schema and presentation; this stage lands that approved text
in `run.md` so the loop actually emits it.

## What was done

Applied the two approved edits from `docs/issue-54/proposals/coding.md` to
`orchestrate/commands/run.md`, verbatim:

- **Step 5**: appended the `flow`/`stage`/`next` bullet after the existing four-item obligation
  bullet — the `flow` restatement rule (≤8 words on first mention, issue-number-only on repeat),
  the six fixed `stage` values, the ≤2-clause `next` cap, the single-item compact one-line form,
  and the flow-first batched header/body form with the shared-`next` condition.
- **Step 6**: prepended the decision-queue global-numbering bullet before the existing dash list —
  turn-wide numbering (not per-flow), the note that numbers are a per-turn display convenience
  (issue-43 read-only condition, no persisted identifier), and the empty-queue omission rule.

The issue-34 four-item bullet (무엇을/왜/무엇이 바뀌었는가/어떻게 검증됐는가) and the issue-44
step-2 routing table and 절차 위반 rule are unchanged — confirmed by diff: only additive bullets
were inserted, no existing line touched.

## What did not work

Nothing — the proposal's diff applied cleanly with no deviation.

## Verification performed (closed_checks)

- `git diff orchestrate/commands/run.md` reviewed against the proposal's Edit 1 / Edit 2 text:
  byte-for-byte match. code_sha: applied at this record's commit.
- Confirmed no other lines in `run.md` changed (`git diff --stat` shows one file, insertions only,
  no deletions) — matches the proposal's "no other lines change" constraint.
- Confirmed the loop stays numbered 1-6 — no new step introduced.

## Warrant hunt

Not dispatched — this is a text-only prompt-file edit (no code path, no runtime behavior) applying
an already-approved, fully-specified diff verbatim; no new failure surface to hunt.

## Open findings

None.
