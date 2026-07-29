# issue-44 — coding: phase-2 record

code_under_review: orchestrate/commands/run.md
loop_state: landed

## Why

Issue #44 asked for a role-selection guide because a real orchestration session defaulted almost
every request to `coding` without ever stating a classification. PR #50's phase-1 proposal
(`docs/issue-44/proposals/role-selection-guide.md`) was approved via
`APPROVE issue-44/coding`, authorizing this phase-2 edit of `orchestrate/commands/run.md`.

## What was done

Applied the approved proposal verbatim to `orchestrate/commands/run.md` (upstream basis:
`docs/issue-44/proposals/role-selection-guide.md`, approved on PR #50):

- Inserted new loop step 2 ("이슈를 등록하기 전에 분류한다"): classification obligation
  (feasibility/product/ux-design/coding, one-line reasoning), the 4-row request-type → leading-role
  table, and the "분류를 말하지 않고 coding 으로 기본값 처리하는 것은 절차 위반이다" rule.
- Extended (renumbered) step 3 ("누구를 깨울지") with the obligation that every "못 잰다"
  judgment line be answered with an explicit role proposal, and that stopping at "못 잰다" is a
  procedure violation.
- Renumbered old steps 3-5 to 4-6; issue-34's step-4 (now step 5) approval-summary gate text is
  unchanged, integrated rather than overwritten as the proposal required.

## Verification

- `git diff orchestrate/commands/run.md`: confirms only the loop-step section changed; the
  precondition section ("띄우기 전에 확인할 것") and the "하지 않는 것" section are untouched.
- Text matches the proposal's "What will be done" block character-for-character (copy-pasted,
  then renumbered surrounding steps).

## What did not work

(none — direct text insertion per an already-fully-specified proposal, no iteration needed)

## closed_checks

- name: diff-scope-check, code_sha: (this commit) — confirmed diff touches only the loop-step
  numbering/insertion in run.md; no other file changed, issue-34's gate text byte-identical.

## Open Findings

None. No blocking findings addressed to coding are open on this issue.
