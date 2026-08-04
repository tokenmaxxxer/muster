---
role: implementation
subject: issue-258
code_under_review: on-the-record/commands/run.md
loop_state: landed
---

## Upstream basis

Phase-1 proposal ([[../proposals/implementation.md]]) approved via PR #259
(human review Approve). Executed as proposed.

## Why

Issue #258: the orchestrator has 43 personal skills but the orchestration
loop never invokes them when drafting issues, so the rigor those skills
encode is lost before it reaches role sessions. The approved proposal
folds skill assessment into `run.md` step 1 to fix this.

## What was done

- `on-the-record/commands/run.md` step 1: inserted the skill-assessment
  sub-step verbatim as specified in the proposal's "What will be done"
  section, between the existing draft sentence and step 2's role
  classification. Positioned before any `gh issue create` instruction.
  - [x] Names the `Skill` tool explicitly and states that reading a skill
    file as plain text does not satisfy the step.
  - [x] States skill invocation does not produce the deliverable and that
    role sessions receive no skills.
  - [x] No file outside `on-the-record/commands/run.md` changed.
  - [x] Step 1/2 numbering unchanged — prose inserted inside step 1's body.

## What did not work

None.

## Verification run

`grep -n 'Skill\|패러프레이즈' on-the-record/commands/run.md` confirms the
inserted text names the `Skill` tool and the paraphrase prohibition, placed
before step 2's role-classification content.

## Open findings

None outstanding.
