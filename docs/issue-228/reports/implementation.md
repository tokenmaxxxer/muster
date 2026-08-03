---
code_under_review: 923416d
loop_state: landed
closed_checks:
  - check: "python3 -m pytest -q test_flows.py test_gates.py test_spawn.py —
      241 passed, 1 failed (t_repo_local_claude_config_stops_the_spawn,
      기존 샌드박스 전용). 0 회귀."
    code_sha: 923416d
  - check: "python3 test_gates.py 자가 러너 — 신규 9건(pr_reference 계획-인지
      8건 + ci.py --phase 가드 1건) 전부 ok, 기존 61건 무회귀(1건은
      동일하게 샌드박스 전용으로 실패)."
    code_sha: 923416d
  - check: "회귀 확인: 변경 전 코드(HEAD의 gates/pr_reference.py,
      gates/ci.py 사본)로 신규 9건을 재실행 — check_body 는 plan
      kwarg 자체를 TypeError로 거부, check_body(228, 'Closes #228',
      'phase2')(plan 없이, 이슈-228 실물 계획 형태)는 []를 반환해
      조기 종결을 실제로 허용함을 확인, ci.check() 는 --phase 없이도
      차단 사유를 내지 않음을 확인 — 요청대로 변경 전 코드에서 실제로
      실패하는 케이스임을 실측."
    code_sha: 923416d
  - check: "python3 gates/ci.py . (이 레포 자신) — exit 1, 사유 정확히
      2건('보호 경로 변경: gates/ci.py', '보호 경로 변경:
      gates/pr_reference.py')뿐, 다른 차단 사유 없음(의도한 대로 게이트
      파일 자체를 고쳤으므로 예상된 결과)."
    code_sha: 923416d
  - check: "warrant-hunter 디스패치(대체, general-purpose, stance:
      silent-failure, issue #222의 composition-regression에서 회전) —
      docs/reports/2026-08-03-hunt-issue-228-plan-aware-closes-gate.md,
      1건 발견(아래 Hunt/Open findings), blocking 아님으로 판정."
    code_sha: 923416d
---

# Implementation — plan-aware phase-2 Closes gate (issue #228, phase 2)

Proposal: [[implementation.md]](../proposals/implementation.md), 승인:
이슈 코멘트 `APPROVE issue-228/implementation`(single-account mode,
role-handoff contract v3 s19, PR 작성자·승인자 동일 계정 jjongkwann).

승인된 제안의 "What will be done" 그대로 구현했다.

## What was done

1. `gates/pr_reference.py`: `check_body(issue, body, phase, plan=None)` —
   `phase == "phase2"`이고 `plan`이 주어졌을 때, 미완 스텝이 2개 이상이거나
   유일한 미완 스텝이 마지막이 아니면 `Closes/Fixes/Resolves`를 차단,
   그 외(계획 없음/빈 계획/마지막 스텝만 미완)는 기존 로직(Closes 요구)
   그대로. 신규 `_issue_view_body`(`gh issue view --json body`, `_pr_view`와
   같은 실패 패턴). `check()`는 `phase == "phase2"`일 때만 이슈 본문을
   읽어 `flows._plan_from_body`(신규 `import flows`)로 계획을 파싱해
   전달 — 이슈 본문을 못 읽으면 fail-closed 차단.
2. `gates/ci.py`: `check(..., phase: str | None = None)` — `pr`/`issue`가
   둘 다 주어졌는데 `phase`가 없으면 "--phase가 필요하다" 차단 사유를
   반환(이전엔 조용히 `"phase1"`로 떨어져 방금 만든 phase-2 차단 로직이
   결코 발동하지 않았다). `main()`의 `opts.get("phase", "phase1")` →
   `opts.get("phase")`.
3. `test_gates.py`: 계획-인지 케이스 8건(plan=None 회귀 불변, 미완 2개
   +Closes 차단/무Closes 통과, 마지막만 미완+Closes 통과/무Closes 차단,
   펜스 안 Closes 인용도 여전히 차단, 이슈-197 실물 역순 체크박스 형태
   차단, core 이슈-88 실물 단일-스텝-완료 형태는 기존 로직으로 낙하) +
   `ci.check()` `--phase` 누락 가드 1건.
4. `docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md`:
   `check_body`의 공개 시그니처 변경과 채택 1-3 Rationale 기록.

## 픽스처 출처(실물 데이터)

`gh issue view`로 직접 확인한 실물 계획 형태를 그대로 텍스트 픽스처로
썼다(`flows._plan_from_body`를 그 텍스트에 실제로 돌려 `plan`을 얻음,
dict를 손으로 짜지 않음):

- **이슈-228 자기 자신**(두 스텝 다 미완, `(1,F)(2,F)`) — 이 이슈가
  고치는 조기 종결 결함의 정확한 재현 형태. 변경 전 코드로
  `check_body(228, "Closes #228", "phase2")`를 실제로 돌려 `[]`(통과)를
  반환함을 확인(위 closed_checks).
- **이슈-218/이슈-222**(둘 다 실물로 `(1,T)(2,F)`, "마지막만 미완") —
  현재 정확히 이 형태에서 Closes 가 요구돼야 하는 케이스.
