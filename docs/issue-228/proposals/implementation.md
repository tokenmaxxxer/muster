files:
- gates/pr_reference.py
- gates/ci.py
- test_gates.py
- docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md

## Request

이슈 #228: `gates/pr_reference.py:check_body`가 phase-2 PR에 `Closes/Fixes/Resolves
#<issue>`를 무조건 요구해서, 실행 계획에 미완 스텝이 남은 이슈가 첫 스텝의
phase-2 PR이 머지되는 순간 GitHub 자동 종결로 닫힌다 — issue-189가 이미 확정한
"계획 소진 판단은 체크박스+보드 상태로, `gh issue close`는 사람이 확인한 뒤에만"
계약을 위반한다. 실측(issue-88, issue-218 둘 다 2-스텝 계획의 step 1 PR 머지로
조기 종결)이 근거. 요구 4가지: (1) 미완 스텝이 남았으면 closing 키워드를
요구하지 않고 오히려 차단, 마지막 스텝에서만 요구, (2) 계획 없는 이슈는 현행
유지, (3) 코드펜스/백틱 인용도 GitHub이 파싱하므로 안전하다고 가정하지 말 것,
(4) `gates/flows.py`의 `_plan_from_body`를 재사용(재구현 금지). 인접 결함
(`gates/ci.py`에서 `--phase` 누락 시 phase-2 검사가 무음 스킵)을 같이 볼지는
이 제안이 판단한다.

## Constraints

- phase-1 PR의 현행 규칙(평문 `#N` 참조 요구, `Closes` 금지)은 손대지 않는다
  (issue 본문 명시 제약) — `check_body`의 `phase == "phase1"` 분기는 무변경.
- `_plan_from_body`는 재사용만 한다 — `gates/flows.py`에 코드 변경 없음
  (요구 4). 반환 계약(`None`=계획 없음, `[]`=헤더는 있으나 유효 스텝 없음,
  리스트=스텝 목록)을 그대로 소비한다.
- `_CLOSES_REF`의 펜스-무인식(fence-oblivious) 매칭은 그대로 둔다 — 이 정규식을
  펜스-인식(fence-aware)으로 바꾸면 요구 3을 정확히 거꾸로 위반한다(GitHub은
  펜스 안 텍스트도 파싱해서 실제로 닫으므로, 게이트가 펜스 안을 건너뛰면 실제
  위험을 놓친다). 이번 세션에서 `_CLOSES_REF`가 이미 펜스 안 매치를 잡는다는
  것을 실측 확인함(survey 참조).
- 이슈 종결 자체(`gh issue close`)는 여전히 사람 몫이다 — 이 게이트는 "기계가
  먼저 닫지 못하게" 막는 것까지이며, 새로운 자동 종결·자동 코멘트 경로를
  추가하지 않는다.
- 새 의존성 추가 금지 — 마크다운 파서 라이브러리 등, 이 저장소에 현재 없는
  의존성을 들이지 않는다(기존 `_plan_from_body`/`_CLOSES_REF` 재사용만으로
  충분).

## Rationale

**채택 1 — "마지막 스텝만 남았을 때만 요구" 판정은 role 매칭 없이 계획의
체크 상태만으로 계산한다: `incomplete = [s for s in plan if not s['done']]`;
`incomplete`가 비었거나 `len(incomplete) == 1`이고 그 유일한 미완 스텝이
`max(step)`이면 요구, 그 외(미완 스텝이 2개 이상이거나, 미완 스텝이 마지막이
아니면)는 차단.**

