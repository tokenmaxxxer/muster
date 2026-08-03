# Hunt — issue #228 plan-aware phase-2 Closes gate (phase 2, after code)

이 세션에도 `warrant:warrant-hunter` 서브에이전트 타입이 등록돼 있지 않아
(available agent 목록에 `claude`/`Explore`/`freelunch:freelunch-worker`/
`general-purpose`/`Plan`/`statusline-setup`뿐), `general-purpose` 에이전트에
adversarial 프롬프트를 직접 넣어 대체 디스패치했다(issue #216/#222와 같은
대체 방식). stance 회전: issue #222가 "composition-regression"을 썼으므로
이번은 **"silent-failure"** — 이 변경이 차단해야 할 상황에서 조용히
통과(에러도 차단 사유도 없이)하는 경로를 찾는다.

코드 리뷰 대상: `923416d`(gates/pr_reference.py, gates/ci.py,
test_gates.py, docs/issue-228/decisions/).

## 발견 1건

**`pr_reference.check_body:40`의 `if plan:` 가드가 "계획 없음"과 "계획
헤더는 있으나 유효 스텝 파싱 실패"를 구분 못 해, 후자도 조용히 기존
로직(Closes만 있으면 통과)으로 떨어진다.**

`flows._plan_from_body`는 헤더가 없으면 `None`, 헤더는 있는데 유효한
`- [ ] step <N> <role>` 줄이 하나도 안 잡히면(예: 대문자 "Step", 다른
불릿 마커 등 저작 변형) `[]`를 돌려준다(gates/flows.py:79-89 docstring이
이 구분을 명시). `check_body`의 `if plan:`은 `None`과 `[]`를 똑같이
falsy로 취급해 두 경우 다 새 미완-스텝 차단 분기(41-52행)를 건너뛴다.

재현:
```python
issue_body = ("## 실행 계획\n"
              "- [ ] Step 1  implementation\n"   # 대문자 "Step" — _PLAN_STEP_RE 불일치
              "- [ ] Step 2  execution-observation\n")
plan = flows._plan_from_body(issue_body)          # -> [] (None 아님)
pr_reference.check_body(228, "Closes #228", "phase2", plan)  # -> [] (통과)
```

## Disposition — 이번 write set 안에서 고치지 않음(Open finding)

1. **승인된 제안이 정확히 이 동작을 명시적으로 결정했다.** proposal의
   "What will be done" 1번: "`plan`이 `None`이거나 `[]`이거나
   `incomplete`가 비었거나 ... 면 기존 로직 그대로." `_plan_from_body`의
   반환 계약(`None`=계획 없음, `[]`=헤더는 있으나 유효 스텝 없음)을
   "그대로 소비한다"고 Constraints에도 명시돼 있다 — `[]`를 구별 없이
   접는 것은 사고가 아니라 phase-1이 이미 내린 결정이다.
2. **제대로 고치려면 요구 4(재사용만, 재구현 금지)를 건드려야 한다.**
   "계획 헤더는 있으나 스텝이 저작 오류로 하나도 안 잡힘"과 "계획 헤더는
   있고 정말로 스텝이 0개"는 `_plan_from_body`의 반환값(`[]`) 하나로는
   구분이 안 된다. 구분하려면 `gates/flows.py`(반환 계약 확장, 이번
   이슈의 frozen write set 밖이자 명시적 Out of scope) 또는 원본 이슈
   본문을 이 파일에서 다시 파싱(파서 재구현, 요구 4 위반) 둘 중 하나가
   필요하다.
3. **`plan is not None`으로 바꾸는 얕은 수정은 새 회귀를 만든다.**
   `max(s["step"] for s in plan)`이 빈 시퀀스에서 `ValueError`를 던진다
   — 정말로 스텝이 0개인 헤더-only 계획(이 또한 실물로 가능,
   `_plan_from_body` docstring이 명시)에서 크래시가 새로 생긴다.

후속 이슈 권고: `_plan_from_body`가 "헤더 있음 + 스텝 0개"와 "헤더 있음 +
파싱 실패한 줄이 있음"을 구분해 돌려주도록(예: 세 번째 반환 형태 또는
파싱 실패 라인 수를 별도 필드로) `gates/flows.py`를 확장하는 별도
이슈 — 이번 이슈의 write set과 승인된 제안 범위 밖.

blocking finding 아님 — 회귀도, 이번 요구사항(1-4) 위반도 아니고, 승인된
설계 결정의 알려진 한계다.
