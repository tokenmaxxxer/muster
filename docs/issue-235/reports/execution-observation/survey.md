---
subject: issue-235
role: execution-observation
observed_role: implementation
observed_pr: 237
code_under_review: 611c0c0
loop_state: phase-1-survey
---

# Current-state survey — issue #235, PR #237 (`implementation` role)

Phase 1. This document is a survey of the current state only: it records
what exists, what was read, and what is not yet known. It renders no
verdict — the three verdict levels are declared in the accompanying
proposal and rendered only in phase 2, after approval.

## Scope under observation

- **Issue**: #235 (`watch 거부 분류기가 denials 와 무상관으로 발화하고
  detail.gate 에 역할 이름을 싣는다 — #232 관찰 Finding 1·2`), OPEN,
  author `jjongkwann`. Its `## 실행 계획` has two steps: step 1
  `implementation`, step 2 `execution-observation`.
- **Observed role**: `implementation`, on branch
  `issue-235/implementation`.
- **Observed session's PR**: **#237**, `issue-235: refusal-classifier
  corroboration fix`, MERGED into `main` as merge commit `d187559`.
- **Observed commits**: `bf5f71f` (phase 1 — survey + proposal),
  `611c0c0` (phase 2 delivery — `spawn.py` +57/-23, `test_spawn.py`
  +75/-0), `e7a13db` (phase 2 record —
  `docs/issue-235/reports/implementation.md`, 187 lines added).
- **Observing session**: this one, on branch
  `issue-235/execution-observation`, whose HEAD at session start was
  `d187559` — byte-identical to `main`, i.e. this branch carried no
  work of its own before this commit.

## What was read this session (parent session, directly)

- `gh issue view 235` — body in full (배경, 결함 1, 결함 2, 요구사항 1-5,
  참고, 실행 계획) and `gh issue view 235 --comments` — both comments:
  one whose entire body is `APPROVE issue-235/implementation`
  (`jjongkwann`, MEMBER), and one reopen note recording that step 2 was
  still unrun when PR #237's closing keyword auto-closed the issue.
- `gh pr list --state all` — the full PR ledger, establishing that
  **no PR exists for `issue-235/execution-observation`** and that #237
  and #238 are the two most recent merges.
- `git log --oneline -20`, `git status --short`, `git rev-parse HEAD`
  and `main` — branch state as recorded above.
- `git show --stat 611c0c0` and `git show --stat e7a13db` — full commit
  messages and change sets.
- `docs/issue-235/reports/implementation.md` (added by `e7a13db`) — the
  observed role's own record, in full: `closed_checks`, What was done,
  Doc-placement ladder, Hunt (three findings), Verification run, Open
  findings, Next steps.
- `docs/issue-235/proposals/refusal-classifier-corroboration.md` (added
  by `bf5f71f`) — the approved proposal, in full: Request, Constraints,
  Rationale with three rejected alternatives, What will be done items
  1-4, Out of scope, How you'll know it worked.
- `docs/specs/approvers.md` — `JiwonJung94`, `jjongkwann`.
- `d2ae7c0:docs/issue-232/reports/execution-observation.md` (head) —
  this role's own prior record for issue #232, which issue #235 names as
  its authoritative evidence (`## 참고`).

Three background evidence-inventory passes were dispatched in parallel
over the same commits under a frozen no-re-execution, coordinate-bearing
contract (regression cases vs. the pre-change blob; the
`permission_denials` buffer-then-flush path; the four-point local
adversarial prescription vs. the delivered diff). Their returns are
inventory, not judgment, and are folded into the unknowns below.

## Phase state of this role

No PR exists on `issue-235/execution-observation`, and no issue comment
whose entire body is `APPROVE issue-235/execution-observation` exists on
#235. Under role-handoff contract v3 s19 this session is therefore in
**phase 1**: research, this survey, a scout brief, and a proposal — then
stop. The record `docs/issue-235/reports/execution-observation.md` is
phase-2 output and is **not** written in this phase.

## Write surfaces this role owns

