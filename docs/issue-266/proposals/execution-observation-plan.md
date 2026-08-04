---
subject: issue-266
role: execution-observation
observed_role: implementation
observed_pr: 267
code_under_review: be53d1ebc227d4549598cb70767d1cf9f641d177
loop_state: phase-1-proposal
---

files:
- docs/issue-266/reports/execution-observation.md

## Request

Issue #266's `## 실행 계획` step 2: independent execution observation of
step 1, delivered by the `implementation` role as PR #267 (commits
`1fdd1ac` phase 1, `d61e93c` phase-2 start, `be53d1e` phase-2 delivery),
merged to `main` as `247051e` at 2026-08-04T04:08:44Z. The invoking prompt
scopes the observation to that step and to measured evidence only
("실측 근거로만"), naming the step-1 content as: dropping the
`roster_entry is None` death signal, an entry-absence red→green regression
test, and a decision-document update.

## Verdict levels to be rendered in phase 2

Declared here, before any evidence discussion, and rendered nowhere in
phase 1. All three levels of the role's three-level verdict will be
addressed in `docs/issue-266/reports/execution-observation.md`; a level
that turns out not to apply will be written as "not applicable, because
X" rather than omitted.

1. **Outcome** — whether PR #267 and
   `docs/issue-266/reports/implementation.md` landed what issue #266's
   three numbered requirements asked for. Evidence: the issue body's
   요구 1 / 요구 2 / 요구 3, checked against the diff hunks
   `be53d1e:spawn.py:1900-1911` and `be53d1e:test_spawn.py` (both hunks:
   the added `test_follow_tolerates_roster_entry_fully_absent_before_session_end`
   and the rewritten `test_follow_detects_dead_session_and_returns_crash_rc`),
   against `docs/issue-266/proposals/roster-lifetime-vs-absence-signal.md:19-30`
   (the (a)-vs-(b) tradeoff the issue required the proposal to make), and
   against `docs/issue-266/reports/implementation.md:203-206`
   (the Verification run) plus its `closed_checks:` block (lines 5-25).
2. **Trajectory** — whether the phase-1→phase-2 path met contract v3 s19:
   survey before proposal, scouting where required, a real human approval
   before any phase-2 artifact. Evidence: the existence and commit
   membership of `docs/issue-266/reports/implementation/survey.md` and
   `…/scout-brief.md` in commit `1fdd1ac` (02:53:18Z); PR #267's creation
   time (02:53:50Z) and `reviews: []`; the issue comment whose entire body
   is `APPROVE issue-266/implementation`, its author, and its timestamp
   (2026-08-04T03:00:27Z) against `docs/specs/approvers.md`; and the
   authored timestamps of `d61e93c` (03:04:51Z) and `be53d1e` (03:21:30Z)
   as the phase-2 artifacts' position relative to that approval.
3. **Step** — which specific artifact, if any, carries a deficiency. The
   candidate artifacts to be checked are enumerated in "What will be
   done" below (S1-S5). Any finding that survives checking will carry the
   four-part blameless shape — impact, timeline, root cause, action item —
   scaled to the single finding, with its citation adjacent to the
   verdict sentence rather than elsewhere in the document.

## Constraints

- **No re-execution.** The observed role's tests, `_watch()`, and the gate
  scripts will not be run. Per the scout brief's inspection ceiling
  (EviACT, arXiv 2605.27238: "the auditor never executes code"), the
  red→green claim is checkable for construction and internal consistency,
  not for having-actually-passed — the record will state that ceiling
  explicitly rather than implying execution was confirmed.
- **No reading of `spawn.py` / `test_spawn.py` at HEAD as evidence.**
  Present-tense source shows what exists now, not what this role did; the
  `be53d1e` diff is the admissible form.
- **No edits outside this role's own paths.** `spawn.py`, `test_spawn.py`,
  `docs/issue-266/reports/implementation*`, and
  `docs/issue-266/decisions/` are the observed role's; nothing under them
  is touched. This includes the still-open follow-up those artifacts name
  — it is reported, never performed.
- **No issue filing.** Contract v3: issues are user-authored only. Findings
  return in this role's record, on this role's PR.
- Pre-existing test failures unrelated to `be53d1e` are outside this
  change's account (transition-based relevance, scout brief).

## Rationale

The survey (`docs/issue-266/reports/execution-observation/survey.md`)
found the field's documentation must-bes already satisfied — both
deviations are written down with their mechanics and a named follow-up —
so a check plan that spends itself on "was the deviation documented"
would spend itself on a settled question. The scout brief's gap line
names the two places the current artifacts do not reach: nothing states
what a reader may conclude from an unre-runnable red→green claim, and
nothing owns the closing-keyword vector that the merge gate does not
inspect. The checks below are therefore weighted: S1 and S2 are
investigative, C1/C2 and S3-S5 are confirmatory against named artifacts.

Weighting is not pre-judging. Each check below states the artifact and
the criterion it will be read against; which way any of them resolves is
phase-2 output.

## What will be done

