---
subject: issue-266
role: execution-observation
observed_role: implementation
observed_pr: 267
observed_commits:
  - 1fdd1ac  # phase 1 — survey + scout brief + proposal
  - d61e93c  # phase-2 start — implementation record opened
  - be53d1e  # phase-2 delivery — drop roster-entry-absence signal
observed_merge: 247051e
loop_state: landed
---

# Execution-observation record — issue #266, step 2

## Independence

This role did not author, edit, or in any way participate in producing the
artifacts it judges here. PR #267, its three commits, and every file they
touched — `spawn.py`, `test_spawn.py`,
`docs/issue-266/reports/implementation.md`,
`docs/issue-266/proposals/roster-lifetime-vs-absence-signal.md`,
`docs/issue-266/decisions/watch-crash-trigger-wording-amendment.md` — were
produced by the `implementation` role on branch `issue-266/implementation`
and merged to `main` as `247051e` before this session began. Nothing under
those paths was modified by this session, and nothing in them was
re-executed: no test run, no `spawn.py watch` invocation, no gate script.
This session's write set is `docs/issue-266/reports/execution-observation.md`
and `docs/issue-266/reports/execution-observation/` only.

This statement precedes every verdict-bearing sentence in this document.

## What was done

Executed the seven checks declared in
`docs/issue-266/proposals/execution-observation-plan.md` (C1, C2, S1–S5)
against the artifacts that plan named, and rendered the role's three-level
verdict — outcome, trajectory, step — below. Four findings survived
checking (F1–F4); three checks resolved clear and are recorded as such
rather than dropped.

## Why

Issue #266's `## 실행 계획` step 2 asks for an independent observation of
step 1. Step 1 was delivered by the `implementation` role as PR #267 and
merged as `247051e` at 2026-08-04T04:08:44Z; this record is the sole
phase-2 artifact of step 2.

## Upstream basis

