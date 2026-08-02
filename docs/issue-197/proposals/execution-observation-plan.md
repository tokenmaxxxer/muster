# Proposal — issue #197 execution-observation, phase-2 verification method

Status: proposal (phase 1). No verdict is rendered anywhere in this document — this
section states which of the three verdict levels will be checked and against what
evidence, per this role's phase-1 facet requirement.

## What phase 2 will check, and against what evidence

**Outcome** — did PR #200 (commits `e7bfdcb`, `9dc099a`, merge `93038c0`) land what
issue #197's four numbered requirements asked. Evidence: the `e7bfdcb` diff already
read in full this session (`gh pr diff 200`) against each requirement's text, plus a
phase-2 character-level comparison of `test_spawn.py`'s new fixture body against
issue #189's actual current body (both already read this session, not yet diffed
against each other) to settle requirement 4's claim that the fixture is the issue-189
body "그대로." No execution of `spawn.py`/`gates/flows.py` will be performed — this
role's directive prohibits re-running the observed role's code. This mirrors
issue-189's execution-observation proposal's own resolution of the same tension
(`docs/issue-189/proposals/execution-observation-plan.md`, "Outcome" section) in favor
of the standing protocol over any instruction to reproduce by running code. Where the
observed role's own record (`implementation.md`) or the PR #200 comment already
contain a live-run transcript, those citations may be used as evidence without this
role re-executing anything — per the same precedent.

The `on-the-record/commands/run.md` diff (requirement 3) will be checked
outcome-level by reading the actual diff (already read via `gh pr diff 200`) against
requirement 3's text — a static prose-presence check, not runtime behavior, so it
does not raise the same re-execution question.

**Trajectory** — was the `implementation` role's phase-1→phase-2 path sound: did it
survey before proposing (its `survey.md` and `scout-brief.md`, already read in
full — show a scout-then-survey-then-propose pattern with an explicit scout
saturation note), get real human approval before phase 2 specifically (`APPROVE
issue-197/implementation`, 2026-08-02T08:27:18Z, already read from the issue's
comments), keep its write set to what the approved proposal declared
(`plan-parser-fix.md`'s `files:` frontmatter: `gates/flows.py`,
`on-the-record/commands/run.md`, `test_spawn.py` — checked in the survey against
`git show 93038c0 --stat`'s four changed files, one of which,
`docs/issue-197/reports/implementation.md`, is the record itself and so expected
outside the code write-set), and whether PR #199's `.warrant-hunt.count` deletion
(flagged in the survey, not evaluated) belongs to this role's write-set-discipline
check or is unrelated repo housekeeping. Evidence: the approval timestamp
cross-referenced against PR #199's and PR #200's commit/merge timestamps (partially
done in the survey — PR #199 merged 3 seconds after the approval comment, PR #200's
first commit 6 minutes after); whether that 3-second gap is meaningful is a phase-2
judgment, not resolved here. Also in scope: whether issue #197's closure
(2026-08-02T11:09:14Z) is consistent with this role's own phase-2 gate not yet being
satisfied at the time of closure (flagged in the survey, not evaluated).

**Step** — which specific artifact, if any, is deficient. Candidates already
surfaced (not judged): the pytest-count figures reported in `implementation.md`'s
§검증 ("133 passed, 17 failed") versus the PR #200 comment's 실측 1/3 ("150 passed, 0
failed" then, post-merge, "150 passed, 2 failed") — same nominal test files,
different raw numbers, not reconciled this session; the `.warrant-hunt.count`
deletion in PR #199; and the issue-closure-timing question above. Evidence for each:
the file:line / comment-URL citations already captured in the survey, plus a phase-2
character-level read of `test_spawn.py`'s new fixture body against the current issue
#189 body (not done this session). Any deficiency finding will carry the four-part
blameless shape (impact, timeline, root cause, action item) this role's directive
requires.

## Independent sweep, beyond the four issue-stated requirements

Phase 2 will also check the "범위 밖" list in `plan-parser-fix.md` (schema doc
unchanged, `_PLAN_STEP_RE` unchanged, no fence-hardening/tilde-fence support added)
against the actual `e7bfdcb` diff, since an out-of-scope item touched anyway would be
a trajectory-level finding; and the Rationale section's three adopted choices (fence
toggle reuse, space-bounded prefix header match, unchanged first-match-wins with a
documented-not-gated duplicate-header rule) against what `e7bfdcb` actually
implements, to confirm the code matches the specific design the approved proposal
recorded rather than a different design that happens to pass the same tests.

## Method constraint carried into phase 2

Every verdict-bearing sentence in the phase-2 record will name its source (commit
SHA, file:line, or PR/issue comment URL) immediately adjacent, per this role's
directive. No file will be cited as evidence of "what happened" independent of a
diff, commit, or comment citation. Where a file:line citation into current `HEAD` is
used, it is used only where already confirmed identical to the `e7bfdcb`/`9dc099a`
diff state — confirmed this session via `git log --oneline --follow -- gates/flows.py`,
which shows `e7bfdcb` as the tip commit touching that file, and `HEAD` (`415a19e`)
matching `origin/main`.

## Gate check before phase 2 opens

As of this session, issue #197's only comment is `APPROVE issue-197/implementation`
— no `APPROVE issue-197/execution-observation` comment exists, and no PR review
Approve exists on any PR for the `issue-197/execution-observation` branch (none is
open yet, per `gh pr list --state all --search "head:issue-197/execution-observation"`,
which returns empty). Per role-handoff contract v3 s19, phase 2 does not open until
one of those two approval paths is satisfied for this role specifically, from a
`docs/specs/approvers.md` account (`JiwonJung94` or `jjongkwann`) — and, if the path
taken is a PR review Approve, from an account other than this PR's author. This
proposal, the accompanying survey, and the PR that carries them are this session's
phase-1 output; phase 2 (the actual verdict record at
`docs/issue-197/reports/execution-observation.md`) is deferred to a future session
after approval.
