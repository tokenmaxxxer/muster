# Proposal: issue-34 — mandatory plain-language summary in orchestrate approval loop

## Request (paraphrased)
Orchestrator currently only relays PRs; it has no stated duty to explain them.
Make explanation a contractual obligation: before requesting phase-1 approval,
read the proposal file(s) and summarize what/why/how; before requesting merge,
read the diff and summarize what changed and how it was verified. Define the
minimum items every approval/merge request must contain.

## Constraints
- Change lives in the orchestrate plugin's procedure text only (no runtime
  enforcement code requested by the issue).
- Must not alter the existing relay/decision rules (feedback/APPROVE/merge/close).

## What will be done
- Edit `orchestrate/commands/run.md` step 4 ("PR 을 설명한다") to add:
  - Phase-1 approval request: must read `docs/issue-<n>/proposals/` and state
    what/why/how before asking for approval; asking without this is a
    procedure violation.
  - Phase-2 merge request: must read the actual diff/commits (`gh pr diff`)
    and state what changed + how it was verified before asking to merge;
    asking without this is a procedure violation.
  - Minimum item list for every approval/merge request: what is being
    changed, why, what changed, how verified.

## Out of scope
- Automated/hook-level enforcement of the summary (deliverable-guard etc.) —
  issue asks for procedure text, not a gate.

## How you'll know it worked
- `orchestrate/commands/run.md` step 4 explicitly states the read-before-ask
  obligations and the minimum item list, with "procedure violation" framing
  for the no-summary case.
