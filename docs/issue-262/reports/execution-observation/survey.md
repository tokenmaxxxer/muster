---
kind: survey
subject: issue-262
role: execution-observation
date: 2026-08-04
phase: 1
---

# Current-state survey — what is under observation, and what is already known

Phase 1. This document records facts read this session and the questions they
leave open. It renders no judgment: every "open question" below is stated as a
question for phase 2, never as a finding.

## Scope of the observation (who/what/which session/which PR)

- **Role observed**: `implementation`.
- **Session observed**: that role's phase-1 → phase-2 run on branch
  `issue-262/implementation`, 2026-08-04 02:17Z – 03:12Z.
- **Issue**: #262 (`gates.py always-writable 제안 파일 패턴이 실제 명명 관행과
  불일치`), execution plan step 1.
- **PR**: #265 — `MERGED 2026-08-04T04:04:48Z`, merge commit `2f89d5a`,
  head ref `issue-262/implementation`.
- **This role's own scope**: issue #262 execution plan step 2
  (`execution-observation`), branch `issue-262/execution-observation`, which
  carried no commits of its own at session start (`git log origin/main..HEAD`
  → empty).

## What was read this session (first-hand, not summarized secondhand)

| Artifact | How it was read |
| --- | --- |
| Issue #262 body + execution plan | `gh issue view 262` |
| Issue #262 comment thread (2 comments) | `gh issue view 262 --comments`; `gh api .../issues/262/comments` |
| Issue #262 event timeline (close/reopen, with attributing commit) | `gh api .../issues/262/timeline` |
| PR #265 metadata: state, merge time, head ref, body, commit list, file list | `gh pr view 265 --json ...` |
| PR #265 reviews and PR-level comments | `gh pr view 265 --json reviews,comments` → `{"comments":[],"reviews":[]}` |
| PR #265 required-check result | `gh pr checks 265` |
| Commit `1c88e07` full message + `--stat` | `git show 1c88e07 --stat --format=...` |
| Commit `1c88e07` code diff (`gates/gates.py`, `test_gates.py`) | `git show 1c88e07 -- gates/gates.py test_gates.py` |
| The observed role's own record, in full (228 lines) | `docs/issue-262/reports/implementation.md` |
| The observed role's approved proposal, in full (176 lines) | `docs/issue-262/proposals/2026-08-04-always-writable-proposal-glob-fix.md` |
| The observed role's phase-1 survey (scout-skip record section) | `docs/issue-262/reports/implementation/survey.md:9-20` |
| Approver roster | `docs/specs/approvers.md` |
| Closes-gate judgment scope (issue #228's surface, read as context) | `gates/pr_reference.py:15-60` |
| Sibling issue #266's comment thread (comparison case) | `gh api .../issues/266/comments` |

Not read as evidence, deliberately: the present contents of `gates/gates.py`
and `test_gates.py` in the working tree. Those show what exists now, not what
the observed role did; the commit diff is the admissible form.

## Facts established

**F1 — delivery shape.** PR #265 carries exactly two commits:
`4ca10d1` (`2026-08-04T02:17:20Z`, phase 1 — proposal + survey) and
`1c88e07` (`2026-08-04T03:12:13Z`, phase 2 — fix + test + record). Files:
`docs/issue-262/proposals/2026-08-04-always-writable-proposal-glob-fix.md`
(+175), `docs/issue-262/reports/implementation/survey.md` (+173),
`docs/issue-262/reports/implementation.md` (+227), `gates/gates.py` (+1/−1),
`test_gates.py` (+16).

**F2 — the code change.** `git show 1c88e07 -- gates/gates.py` shows one line
inside `_always_writable(role)` (hunk `@@ -472,7 +472,7 @@`):
`f"docs/issue-*/proposals/{role}.md"` → `"docs/issue-*/proposals/**"`.

**F3 — the test.** The same commit adds
`t_role_scope_proposal_date_slug_filename_passes` (hunk `@@ -918,6 +918,22 @@`
in `test_gates.py`), which writes a date-slug-named file under
`docs/issue-262/proposals/` in a temp repo and asserts `role_scope(...) == []`.

**F4 — approval event.** Issue comment
[`#issuecomment-5173982238`](https://github.com/tokenmaxxxer/on-the-record/issues/262#issuecomment-5173982238)
(`2026-08-04T02:40:37Z`, author `jjongkwann`), body exactly
`APPROVE issue-262/implementation`. `docs/specs/approvers.md` lists
`jjongkwann`. PR #265 carries zero PR reviews, consistent with the
single-account approval path.

**F5 — ordering.** phase-1 commit `4ca10d1` (02:17:20Z) → PR #265 opened
(issue timeline `cross-referenced`, 02:17:50Z) → approval comment (02:40:37Z)
→ phase-2 commit `1c88e07` (03:12:13Z) → merge (04:04:48Z).

