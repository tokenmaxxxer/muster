# Survey — issue #197: execution-observation of PR #200 (`implementation` role, phase 2)

## Scope

Observed: role `implementation`, subject `issue-197`. Sessions landed as PR #199
(`implementation` phase 1 — survey + scout-brief + proposal, merge commit `dc7f4c3`,
merged 2026-08-02T08:27:21Z) and PR #200 (`implementation` phase 2 — code + record,
merge commit `93038c0`, merged 2026-08-02T08:43:49Z). Code commit under observation:
`e7bfdcb1ddbcf1d67543c228f5c089621cdae507`. The observed role's own phase-2 record
commit: `9dc099a22a5d00be11260342d6899b2ac8b8e10e`. Both commits sit inside PR #200's
branch history (`git log --oneline -3 9dc099a` → `9dc099a`, `e7bfdcb`, then `1c230db`
already merged separately via PR #199); `93038c0` is confirmed as PR #200's actual
merge commit (`git show 93038c0 --stat`: `Merge pull request #200 from
tokenmaxxxer/issue-197/implementation`, four files touched —
`docs/issue-197/reports/implementation.md`, `gates/flows.py`,
`on-the-record/commands/run.md`, `test_spawn.py`, 229 insertions / 2 deletions).

This survey scopes the full PR #200 diff as the phase-2 subject (issue #197's four
numbered requirements together), rather than narrowing to one requirement the way
issue-189's execution-observation survey did — issue #197 is itself a single named
defect and its fix (inherited as open finding 1 from the issue-189
execution-observation verdict), not a multi-part feature, so there is no comparable
need to defer sub-facets to a later pass.

## Scope skip record (scout-directive)

Scouting is skipped. Skip condition: the spec — this role's own directive (the
three-level outcome/trajectory/step verdict format, the citation-adjacency rule, the
blameless four-part finding shape, and the record file path) — leaves no design
decision open for this proposal to make; the acceptance criteria to check against are
already enumerated in the approved `docs/issue-197/proposals/plan-parser-fix.md`. This
is a mechanical evidence-gathering task against a fixed spec, not a product/design
choice to scout industry practice for.

## What was read this session