거부한 대안(rejected alternative): PR의 head 브랜치에서 role을 뽑아
(`gates/ci.py:51`의 `_pr_head_ref`+`role_scope` 패턴처럼) 계획의 어느 스텝이
"이 PR이 델리버리하는 바로 그 스텝"인지 role로 정확히 짚어낸 뒤 "그 스텝을
제외한 나머지가 전부 완료됐는가"로 판정하는 방식. 이 대안을 기각한 이유는
이번 세션의 실측(survey)이 보여준다: 이 레포의 실물 이슈 #197은 이미 닫혔고
전체 작업이 끝났음에도 step 1(`implementation`)의 체크박스가 여전히 `[ ]`,
더 나중 step 2(`execution-observation`)가 `[x]`인 역순 상태로 남아 있다 —
즉 체크박스 위생은 완벽하지 않다. role 매칭으로 "정확히 이 스텝"을 짚어내는
정교한 설계를 택해도 이런 저작 누락(체크 안 남김)까지 고쳐주지는 못한다 —
매칭 대상 role이 계획에 없거나 role 자체를 판정에 새로 끌어들이는 대가만
크고(새 파라미터, `ci.py`→`pr_reference.check()` 시그니처 확장), 실측 리스크는
줄지 않는다. 반면 채택한 "미완 스텝 개수 기반" 판정은 이 정확히 같은 상황
(#197이 살아있었다면)에서 **과잉 차단**(step 2도 차단)한다 — 이 파일 전역에
이미 있는 fail-closed 관례(`pr_reference.py:57`의 "검사 불가는 통과가 아니다",
`ci.py:53`의 "fail closed")와 방향이 같고, 이슈 본문 자체가 명시한 대로
"이슈 종결 자체는 여전히 사람 몫"이라 과잉 차단의 비용은 사람이 한 번 더
확인하는 정도로 낮다. 이번 세션에서 이 레포의 실물 다중스텝 이슈 11건 전부를
스캔해(survey 표) 검증: 살아있는 두 건(#222, #218)이 정확히 "마지막 스텝만
미완"일 때 실제로 그 스텝이 진행 중이었다 — 판정이 실물 데이터와 일치한다.

**채택 2 — 인접 결함(`gates/ci.py`의 `--phase` 무음 스킵)을 이번 제안에
포함한다.** 거부한 대안(rejected alternative): 범위 밖으로 남기고 이 게이트
로직만 고친다. 기각 이유: 이번 이슈가 고치는 바로 그 phase-2 차단 로직이
`gates/ci.py`를 거쳐야 실제로 실행되는데, `--phase`를 안 주면 조용히
`"phase1"`로 떨어져 새로 만드는 차단 로직 자체가 결코 발동하지 않는다 —
지금 고치는 버그와 **같은 실패 계열**(문서화된 계약은 있으나 기계가 조용히
안 지킴)이 두 번째 문으로 재발한다. 이번 세션 실측: 이 레포 전체에서
`--phase`가 실제로 호출된 사례는 0건(코드 시그니처와 issue-126 리포트의
언급뿐) — 지금 고치지 않으면 이 이슈가 고치는 로직 자체가 죽은 코드로
남을 위험이 확정적이다. 파일이 이미 프로즌 write set 안(`gates/ci.py`)이라
추가 파일을 끌어들이지 않는다 — 최소 변경.

**채택 3 — 계획이 있고 마지막 스텝이 아닐 때, closing 키워드는 차단하되
평문 `#issue` 참조를 새로 요구하지는 않는다.** 거부한 대안(rejected
alternative): phase-1처럼 평문 참조를 요구하는 폴백을 추가한다(추적성
유지). 기각 이유: 이슈 본문 요구 1은 정확히 "요구하지 않고 오히려 차단"만
명시했고, 새 참조 요구를 얹는 것은 이 이슈가 요청하지 않은 범위 확장이다
— 필요하면 별도 이슈로 다룬다.

## What will be done

1. **`gates/pr_reference.py`**:
   - `check_body(issue, body, phase, plan=None)` — 새 키워드 인자 `plan:
     list[dict] | None = None`(기본값 유지로 기존 4개 테스트·모든 기존
     호출부 무변경 통과). `phase == "phase2"`이고 `plan`이 주어졌을 때만
     새 분기: `incomplete = [s for s in plan if not s["done"]]`;
     `max_step = max(s["step"] for s in plan) if plan else None`.
     - `plan`이 `None`이거나 `[]`이거나 `incomplete`가 비었거나
       (`len(incomplete) == 1` and `incomplete[0]["step"] == max_step`)면
       기존 로직 그대로(Closes 요구).
     - 그 외(미완 스텝 2개 이상, 또는 유일한 미완 스텝이 마지막이 아님)면
       `_CLOSES_REF.search(body)`가 이 issue를 가리키면 차단 사유 반환
       ("계획에 미완 스텝이 남아 있다 — 마지막 스텝의 phase-2 PR에서만
       Closes/Fixes/Resolves를 쓴다"), 없으면 통과(`[]`).
   - `_issue_view_body(repo, issue) -> str | None` 신규 — `gh issue view
     <issue> --json body`로 이슈 본문을 읽는다(`_pr_view`와 같은 실패 시
     `None` 패턴).
   - `check(repo, pr, issue, phase)`: PR 본문을 읽은 뒤, `phase ==
     "phase2"`일 때만 `_issue_view_body`로 이슈 본문을 읽어
     `flows._plan_from_body`(신규 `import flows`)로 계획을 파싱, `plan`으로
     `check_body`에 전달. 이슈 본문을 못 읽으면(네트워크 실패 등) 계획
     상태를 알 수 없으므로 fail-closed 차단 사유를 반환한다(이 파일의
     기존 "검사 불가는 통과가 아니다" 관례와 동일 방향).
2. **`gates/ci.py`**: `check()`가 `pr`와 `issue`가 둘 다 주어졌는데 `phase`가
   명시되지 않았으면(신규: `phase: str | None = None` 기본값으로 CLI/라이브러리
   양쪽에서 "안 줌"과 "phase1을 명시함"을 구분) 무음 phase1 폴백 대신 차단
   사유("--phase가 필요하다(phase1|phase2) — 생략하면 phase-2 검사가 조용히
   건너뛰어진다")를 반환한다. `main()`의 `phase = opts.get("phase", "phase1")`을
   `phase = opts.get("phase")`로 바꿔 CLI도 같은 가드를 통과하게 한다.
3. **`test_gates.py`**: `pr_reference.check_body`에 계획-인지 케이스 추가 —
   (a) 계획 없음(`plan=None`) 회귀 불변 확인, (b) 미완 스텝 2개 + Closes
   있음 → 차단, (c) 미완 스텝 2개 + Closes 없음 → 통과, (d) 마지막 스텝만
   미완 + Closes 있음 → 통과(기존과 동일), (e) 마지막 스텝만 미완 + Closes
   없음 → 차단(기존과 동일 방향), (f) 코드펜스 안에 인용된 Closes가 미완
   스텝 상황에서도 여전히 차단됨(요구 3 회귀 가드). `ci.check`에 `--phase`
   누락 가드 케이스 추가.
4. **`docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md`**:
   `check_body`의 공개 시그니처 변경(신규 `plan` 파라미터)과 위 Rationale
   채택 1-3을 기록한다.

## Out of scope

- `gates/flows.py`(`_plan_from_body`) 코드 변경 — 요구 4, 재사용만.
- phase-1 PR 규칙 변경 — 이슈 본문 제약으로 명시적 범위 밖.
- role 매칭으로 "정확히 이 스텝"을 짚어내는 정교한 판정(Rationale 채택 1의
  거부한 대안) — 실측 리스크를 안 줄이면서 새 파라미터·시그니처 확장만
  요구.
- `closure_sweep.py` 변경 — 별도 게이트(사후 일관성 스윕), 이번 이슈의
  사전 PR-본문 게이트와 책임이 다르고 이슈 본문이 언급하지 않음.
- 이슈 종결 자동화(예: 마지막 스텝 완료 시 자동 코멘트/자동 close) 추가 —
  이슈 본문이 "이슈 종결 자체는 여전히 사람 몫"이라고 명시.
- `## 실행 계획` 문법·`_PLAN_STEP_RE` 변경 — 이번 결함과 무관, issue-197이
  이미 정리한 영역.
- 체크박스 저작 누락(issue-197에서 발견된 #197의 역순 상태 같은 사례)을
  능동적으로 감지·보고하는 새 게이트 — 이번 이슈 범위 밖, fail-closed
  방향으로 안전하게 흡수됨(Rationale).

## How you'll know it worked

- `python3 -m pytest test_gates.py -q` — 기존 61건 통과 유지(1건
  `t_repo_local_claude_config_stops_the_spawn`는 이 세션의 샌드박스 권한
  때문에 이 이슈와 무관하게 실패, 손대지 않음), 신규 케이스(계획-인지
  6건 + `ci.py` `--phase` 가드) 전부 통과.
- 라이브 확인: 이 레포 자신의 이슈 #228(현재 2-스텝, 둘 다 미완)에 대해
  `pr_reference.check_body(228, "Closes #228", "phase2", plan)`을
  `flows._plan_from_body`로 얻은 실제 `plan`과 함께 호출하면 차단 사유가
  나오는지 직접 실행해 확인 — 이 이슈 자신이 고치는 버그의 실물 재현
  케이스로 검증 가능(issue-197 선례와 같은 방식).
- `python3 gates/ci.py . --pr <아무 PR> --issue 228`을 `--phase` 없이
  실행하면 차단(무음 스킵 안 됨)을 직접 확인.
