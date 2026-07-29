files: orchestrate/commands/run.md

# Proposal — issue-68: cross-issue mission board

Phase 1 (proposal only). This document describes the intended edit to
`orchestrate/commands/run.md` as text; the file itself is not modified by this PR. Phase 2
(applying this edit) is gated on human `APPROVE issue-68/coding` per role-handoff contract v3.

## Request

Issue #68 asks the orchestrate procedure to define a mission-board rendering: a status-grouped,
read-only, at-a-glance view across all open flows (issues), so the user does not have to ask
"what did I request and where does each stand" per-flow. It builds directly on:

- issue #43's feasibility verdict (CONDITIONAL-GO, four conditions: pure read view, no
  bulk-approve, explicit parking-lot promotion criteria, re-verify unverified survey angles),
- issue #54's flow/stage/next schema and its exact rendering forms, and
- issue #64's re-verification, which reaffirms the status-grouped list-view shape (citing Devin,
  Cursor, and GitHub's Copilot coding agent as independent industry convergence on
  running/waiting-for-review/done) and reaffirms no competitor has cross-session bulk-approve.

No secrets or credentials are referenced anywhere in the source issue or this proposal.

## Constraints

The following five requirements are binding on the edit (paraphrased from the task brief, matching
issue #68's acceptance criteria and the #43/#64 conditions):

1. **Status-grouped list view.** Flows/issues are grouped into exactly three status groups:
   running, waiting-for-human-decision, done.
2. **Exact item form.** Every item in every group is rendered in issue-54's exact compact form:
   `[이슈 #<n>] <summary> · <stage> → <next>`.
3. **Read-only, no new artifact.** The board is computed at render time from `loop_state` (in
   `docs/issue-<n>/reports/<role>.md`) and GitHub issue/PR state. No new stored file, board, or
   queue is introduced or persisted.
4. **No bulk-approve.** The board only aggregates and displays; the waiting-for-decision group
   never triggers or represents a batched approval action. Every approval remains an individual
   act per existing step 6.
5. **Parking-lot section with explicit promotion criterion.** A parking-lot section exists,
   separate from the three status groups, with a stated, explicit rule for how an item leaves
   parking-lot and re-enters the board (i.e., becomes a tracked issue).

## What will be done

Add one new subsection to `orchestrate/commands/run.md`, inserted as a new numbered step **5-bis**
between the existing step 5 ("PR을 설명한다") and step 6 ("사용자의 결정을 중계한다"), titled
`## 미션 보드 (Mission Board)`. It is additive text only — no existing step is renumbered or
removed; step 5 and step 6 keep their current content unchanged. Below is the exact proposed
section text (Korean, matching the file's existing language and voice), shown as a fenced block —
this is proposed text only, not an applied diff:

```diff
--- a/orchestrate/commands/run.md
+++ b/orchestrate/commands/run.md
@@ 기존 5번 스텝 뒤, 6번 스텝 앞에 삽입 @@
+## 미션 보드 (Mission Board)
+
+미션 보드는 여러 이슈(flow)에 걸친 현재 상태를 한눈에 보여주는 읽기 전용 집계 뷰다.
+저장되는 파일이 아니다 — 매번 아래 절차대로 그 자리에서 계산해서 렌더링한다.
+
+### 언제 (렌더 트리거)
+
+다음 두 경우에만 렌더한다. 그 외 매 턴마다 자동으로 그리지 않는다:
+
+1. **사용자 요청 시** — 사용자가 명시적으로 보드/현황/진행상황을 묻는 턴.
+2. **주요 전환점 시** — 새 이슈를 등록한 직후, 역할 세션이 완료 통지를 보낸 직후(5번
+   스텝의 PR 요약과 별도로, 그 항목이 속한 전체 현황을 함께 보여줄 때), 또는 사용자의
+   결정을 중계한 직후(6번 스텝 실행 후 최신 상태를 반영해 다시 보여줄 때).
+
+### 무엇으로 (입력)
+
+`main`에 머지된 `docs/issue-<n>/reports/<role>.md`의 `loop_state` 필드와, 해당 이슈/PR의
+GitHub 상태(`gh issue view`, `gh pr view`, `gh pr status` 등)만 읽는다. 새 필드를 이 파일들에
+추가하지 않는다 — 이미 있는 `loop_state`와 GitHub 상태만으로 아래 분류를 계산한다.
+
+### 어떻게 (분류 로직)
+
+각 flow(이슈)를 다음 네 그룹 중 정확히 하나로 분류한다. 우선순위는 아래 순서대로 —
+먼저 맞는 조건에서 멈춘다:
+
+1. **parking-lot** — 아직 `gh issue create`로 등록되지 않은 항목(1번 스텝에서 초안만
+   나오고 사용자 확인을 못 받은 요구, 또는 명시적으로 "나중에"로 보류된 요구). 세 상태
+   그룹과 분리된 별도 섹션에 나열한다 (아래 참고).
+2. **waiting-for-human-decision** — 열린 이슈의 최신 board record `loop_state`가 사용자의
+   결정을 필요로 하는 상태이거나(예: 제안 PR이 열려 있고 아직 `APPROVE`/반려 코멘트가
+   없음, 머지 대기 중인 PR), 6번 스텝의 결정 큐에 올라갈 항목.
+3. **running** — 역할 세션이 아직 살아 있거나(`spawn.py ps`에 해당 이슈가 보임), 최신
+   `loop_state`가 진행 중 값(예: `verdict-recorded`가 아닌 조사/구현 중간 상태)이고 사람의
+   결정을 기다리지 않는 경우.
+4. **done** — 최신 board record의 `loop_state`가 종결 상태(예: `landed`, `closed`)이고
+   해당 이슈가 GitHub 상에서도 닫혀 있거나 더 이상 열린 PR이 없는 경우.
+
+### 렌더 형식
+
+세 상태 그룹 각각을 헤더로 나열하고, 그 아래 항목마다 이슈-54의 압축 한 줄 형식을 그대로
+쓴다 (새 형식을 만들지 않는다):
+
+```
+### Running
+[이슈 #<n>] <flow 요약, ≤8단어> · <stage> → <next>
+
+### Waiting for human decision
+[이슈 #<n>] <flow 요약, ≤8단어> · <stage> → <next>
+
+### Done
+[이슈 #<n>] <flow 요약, ≤8단어> · <stage> → <next>
+```
+
+그룹에 항목이 없으면 그 헤더 자체를 만들지 않는다 (6번 스텝의 "빈 큐를 만들지 않는다"
+규칙과 동일한 원칙 — 빈 "0건" 섹션을 렌더하지 않는다).
+
+### Parking-lot 섹션
+
+세 상태 그룹과 분리된 별도 섹션으로 마지막에 둔다:
+
+```
+### Parking-lot
+- <한 줄 요약> — 아직 이슈 아님
+```
+
+**승격 기준 (parking-lot → 보드 진입, 명시):** parking-lot 항목은 사용자가 그 항목에 대해
+**명시적으로 이슈 스레드를 열자고 말한 시점**에만 보드에 진입한다 — 즉 1번 스텝의 절차대로
+`gh issue create`가 실행된 순간이다. 시간 경과, 다른 항목의 처리, 또는 오케스트레이터의
+판단만으로는 승격되지 않는다 (침묵은 승격이 아니다 — 6번 스텝의 "침묵은 동의가 아니다"
+원칙과 동일). 이슈가 생성되면 그 항목은 parking-lot 섹션에서 제거되고, 다음 렌더부터
+running/waiting/done 세 그룹 중 하나로 정상 분류된다.
+
+### 하지 않는 것
+
+- 보드는 절대 행동을 취하지 않는다 — 집계·표시만 한다. waiting-for-human-decision 그룹을
+  일괄 승인하는 조작은 없다 (6번 스텝의 결정 큐를 대체하지 않는다 — 실제 승인/머지/반려는
+  여전히 6번 스텝에서 항목별로 처리한다).
+- 보드 자체를 파일로 저장하지 않는다 — 매번 위 입력으로부터 다시 계산한다.
```

This is proposed text only; it will be applied verbatim (or refined per review feedback) in the
phase-2 coding PR after `APPROVE issue-68/coding`.

## Out of scope

- Bulk-approve or any batched action on the waiting-for-human-decision group (issue #43 condition
  2, issue #64 reaffirmed finding — no surveyed tool has this).
- A persisted board file, cache, or database of any kind — the board is recomputed at every
  render (issue #43 condition 1).
- A historical or archived view of past board states — only the current status is shown; no
  time-travel or diffing across renders.
- Automatic promotion of parking-lot items by timeout, heuristic, or orchestrator judgment — only
  the user's explicit "open this as an issue" act promotes an item.
- Any change to the flow/stage/next schema itself, or to step 6's decision-relay mechanics — the
  board reuses them unchanged.
- Any UI/rendering surface beyond the conversational text form already used elsewhere in run.md
  (no new file format, no external dashboard).

## How we'll know it worked

Phase 2's edit to `orchestrate/commands/run.md` is conformant if and only if:

1. A `## 미션 보드 (Mission Board)` (or equivalently named) section exists in the file, inserted
   between the existing step 5 and step 6, without altering their existing content.
2. The section states explicit, unambiguous render triggers (on-request and at named transition
   points) — not "rendered every turn" and not left implicit.
3. The section defines exactly three status groups (running / waiting-for-human-decision / done)
   plus a fourth, clearly separate parking-lot section — four groups total, three-plus-one, not
   merged.
4. Every example/format line in the section uses the exact issue-54 compact form
   `[이슈 #<n>] <summary> · <stage> → <next>` with no invented alternate format.
5. The section states explicitly that all inputs are derived from `loop_state` in
   `docs/issue-<n>/reports/<role>.md` and GitHub issue/PR state, and explicitly disclaims any new
   stored file/artifact.
6. The section states explicitly that the board never performs or represents a bulk-approve
   action, and that decisions still route through the existing step 6 mechanics.
7. The section states an explicit, checkable parking-lot promotion criterion (not "eventually" or
   left to orchestrator judgment) — the criterion phase 1 proposes is: promotion happens exactly
   when `gh issue create` is run for that item, per step 1.
8. No new file is created and no other file in the repo is modified by the phase-2 edit — the
   write set stays exactly `orchestrate/commands/run.md`.