- Issue #266 body — 요구 1 (pick (a) or (b) with tradeoffs), 요구 2
  (entry-absence red→green regression test), 요구 3 (#224's drain order,
  `WATCH_CRASH_RC`, `wrapper_pid` stay #224's).
- Approval for this phase 2: issue comment whose entire body is
  `APPROVE issue-266/execution-observation`, author `jjongkwann`,
  2026-08-04T04:30:34Z —
  <https://github.com/tokenmaxxxer/on-the-record/issues/266#issuecomment-5174627893>.
  `jjongkwann` is listed in `docs/specs/approvers.md`; PR #270's author is
  the same account, so this is contract v3 s19 single-account mode.
- Approved plan: `docs/issue-266/proposals/execution-observation-plan.md`
  (PR #270, phase 1).

## Inspection ceiling (stated, not implied)

Per the scout brief's adopted must-be
(`docs/issue-266/reports/execution-observation/scout-brief.md:24-29`,
EviACT), this audit never executed anything. Every claim below about the
recorded red→green proof
(`docs/issue-266/reports/implementation.md:203-206`) is a claim about
**construction and internal consistency** — that the test's arrange builds
the state the issue named, and that the recorded red output is the output
the pre-image predicate would produce. It is not a claim that the run
happened; that remains the observed role's assertion, unverified here by
design.

## Evidence read this session

| Artifact | How read |
|---|---|
| Issue #266 body and all three comments | `gh issue view 266`, `gh api …/issues/266/comments` |
| PR #267 metadata (body, commits, `reviews`, merge) | `gh pr view 267 --json …` |
| `be53d1e` full message + `--stat` | `git show be53d1e --stat --format=…` |
| `be53d1e` diffs of `spawn.py` and `test_spawn.py` | `git show be53d1e -- <path>` |
| `be53d1e:spawn.py` at :1855-1912, :3000, :3102 | `git show be53d1e:spawn.py` |
| `be53d1e^:spawn.py` at :1903, :2995, :3097 | `git show be53d1e^:spawn.py` |
| `be53d1e:test_spawn.py` at :3399-3626 (whole `WatchFollow`) | `git show be53d1e:test_spawn.py` |
| `1fdd1ac`, `d61e93c` `--stat` + authored dates | `git show --stat --format=…` |
| `docs/issue-266/proposals/roster-lifetime-vs-absence-signal.md` | Read (full) |
| `docs/issue-266/reports/implementation.md` | Read (full, 225 lines) |
| `be53d1e:docs/issue-266/decisions/watch-crash-trigger-wording-amendment.md` | `git show` |
| `247051e:docs/issue-224/decisions/watch-crash-exit-code.md:18-32` | `git show 247051e:…` |
| `docs/handbooks/operations.md:660-690` | `sed -n`, `grep -n` |
| `gates/pr_reference.py` (`check_body`/`check` surfaces) | `grep -n` |
| `docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md:1-60` | `sed -n` |
| `board-gate.sh:24` (R4 statement) | `grep -n` on the core plugin hook |
| `docs/specs/approvers.md` | `cat` |

Deliberately **not** read as evidence: `spawn.py` and `test_spawn.py` at
HEAD. Present-tense source shows what exists now, not what the observed
role did; `be53d1e` and its parent are the admissible form and are what
was read.

## Checks

### C1 — outcome, against the issue's three requirements

**요구 1 is met.** `be53d1e:spawn.py` narrows the `--follow` death
predicate from `if roster_entry is None or not pid or not _alive(pid):`
(`be53d1e^:spawn.py:1903`) to `if pid is not None and not _alive(pid):`
(`be53d1e:spawn.py:1908`) — alternative (b), the branch the issue offered.
The tradeoff the issue demanded ("제안이 트레이드오프와 함께 선택") is
made in writing at
`docs/issue-266/proposals/roster-lifetime-vs-absence-signal.md:19-30`: (a)
is rejected with a named mechanism (`roster_kill` at :1923 and `roster_ps`
at :1355 reap the same key on the already-dead `pid`, reopening the race a
`roster_remove` move would not close), and (b)'s cost is stated rather
than hidden ("진짜 크래시하면 … `WATCH_CRASH_RC` 를 리턴하지 않고 …
`0`(stall)으로 리턴한다", same file :30).

**요구 2 is met in construction.** The added test
`test_follow_tolerates_roster_entry_fully_absent_before_session_end`
(`be53d1e:test_spawn.py:3601-3626`) constructs exactly the tail state the
issue named — `spawn.roster_remove("issue-180/implementation")` for "명부
비어 있음", a faked `_await_bounded` that returns without progress twice
for "프로세스는 후처리 중", and no `session-end` until the third call for
"session-end 미기록". Against the pre-image predicate
(`be53d1e^:spawn.py:1903`) an absent entry makes the first disjunct true,
so `_watch` returns `WATCH_CRASH_RC = 2` where the test asserts `0` — the
recorded red output `AssertionError: 2 != 0`
(`docs/issue-266/reports/implementation.md:203`) is the output that
predicate produces on this arrange. Subject to the inspection ceiling
above, the red→green claim is internally consistent; it is not
independently confirmed to have run.

**요구 3 is met at code level.** `git show be53d1e --numstat` lists exactly
four files — `spawn.py` +6/−1, `test_spawn.py` +42/−6, the new decision
doc +56/−0, the implementation record +202/−29. The `spawn.py` change is confined to the
predicate line and a five-line comment; the `session-end`-first drain
block (`be53d1e:spawn.py:1884-1892`), the `WATCH_CRASH_RC` constant, and
the `wrapper_pid` field are untouched by the diff. See F1 — the code is
retained but its only regression test stopped discriminating it.

### C2 — trajectory, against contract v3 s19

Phase-1 artifacts precede the proposal's execution and are one commit:
`git show --stat 1fdd1ac` (authored 2026-08-04T02:53:18Z) contains exactly
`docs/issue-266/reports/implementation/survey.md`,
`…/implementation/scout-brief.md`, and
`docs/issue-266/proposals/roster-lifetime-vs-absence-signal.md` — survey
and scout brief exist and ship with the proposal, no phase-2 file among
them. Approval is real and is the correct mechanism for single-account
mode: PR #267 carries `reviews: []` (`gh pr view 267 --json reviews`), and
the approval is the issue comment whose entire body is the exact string
`APPROVE issue-266/implementation`, author `jjongkwann`, type `User`,
2026-08-04T03:00:27Z
(<https://github.com/tokenmaxxxer/on-the-record/issues/266#issuecomment-5174096377>);
`jjongkwann` is listed in `docs/specs/approvers.md`. Both phase-2 commits
follow it — `d61e93c` at 03:04:51Z opens the record as the first phase-2
act (its `--stat` is `docs/issue-266/reports/implementation.md` alone,
+51), `be53d1e` at 03:21:30Z carries the code. Nothing phase-2-shaped is
dated before 03:00:27Z. The trajectory is sound.

### S1 — the `Closes #266` in the commit message

`be53d1e`'s message body contains the line `Closes #266` (`git show
be53d1e --format=%B`), while PR #267's body carries no closing keyword and
says so explicitly ("closing keyword removed by relay per plan-aware
rule"). Guardrail question first, per the scout brief's adopted
classification (`…/scout-brief.md:36-39`): the enforcing control is
`gates/pr_reference.py:check()`, which reads the PR body via
`_pr_view` → `gh pr view --json body` (`gates/pr_reference.py:92`) and the
issue body for the plan (`:97-101`) — commit messages are read by neither.
`docs/handbooks/operations.md:682-683` documents the same one-surface
scope, and `:687-689` records that the check is not even registered as
required on main's branch protection yet. GitHub's own auto-close, by
contrast, honours closing keywords in commit messages landing on the
default branch, which is why merging `247051e` closed the issue 29 seconds
before the human reopened it
(<https://github.com/tokenmaxxxer/on-the-record/issues/266#issuecomment-5174498053>,
04:09:13Z). This resolves to F2 — booked primarily against the control,
with the authoring half named honestly.

### S2 — the approved write set contained an unwritable path

`docs/issue-266/proposals/roster-lifetime-vs-absence-signal.md`'s `files:`
block line 4 names `docs/issue-224/decisions/watch-crash-exit-code.md`, and
its "What will be done" item 4 (`:37`) requires editing it. `board-gate.sh`
R4 — "A role session writes an issue tree only from that issue's [branch]"
(`board-gate.sh:24`, contract v3 s10) — makes that write impossible from
branch `issue-266/implementation`, so the write set the human approved in
phase 1 contained a path this branch could never write. The observed role
hit it at execution time and recorded it as a deviation with its mechanism
(`docs/issue-266/reports/implementation.md:91-96` and `:128-141`), which is
what change-control practice asks of a deviation
(`…/scout-brief.md:17-23`); the deviation itself is therefore not the
finding. The residual is: `247051e:docs/issue-224/decisions/watch-crash-exit-code.md:25-26`
still reads "`2` (new) — `--follow` detected the session's pid is dead (or
its roster entry is gone)", which `be53d1e:spawn.py:1908` has made false.
That resolves to F4.

### S3 — the second dropped branch — clear, no finding

The delivered predicate drops two former death branches, not the one the
issue named: `roster_entry is None`, and falsy `pid` (an entry present
with no `wrapper_pid` field). Issue #266 요구 1(b) names only the first.
The binding document is the approved proposal, and it names both
explicitly — "엔트리 부재(`roster_entry is None`) 또는 엔트리는 있지만
`wrapper_pid` 필드가 없는 경우(`pid is None`)는 더 이상 즉시 사망 신호로
안 쓰고"
(`docs/issue-266/proposals/roster-lifetime-vs-absence-signal.md:34`) —
and prescribes the exact replacement text `if pid is not None and not
_alive(pid):`, which `be53d1e:spawn.py:1908` matches character for
character. The delivered predicate stays inside what the human approved.
Checked and clear.

### S4 — the rewritten test versus 요구 3

`test_follow_detects_dead_session_and_returns_crash_rc`'s arrange changed
from `spawn.roster_remove("issue-180/implementation")`
(`be53d1e^`, visible as the `-` line in `git show be53d1e -- test_spawn.py`)
to registering an entry whose `wrapper_pid` is a confirmed-dead process
(`be53d1e:test_spawn.py:3479-3485`). The rewrite is justified and the
record's justification matches the diff: pre-image, the test constructed
entry-absence — the very state (b) redefines as non-crash — so under the
fix its mock would loop forever, exactly as
`docs/issue-266/reports/implementation.md:104-127` describes. The rewrite
also gives #224's `wrapper_pid` branch its first real test; pre-image, no
test in `WatchFollow` exercised it. So the rewrite is an improvement, not
a loss — but the same latent problem in a sibling test went unexamined,
which is F1.

### S5 — line-number citations

The comment introduced by this very commit (`be53d1e:spawn.py:1909-1912`
in the post-image) cites `roster_remove` at `spawn.py:2995` and the
`session-end` append at `spawn.py:3097`. Those are the pre-image
positions (`be53d1e^:spawn.py:2995`, `:3097`); in the post-image the same
statements sit at `be53d1e:spawn.py:3000` and `:3102`, shifted by exactly
the five comment lines the commit added above them. The same pre-image
offset runs through the commit message, the record
(`docs/issue-266/reports/implementation.md:51`), and the decision doc,
all of which cite `spawn.py:1903` for a predicate that lives at
`be53d1e:spawn.py:1908`. This resolves to F3. Separately, the issue body's
own `:2901`/`:3003` were stale before this work began and are not this
change's account (transition-based relevance,
`…/scout-brief.md:31-34`).

## Verdicts

### Outcome — landed, with one qualification

PR #267 landed what issue #266 asked. All three requirements are satisfied
by `be53d1e`: the predicate narrowed with a written tradeoff
(`be53d1e:spawn.py:1908`;
`…/proposals/roster-lifetime-vs-absence-signal.md:19-30`), the
entry-absence regression test constructed and its red→green recorded
(`be53d1e:test_spawn.py:3601-3626`;
`docs/issue-266/reports/implementation.md:203-206`), and #224's landed
items left untouched by the diff (`git show be53d1e --numstat`: four files,
`spawn.py` +6/−1 confined to the predicate and its comment). The
qualification: 요구 3's "유지" holds for the drain code but not for its
test coverage (F1), and the trigger documentation the proposal committed
to correcting is still wrong on `main` (F4).

### Trajectory — sound

The phase-1→phase-2 path met contract v3 s19 in order and in substance.
Survey and scout brief exist and shipped with the proposal in `1fdd1ac`
(02:53:18Z), not after it; approval is a real human act by an
`approvers.md` account through the correct single-account mechanism
(exact-string issue comment, 03:00:27Z, issuecomment-5174096377); the
record was opened as the first phase-2 act (`d61e93c`, 03:04:51Z) and the
code followed (`be53d1e`, 03:21:30Z). Both execution-time deviations were
written down with their mechanisms at the time they were taken
(`docs/issue-266/reports/implementation.md:98-141`), which is the
artifact a working change-control process is supposed to produce
(`…/scout-brief.md:17-23`) — the deviations are not held against the
trajectory.

### Step — four deficient artifacts

`be53d1e:test_spawn.py:3497-3520` (F1, the material one),
`be53d1e`'s commit message (F2, primarily a control gap),
`be53d1e:spawn.py:1910-1911` (F3, cosmetic),
and `docs/issue-266/reports/implementation.md:208-211` read against
`247051e:docs/issue-224/decisions/watch-crash-exit-code.md:25-26` (F4).

## Findings

### F1 — the drain-priority guard lost its only discriminating test

**Impact.** `be53d1e:spawn.py:1884-1892` — the block that drains a
residual `session-end` before the death check, which PR #255 feedback 1
put there and issue #266 요구 3 requires be kept — is, after `be53d1e`, no
longer protected by any test that would fail if it were deleted. Its one
guard, `test_follow_prioritizes_pending_session_end_over_pid_check`
(`be53d1e:test_spawn.py:3497-3520`), builds its "pid is dead" precondition
by calling `spawn.roster_remove("issue-180/implementation")`
(`:3504`) — the exact signal `be53d1e:spawn.py:1908` stopped treating as
death. Traced against the loop at `be53d1e:spawn.py:1875-1912` with
`setUp`'s empty events file (`be53d1e:test_spawn.py:3404-3428` registers a
roster entry and writes no events): with the drain block hypothetically
removed, iteration 1 consumes the `progress` line, reaches the death check,
finds `roster_entry is None → pid is None`, does not crash, and iteration 2
consumes the `session-end` line and returns `0` with `len(calls) == 2` —
the same `rc` and the same call count the test asserts. Against the
pre-image predicate (`be53d1e^:spawn.py:1903`) the same deletion would have
returned `WATCH_CRASH_RC` on iteration 1 and failed the test. The test
went from discriminating to vacuous. No other `WatchFollow` test covers
the ordering: of the nine (`be53d1e:test_spawn.py:3430`, `:3450`, `:3467`,
`:3497`, `:3522`, `:3550`, `:3565`, `:3583`, `:3601`), the two that plant a
live `wrapper_pid` can never crash regardless of the guard, and `:3467`
writes no `session-end` at all.

**Timeline.** 2026-08-04T03:21:30Z, `be53d1e`. The observed role diagnosed
this exact failure mode in the sibling test and rewrote it
(`docs/issue-266/reports/implementation.md:104-127`), and the
composition-regression hunt compared the new test against the *rewritten*
one (`…/implementation.md:189-191`); neither pass swept the remaining
`WatchFollow` tests for the same `roster_remove`-as-death-precondition
idiom.

**Root cause.** The rewrite was scoped by a symptom — the test that hung —
rather than by the predicate change's blast radius. `roster_remove` in an
arrange was load-bearing in more than one test, and only the one that
failed loudly got re-examined; the one that kept passing silently stopped
testing anything.

**Action item (for the human to judge; this role files nothing).** A
follow-up on `test_spawn.py` should re-arm
`test_follow_prioritizes_pending_session_end_over_pid_check` by giving it
the same live-entry/dead-`wrapper_pid` arrange the rewritten `:3467` now
uses, so the residual-`session-end` drain is again the only thing standing
between the test and `WATCH_CRASH_RC`.

### F2 — the closing keyword rode in on a surface no control inspects

**Impact.** Issue #266 auto-closed on merge with plan step 2 still
incomplete, because `be53d1e`'s message body contains `Closes #266`. The
plan-aware rule
(`docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md:20-27`)
blocks a closing keyword while more than one plan step is incomplete, and
both of #266's steps were incomplete at merge time. The recovery cost was
small — the human reopened 29 seconds later
(<https://github.com/tokenmaxxxer/on-the-record/issues/266#issuecomment-5174498053>) —
but the closure was wrong while it stood.

**Timeline.** Keyword authored 03:21:30Z in `be53d1e`; PR #267's body
carries none (the body notes the relay removed it); merge `247051e` at
04:08:44Z auto-closed the issue; reopened 04:09:13Z.

**Root cause — control gap first.** `gates/pr_reference.py:check()` reads
only the PR body (`gates/pr_reference.py:92`) plus the issue body for the
plan (`:97-101`); commit messages are inspected by nothing, and
`docs/handbooks/operations.md:682-683` documents that one-surface scope as
intended while `:687-689` records the check is not yet even required on
main. So the vector had no owner. The authoring half, stated plainly and
without blame: the closing keyword was removed from the PR body but left
in the commit message of the same delivery, so the two surfaces
disagreed.

**Action item (for the human to judge).** The human's reopen comment
already routes this to "#245 관찰/후속의 검토 대상"; this record concurs
and adds the specific shape — the gate's Closes check should read the
PR's commit messages (`gh pr view --json commits`) alongside the body,
since GitHub's auto-close honours both.

### F3 — the new comment's line citations are stale in their own commit

**Impact.** `be53d1e:spawn.py:1910-1911` tells a reader that
`roster_remove` is at `spawn.py:2995` and the `session-end` append at
`spawn.py:3097`; in the tree that comment ships in, they are at
`be53d1e:spawn.py:3000` and `:3102`. A reader following the citation lands
five lines short, inside `_spawn_one`'s tail but not on the call the
comment is about. Cosmetic, but it is the one navigational aid the fix
leaves behind.

**Timeline.** 2026-08-04T03:21:30Z, `be53d1e` — the references were
correct when written against the pre-image (`be53d1e^:spawn.py:2995`,
`:3097`) and were invalidated by the same commit's own five added comment
lines.

**Root cause.** Line-number citations were computed against the working
tree before the edit and not re-checked after it. The same pre-image
offset propagated into the commit message, the record
(`docs/issue-266/reports/implementation.md:51`) and the decision doc,
all citing `spawn.py:1903` for a predicate that ships at
`be53d1e:spawn.py:1908`.

**Action item (for the human to judge).** Either refresh the two numbers
in the comment, or cite by symbol (`_spawn_one`'s `roster_remove` /
`session-end` append) rather than by line — the latter survives the next
edit to the same file.

### F4 — the stale trigger doc has no forward pointer, and is booked as "no open finding"

**Impact.** `247051e:docs/issue-224/decisions/watch-crash-exit-code.md:25-26`
still documents `WATCH_CRASH_RC`'s trigger as "the session's pid is dead
(or its roster entry is gone)", which `be53d1e:spawn.py:1908` made false.
The correction exists at
`be53d1e:docs/issue-266/decisions/watch-crash-trigger-wording-amendment.md`,
but nothing links the stale file to it — and the stale file cannot be
edited from any issue-266 branch (`board-gate.sh:24`, R4), including this
one, so this session cannot add the pointer either. A reader who starts at
the issue-224 decision doc — the natural entry point for "what does exit
code 2 mean" — gets the old semantics with no path to the amendment. The
amendment doc's own stated goal ("a future reader hitting the stale
`docs/issue-224/` text has no path to the truth") is therefore only half
achieved: the truth is reachable from issue #266's tree, not from where the
reader actually lands.

**Timeline.** Deviation taken and recorded 03:21:30Z (`be53d1e`;
`docs/issue-266/reports/implementation.md:128-141`); merged 04:08:44Z with
the issue-224 text unchanged — verified by reading that file at `247051e`.

**Root cause.** The proposal's approved write set named a path R4 forbids
from that branch (S2), and the redirect that followed could only write
forward, never backward. Below that: no mechanism in this repo lets a
correction announce itself at the location being corrected across issue
trees. The residual's only tracker is a "Next steps" line inside a merged
record (`docs/issue-266/reports/implementation.md:213-220`), while that
same record's `## Open findings` says "None" (`:208-211`) — a live
inaccuracy on `main` is thereby recorded as closed.

**Action item (for the human to judge).** The follow-up the record names
is still open and only the human, or a session on
`issue-224/implementation`, can perform it: replace lines 25-26 of
`docs/issue-224/decisions/watch-crash-exit-code.md` with the corrected
paragraph from
`docs/issue-266/decisions/watch-crash-trigger-wording-amendment.md` and
add a pointer to it.

## Open findings

F1, F2, F3, F4 above are open as of this record. None is fixable by this
role: F1 and F3 sit in the observed role's `spawn.py`/`test_spawn.py`, F2
in `gates/`, F4 under `docs/issue-224/` — all outside this role's write
set, and R4 blocks the last one from this branch outright.

## Next steps

None for this role. Step 2 of issue #266's `## 실행 계획` is delivered by
this record; the checks declared in the approved plan are all accounted
for (C1, C2 rendered; S1 → F2, S2 → F4, S4 → F1, S5 → F3; S3 checked and
clear).

## Open-finding resolution path

The human judges F1–F4 on PR #270. Under contract v3 issues are
user-authored only, so this role files none and edits none of the observed
artifacts; if the human judges a finding valid, they file the issue and it
enters the board as its own subject.