- `gh issue view 197 --comments` and
  `gh issue view 197 --json number,title,body,state,author,createdAt,comments` — the
  full issue body (요구사항 1-4, "이미 결정된 것", "알려진 제약", "방향", "범위 밖",
  and the issue's own `## 실행 계획` 2-step block) and its one comment, `APPROVE
  issue-197/implementation`, author `jjongkwann`, association MEMBER,
  2026-08-02T08:27:18Z,
  https://github.com/tokenmaxxxer/on-the-record/issues/197#issuecomment-5156534388.
  Issue state observed as `CLOSED`, `closedAt: 2026-08-02T11:09:14Z`
  (`gh issue view 197 --json closedAt,closed,state`) — noted as a fact only; whether
  closure ahead of this role's own gate being satisfied matters is a phase-2
  candidate, flagged below, not evaluated here.
- `docs/issue-197/proposals/plan-parser-fix.md` (on `main`) — the approved phase-1
  proposal in full: requirements 1-4, the "방향" candidates, the Rationale's three
  adopted choices and their named rejected alternatives, and the "범위 밖" list.
- `docs/issue-197/reports/implementation.md` (on `main`) — the observed role's own
  phase-2 record in full, frontmatter `code_under_review:
  e7bfdcb1ddbcf1d67543c228f5c089621cdae507`, `loop_state: landed`, three
  `closed_checks` entries.
- `docs/issue-197/reports/implementation/scout-brief.md` and
  `docs/issue-197/reports/implementation/survey.md` (on `main`) — the observed role's
  own phase-1 research trail, in full.
- `gh pr view 200`, `gh pr diff 200`, `gh pr view 200 --comments` — PR #200's summary,
  full diff (`gates/flows.py` +21/-2, `on-the-record/commands/run.md` +10,
  `test_spawn.py` +62, plus the new `docs/issue-197/reports/implementation.md`), and
  its one comment (an orchestrator-posted live-verification note: 실측 1-3, pytest
  counts and a `flows --json` output quoted verbatim).
- `gh pr view 199 --json number,mergedAt,mergeCommit,baseRefName,headRefName,title`
  and `git show dc7f4c3 --stat` — confirms PR #199 is the phase-1 PR (merge
  `dc7f4c3`, merged 2026-08-02T08:27:21Z), touching the three phase-1 docs plus one
  unrelated-looking line: `.warrant-hunt.count` deleted — flagged below as an
  unevaluated candidate.
- `git show 93038c0 --stat` — confirms `93038c0` is PR #200's merge commit, per
  above.
- `git log --oneline 4c15fd6..9dc099a` and `git log --oneline -3 9dc099a` — the two
  commits inside PR #200 (`e7bfdcb` code, `9dc099a` record) and the preceding
  phase-1 commit (`1c230db`, already merged separately via PR #199 before PR #200
  opened).
- `gh pr view 200 --json baseRefName,headRefName,createdAt,commits,mergedAt` —
  commit `e7bfdcb` authored 2026-08-02T08:33:17Z, `9dc099a` authored
  2026-08-02T08:34:10Z, PR #200 created 08:34:59Z, merged 08:43:49Z.
- `git log --oneline --follow -- gates/flows.py` — confirms `e7bfdcb` is the tip
  commit touching this file (prior touches: `b60843f` issue-189, `de58ad8`
  issue-178); current `HEAD` (`415a19e`) matches `origin/main`, and the two commits
  after `93038c0` on `main` (merge PRs #202/#203, issue-201) do not touch
  `gates/flows.py` — no commit after `e7bfdcb` has altered `_plan_from_body` /
  `flows_payload`.
- `docs/specs/approvers.md` — approver accounts `JiwonJung94`, `jjongkwann`.
- `gh pr list --state all --search "head:issue-197/execution-observation"` —
  confirms no PR yet exists for this role's branch.
- `docs/issue-189/reports/execution-observation/survey.md` and
  `docs/issue-189/proposals/execution-observation-plan.md` (read for format/
  structure precedent only — this repo's established phase-1 pattern for this
  exact role).

## Current-state facts about PR #200, mapped to issue #197's four requirements (read statically, not executed)

**Requirement 1** ("코드펜스 안 내용은 계획 블록 후보에서 제외된다"). The
`gates/flows.py` diff (`e7bfdcb`, read via `gh pr diff 200`) adds an `in_fence`
toggle to both the header-search loop and the step-collection loop inside
`_plan_from_body` — a line starting with ` ``` ` flips `in_fence`, and lines are
skipped while it is true. The diff's own added docstring text states this mirrors
`gates/gates.py:387-392`'s `record_no_tool_residue_in` pattern.

**Requirement 2** ("이슈 #189 실물 본문 … 에서 실제 계획이 정확히 파싱된다").
`test_spawn.py`'s diff adds
`test_flows_plan_skips_fenced_example_and_matches_variant_header`, whose `body`
literal (read via `gh pr diff 200`) reproduces the issue #189 body text already read
in this session — including the "## 배경" section's statistics code fence, the
"## 방향" section's fenced 4-step grammar sample, and the real
`## 실행 계획 (이 이슈 자체 — 요구 1의 첫 적용 사례)` 3-step block. The test's
assertion targets the 3-step form with the em-dash description suffixes intact.
Separately, the PR #200 comment (실측 2) quotes a live `spawn.py flows --json` run's
JSON output for issue 189 in the same 3-step, em-dash-suffixed shape.

**Requirement 3** ("문법 정의 … 가 펜스/헤더 규칙을 명시하도록 갱신된다").
`on-the-record/commands/run.md`'s diff adds a
"### 저작 규칙 (파서가 실제로 보는 것, issue #197)" subsection with three bullets:
samples must be fenced, headers tolerate a space-bounded suffix, and exactly one
non-fenced plan header is allowed per body (a second is documented as an authoring
error, first one wins).

**Requirement 4** ("이슈 #189 본문 … 이 회귀 픽스처로 추가된다"). Same test as
requirement 2 — the `test_flows_plan_skips_fenced_example_and_matches_variant_header`
body literal is presented, by the diff's own docstring, as the issue #189 body text.
This session read both the current issue #189 body and the diff's fixture text, but
did not diff them against each other character-for-character — reserved for phase
2's step-level check.

Whether each of the four traces above amounts to the requirement being satisfied is a
judgment deferred to phase 2 — this role's phase-1 facet prohibits verdict language.

## PR #200's own stated verification, and a companion PR comment (neither re-run this session)

`docs/issue-197/reports/implementation.md`'s §검증 states
`python3 -m pytest test_spawn.py test_gates.py -q` produced "133 passed, 17 failed
(baseline pre-existing failures)" in that session's workspace, attributing the 17
failures to no `gh`/network access there, plus a live `spawn.py flows --json` run
reproducing the 3-step shape. The PR #200 comment (read via `gh pr view 200
--comments`) reports different raw counts from what it states is a separate,
network-open workspace: 실측 1 "150 passed, 0 failed" (against a stated main baseline
of 147 passed), and 실측 3, taken after merge (main = `93038c0`), "2 failed, 150
passed," attributing the 2 failures to an unrelated issue #201 regression already
reproduced at pre-PR-200 commit `4c15fd6`. Both figures were read this session but
not independently reconciled or re-run — this role's directive prohibits re-executing
the observed role's code. Whether the two reported figures are consistent (once each
document's own stated network-availability difference is accounted for) is left as a
phase-2 candidate, evidenced only by the citations above.

## Other candidates surfaced while reading the diff (not evaluated)

- `.warrant-hunt.count` — deleted by PR #199 (the phase-1 docs PR), 1 line, a file
  outside the approved proposal's own declared `files:` scope
  (`gates/flows.py`, `on-the-record/commands/run.md`, `test_spawn.py`, per
  `plan-parser-fix.md`'s frontmatter). Not evaluated as a write-set-discipline
  question here — reserved for phase 2's trajectory check.
- Approval-to-phase-1-merge ordering: the issue comment `APPROVE
  issue-197/implementation` is timestamped 2026-08-02T08:27:18Z; PR #199 (phase-1
  docs) merged 2026-08-02T08:27:21Z, three seconds later. Whether PR #199's phase-1
  artifacts were the object of that approval, or the two events are independent and
  merely close in time, is not settled by anything read this session — flagged as a
  trajectory candidate only.
- Issue #197 was closed (`closedAt: 2026-08-02T11:09:14Z`) roughly 2h25m after PR
  #200 merged (08:43:49Z); this role's own phase-2 gate (`APPROVE
  issue-197/execution-observation`) had not been satisfied as of this session
  (confirmed above — the issue's only comment approves `implementation`, not this
  role). Whether the issue's own `## 실행 계획` step-2 checkbox was flipped before or
  independent of that closure was not read this session — a candidate for phase 2's
  trajectory check, not evaluated here.
- The pytest-count figures reported in `implementation.md` versus the PR #200
  comment (see previous section) — same nominal test files, different raw numbers,
  not reconciled this session.

## Not this role's job to resolve

Per this role's standing prohibition, no code under observation (`gates/flows.py`,
`spawn.py`) was executed this session — only `gh`/`git` read commands against `main`,
PR #199, PR #200, and issue #197/#189. No file under `gates/`,
`on-the-record/commands/`, `test_spawn.py`, `test_gates.py`, or the implementation
role's own `docs/issue-197/` artifacts was written or edited this session or on this
branch.
