---
code_under_review: b60843f47a194bee278ee93a03044ca7a03d4501
record_under_review: 8d2c96abc119d1a2a75a0fdd38223b1a28fb2702
loop_state: landed
---

# Execution observation — `implementation` role on issue #189, phase 2 (PR #193)

Gate: this record opens only after `APPROVE issue-189/execution-observation`
(issue comment, single-account mode, author `jjongkwann` — an
`docs/specs/approvers.md` account — at 2026-08-02T07:30:24Z,
https://github.com/tokenmaxxxer/on-the-record/issues/189#issuecomment-5156219839).
The accompanying phase-1 survey and proposal (PR #195, merged) are this
role's own prior output; this file is the sole phase-2 artifact.

## Independence statement

This role did not author or edit the observed artifact. Nothing under
`gates/`, `on-the-record/commands/`, `test_spawn.py`, `test_gates.py`,
`docs/specs/flows-schema.md`, or `docs/issue-189/reports/implementation.md`
/ `docs/issue-189/reports/implementation/` was touched this session or on
this branch — only `docs/issue-189/reports/execution-observation.md` (this
file) and, in phase 1, `docs/issue-189/reports/execution-observation/` and
`docs/issue-189/proposals/execution-observation-plan.md` were written. No
code under observation (`gates/flows.py`, `gates/closure_sweep.py`) was
executed this session — every claim below is either a static read of the
`b60843f` diff / current `HEAD` (`24a8562`, confirmed identical on the
observed files via `git log --oneline --follow -- gates/flows.py` in the
phase-1 survey) or a citation of the observed role's own record
(`8d2c96a`, `docs/issue-189/reports/implementation.md`) or the
orchestrator's own execution trace posted to PR #195
(https://github.com/tokenmaxxxer/on-the-record/pull/195#issuecomment-5156219716),
never a re-run of `spawn.py`/`gates/flows.py` performed by this role.

## What was done

Phase 2 read, this session, beyond what phase 1 (`docs/issue-189/reports/execution-observation/survey.md`,
PR #195) had already captured: `docs/issue-189/reports/implementation.md`
(the observed role's own phase-2 record, `8d2c96a`, via the `Read` tool —
`cat` was refused by this repo's `board-gate.sh` as a foreign-record read);
`git show b60843f -- gates/flows.py`, `-- gates/closure_sweep.py`,
`-- test_spawn.py`, `-- test_gates.py`, `-- on-the-record/commands/run.md`,
`-- docs/specs/flows-schema.md` (full diffs, all six files the observed
commit touches); `docs/issue-189/proposals/execution-plan.md` and
`docs/issue-189/proposals/implementation-plan.md` in full; `gh pr view 193
--json commits,mergedAt,body,author`; `gh pr view 195 --json comments` (the
orchestrator's execution-observation evidence comment); `gh issue view 189
--json body,comments` (the three `APPROVE` comments and their timestamps);
`docs/specs/approvers.md`. No code under observation was executed — see
Independence statement above. Basis for what to check: the approved
`docs/issue-189/proposals/execution-observation-plan.md` (PR #195, approved
via `APPROVE issue-189/execution-observation`), which named the three
verdict levels and, under "Independent sweep," the two additional
candidates (`--limit 1000`, `_PLAN_STEP_RE` spacing) plus the
`implementation.md` synthetic-fixture substitution as leads to judge in
phase 2 — all three are judged below (Outcome, Trajectory, Step).

## Outcome — did PR #193 land what the issue asked

**Requirements 1-3, 5 (`run.md` prose, `execution-plan.md` §1-3, §5) — met.**
Every acceptance-criterion clause traces to a matching sentence in the
`on-the-record/commands/run.md` diff, `git show b60843f -- on-the-record/commands/run.md`:
grammar block verbatim (§1.1, matches `execution-plan.md:16-19` against the
new "### 문법" section); agreement-before-write procedure (§1.2, "합의 절차"
section); `gh issue edit --body`-only edits, one plan-only change per call,
no new audit file, orchestrator-only edits (§2.1-2.3, "최소·감사 가능한 편집"
section); step-completion definition and no-auto-progress-without-go-ahead
(§3.1-3.2, "자동 진행 없음" section); prose-only, no new gate (§3.3, confirmed
independently by `git show b60843f --stat` showing only pre-existing files
touched, no `create mode` line in `git show b60843f --summary`); issue #120
per-spawn reasoning preserved (§3.4, same section, final sentence); plan
exhaustion → human-confirmed closure, `closure_sweep` unchanged detect-only
(§5.1-5.5, "계획 소진" section, cross-checked against the actual
`gates/closure_sweep.py` diff which adds only an optional prefetch parameter
and no new violation kind or close capability). One placement nuance: §2.4's
"checkbox flips only after step completion" clause is not restated under the
"최소·감사 가능한 편집" heading itself but the equivalent constraint appears
under "자동 진행 없음" ("그 스텝의 체크박스는 줄 위 모든 역할이 머지될 때까지
미완료로 남는다", same `run.md` diff) — substantively present, not a
criterion violation.

**Requirement 4 (`flows[].plan` visibility, `execution-plan.md` §4.4) —
items 2-5 met, item 1 met on its literal text but empirically produces wrong
data for the issue it was built to serve.** Item 2 (`plan` is `null`/list
per §4.3): `gates/flows.py:286` (`"plan": plan_by_issue.get(issue_n)`,
`b60843f`). Item 3 (no new `gh` call class): `gates/closure_sweep.py:71`
(`find_violations(..., issue_states=None)`, `b60843f`) plus
`docs/specs/flows-schema.md` §4 diff (`b60843f`) documenting `gh issue view`
as now a fallback-only path. Item 4 (schema additive, version unchanged):
`docs/specs/flows-schema.md` diff (`b60843f`) — `schema_version` line not
touched by the diff hunk. Item 5 (no new file/record/gate):
`git show b60843f --stat --summary` — six pre-existing files only, no
`create mode` entries. Item 1 (entry appears for an open plan-only issue
with no board record) is met at the "entry exists" level —
`gates/flows.py:224` (`all_subjects = dict(b)`, union-expansion) and
`test_spawn.py:1892`
(`test_flows_plan_only_issue_with_no_board_record_still_gets_entry`,
`b60843f`) both confirm the mechanic. But run against the real issue #189
body by the orchestrator on 2026-08-02 (main `41b2051`, PR #193 already
merged), `python3 spawn.py flows --json -C .` produced a `plan` array for
issue 189 sourced from the fenced illustration block in the issue's "방향"
section, not the issue's actual `## 실행 계획 (이 이슈 자체 …)` block —
verbatim JSON quoted in
https://github.com/tokenmaxxxer/on-the-record/pull/195#issuecomment-5156219716
("실측 1"). This is the same PR-comment evidence the invoking prompt
authorized citing in place of a re-run; this role did not execute
`spawn.py` to produce or reproduce it. Root cause, read statically in
`gates/flows.py:81` (`if line.strip() == "## 실행 계획":`, `b60843f`): an
exact-equality header match with no code-fence awareness, so a
` ```markdown ` -fenced example block whose first line happens to be
`## 실행 계획` matches before the issue's real header
(`## 실행 계획 (이 이슈 자체 — 요구 1의 첫 적용 사례)`, which never
exact-matches because of its trailing parenthetical). The `implementation`
plan's frozen grammar (`execution-plan.md:22-23`, "`## 실행 계획` is the
exact, literal block header; parsing stops at the next `##` heading") is
itself silent on fenced illustration blocks, so the parser is
spec-conformant on the literal grammar and still produces wrong output on a
real document — the acceptance criterion's *text* ("includes an entry …")
is satisfied; its evident *purpose* (accurate plan visibility from
creation onward) is not, for this real case.

**Independent candidate — `--limit 1000` cap on `_issue_list_all`
(`gates/flows.py:58`, `b60843f`) — not a deficiency.** The same commit's
`docs/specs/flows-schema.md` §4 diff documents the cap explicitly and
states `gh issue view` remains a fallback "for a subject whose issue number
falls outside the prefetched set (e.g. the `--limit 1000` cap)" — a
disclosed, graceful-degradation path, not a silent gap. The repo's highest
issue number touched this session is 195, far under the cap.

**Independent candidate — `_PLAN_STEP_RE`'s single-space requirement
between `-` and `[` (`gates/flows.py:69`,
`r"^-\s\[([ xX])\]\s+step\s+(\d+)\s+(.+)$"`, `b60843f`) — not a
deficiency.** The frozen grammar it implements,
`execution-plan.md:17-19` ("`- [ ] step <N>  <role>…`"), itself specifies
exactly one space in that position; the regex matches its own governing
spec exactly. No acceptance criterion requires tolerance for other
spacings, and no empirical failure was observed for this path (unlike the
fence/header gap above, which PR #195's comment demonstrated failing on
real data).

## Trajectory — was the phase-1→phase-2 path sound

**Survey-before-propose: sound.** `docs/issue-189/reports/implementation/survey.md`
(read in full this session, referenced in the phase-1 proposal's Rationale)
precedes `docs/issue-189/proposals/implementation-plan.md` (also read in
full this session), and the proposal's own Rationale section cites specific
findings from that survey (e.g. the `_pr_list_all`/`--state open` drift
noted as "identified during survey, not this issue's concern").

**Real human approval before each phase: confirmed.** `APPROVE
issue-189/product-discovery` — issue comment, author `jjongkwann`
(approvers.md), 2026-08-02T06:02:57Z,
https://github.com/tokenmaxxxer/on-the-record/issues/189#issuecomment-5155812880
— gates PR #190 (product-discovery/`execution-plan.md`, out of this role's
observation scope but the upstream approval this issue's plan depends on).
`APPROVE issue-189/implementation` — issue comment, same author/account,
2026-08-02T06:29:54Z,
https://github.com/tokenmaxxxer/on-the-record/issues/189#issuecomment-5155932985
— gates phase 2 of the observed role. PR #193's first commit
(`b60843f`, authored 2026-08-02T06:52:59Z per `gh pr view 193 --json commits`)
postdates that approval by ~23 minutes; PR #193 merged 2026-08-02T07:02:13Z
(same `gh pr view 193` output) — ordering is sound, no phase-2 code
predates its phase-2 approval.

**Write-set discipline: confirmed.** `implementation-plan.md`'s frontmatter
`files:` list (`on-the-record/commands/run.md`, `gates/flows.py`,
`gates/closure_sweep.py`, `docs/specs/flows-schema.md`, `test_spawn.py`,
`test_gates.py`) matches `git show b60843f --stat`'s six changed files
exactly, no extras and none missing.

**Verification-method gap: a trajectory-level deficiency.**
`implementation-plan.md:213-216`'s "How you'll know it worked" specifies a
manual check: `python3 spawn.py flows --json -C <repo-with-a-plan-only-issue>`
against a real repo. `docs/issue-189/reports/implementation.md` (record
`8d2c96a`, lines 91-96 per this session's `Read`) states this manual run
was skipped ("이 워크스페이스에 GitHub 레포 쓰기·`gh` 인증 스코프가 없어
실행하지 않았다") and substitutes
`test_spawn.py::FlowsPayload.test_flows_plan_only_issue_with_no_board_record_still_gets_entry`
as equivalent evidence, asserting it "정확히 이 시나리오 … 를 실측 픽스처로
고정하고 있고 … 이것이 'Manual check' 항목이 실제로 요구하는 동작 증거를
커버한다" (same file, lines 92-96). Disclosing the substitution openly was
sound practice — the record does not hide the deviation. But the
equivalence claim does not hold: the substituted fixture's body
(`test_spawn.py:1894`, `body = "## 실행 계획\n- [ ] step 1  product-discovery\n"`)
contains no code fence and an exact-match header, so it could not have
exercised the fence/header-tolerance gap that the orchestrator's real run
against issue #189 itself (a repo that, unlike the fixture, has both a
board record and a document with a fenced illustration) then exposed
(cited above,
https://github.com/tokenmaxxxer/on-the-record/pull/195#issuecomment-5156219716).
The environment constraint (no `gh` write scope) was real and disclosed;
the overclaim was treating a narrower synthetic case as covering the
manual check's actual intent.

## Step — which specific artifact is deficient

**Finding 1 (confirmed).** `gates/flows.py:81`'s `_plan_from_body` header
match (`if line.strip() == "## 실행 계획":`, commit `b60843f`) has no
code-fence boundary awareness, so a fenced illustration block whose first
line is `## 실행 계획` is matched before a real plan block with a
non-exact-match header (trailing parenthetical text) appearing later in
the same document.
- *Impact*: for issue #189 itself, `flows[].plan` reports the fenced
  example's 4-step content instead of the issue's real 3-step plan —
  wrong data on the one subject exercising this feature in production, per
  the orchestrator's live capture
  (https://github.com/tokenmaxxxer/on-the-record/pull/195#issuecomment-5156219716).
- *Timeline*: introduced `b60843f` (2026-08-02T06:52:59Z); PR #193 merged
  2026-08-02T07:02:13Z without catching it (`gh pr view 193 --json
  mergedAt`); observed failing on real data 2026-08-02 ~15:5x KST, same day
  (orchestrator's PR #195 comment, timestamped 2026-08-02T07:30:23Z UTC).
- *Root cause*: `execution-plan.md:22-23`'s frozen grammar is silent on
  fenced illustration blocks; the implementation's test suite
  (`test_spawn.py:1863-1902`, `b60843f`, all three new `FlowsPayload` tests)
  only exercises clean, fence-free, exact-header bodies, so the gap was
  never exercised pre-merge; the one verification step that could have
  caught it (`implementation-plan.md:213-216`'s manual check) was not run
  (Trajectory section above).
- *Action item*: not performed by this role (observation only, per this
  role's standing prohibition on editing the observed artifact) — noted
  for the human to route to a fix issue if they judge it warranted.

**Finding 2 (confirmed, trajectory-linked to Finding 1).**
`docs/issue-189/reports/implementation.md`'s §검증 (record `8d2c96a`) claims
its synthetic-fixture substitution "정확히" covers the approved plan's
manual-check requirement; it does not, per Trajectory above. This is the
process gap that let Finding 1 ship without any test or manual run
exercising it.
- *Impact*: false confidence in the phase-2 record's own closed-checks
  claim — the record reads as if the manual check's intent was satisfied
  when the specific scenario that later failed was never tried.
- *Timeline*: written `8d2c96a` (2026-08-02T06:54:25Z), ~2 minutes after
  the code commit, same session.
- *Root cause*: the workspace's stated lack of `gh` write/auth scope
  (`implementation.md` line 91-92) forced a substitution; the substitution
  was chosen for scenario-shape convenience (plan-only issue, no board
  record) rather than for coverage of the header/fence-matching logic that
  the same commit's diff also changed.
- *Action item*: not performed by this role — noted for the human.

## Open findings

Both carried forward from the Step section above, for the human to route
to a fix issue if judged warranted (this role files no issues itself):

1. `gates/flows.py:81` — `_plan_from_body`'s exact-match header scan has no
   code-fence awareness, producing wrong `flows[].plan` content for issue
   #189 itself. Evidence:
   https://github.com/tokenmaxxxer/on-the-record/pull/195#issuecomment-5156219716,
   `gates/flows.py:81` (`b60843f`).
2. `docs/issue-189/reports/implementation.md` §검증 — the manual-check
   substitution (synthetic fixture in place of a live `flows --json` run)
   overclaims equivalence; the fixture used
   (`test_spawn.py:1894`, `b60843f`) does not exercise the fence/header gap
   Finding 1 describes.

## Summary

Outcome: run.md prose requirements (1-3, 5) and `flows[].plan` acceptance
criteria 2-5 are met, cited above. Criterion 4.4 item 1 is met on its
literal text and fails its evident purpose for the real subject it was
built for (Finding 1). Trajectory: survey-before-propose and both
phase-gate approvals are sound and cited; the verification-method
overclaim (Finding 2) is the one process deficiency. Step: two confirmed
findings, both step-level, one in code (`gates/flows.py:81`) and one in
the observed role's own verification record; two independently-flagged
candidates (`--limit 1000`, `_PLAN_STEP_RE` spacing) were checked and found
not to be deficiencies, cited above.
