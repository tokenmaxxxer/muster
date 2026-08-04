---
subject: issue-224
role: execution-observation
observed_role: implementation
observed_pr: 255
code_under_review: c71faba05224f06cb3a10341c5ae3a8c720d487b
loop_state: phase-2-in-progress
---

# Execution-observation record — issue #224, step 2

## Independence

This role did not author, edit, or execute any part of the observed
artifact, in this session or any other. `spawn.py`, `gates/flows.py`,
`test_spawn.py`, `test_flows.py`,
`docs/issue-224/proposals/query-watch-reliability.md`,
`docs/issue-224/decisions/watch-crash-exit-code.md`, and
`docs/issue-224/reports/implementation.md` were read only — every code
citation below addresses the blob at commit `c71faba05` extracted with
`git show`, never the working tree, and neither `spawn.py` nor either
test suite was run at any point. The only paths this branch writes are
`docs/issue-224/reports/execution-observation.md`,
`docs/issue-224/reports/execution-observation/`, and
`docs/issue-224/proposals/execution-observation-plan.md`. Findings below
are returned here and nowhere else: no issue was filed, no edit was made
to the observed role's write set, and no approval was rendered or
relayed.

Everything after this section is verdict-bearing.

## What was done

Ran the nine checks C1–C9 declared in the approved plan
(`docs/issue-224/proposals/execution-observation-plan.md:60-120`)
against the artifacts PR #255 actually produced, then rendered the
three verdict levels (outcome, trajectory, step) required of this role.
No re-execution of the observed role's task: alternative 1 of the plan
(`:124-131`) had already rejected re-running the suites as prohibited
and non-probative, and it was not run.

## Why

Issue #224's `## 실행 계획` lists step 2 as `execution-observation` of
step 1. Step 1 was delivered by the `implementation` role as PR #255
and merged to `main` as `d14d44da`. Phase 2 of this observation opened
on the issue-level approval comment
https://github.com/tokenmaxxxer/on-the-record/issues/224#issuecomment-5173757435
(body exactly `APPROVE issue-224/execution-observation`, author
`jjongkwann`, type `User`, 2026-08-04T02:04:03Z), whose account is
listed at `docs/specs/approvers.md:2`.

## Upstream basis