**F6 — the issue closed on merge, and a human reopened it.** Issue #262
timeline: `closed 2026-08-04T04:04:49Z`, attributed to `commit_id
1c88e073e1257c6c20605170d65e226d1e83aa04`; `reopened 2026-08-04T04:09:39Z` by
`jjongkwann`, preceded by comment
[`#issuecomment-5174500409`](https://github.com/tokenmaxxxer/on-the-record/issues/262#issuecomment-5174500409)
(04:09:38Z): "재오픈: 실행 계획 step 2(execution-observation)가 남아 있다.
원인 동일 — 머지된 커밋 메시지 내 'Closes #262' (closes-gate 는 PR 본문만
검사)."

**F7 — where the closing keyword actually sat.** `git show 1c88e07` prints a
message body containing the line `Closes #262`. PR #265's *body*, by contrast,
references the issue in prose only and states: "Per contract, this phase-1 PR
references `#262` in prose only — merging it must not auto-close the issue",
plus a trailing "(issue #262 — phase 2 delivery; plan step 2 remains, no
closing keyword by design)". PR #265's title still reads
"issue-262: phase 1 - always-writable proposal glob fix (survey + proposal)".

**F8 — the gate that governs this passed.** `gh pr checks 265` →
`closes-gate  pass  8s`
([run 30876637468](https://github.com/tokenmaxxxer/on-the-record/actions/runs/30876637468/job/91889356238)).
`gates/pr_reference.py:29-47` judges **PR body text only** and, when the plan
has an incomplete non-final step, actively *rejects* a closing keyword in a
phase-2 PR body. Commit messages are outside that function's input.

**F9 — the same shape occurred on a sibling issue in the same window.**
Issue #266 comment
[`#issuecomment-5174498053`](https://github.com/tokenmaxxxer/on-the-record/issues/266#issuecomment-5174498053)
(04:09:13Z): "재오픈: … PR #267 본문의 closing 키워드는 머지 전 제거했으나
자동 종결됨 — 머지된 커밋 메시지 내 closing 키워드가 유력 원인".

**F10 — issue requirement wording vs delivered glob.** Issue #262 requirement 1
asks for "해당 이슈 트리의 `docs/issue-<n>/proposals/` 아래 임의 파일명" and
requires the proposal to examine the side effects of widening ("다른 이슈
트리의 proposals 까지 열리지 않는지"). The delivered literal is
`docs/issue-*/proposals/**` (F2). The proposal argues at
`docs/issue-262/proposals/2026-08-04-always-writable-proposal-glob-fix.md:64-81`
that the `issue-*` segment was already unbound pre-fix, and rejects binding to
the branch's issue number.

**F11 — requirements 2 and 3 have recorded answers.** Red/green runs are
transcribed at `docs/issue-262/reports/implementation.md:33-57`; the
requirement-3 conclusion ("keep `--closes-only`") with two stated reasons is at
`docs/issue-262/reports/implementation.md:79-127`.

**F12 — proposal text vs delivered test.** Proposal "What will be done" item 2
(`…-glob-fix.md:121-127`) says the regression test "**commits** a dated-slug
file under `docs/issue-<n>/proposals/`". The record's "What was done" item 2
(`implementation.md:23-29`) says the test "commits no file, leaves a
date-slug-named file … uncommitted", and hunt finding 3
(`implementation.md:212-216`) gives the convention reason. The record's "What
did not work" section (`implementation.md:129-132`) states "None. The one-line
fix and the new test matched the approved proposal's 'What will be done' on the
first attempt".

**F13 — record section inventory.** `docs/issue-262/reports/implementation.md`
sections: What was done / Red-green regression proof / Requirement 3 / What did
not work / Open findings / Doc-placement ladder / Hunt. No "Rationale for
deviations" section. The comparison record
`docs/issue-245/reports/implementation.md:200` does carry one, and issue #262's
own body cites that section by name.

**F14 — scout skip is recorded.** `docs/issue-262/reports/implementation/survey.md:9-20`
carries a "Scout skip record" section claiming the pure-bugfix skip condition.

## Open questions this survey leaves for phase 2 (not answers — questions)

- **Q1 (control-vs-outcome).** F6+F7+F8: the governing gate passed on the
  surface it inspects while the outcome it exists to prevent occurred through
  an uninspected channel. What does an evidence-based observation owe here —
  how is "the control was satisfied and the protected outcome still failed"
  handled, and at which level (outcome / trajectory / step) does it belong?
- **Q2 (declared-vs-actual deviation).** F12+F13: how should an observation
  treat an author's own "no deviations" statement standing next to an artifact
  that differs from the approved plan text, when the difference is defended
  elsewhere in the same record?
- **Q3 (scope of a widening fix).** F10: how do reviews of authorization/
  permission-scope changes judge a fix that widens a matcher beyond the
  requirement's stated scope on a "it was already unbound" argument?
- **Q4 (recurrence).** F9: the same shape appeared on a sibling issue in the
  same window. What does blameless practice require of an observation when the
  event is a recurrence rather than a one-off?

These four are the gaps the scout sweep is aimed at.