- **core 저장소(tokenmaxxxer-core) 이슈-90**(같은 `(1,T)(2,F)` 형태) —
  다른 저장소지만 같은 계획 문법을 쓰는 별도 실물 확인.
- **이슈-197**(닫힌 이슈, `(1,F)(2,T)` — step 1 이 여전히 `[ ]`, 더
  나중 step 2 가 `[x]`인 역순 저작 상태) — fail-closed 방향 adversarial
  가드.
- **core 저장소 이슈-88**(단일 스텝, 이미 완료 — `(1,T)`) — plan 이
  주어져도 incomplete 이 비면 기존 로직(Closes 요구)으로 낙하하는지
  확인.

주: 원 이슈 본문의 "실측" 문단이 인용한 "issue-88 / PR #89"는 사전
조사에서 on-the-record 저장소의 issue-88 이 아니라(그 번호는 이 저장소
에서 이슈-87의 병합된 phase-1 PR이며 plan 을 안 가짐) core 저장소의
issue-88(PR #89)을 가리킨다는 걸 확인했다 — 위 "픽스처 출처"의 core
이슈-88 이 그 실물이다. 자세한 경위는 아래 "What did not work" 참고.

## Hunt

phase-2 완료 전 warrant-hunter를 디스패치했다(hunt cadence). 이 세션에는
`warrant:warrant-hunter` 서브에이전트 타입이 등록돼 있지 않아
(available agent 목록에 없음), adversarial 프롬프트를 `general-purpose`
에이전트에 직접 넣어 대체 디스패치했다(issue #216/#222와 같은 방식).
stance 회전: issue #222가 "composition-regression"을 썼으므로 이번은
**"silent-failure"**.

**결과: 1건 발견, blocking 아님.** 기록:
[docs/reports/2026-08-03-hunt-issue-228-plan-aware-closes-gate.md](../../reports/2026-08-03-hunt-issue-228-plan-aware-closes-gate.md).
`flows._plan_from_body`가 "계획 헤더 없음"(`None`)과 "계획 헤더는 있으나
유효 스텝 파싱 실패"(`[]`)를 구분해 돌려주는데, `check_body`의
`if plan:` 가드는 둘 다 falsy 로 취급해 후자도 조용히 기존 로직(Closes
요구)으로 접는다 — 저작 형식이 어긋난(예: "Step" 대문자) 계획도 "계획
없음"과 똑같이 다뤄진다. 처리는 아래 Open findings 참고.

## Open findings

- finder: implementation:warrant-hunter(대체, general-purpose,
  stance: silent-failure)
  finding: `pr_reference.check_body`의 `if plan:`이 `_plan_from_body`의
  `None`(계획 없음)과 `[]`(계획 헤더는 있으나 유효 스텝 파싱 실패)를
  구분 못 해, 저작 오류로 스텝이 하나도 안 잡힌 계획도 "계획 없음"과
  같은 경로(Closes 요구)로 조용히 떨어진다.
  report: docs/reports/2026-08-03-hunt-issue-228-plan-aware-closes-gate.md
  processing: 이번 write set 안에서 고치지 않음 — (1) 승인된 제안의
  "What will be done" 1번이 `plan`이 `None`이거나 `[]`이면 기존 로직
  그대로라고 명시적으로 결정했고, `_plan_from_body`의 반환 계약을
  "그대로 소비한다"는 Constraints도 이미 이 접음을 전제한다; (2) 제대로
  구분하려면 `gates/flows.py`의 반환 계약을 확장해야 하는데 이는 요구
  4(재사용만, 재구현 금지)와 이 이슈의 명시적 Out of scope를 넘는다;
  (3) `if plan is not None:`으로 얕게 바꾸면 정말로 스텝이 0개인
  헤더-only 계획에서 `max()`가 빈 시퀀스에 대해 `ValueError`를 던지는
  새 회귀가 생긴다. 후속 이슈 권고: `_plan_from_body`가 "스텝 0개"와
  "파싱 실패 줄 있음"을 구분해 돌려주도록 `gates/flows.py`를 확장.
  code_sha: 923416d(발견 시점, 미수정)

## What did not work

- 원 이슈 본문의 "실측"이 인용한 on-the-record `issue-88`(`PR #89`
  머지 → 자동 종결)을 실물 픽스처로 그대로 쓰려 했으나, `gh issue view
  88`이 실제로는 이슈가 아니라 병합된 PR #88(이슈-87의 phase-1 제안,
  plan 없음)을 가리킴을 확인 — on-the-record 에는 plan 을 가진
  issue-88 이 없다. 대신 core 저장소(tokenmaxxxer-core)의 issue-88이
  같은 배경 문단이 인용한 "issue #88(PR #89)"의 실물임을
  `core_root` 저장소 조회로 확인해 그쪽 데이터로 픽스처를 만들었다.

## Doc placement (ladder)

- [x] changed public signature (`check_body`의 신규 `plan` 파라미터) →
  `docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md`

새 env var/config key/dep/migration 없음 — 해당 사다리 항목 없음.