| Surface | Phase | State now |
|---|---|---|
| `docs/issue-235/reports/execution-observation/survey.md` | 1 | this file |
| `docs/issue-235/reports/execution-observation/scout-brief.md` | 1 | written this session |
| `docs/issue-235/proposals/execution-observation-plan.md` | 1 | written this session |
| `docs/issue-235/reports/execution-observation.md` | 2 | absent — waits for approval |

Nothing under `spawn.py`, `test_spawn.py`,
`docs/issue-235/proposals/refusal-classifier-corroboration.md`, or
`docs/issue-235/reports/implementation*` is a write surface of this
role, in any phase.

## Unknowns — what this survey could not settle

These are the gaps the scout sweep is aimed at and the proposal plans
against. Each is stated as an open question, not a finding.

1. **Discrimination of the four regression cases against the pre-change
   blob.** `611c0c0`'s commit message and
   `e7a13db:docs/issue-235/reports/implementation.md:151-161` both
   assert all four failed pre-fix. The observed role's evidence for that
   is a test run this role may not repeat. What is *not* yet settled is
   whether each of the four added test bodies is statically forced to
   diverge on `bf5f71f:spawn.py` — i.e. whether the assertion each test
   makes is reachable-but-different on the pre-change code, per case,
   derived from the two blobs' text alone.

2. **Whether the buffer-then-flush gate carries both properties issue
   #235 requirement 1 asks for.** The record describes a
   `pending_refusals` dict flushed only inside the terminal
   `type:"result"` branch when `denials` is non-empty
   (`e7a13db:docs/issue-235/reports/implementation.md:34-45`). Open: (a)
   does a zero-denials session provably emit nothing on every path,
   including the `unclassified-refusal` fallback; (b) can a spurious
   buffered candidate occupy the dedup key or the "did anything flush"
   flag such that a *real* denial in the same session loses the report
   it would otherwise get. Requirement 4(iii) names exactly the second
   as a required case, so the question is whether the delivered gate's
   shape answers it in general or only for the one fixture.

3. **Coverage delta versus pre-change code.** The gate converts an
   unconditional per-line emission into a conditional one. Open: is
   there any input shape for which `bf5f71f:spawn.py` emits a refusal
   event and `611c0c0:spawn.py` emits none — i.e. where session-end
   reporting is *narrower*, not merely more precise? The observed role's
   own Hunt finding 1
   (`e7a13db:docs/issue-235/reports/implementation.md:94-115`) already
   names one such shape (crash/EOF before the terminal `result` line)
   and leaves it open; whether that is the only one is unsettled.

4. **Dedup granularity.** The record says `pending_refusals` keeps the
   "first classification per key wins, matching the prior per-session
   dedup intent"
   (`e7a13db:docs/issue-235/reports/implementation.md:36-38`). Open:
   what exactly the key is, and whether an input shape exists in which a
   spurious candidate claims a key first and a genuine event under the
   same key is therefore never emitted — a per-layer once-only mask.

5. **The four-point local adversarial prescription.** Issue #235's 배경
   cites a local sandbox experiment whose verifier rejected twice; the
   invoking prompt states that prescription has four parts (anchor /
   keep the fallback unconditional / dedup safety / a 153-fixture
   corpus). Points 1 and 3-4 map onto issue requirements 2 and 4;
   "unconditional fallback" and "153 fixtures" have no counterpart in
   issue #235's 요구사항 text as read this session. Open: whether that
   prescription exists in any admissible in-repo source, and if so what
   its exact wording is — a prescription this role cannot cite is not
   evidence this role can use. (Research settled this one: see
   `docs/issue-235/reports/execution-observation/research-evidence.md`,
   "Provenance of the 'four-point prescription'" — no admissible source
   carries the four-point form; the in-repo text is a three-point list.)

6. **Trajectory record completeness.** The approval for the observed
   role is the issue comment `APPROVE issue-235/implementation`; the
   observed record cites it at
   `e7a13db:docs/issue-235/reports/implementation.md:15-19`. Not yet
   settled: whether that comment's timestamp precedes `611c0c0`'s
   author date (`2026-08-03 15:03:13 +0900`), and whether `bf5f71f`
   confined itself to the two phase-1 homes.
