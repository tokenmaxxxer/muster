files:
- pytest.ini
- README.md
- gates/ci.py
- test_gates.py
- gates/flows.py
- test_flows.py

## Request

이슈 #222: 2026-08-03 감사가 찾은 테스트·배선 위생 결함 3건. (1) pytest가
`t_` 접두사 자가 러너인 `test_gates.py`를 0건 수집한다 — 전체 스위트를
pytest 한 번으로 강제하는 지점이 없다. (2) `record_fulfils_diff` 게이트
(issue #155, issue #145 사고 재발 방지용)가 은퇴한 라우터의 죽은 `ALL`
레지스트리에만 등록돼 있고 `gates/ci.py::check()`에 배선되지 않아
프로덕션(수동 `python3 gates/ci.py .` 확인 경로)에서 한 번도 안 돈다 —
테스트만 통과하는 게이트. (3) `gates/flows.py`의 `_STAGE_MAP`이
`docs/specs/flows-schema.md` §2.2가 약속한 5값(`proposal`/`approved`/
`implementing`/`delivered`/`closed`) 중 앞의 둘만 도출해, 완료되거나
닫힌 이슈도 raw `loop_state`로 나온다 — repo-status-board가 이 값을
쓸 수 없는 공급자측 원인.

## Constraints

- 이슈 3은 `docs/specs/flows-schema.md`가 규율하는 5값 enum과
  `stage_derived`의 의미를 그대로 채우는 방향이다 — 스키마 문서 변경
  없음, 필드 추가 없음, `schema_version` 범프 없음.
- 이슈 2에서 삭제가 아니라 배선을 택할 경우에도 대체가 아니라 보강임을
  survey가 확인해야 한다(제약 원문). survey에서 확인: `ci.check()`가
  이미 부르는 다른 게이트 중 "레코드의 fulfils claim이 실제 diff와
  일치하는가"를 보는 것은 없다.
- `spawn.py`, `test_spawn.py`는 건드리지 않는다 — 이슈 본문 명시,
  issue #218이 동시에 수정 중이라 손대면 충돌한다.
- `roles/*.json`의 `record_fields.loop_state` enum은 그대로 둔다 — survey가
  확인한 대로 빌드형 role 6개가 이미 4값(`scope-proposed`/
  `scope-approved`/`in-progress`/`landed`)으로 수렴해 있어 스키마
  변경이 필요 없다.

## Rationale

**결함 2 — 배선 vs 삭제: 배선을 택한다.** survey가 확인한 대로
`record_fulfils_diff`는 `record_enums`와 글자 그대로 같은 dual-mode
시그니처(`d / "work"`가 있으면 그쪽, 없으면 `d` 자체)로 이미 만들어져
있고, `record_enums`는 그 시그니처 그대로 `ci.py`에서 `gates.record_enums(repo,
{})`로 직접 호출되고 있다 — 즉 배선 비용은 `ci.py`에 한 줄
(`bad += gates.record_fulfils_diff(repo, {})`) 추가뿐이다. 실측
재현(스크래치 스크립트)으로 `ci.check()`가 오늘 진짜 커밋되지 않은
삭제 주장을 놓친다는 것도 확인했다 — issue #145가 실제로 겪은 사고
형태가 `ci.check()` 경로에서는 여전히 열려 있다는 뜻이다. scout-brief가
확인한 대로(Jira/Linear의 상태 카테고리 관례), 이미 존재하고 검증된
검사를 대체 없이 없애는 쪽보다 한 줄로 실제 배선을 완성하는 쪽이 이
결함의 "테스트만 통과, 프로덕션은 안 돎"이라는 정의 자체를 없앤다.

거부한 대안(rejected alternative) — **게이트와 죽은 라우터 스캐폴딩
(`writeset`/`deps`/`ALL`/`check(names, d, cfg)`)을 함께 삭제.** survey가
확인한 대로 이 속성(레코드의 fulfils claim ↔ diff 일치)을 대체하는
게이트가 없어, 삭제하면 issue #145 재발 방지 자체가 사라진다. 게다가
`ALL`/`check()`/`writeset`/`deps`는 `record_fulfils_diff`와 무관하게 이미
100% 죽은 코드다(survey: 이 넷을 부르는 곳이 테스트 포함 0건) — 이걸
치우는 것은 이슈가 이름 붙인 3개 결함과 다른, 그 자체로 결정이 필요한
별도 정리다(자체 테스트 커버리지도 있어 write-set이 커진다:
`t_rename_bypass`, `t_commit_bypass`, `t_writeset_*`,
`t_deps_fail_closed` 등). 3건 위생 수정이라는 이슈의 좁은 틀에서
분리해 Out of scope로 남긴다.

**결함 3 — `closed`를 loop_state 매핑보다 우선하는 종결 상태로 만든다.**
`_STAGE_MAP`에 `in-progress`→`implementing`, `landed`→`delivered`를
추가하는 것은 survey가 확인한 4값 enum 수렴을 그대로 반영할 뿐이라
대안이랄 게 없다. `closed`는 다르다 — `loop_state`가 아니라 GitHub
이슈 자체의 상태에서 나와야 하므로 설계가 필요했다.

거부한 대안(rejected alternative) — **`closed`를 `_STAGE_MAP`과 같은
dict 항목으로 취급(예: 별도 `_ISSUE_STAGE_MAP`을 만들어 결과를
`_STAGE_MAP` 결과와 나중에 "합치되, 우선순위 규칙은 호출자가 판단").**
scout-brief가 확인한 대로 Jira/Linear 둘 다 "종결 상태는 그 앞의 진행
상태와 무관하게 항상 이긴다"는 것을 계산 로직 차원에서 강제한다(별도
카테고리가 아니라 우선순위 규칙). 합치기를 호출자(`flows_payload`)
책임으로 미루면 그 규칙이 흩어져 다음 호출부가 실수로 반대 순서로
합칠 위험이 남는다 — `_stage_for(loop_state, issue_state)`가 함수
내부에서 `issue_state == "CLOSED"`를 먼저 검사하고 그 자리에서
`("closed", True)`를 반환하도록 만들어, 우선순위 규칙 자체를 한
곳(`_stage_for`)에 고정한다.

