# Hunt — issue #222 test/wiring hygiene fixes (phase 2, after code)

이 세션에는 `warrant:warrant-hunter` 서브에이전트 타입이 등록돼 있지 않아
(available agent 목록에 `claude`/`Explore`/`freelunch:freelunch-worker`/
`general-purpose`/`Plan`/`statusline-setup`뿐), `general-purpose` 에이전트에
adversarial 프롬프트를 직접 넣어 대체 디스패치했다(issue #216과 같은 대체
방식). stance 회전: issue #216은 "assume-broken"을 썼으므로 이번은
**"composition-regression"** — 이 변경이 코드 자체가 아니라 **나머지
시스템과의 조합**에서 깨지는 경로를 찾는다.

코드 리뷰 대상: `ffdf496`(pytest.ini, README.md, gates/ci.py, test_gates.py,
gates/flows.py, test_flows.py).

## 점검한 4개 벡터, 전부 무결과(NOTHING FOUND)

1. **`_stage_for`의 다른 호출부** — repo 전체 grep, `flows_payload`(갱신된
   호출부)와 `test_flows.py`(신규) 외 호출부 없음. `issue_state`가
   기본값 `None`이라 가상의 단일-인자 호출부가 있었어도 이전과 동일하게
   동작.
2. **`record_fulfils_diff`/`ci.check()`의 다른 호출부** — `spawn.py::
   gate_report`(advisory, 절대 안 막음)와 `gates/ci.py::main()`(실제 차단
   진입점) 뿐. 이 레포에 CI workflow/셸 래퍼가 이 둘을 부르는 다른 지점
   없음. `python3 gates/ci.py .`를 실측 실행해 기존 보호 경로 검사 외의
   새 차단 사유가 없음을 확인.
3. **pytest.ini의 `t_*` 수집이 다른 곳을 잘못 줍는지** — repo 전체에서
   최상위 `t_` 함수를 정의하는 파일은 `test_gates.py`/`test_flows.py`뿐
   (grep 확인). `python_files` 오버라이드가 없어 `test_*.py` 파일만
   스캔 대상이라 오탐 수집 없음.
4. **`_STAGE_MAP`/`closed` 값을 하드코딩하거나 전제하는 다른 파일** —
   없음. `docs/specs/flows-schema.md`가 이미 5값 enum(`closed` 포함)을
   문서화해 뒀던 상태라 이번 코드가 그 계약을 따라잡은 것뿐.
   `test_spawn.py::FlowsPayload`는 `issue_state_by_n`을 채우는 픽스처가
   없어 영향 없음.

에이전트가 별도로 전체 스위트(`python3 -m pytest -q`)를 자체 재현해,
32건 실패가 전부 이미 disclosed된 `test_approve_scope.py`의 전역
`subprocess.run` 미복원 오염으로 수렴함을 `pytest test_approve_scope.py
test_gates.py::t_fulfils_delete_claim_absent_from_diff_blocks` 조합으로
재확인 — 그 파일을 빼면 227 passed, 1 (샌드박스 전용) 실패로 클린.

## Disposition

4개 벡터 전부 실측 확인 결과 무결과 — write set 확장 없이 종결. blocking
finding 아님. `test_approve_scope.py` 오염은 phase-2 record의 "Rationale
for deviations"에서 별도로 기록(write set 밖, 이 이슈가 만든 결함
아님, 손대지 않음).