- Issue #224 body — three named defects, plus two scope judgments the
  issue delegated to the proposal ("제안이 판단", "제안이 비용을 보고
  판단").
- Observed phase-1 commit `9eb1f71fa` (2026-08-03T11:09:18Z) — survey,
  scout brief, proposal.
- Observed phase-2 commit `c71faba05` (2026-08-03T12:35:25Z) — the code
  under review.
- `docs/issue-224/proposals/execution-observation-plan.md` — this
  role's approved plan, whose C1–C9 this record answers.

## Evidence read this session

Read directly, not summarized secondhand: issue #224 body and both of
its comments (`gh api .../issues/224/comments --paginate`); PR #255
metadata (`author jjongkwann`, `createdAt 2026-08-03T11:09:40Z`,
`reviews []`, `mergedAt 2026-08-04T01:29:43Z`, `state MERGED`); PR
#255's single conversation comment
https://github.com/tokenmaxxxer/on-the-record/pull/255#issuecomment-5166078117
(2026-08-03T12:05:14Z, the three feedback items); the approval comment
https://github.com/tokenmaxxxer/on-the-record/issues/224#issuecomment-5166077886
(2026-08-03T12:05:12Z, body exactly `APPROVE issue-224/implementation`);
`git show --stat 9eb1f71fa`; `git diff --stat 9eb1f71fa c71faba05`; the
`spawn.py`, `gates/flows.py`, `test_spawn.py`, `test_flows.py` blobs at
`c71faba05`; `9eb1f71fa:docs/issue-224/reports/implementation/scout-brief.md`;
and the committed `docs/issue-224/proposals/query-watch-reliability.md`,
`docs/issue-224/decisions/watch-crash-exit-code.md`,
`docs/issue-224/reports/implementation.md`, `docs/specs/approvers.md`.

## Checks C1–C9

**C1 — does the roster entry outlive the window the crash predicate is
meant to tolerate? No.** `_spawn_one()` removes the roster entry at
`c71faba05:spawn.py:2901` (`roster_remove(roster_key)`), on the line
immediately after `rc = proc.wait()` at `:2900`; `roster_remove()` at
`c71faba05:spawn.py:1328-1332` pops the key outright. The
`session-end` event is appended much later, at
`c71faba05:spawn.py:3003`, after `board_snapshot`/delta (`:2913-2915`)
and `ledger_write` (`:2966-2978`). The key removed is
`roster_key = f"issue-{issue}/{role}"` (`c71faba05:spawn.py:2724`) —
byte-identical to the key `_watch()` looks up at
`c71faba05:spawn.py:1793`. So across the whole interval
[`:2901`, `:3003`) — precisely the post-processing tail the deviation
was introduced to tolerate — `_roster_load().get(key)` is `None`, and
the predicate's first disjunct `roster_entry is None`
(`c71faba05:spawn.py:1845`) is true regardless of `wrapper_pid`.

**C2 — does the drain check cover the same window? No.** The drain
check at `c71faba05:spawn.py:1832-1836` returns `continue` only if a
`session-end` line already exists past the offset. Inside C1's interval
no such line exists on disk — it is written at `:3003`, i.e. at the
interval's far end. The drain check therefore falls through to the
liveness branch for the entire window.

**C3 — does the tail regression test construct a state C1's ordering
permits? No.** `test_follow_tolerates_post_processing_tail_before_session_end`
(`c71faba05:test_spawn.py:3223-3249`) arranges a *present* roster entry
with a live `wrapper_pid` (`spawn.roster_register(...)` at `:3232-3235`,
on top of the same registration already done in `setUp` at `:3136-3139`)
and only then simulates the tail. Production, per C1, has no entry at
all in that window. The test's arrange block and the production state
it names diverge.

**C4 — feedback item 1 (drain-before-liveness ordering): satisfied.**
The requester's text at
https://github.com/tokenmaxxxer/on-the-record/pull/255#issuecomment-5166078117
offered two acceptable responses — mirror `session_end_verdict()`'s
ordering, or record the reason for a different design. The landed code
takes the first: `session_end_verdict()` checks `session-end` presence
at `c71faba05:spawn.py:1236` before `alive_fn(pid)` at `:1240`, and
`_watch()`'s follow loop likewise runs the drain scan at `:1832-1836`
before the liveness lookup at `:1843-1845`, with the ordering and its
reason stated in-line at `:1826-1831`. The record explains the same at
`docs/issue-224/reports/implementation.md:37-55`. Ordering matched.

**C5 — feedback item 2 (exit-code value): satisfied.**
`WATCH_CRASH_RC = 2` is pinned at `c71faba05:spawn.py:1783` and
documented at `docs/issue-224/decisions/watch-crash-exit-code.md:12-16`,
with the three-value contract enumerated at `:18-29` and the
reuse-`1` and namespaced-code alternatives rejected on stated grounds
at `:31-56`. `2` sits inside the 1–127 handled-error band of the
convention recorded in this role's scout brief
(`docs/issue-224/reports/execution-observation/scout-brief.md:32-35`,
sourced to https://www.baeldung.com/linux/status-codes), and is
distinct from the pre-existing `0`/`1`.

**C6 — feedback item 3 (test file placement): satisfied.** The
placement is settled and reasoned at
`docs/issue-224/reports/implementation.md:73-83` — `test_flows.py`, not
`test_spawn.py::FlowsPayload`, because neither file previously
unit-tested `_pr_list_all`'s own `subprocess.run` call and `test_flows.py`
already tests `gates/flows.py` functions directly. The test landed
there: `c71faba05:test_flows.py:58-68` (`class PrListAllLimit`). The
choice is also carried on the doc-placement ladder at `:187-191` with a
stated reason for not opening a separate `decisions/` entry.

**C7 — deviation justification for `wrapper_pid`: legitimately
triggered, recorded, but its stated effect does not hold.** The
approved wording named the existing field —
`docs/issue-224/proposals/query-watch-reliability.md:79-82` ("로스터에서
같은 키 … 의 현재 pid 를 다시 조회해 `_alive(pid)`를 확인 — 죽었으면
(엔트리 부재 포함)"), repeated at `:124-132`. The landed code reads
`roster_entry.get("wrapper_pid")` instead
(`c71faba05:spawn.py:1844`), fed by a new field at
`c71faba05:spawn.py:2781`. Trigger: legitimate — the mandatory hunt
reproduced a real false positive against the literal wording, recorded
at `docs/issue-224/reports/implementation.md:125-147` and `:254-274`.
Containment claim: verified true — `roster_kill()` still reads `pid`
(`c71faba05:spawn.py:1858-1859`) and `gates/flows.py` still reads `pid`
for its liveness display and payload (`c71faba05:gates/flows.py:354`,
`:363`), and the diff `9eb1f71fa..c71faba05` touches neither.
Completeness: insufficient — the justification at `:254-274` asserts
the new field "stays alive for the whole `_spawn_one()` invocation" and
stops there; it never states that the approved predicate's other
disjunct, entry-absence (proposal `:81`, landed at
`c71faba05:spawn.py:1845`), fires across that same invocation's tail
because of `roster_remove()` at `c71faba05:spawn.py:2901`. A requester
reading `:254-274` could not have re-decided on that basis. This is the
step-level finding below.

**C8 — the two query fixes: both landed and tested.** S1:
`c71faba05:spawn.py:845-856` passes `--paginate --slurp` and flattens
with `[c for page in data for c in page]` at `:854`, keeping the
pre-existing `except ValueError` empty-list fallback at `:852-853`;
covered by `c71faba05:test_spawn.py:2599-2621` (2-page shape flattens to
2 dicts, and both flags asserted present in the constructed command) and
`:2623-2640` (the real zero-comment `[[]]` shape yields `[]`). The
`--slurp`-wraps-pages semantics this relies on is the externally
documented behaviour recorded at
`docs/issue-224/reports/execution-observation/scout-brief.md:28-31`
(https://cli.github.com/manual/gh_api, https://github.com/cli/cli/issues/10459).
S2: `c71faba05:gates/flows.py:52-55` adds `"--limit", "1000"` after the
`--json` argument, matching the sibling `_issue_list_all()` idiom the
proposal named (`query-watch-reliability.md:121-123`); covered by
`c71faba05:test_flows.py:62-68`.

**C9 — record completeness: one internal inconsistency, one
undispositioned item.** (a) `docs/issue-224/reports/implementation.md:89`
says "4 new tests" and then names three at `:90-97`; `git diff
9eb1f71fa c71faba05 -- test_spawn.py` adds exactly three
`def test_follow_*` methods (`c71faba05:test_spawn.py:3178`, `:3198`,
`:3223`). Six new tests landed in total across both files (three
`WatchFollow`, two `IssueComments`, one `PrListAllLimit`) — the "4" is a
miscount local to item 5c, not a missing test. (b) The phase-1
proposal's manual check
(`query-watch-reliability.md:180-184` — look at a real >30-comment
thread in this repo, or skip if none exists) is never explicitly
performed-or-waived in the record's Verification section
(`implementation.md:99-105`); the nearest thing is hunt finding 4
(`implementation.md:228-230`), which reports the flatten assumption
verified against real multi-page `gh api` output on an *external* repo.
That is equivalent or better evidence, but the proposal's own
conditional is left unanswered as written.

## Verdicts

### Outcome — landed, with one qualification

PR #255 landed what issue #224 asked. Defect 1 is fixed at
`c71faba05:spawn.py:845-856`; defect 2 at
`c71faba05:gates/flows.py:52-55`; defect 3's stated harm — "영원히
기다린다 … 오케스트레이터 영구 블록" — is fixed, in that a `--follow`
against a session with no roster entry and no `session-end` now returns
`WATCH_CRASH_RC` in finite iterations rather than looping forever
(`c71faba05:spawn.py:1845-1848`, asserted by
`c71faba05:test_spawn.py:3178-3196` including its `assertLess(len(calls), 5)`
bound). Both scope judgments the issue delegated were made and reasoned
rather than skipped: the "참고 관찰" (watch returning on every event) at
`query-watch-reliability.md:87-100` and the two same-family candidates at
`:102-113`, each with a stated rejection ground and a matching
Out-of-scope entry at `:150-163`. Qualification: the false-positive the
hunt itself surfaced is not eliminated by the fix that claims to
eliminate it — see the step verdict.

### Trajectory — sound

Scouting ran and produced a committed brief:
`9eb1f71fa:docs/issue-224/reports/implementation/scout-brief.md`, which
carries adopt/skip lines, a `Sources:` block of four external URLs plus
internal line references, and an explicit stage/mode statement
("1스테이지(WebSearch 2건 병렬…), 판단점 1회 후 종료"). The survey
preceded the proposal rather than following it: the proposal cites
`survey.md` as already-existing evidence at
`query-watch-reliability.md:22`, `:42`, `:71` and cites `scout-brief.md`
at `:70`, `:76`. Approval was real and correctly typed — PR #255's
`reviews` array is empty and its author is `jjongkwann`, i.e.
single-account mode, so approval came as the issue-level comment
https://github.com/tokenmaxxxer/on-the-record/issues/224#issuecomment-5166077886
whose body is exactly `APPROVE issue-224/implementation` (string
equality, no prose), posted by `jjongkwann` (`type: User`), an account
listed at `docs/specs/approvers.md:2`. Ordering holds: phase-1 commit
`9eb1f71fa` 2026-08-03T11:09:18Z → PR #255 opened 2026-08-03T11:09:40Z
→ approval 2026-08-03T12:05:12Z → phase-2 commit `c71faba05`
2026-08-03T12:35:25Z → merge `d14d44da` 2026-08-04T01:29:43Z. No
phase-2 artifact predates the approval: `git show --stat 9eb1f71fa`
contains only the proposal, survey, and scout brief, and every code and
record file appears first in `git diff --stat 9eb1f71fa c71faba05`. The
mandatory hunt ran, its stance rotation is stated, and it is what caught
the pid-vs-tail defect (`docs/issue-224/reports/implementation.md:196-252`)
— including catching that the phase-1 scout brief's own premise ("이미
있는 정확한 신호(pid)") was wrong. Deviating on that basis, and
recording the deviation at `:254-274`, is the correct trajectory
response; the deficiency is in the deviation's depth, not in taking it.

### Step — one deficient artifact

`c71faba05:spawn.py:1845` together with
`c71faba05:test_spawn.py:3223-3249`. Detailed below.

## Finding — the `wrapper_pid` deviation does not close the window it was taken for

**Impact.** During `_spawn_one()`'s post-processing tail — from
`roster_remove(roster_key)` at `c71faba05:spawn.py:2901` until
`_append_event(events_path, "session-end", outcome)` at `:3003`, an
interval spanning `ensure_pushed()`'s real `git push`, gate/ownership
reporting, `classify`, and `ledger_write` — a concurrent
`spawn.py watch --follow` that reaches its liveness branch reports a
crash for a session that is completing normally. The drain check at
`:1832-1836` cannot suppress it (C2: `session-end` is not on disk yet),
and `roster_entry is None` at `:1845` is true (C1), so the branch
returns `WATCH_CRASH_RC = 2` (`:1848`) — which `main()` propagates as
the CLI's process exit code, per
`docs/issue-224/decisions/watch-crash-exit-code.md:12-16`. This is the
same false-positive class, in the same window, with the same operator
consequence, that the hunt reported as CONFIRMED-and-fixed at
`docs/issue-224/reports/implementation.md:213-223`.

**Timeline.** `9eb1f71fa` (2026-08-03T11:09:18Z) approved the literal
`pid` predicate including its entry-absence disjunct
(`query-watch-reliability.md:81`). During phase 2 the hunt reproduced
the tail false-positive against that predicate
(`implementation.md:125-147`). The response, landed in `c71faba05`
(2026-08-03T12:35:25Z), changed only which field the *second and third*
disjuncts read (`pid` → `wrapper_pid`, `c71faba05:spawn.py:1844`),
leaving the first disjunct untouched. The regression test written
alongside it (`c71faba05:test_spawn.py:3223-3249`) registers a roster
entry in its arrange block, so it exercises a state in which only the
changed disjuncts can fire, and passes. Merged as `d14d44da`
(2026-08-04T01:29:43Z).

**Root cause.** The deviation was scoped to the field the hunt's
repro had implicated, not to the predicate the repro's window actually
satisfies. `roster_remove()` at `:2901` is pre-existing code untouched
by this change (`git diff 9eb1f71fa c71faba05 -- spawn.py` contains no
hunk there), so the entry-lifetime question never entered the diff's
field of view — while the predicate at `:1845` reads that lifetime as a
death signal. This is the exact failure mode the field records as its
first must-be for this change class: delete the registry entry *after*
the process has finished its shutdown work, not before, because a
monitor reading the gap calls a live process dead
(`docs/issue-224/reports/execution-observation/scout-brief.md:12-22`,
sourced to https://github.com/spring-projects/spring-boot/issues/4369
and https://bugs.freedesktop.org/show_bug.cgi?id=45713). The test not
catching it is the field's second must-be — a regression test must
construct a state production can actually reach (`scout-brief.md:23-27`,
https://microsoft.github.io/code-with-engineering-playbook/automated-testing/unit-testing/mocking/).

**Action item.** For the human to judge and, if they agree, to file:
either move `roster_remove(roster_key)` from `spawn.py:2901` to after
the `session-end` append at `:3003` so the entry's lifetime covers the
tail, or drop `roster_entry is None` from the `:1845` predicate as a
death signal and treat entry-absence as "unknown, keep waiting until the
stall safety net fires". Whichever is chosen, the regression test at
`test_spawn.py:3223-3249` should arrange the *absent-entry* tail state
rather than registering one. This role files nothing and edits nothing
in that write set — under role-handoff contract v3 issues are
user-authored only, and this record is where the finding is returned.

## Open findings

1. **The finding above** — `c71faba05:spawn.py:1845` /
   `c71faba05:test_spawn.py:3223-3249`. Confirmed against the artifact,
   not fixed here (fixing it would mean editing the observed role's
   write set, which this role must not do).
2. **`implementation.md:89`'s "4 new tests" vs the three named at
   `:90-97`** (C9a). A documentary miscount local to that item; the
   three `WatchFollow` tests all exist at
   `c71faba05:test_spawn.py:3178`, `:3198`, `:3223`, and six new tests
   landed in total. No functional consequence.
3. **The phase-1 manual check at
   `query-watch-reliability.md:180-184` is neither marked performed nor
   waived** in `implementation.md:99-105` (C9b). Hunt finding 4
   (`implementation.md:228-230`) reports equivalent verification against
   an external repo's real multi-page `gh api` output, so the
   substantive risk is covered; only the disposition is missing.

**Resolution path.** All three are returned to the human on this role's
PR and are theirs to judge. Finding 1 is the one worth a follow-up
issue — it is a live false-positive path in merged code, and its two
candidate fixes are named in the action item above. Findings 2 and 3
are record-hygiene items with no functional consequence; the natural
place to absorb them is whatever issue next touches
`docs/issue-224/reports/implementation.md`, if any. Nothing here is
resolvable by this role, because every candidate edit lands inside the
observed role's write set.

## Next steps

1. Commit this record on `issue-224/execution-observation` and flip
   `loop_state` to `landed`.
2. Push the branch and open the PR against `main` carrying this record
   as its sole phase-2 artifact.
3. Stop. Merge or closure of that PR is the human's act, and finding 1
   becomes an issue only if the human files it.
