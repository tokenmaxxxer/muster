---
status: proposed
files:
  - on-the-record/commands/run.md
---

Scout-directive skip condition applies: the spec (issue #294's own
Acceptance section) leaves no open design decision — it names the exact
two things the text must do. See docs/issue-294/reports/implementation/survey.md
for the full survey; scouting was skipped for that stated reason.

## Request

Step 6 of run.md ("결과 수용") merges a PR with a single command and no
check verification. For 44 of 48 org repos there are no CI checks at
all, so an orchestrator following the contract literally can merge on
the PR body's self-report alone. Fix: make reading and passing
`gh pr checks <n>` a required precondition of merge, with an explicit
escalate branch when no checks exist (absence of checks is not the same
as checks passing).

## Constraints

- Only `on-the-record/commands/run.md` changes — no code, no test
  suite, no CI config (those are #290/#291's substrate half, explicitly
  out of scope per #294's own acceptance text).
- Must not silently treat "no checks configured" as pass — #294 calls
  this out by name as today's failure mode.
- Must not conflate a missing check with a real defect signal, but must
  also not treat a red `closes-gate` (a known false-positive class per
  #284, closed) as grounds to merge past it — the fix names required
  checks passing, not "any green is fine."

## Rationale

Considered leaving the branch implicit (just add "check `gh pr checks`
first" as a soft reminder) and trusting the reader to infer the
escalate path. Rejected: #294's own measured evidence is that discretion
without a written branch is exactly what already failed three of five
real merges — an implicit reminder repeats the defect the issue reports.
Writing an explicit escalate branch (mirroring the existing explicit
"비정규 형태" branch already in the same step) matches the file's own
established pattern for exception handling instead of inventing a new
one.

## What will be done

Insert, before the existing 결과 수용 line, a required check-verification
step: run `gh pr checks <n>`; if any required check is failing, do not
merge — escalate to the user instead of proceeding to acceptance; if no
checks are configured at all, treat that the same as "nothing to verify
against" and escalate rather than silently merging. Keep the existing
`gh pr merge` acceptance line as the action taken only after this
precondition clears (or after the user, having been told there is
nothing to check, explicitly still says to proceed).

## Out of scope

- Adding CI workflows or branch protection to core/the 43 rulebooks
  (#290, #291) — cross-referenced, not fixed here.
- Any change to closes-gate's phase-flip behavior (#284, closed).
- Any Stop-hook / orchestrator-reply-inspection mechanism (#298).

## How you'll know it worked

`on-the-record/commands/run.md` step 6's acceptance branch textually
requires `gh pr checks <n>` before `gh pr merge`, names an explicit
escalate action for both a failing required check and no checks
configured, and cross-references #290/#291 by number in the same
paragraph.