**테스트 배치 — `test_spawn.py`를 건드리지 않고 새 `test_flows.py`를
만든다.** `gates/flows.py`의 유일한 기존 테스트 홈은 `test_spawn.py`의
`FlowsPayload` 클래스이지만, 이슈 본문이 `test_spawn.py`를 명시적으로
금지한다(#218 동시 수정).

거부한 대안(rejected alternative) — **`FlowsPayload`의 셋업 로직을
가져와 쓰되 실제로는 아무 것도 커밋하지 않고 인메모리로만 돌린다(파일을
건드리지 않으니 "손대지 않음"으로 본다).** 기각 이유: "건드리지 않는다"는
제약의 취지는 파일 diff 충돌 회피이지, import 방식의 문제가 아니다 —
하지만 `FlowsPayload`의 셋업이 `test_spawn.py` 모듈 스코프 안에 있어
그 테스트를 재사용하려면 어차피 `test_spawn.py`를 import하거나 수정해야
하고, #218이 그 파일의 클래스 구조 자체를 바꿀 수도 있어 import
의존만으로도 깨지기 쉽다. 새 파일에 `FlowsPayload.setUp`과 같은
얕은 몽키패치 패턴(±15줄, `spawn.ROOT`/`flows._pr_list_all`/
`flows._issue_list_all` 패치)만 그대로 복제하는 쪽이 코드 중복은
작지만 결합은 0이다 — `test_spawn.py`가 어떻게 바뀌든 이 새 파일은
영향을 안 받는다.

## What will be done

1. **`pytest.ini`(신규)**: `[pytest]` 섹션에 `python_functions = test_* t_*`
   한 줄. `test_gates.py`의 61개 `t_*` 함수 전부가 pytest 수집 대상이
   된다(실측: 224건 수집, 60 passed + 기존 샌드박스 전용 실패 1건 —
   위 survey 참고).
2. **`README.md`**: "## Self-check" 섹션(현재 `python3 test_gates.py`만
   문서화)에 `python3 -m pytest`가 이제 `pytest.ini` 덕분에 전체
   스위트(`test_gates.py` 포함)를 돌린다는 한 줄 추가.
3. **`gates/ci.py`**: `check()`의 기존 세 줄(`record_enums`/
   `record_wellformed_in`/`record_no_tool_residue_in`) 바로 뒤에
   `bad += gates.record_fulfils_diff(repo, {})` 한 줄 추가.
4. **`test_gates.py`**: `import ci`(이미 `sys.path`에 `gates/` 있음) 추가,
   `_fulfils_repo` 픽스처를 재사용해 "레코드가 삭제를 주장하지만 diff에
   없다" 상황을 `ci.check(work)`에 직접 넣어 그 문자열이 결과에 있는지
   단언하는 새 테스트 1건(`t_ci_check_wires_record_fulfils_diff`) —
   "게이트가 등록만 되고 안 불린다"는 이번 결함의 재발을 실제로 막는
   유일한 계층(오늘은 `ci.check()`를 직접 부르는 테스트가 이 파일에도
   `test_spawn.py`에도 0건이었음 — survey 확인).
5. **`gates/flows.py`**:
   - `_STAGE_MAP`에 `"in-progress": "implementing"`, `"landed":
     "delivered"` 추가, 주석을 "중앙 enum 없음"에서 실제로 수렴한
     6개 빌드형 role + 29개 단일-상태 role 근거로 갱신.
   - `_stage_for(loop_state, issue_state=None)`으로 시그니처 확장:
     `issue_state == "CLOSED"`면 매핑 조회보다 먼저 `("closed", True)`를
     반환.
   - `flows_payload()`의 stage 계산 호출부(현재 `_stage_for(stage_source)`)를
     `_stage_for(stage_source, issue_state_by_n.get(issue_n))`로 교체 —
     `issue_state_by_n`은 이미 같은 함수 스코프에 존재하는 값이라 새
     `gh` 호출이 없다(issue #216 제약과 같은 폴링 비용 계약 유지).
6. **`test_flows.py`(신규)**: `FlowsPayload.setUp`과 동일한 몽키패치
   패턴(자체 정의, `test_spawn.py` import 없음)으로:
   - `_stage_for`의 5개 매핑 전부(`scope-proposed`/`scope-approved`/
     `in-progress`/`landed`/이슈-닫힘) + 미매핑 raw 폴백 케이스.
   - `closed`가 `loop_state`(예: `in-progress`, 아직 안 끝난 것처럼
     보이는 값)와 무관하게 이슈가 `CLOSED`면 이긴다는 통합 케이스
     (`flows_payload()` 전체 경유).
   - 기존 `test_spawn.py::FlowsPayload::test_flows_section_stage_mapping_and_unmapped_fallback`가
     검증하는 "미매핑은 raw로 남는다" 동작이 이번 변경으로 안 깨진다는
     것을 이 새 파일에서도 별도로 확인(원본은 손대지 않음).

## Out of scope

- `writeset`/`deps`/`ALL`/`check(names, d, cfg)`(죽은 라우터 스캐폴딩)
  삭제 — Rationale에서 기각한 대안. `record_fulfils_diff`를 지우지
  않기로 했으므로 이슈의 제약(삭제 시 스캐폴딩도 함께)이 발동하지
  않고, 이 넷의 삭제는 별도 결정과 별도 write-set이 필요하다.
- 이 레포(on-the-record) 자신의 `docs/specs/write_scope.md` 작성 —
  survey가 발견한, `role_scope()`가 `--pr`과 함께 돌면 이번 이슈가
  건드리는 루트 파일들을 전부 write_scope 이탈로 볼 부수 관찰. 이
  레포에 자동 CI가 없어(survey 확인) 실제 병합을 막지 않고, 3건 위생
  수정과 무관한 별도 결정이다.
- `roles/*.json`의 `loop_state` enum 자체 변경 — 이미 수렴돼 있어
  불필요(Constraints).
- `docs/specs/flows-schema.md` 수정 — 5값 enum과 `stage_derived` 의미
  불변(Constraints).
- `spawn.py`/`test_spawn.py` 변경 — 이슈 본문 명시, #218 충돌 회피.
- `.github/workflows/` 신설(CI 자동화 자체를 새로 배선하는 것) — survey가
  확인한 부수 관찰이지 이슈가 요청한 것이 아니다.

## How you'll know it worked

- `python3 -m pytest -q` — 전체 스위트가 `test_gates.py`의 61개
  `t_*` 케이스를 포함해 수집·실행되고(`--collect-only`로 개수 확인),
  기존 실패(sandbox 전용 1건) 외 회귀 없음.
- `python3 -m pytest -q test_flows.py` 전부 통과 — 5값 매핑 + raw
  폴백 + closed-우선 케이스.
- `python3 -m pytest -q test_gates.py::t_ci_check_wires_record_fulfils_diff`
  통과 — 배선 자체를 검사하는 새 회귀 가드.
- `python3 gates/ci.py .` 이 레포 자신에서 실행, 예외 없이 끝남 —
  `gates/ci.py`/`gates/flows.py` 자체가 `PROTECTED_ROOT_DIRS`(`gates`)
  경로라 이 PR의 diff에 대해 "보호 경로 변경" 2건이 뜨는 것은 정상
  (게이트 코드 변경 자체를 사람이 보게 만드는 기존 설계) — 그 2건
  외에 다른 차단 사유(write-set 이탈, 의존성 등)가 없는지 확인.
- `python3 spawn.py flows --json -C .` 이 레포 자신에서 실행해 예외
  없이 JSON이 나오고, 최소 하나의 CLOSED 이슈가 있는 subject의
  `flows[].stage`가 `"closed"`/`stage_derived: true`로 찍히는지 직접
  확인(합성이 아니라 이 세션 자신의 라이브 실행 결과).
