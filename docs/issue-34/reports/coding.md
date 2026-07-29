# Coding record — issue-34

code_under_review: 2253f9d
loop_state: landed

## What was done
Executed the approved proposal (`docs/issue-34/proposals/coding.md`, approved
via PR #36 review) by editing `orchestrate/commands/run.md` step 4:
- Phase-1 approval requests now require reading `docs/issue-<n>/proposals/`
  and stating what/why/how before asking for approval; skipping this is
  framed as a procedure violation.
- Phase-2 merge requests now require reading the actual diff (`gh pr diff`)
  and stating what changed + how it was verified before asking to merge;
  skipping this is framed as a procedure violation.
- Minimum item list defined for every approval/merge request: what is being
  changed, why, what changed, how verified.

## Why
Upstream basis: issue #34 requirement + approved proposal
`docs/issue-34/proposals/coding.md` (approved via PR #36 review comment).
The orchestrator previously only relayed PRs with no obligation to explain
them; this makes read-before-ask explanation a contractual step.

## What did not work
N/A — the phase-1 session's unstaged draft already matched the approved
proposal in full; no rework was needed.

## Verification
Reviewed the diff against the proposal's "How you'll know it worked"
criterion (explicit read-before-ask obligations + minimum item list +
procedure-violation framing present in step 4) — confirmed by inspection.
This is a procedure-text-only change (markdown instructions for the
orchestrate plugin); no runtime code/tests were introduced, matching the
proposal's stated constraints and out-of-scope section.

## Closed checks
- closed_checks: diff-matches-proposal-scope (code_sha: 2253f9d) — confirmed
  edit only touches step 4 of run.md, no relay/decision-rule changes.

## Hunt
warrant-hunter not dispatched: change is a single markdown procedure edit
with no code paths, no execution surface, and no state/composition to
probe — proposal's own "how you'll know it worked" criterion sufficiently
bounds this size of change.

## Open findings
None.
