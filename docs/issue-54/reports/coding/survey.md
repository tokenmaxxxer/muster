# Coding survey — issue-54: structural-context reporting

Status: phase-1 (research only). No edits made to `orchestrate/commands/run.md` in this session.

upstream: docs/issue-54/reports/product.md (binding requirements, PR #55),
docs/issue-54/reports/ux-design.md (binding presentation spec, PR #56)

## What run.md currently does

`orchestrate/commands/run.md` is the coordinator-session prompt for the `/run` command. It defines
a six-step loop the coordinator follows inside a conversation with the user:

1. **Requirement → issue.** Turn the user's ask into a draft issue, register only after
   confirmation.
2. **Classify before registering** (issue-44 obligation, see below).
3. **Decide who to wake** via `spawn.py wake`.
4. **Spawn role sessions** in the background via `spawn.py <role> ...`.
5. **Explain the PR** the role opened — this is where issue-34's obligation lives (see below) and
   is the step product.md and ux-design.md both target for the new `flow`/`stage`/`next` fields.
6. **Relay the user's decision** back to the role's PR (comment / approve / merge / close).

## Where the issue-34 obligation lives

Issue-34 added a "read before ask" plain-language summary requirement to step 5. Verbatim from the
current file (lines 51-65):

```
5. **PR 을 설명한다.** 역할이 올린 PR 을 읽고 사용자에게 요약한다: 무엇을
   제안/보고했고, 지금 1단계(제안)인지 2단계(실행 완료)인지.
   - **1단계 승인 요청 시:** 제안 파일(`docs/issue-<n>/proposals/`)을 실제로
     읽고, 다음을 반드시 채워 자연어로 요약한 뒤에만 승인을 물어라 —
     (1) 무엇을 바꾸려 하는가, (2) 왜 (요구/제약과의 연결), (3) 어떻게
     (접근 방식). 파일을 안 읽고 "제안 PR 이 올라왔습니다, 승인할까요?"
     처럼 묻는 것은 절차 위반이다.
   - **2단계 머지(수용) 요청 시:** 실제 diff/커밋(`gh pr diff <n>` 등)을
     읽고, 다음을 반드시 채워 요약한 뒤에만 머지를 물어라 — (1) 무엇이
     바뀌었는가(파일·핵심 변경), (2) 어떻게 검증됐는가(실행한 테스트·확인
     내용, 역할의 기록에서 확인). 파일을 안 읽고 "PR 이 열렸습니다,
     승인할까요?" 처럼 묻는 것은 절차 위반이다.
   - 모든 승인/머지 요청은 최소한 다음 네 항목을 담아야 한다: 무엇을
     바꾸는가, 왜 바꾸는가, (머지 시) 실제로 무엇이 바뀌었는가, 어떻게
     검증됐는가. 이 요약 없이 여닫힌 질문만 던지는 것은 절차 위반이다.
```

This is the what/why/what-changed/how-verified obligation product.md's acceptance criterion 4
and 5 refer to. It must remain intact; the new `flow`/`stage`/`next` fields are additive and sit
alongside it, not interleaved into it (per product.md AC4 and ux-design.md trace item 4).

Confirmed via `git log`:
```
88f8feb Merge pull request #36 from tokenmaxxxer/issue-34/coding
a3a8665 docs(issue-34): phase-2 execution record for coding
2253f9d feat(issue-34): mandate read-before-ask summaries in orchestrate approval loop
031607b docs(issue-34): phase-1 proposal for approval-loop plain-language summary requirement
```

## Where the issue-44 obligation lives

Issue-44 added a role-classification step, now step 2 of the loop. Verbatim from the current file
(lines 20-35):

```
2. **이슈를 등록하기 전에 분류한다.** 어떤 역할이 이끄는지 — feasibility(조사
   먼저) / product(요구사항·수용기준 먼저) / ux-design(UX 판단) / coding(바로
   구현 정당) — 한 줄 근거와 함께 대화에서 명시적으로 말한다. 아래 표를
   참고하되, 표에 없는 요청은 표를 확장하지 말고 근거를 대화로 설명한다.
   **분류를 말하지 않고 coding 으로 기본값 처리하는 것은 절차 위반이다.**

   | 요청 유형 | 리드 역할 | 근거 |
   | --- | --- | --- |
   | "X 를 개선/최적화해줘" (원인·해결책 불명, 결함 위치 미확정) | feasibility | 손대기 전 조사 필요 — 이슈-43 이 이 케이스에서 나왔다 |
   | "정책/행동을 바꿔야 한다" (새 규칙, 새 계약 조항) | product | 요구사항·수용기준부터 확정 필요 |
   | 상호작용/화면·문구 등 사용자 경험 판단이 걸린 요청 | ux-design | 구현보다 UX 판단이 먼저 |
   | "이 위치의 결함을 고쳐줘" (위치·원인이 이미 특정됨) | coding | 바로 구현 정당 |

   product·ops 관련 요청인데 wake 가 "못 잰다"로 표시하는 판단 줄(아래 3번)이
   걸려 있다면, 이 분류도 그 판단에 근거해 명시적으로 제안한다 — 침묵 통과는
   허용되지 않는다.
```

This is the "role classification line" product.md's acceptance criterion 5 refers to (`stage`
must never restate or duplicate this classification — `stage` is a lifecycle-position axis,
distinct from "which role leads"). It is filed in a different loop step (step 2, at issue-creation
time) than issue-34's obligation (step 5, at report time), so there is no structural overlap risk
between them; the new fields land only in step 5 (and step 6 for `next`'s branch mechanics), per
product.md's scope note and ux-design.md's trace item 9.

Confirmed via `git log`:
```
0dce2e7 Merge pull request #50 from tokenmaxxxer/issue-44/coding
db777d6 feat(issue-44): add role-selection classification step to orchestrate loop
fe211cf docs(issue-44): phase-1 survey and proposal for role-selection guide
```

## Issue-43's read-only-view condition

Referenced by the issue-54 GitHub issue and by product.md §5. Step 6 (lines 66-77) already reads
decisions from the live conversation and relays them via `gh pr comment` / `gh pr review` / `gh pr
merge` / `gh pr close` — no persisted queue or store exists in run.md today. The proposed edit must
preserve this: `flow`, `stage`, and `next` (and ux-design.md's decision-queue numbering) are all
computed at report/render time from state already read in steps 4-6 (issue title/body, the role's
PR, `docs/issue-<n>/reports/<role>.md` and its `loop_state`) — no new file, board, or queue is
introduced.

## Write-set for phase 2

Confirmed: **`orchestrate/commands/run.md` only.**

- Product.md's scope section explicitly names this file as the sole coding-stage target, integrated
  into step 5 (and step 6 for `next`'s branch outcomes) — no new numbered loop step.
- Ux-design.md is a presentation spec with "no code, no changes to `orchestrate/commands/run.md`
  itself" as its own deliverable boundary; it explicitly hands the verbatim-application job to the
  coding stage against this same single file.
- No other file in the repo defines the loop steps, the reporting format, or role-classification
  text — `roles/*.json` (mentioned in run.md step "띄우기 전에 확인할 것" 1) hold per-role
  catalogs (decides/use_when/produces) but not the reporting-format prose targeted by issue-54.
  Nothing in the issue, product.md, or ux-design.md asks for changes there.
- No test suite or CI config governs `run.md` (it is a plugin command prompt, not executable code)
  — "how you'll know it worked" is therefore text-inspection against the 9 acceptance criteria,
  not an automated check. This is noted in the proposal.

## References

- Issue: `gh issue view 54`
- Product record: `docs/issue-54/reports/product.md` (PR #55)
- UX design record: `docs/issue-54/reports/ux-design.md` (PR #56)
- Target file (read, not edited, this session): `orchestrate/commands/run.md`