Write `docs/issue-266/reports/execution-observation.md` as the first act
of phase 2, with the independence statement (this role did not author or
edit PR #267's artifacts) placed **before** any verdict language, and
`loop_state` updated at each transition. Into it:

- **C1 (outcome).** Read 요구 1 against `be53d1e:spawn.py:1900-1911` and
  `…proposals/roster-lifetime-vs-absence-signal.md:19-30`; 요구 2 against
  the added test's arrange/assert lines in `be53d1e:test_spawn.py` and the
  issue's own words for the tail state ("session-end 미기록 + 명부 비어
  있음 + 프로세스는 후처리 중"); 요구 3 against the diff's complete file
  list and whether the drain order, `WATCH_CRASH_RC`, and `wrapper_pid`
  lines appear in it at all.
- **C2 (trajectory).** Read the phase-1 artifacts' commit membership
  (`git show --stat 1fdd1ac`), `docs/issue-266/reports/implementation/scout-brief.md`
  and `…/survey.md` for the survey-before-proposal and scout-or-skip-record
  order, and the approval chain (comment string equality, author against
  `docs/specs/approvers.md`, single-account mode, timestamps vs. `d61e93c`).
- **S1.** `be53d1e`'s commit-message body line `Closes #266`, read against
  the plan-aware Closes rule
  (`docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md:20-27`:
  a closing keyword is blocked while more than one plan step is
  incomplete), against the surface that rule's enforcement inspects
  (`docs/handbooks/operations.md:662-666`, PR **body**), against PR #267's
  own body text, and against the human's reopen comment at 04:09:13Z.
  Classification follows the scout brief's guardrail-first must-be: what
  the control inspects is asked before what the author typed.
- **S2.** `…proposals/roster-lifetime-vs-absence-signal.md`'s `files:`
  line 4 (`docs/issue-224/decisions/watch-crash-exit-code.md`) against the
  branch-ownership rule the record cites (`board-gate.sh` R4 / contract v3
  s10), against `docs/issue-266/decisions/watch-crash-trigger-wording-amendment.md`,
  and against what `docs/issue-224/decisions/watch-crash-exit-code.md:25-26`
  reads at `247051e` — i.e. whether the write set approved in phase 1
  contained a path this branch could never write, and where the residual
  is tracked.
- **S3.** The delivered predicate's second dropped branch (falsy `pid`)
  against issue #266 요구 1(b), which names only `roster_entry is None`,
  and against `…proposals/roster-lifetime-vs-absence-signal.md:34`, which
  names both — i.e. which document bounds the approved change, and whether
  the delivered predicate stays inside it.
- **S4.** The pre-image and post-image of
  `test_follow_detects_dead_session_and_returns_crash_rc` in
  `be53d1e:test_spawn.py` against 요구 3's "#224's landed items stay
  theirs" — whether the branch #224's test protected still has a test
  after the rewrite, and whether the record's justification
  (`docs/issue-266/reports/implementation.md:104-127`) matches the diff.
- **S5.** The hardcoded line references inside the new `spawn.py` comment
  (`spawn.py:2995`, `spawn.py:3097`) and inside the new test's docstring,
  against the same references' values in the issue body (`:2901`, `:3003`)
  — i.e. the durability of line-number citations across the same file's
  own edits.

Each of C1, C2, S1-S5 lands as a citation-bearing paragraph; S-items that
resolve to no finding are recorded as checked-and-clear rather than
dropped, so the record shows its own coverage.

## Out of scope

- Re-running `test_spawn.py`, `gates/`, or `spawn.py watch` in any form.
- Any edit to `spawn.py`, `test_spawn.py`, `docs/issue-266/reports/implementation*`,
  or `docs/issue-266/decisions/` — including performing the follow-up
  those artifacts name (pasting the corrected paragraph into
  `docs/issue-224/decisions/watch-crash-exit-code.md`).
- Re-opening issue #224's own merged work (PR #255): the drain order,
  `WATCH_CRASH_RC`, and `wrapper_pid` are #224's, and #266 요구 3 keeps
  them. They are read only as the boundary #267 had to stay inside.
- Re-designing the fix, proposing alternative (a), or evaluating the
  `roster_kill`/`roster_ps` coupling on its merits — the design choice was
  approved by the human and is not this role's to relitigate.
- Filing any issue for anything found. Findings go in the record; the
  human judges them on this PR.

## How you'll know it worked

- `docs/issue-266/reports/execution-observation.md` exists on this branch,
  **committed**, with the independence statement preceding the first
  verdict-bearing sentence in document order.
- All three levels — outcome, trajectory, step — appear, each either
  rendered or written as "not applicable, because X".
- Every verdict-bearing sentence has its citation (commit SHA, `file:line`,
  or comment URL/timestamp) adjacent to it, not merely present elsewhere.
- Each of C1, C2, S1-S5 is accounted for in the record, including the ones
  that resolve to nothing.
- Any finding carries impact, timeline, root cause, and action item.
- No file outside `docs/issue-266/reports/execution-observation*` and
  `docs/issue-266/proposals/execution-observation-plan.md` is modified by
  this session — checkable with `git show --stat` on this branch's commits.
