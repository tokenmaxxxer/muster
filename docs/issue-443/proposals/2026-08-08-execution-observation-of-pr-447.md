---
kind: proposal
subject: issue-443
role: execution-observation
date: 2026-08-08
loop_state: scope-proposed
---

# Proposal — independent execution observation of issue #443 step 1 (PR #447)

files:
- `docs/issue-443/reports/execution-observation.md` (new, phase-2 only —
  this role's sole phase-2 artifact)

This role writes nothing else. It does not touch
`on-the-record/hooks/contract-guard.sh`, `on-the-record/hooks/test_contract_guard.py`,
`docs/issue-443/proposals/2026-08-08-contract-guard-target-repo-resolution.md`,
`docs/issue-443/reports/implementation.md`,
`docs/issue-443/reports/implementation/survey.md`, or
`docs/reports/2026-08-08-hunt-contract-guard-target-repo-resolution.md` —
those are the observed role's own artifacts, and this role did not author
or edit them. No re-execution of the observed role's task (no running
`pytest`, no invoking `contract-guard.sh`), no re-reading a post-merge
working-tree copy of the hook as evidence of what that role did (the
merged commit diff is the admissible form), no issue filing.

## Request

Issue #443's execution plan, step 2: `execution-observation` of step 1.
Step 1 is the `implementation` role's phase-1 → phase-2 run on branch
`issue-443/implementation`, delivered as PR #447 (MERGED
2026-08-08T08:22:39Z, merge commit `6d058ff`), carrying commit `8e7d1b4`
(phase 1: proposal + survey), `b73b502` (phase-1 warrant-hunter record, no
finding), and `01a2c9d` (phase 2: `contract-guard.sh` fix, `test_contract_guard.py`,
its own record — including a same-session fix for a before-landing hunt
finding).

## Which verdict levels will be checked, and against what evidence

Stated here, before any judgment exists. Nothing in this proposal is a
verdict, provisional or otherwise; the questions below are questions, and
phase 2 answers them. All three levels will be addressed in phase 2,
writing "not applicable, because X" for any level that turns out not to
apply rather than omitting it silently.

| Level | Question phase 2 answers | Evidence it will be answered from |
| --- | --- | --- |
| **outcome** | Did PR #447 land what issue #443 asked — 요구사항 1 (target-repo resolution for `-R`/`--repo`, full PR URL, `cd <path> &&`, with unresolvable forms left as explicit unreached), 요구사항 2 (a red-green cross-repo case fixed in a gate test suite), 요구사항 3 (any newly-parsed URL form kept consistent with the file's existing unreached comments) — and did it honour the 제약 (phase-2 `Closes` predicate itself unchanged; no retroactive fix; zero-install; fail-open discipline preserved)? | `gh issue view 443` body; `git show 01a2c9d -- on-the-record/hooks/contract-guard.sh` full diff; `on-the-record/hooks/test_contract_guard.py` (all 7 tests); `gh pr checks 447` (`closes-gate pass`, `test pass`); `docs/issue-443/reports/implementation.md` (What was done, Resolution path); the approved proposal's Constraints/Rationale sections. |
| **trajectory** | Was the phase-1 → phase-2 path sound — survey before proposal, scouting run or its skip recorded, a real human approval under contract v3 s19 before phase-2 work began, and phase-2 output confined to the approved write set? | Commit order/timestamps `8e7d1b4` (08:10:07Z) → `b73b502` (08:12:42Z) → approval comment (08:12:56Z) → `01a2c9d` (08:20:09Z) → PR merged (08:22:39Z); issue #443 comment body exactly `APPROVE issue-443/implementation` by `JiwonJung94`, checked against `docs/specs/approvers.md`; `gh pr view 447 --json reviews` → `[]` (single-account path); `docs/issue-443/reports/implementation/survey.md`'s scout-skip reasoning; the proposal's frozen write set (`contract-guard.sh`, `test_contract_guard.py`) vs `gh pr view 447 --json files`. |
| **step** | Which specific artifact, if any, is deficient — checked per artifact: the `contract-guard.sh` diff, `test_contract_guard.py`, `docs/issue-443/reports/implementation.md`'s own account, and commit `01a2c9d`'s message. | The same diffs and record text, plus the two open discrepancies logged in `docs/issue-443/reports/execution-observation/survey.md` ("Candidate discrepancies noticed, not yet judged"): the "8 cases" vs 7 delivered test functions wording, and the red-run transcript that `implementation.md:32-33` points to ("see below") but does not contain. |

## Rationale — why no scout brief

Scouting was skipped under the scout directive's "spec literally leaves no
design decision open" condition: this role's checked dimensions (the
three-level verdict, the blameless four-part finding shape, citation
discipline) are fixed by the role's own standing directive, not by a
product-shaped or competitive field. Recorded in
`docs/issue-443/reports/execution-observation/survey.md` under "Skip
conditions checked".

## Out of scope

- Re-running `pytest` or `contract-guard.sh`, or reading the working
  tree's current copy of either as evidence of what the observed role did
  — the merged commit diff is the only admissible form.
- Any edit to the observed role's `src/`, `on-the-record/hooks/`,
  proposal, survey, or record; any edit anywhere outside
  `docs/issue-443/reports/execution-observation.md` and this role's own
  phase-1 files.
- Filing an issue for anything found. Under contract v3 issues are
  user-authored only; confirmed deficiencies return as findings in this
  role's record, on this role's PR, for the human to judge.
- Re-opening or re-judging the before-landing hunt finding that
  `implementation.md` already reports resolved — Check-level review of
  whether that resolution is sound belongs to the outcome/step verdicts
  above, not a fresh hunt.

## How you'll know it worked

- `docs/issue-443/reports/execution-observation.md` exists on branch
  `issue-443/execution-observation`, committed, with the independence
  statement appearing before the first verdict-bearing sentence.
- All three verdict levels are present, each explicitly answered (or
  marked "not applicable, because X"), and every verdict-bearing sentence
  carries a citation — commit SHA, `file:line`, or comment URL — directly
  adjacent.
- The two open discrepancies from the survey reach a stated conclusion,
  traceable to an artifact listed in the survey's "What was read this
  session".
- Any deficiency finding carries impact / timeline / root cause / action
  item.
- `git diff --stat origin/main...HEAD` for this branch touches only
  `docs/issue-443/reports/execution-observation*` and
  `docs/issue-443/proposals/2026-08-08-execution-observation-of-pr-447.md`.
