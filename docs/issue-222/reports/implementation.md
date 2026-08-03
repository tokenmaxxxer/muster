---
code_under_review: ffdf496
loop_state: landed
closed_checks:
  - check: "python3 -m pytest -q test_flows.py test_gates.py test_spawn.py —
      1 failed (t_repo_local_claude_config_stops_the_spawn, 기존 샌드박스
      전용), 226 passed. 0 회귀."
    code_sha: ffdf496
  - check: "python3 -m pytest -q test_flows.py — 9 passed (5값 매핑 +
      raw 폴백 + closed-우선 유닛 6건, 통합 케이스 2건, 무매핑 폴백
      회귀 1건)."
    code_sha: ffdf496
  - check: "python3 -m pytest -q test_gates.py::t_ci_check_wires_record_fulfils_diff
      — 1 passed. 배선 자체를 검사하는 회귀 가드 통과."
    code_sha: ffdf496
  - check: "python3 gates/ci.py . (이 레포 자신) — exit 1, 사유 정확히
      2건('보호 경로 변경: gates/ci.py', '보호 경로 변경: gates/flows.py')
      뿐, 다른 차단 사유 없음."
    code_sha: ffdf496
  - check: "python3 spawn.py flows --json -C . (이 레포 자신, 라이브) —
      exit 0, schema_version 1, repo tokenmaxxxer/on-the-record 정확히
      찍힘, issue 162/167/170/172/178/180/182 등 14건이
      stage:\"closed\", stage_derived:true로 찍힘(closed 우선 규칙
      실측 확인). stage:\"implementing\"도 관측(in-progress 매핑 실측
      확인). stage_derived:false 6건은 전부 stage:\"(none)\"(loop_state
      없는 raw 폴백, 기존 동작 무변경)."
    code_sha: ffdf496
  - check: "warrant-hunter 디스패치(대체, general-purpose,
      stance: composition-regression, issue #216의 assume-broken에서
      회전) — docs/reports/2026-08-03-hunt-issue-222-test-wiring-hygiene.md,
      4개 벡터 전부 무결과."
    code_sha: ffdf496
---

# Implementation — 테스트·배선 위생 3건 (issue #222, phase 2)

Proposal: [[test-wiring-hygiene.md]](../proposals/test-wiring-hygiene.md),
승인: 이슈 코멘트 `APPROVE issue-222/implementation`(single-account mode,
role-handoff contract v3 s19, PR 작성자·승인자 동일 계정 jjongkwann).

## What was done

승인된 제안의 write set 6개 항목을 그대로 이행했다(`ffdf496`) — write set
(`pytest.ini`, `README.md`, `gates/ci.py`, `test_gates.py`,
`gates/flows.py`, `test_flows.py`) 밖으로 나가지 않았다:

1. **`pytest.ini`(신규)**: `[pytest]` / `python_functions = test_* t_*`
   한 줄. `test_gates.py`의 `t_*` 함수(기존 61개 + 신규 1개 = 62개)가
   전부 pytest 수집 대상이 됨(`--collect-only`: 234건, 기존 163 +
   test_gates 62 + test_flows 9).
2. **`README.md`**: "## Self-check" 섹션에 `python3 -m pytest`가
   `pytest.ini` 덕분에 `test_gates.py` 포함 전체 스위트를 돈다는 한 줄
   추가.
3. **`gates/ci.py`**: `check()`의 기존 세 줄(`record_enums`/
   `record_wellformed_in`/`record_no_tool_residue_in`) 바로 뒤에
   `bad += gates.record_fulfils_diff(repo, {})` 추가(`gates/ci.py:56`
   부근).
4. **`test_gates.py`**: `import ci` 추가, `_fulfils_repo` 픽스처를
   재사용해 "레코드가 삭제를 주장하지만 diff에 없다" 상황을
   `ci.check(work)`에 직접 넣는 `t_ci_check_wires_record_fulfils_diff`
   신규 — "게이트가 등록만 되고 안 불린다"는 결함의 재발 방지 가드.
5. **`gates/flows.py`**: `_STAGE_MAP`에 `"in-progress": "implementing"`,
   `"landed": "delivered"` 추가, 주석을 6개 빌드형 role의 4값 수렴
   근거로 갱신. `_stage_for(loop_state, issue_state=None)`으로 확장 —
   `issue_state == "CLOSED"`면 매핑 조회보다 먼저 `("closed", True)`
   반환. `flows_payload()`의 호출부를
   `_stage_for(stage_source, issue_state_by_n.get(issue_n))`로 교체(기존
   스코프에 이미 있는 값이라 새 `gh` 호출 없음).
6. **`test_flows.py`(신규)**: `test_spawn.py`를 건드리지 않고(issue #218
   충돌 회피) `FlowsPayload.setUp`의 몽키패치 패턴을 자체 정의로 복제.
   유닛 테스트 6건(`_stage_for`의 5개 매핑 + 미매핑 raw 폴백), 통합
   테스트 2건(`flows_payload()` 경유 — 기존 `test_spawn.py::
   FlowsPayload::test_flows_section_stage_mapping_and_unmapped_fallback`와
   같은 동작의 무회귀 확인 + closed가 loop_state와 무관하게 이기는
   케이스).

## Why / Upstream basis

`docs/issue-222/proposals/test-wiring-hygiene.md`(frozen write set),
`docs/issue-222/reports/implementation/survey.md`(phase-1 survey) — 이슈
본문이 특정한 결함 3건(pytest 0건 수집, `record_fulfils_diff` 미배선,
`_STAGE_MAP` 2/5 도출)의 근본 원인과 고정된 수정 방향 그대로 이행. 결함
2에서 배선(삭제 아님)을 택한 이유와 결함 3에서 closed를 매핑 딕셔너리가
아닌 우선순위 규칙으로 만든 이유는 제안 Rationale에 이미 기록됨(재론
안 함).

## 검증 — 제안 "How you'll know it worked" 대응

프론트매터 `closed_checks`에 실행 결과 원문 기록. 요약:

1. `test_flows.py`/`test_gates.py`/`test_spawn.py`를 함께 돌리면(write
   set이 실제로 손댄 세 파일 + 그 이웃 회귀 표면) 226 passed, 1 failed
   (기존 샌드박스 전용) — 회귀 0건.
2. `test_flows.py` 단독 9 passed, `t_ci_check_wires_record_fulfils_diff`
   단독 1 passed.
3. `gates/ci.py .`/`spawn.py flows --json -C .` 둘 다 이 레포 자신에서
   라이브 실행 — 예외 없음, closed-우선 규칙과 in-progress→implementing
   매핑이 실물 데이터(이슈 14건 closed, 다수 implementing)에서 그대로
   확인됨.

**단, 제안 문구가 암시한 "저장소 루트에서 맨몸 `python3 -m pytest -q`가
샌드박스 실패 1건 외 클린"은 문자 그대로는 성립하지 않는다** — 아래
Rationale for deviations에서 설명.

## What did not work

- `test_flows.py`의 첫 초안에서 closed-우선 통합 케이스를 role
  `"coding"`으로 썼다가 `KeyError`로 실패 — `spawn.board()`가
  `spawn.ROLES`(고정 튜플, `"coding"`이 아니라 `"implementation"`)에
  없는 role의 레코드 파일은 조용히 건너뛴다는 걸 놓쳤다. `_write_record`
  호출을 role `"implementation"`으로 고쳐 해결.

## Open findings

없음 — Hunt 절이 관측한 것은 전부 disposition을 마쳤다(아래 Hunt 참고).

## Hunt

phase-2 완료 전 warrant-hunter를 디스패치했다(hunt cadence). 이 세션에는
`warrant:warrant-hunter` 서브에이전트 타입이 등록돼 있지 않아
(available agent 목록에 없음), adversarial 프롬프트를 `general-purpose`
에이전트에 직접 넣어 대체 디스패치했다. stance 회전: issue #216이
"assume-broken"을 썼으므로 이번은 **"composition-regression"**(이
변경이 나머지 시스템과의 조합에서 깨지는 경로).

**결과: 4개 벡터 전부 무결과.** 기록:
[docs/reports/2026-08-03-hunt-issue-222-test-wiring-hygiene.md](../../reports/2026-08-03-hunt-issue-222-test-wiring-hygiene.md).
점검한 벡터 — `_stage_for`의 다른 호출부(없음), `record_fulfils_diff`/
`ci.check()`의 다른 호출부(spawn.py의 advisory `gate_report`와
`ci.py::main()` 뿐), pytest.ini의 `t_*` 수집이 다른 파일을 잘못
줍는지(안 그럼), `_STAGE_MAP`/`closed` 값을 전제하는 다른 파일(없음,
`docs/specs/flows-schema.md`가 이미 5값 문서화해 둔 상태). 에이전트가
전체 스위트를 자체 재현해 아래 배선 부수 발견과 out-of-scope 오염
둘 다 독립적으로 재확인했다.

## Rationale for deviations

승인된 제안의 "What will be done"에서 두 가지가 갈라졌다 — 둘 다
write set 확장 없이, 이행 중 실측으로 드러난 필요 때문이다.

1. **`test_gates.py::t_rulebook_falls_back_to_github`의 env var 복원
   버그를 write set 안에서 고쳤다(제안에 없던 수정).** 제안 항목 4는
   `test_gates.py`에 `import ci` + 신규 배선 테스트 1건만 명시했다.
   실제로 `python3 -m pytest -q test_gates.py test_spawn.py`를 처음
   돌려보니 19건이 실패했다 — `t_rulebook_falls_back_to_github`이
   `TOKENMAXXXER_RULEBOOKS`를 `del`만 하고 `conftest.py`가 세션
   전체에 `setdefault`해 둔 기본값을 복원하지 않아서였다. pytest.ini
   이전에는 `test_gates.py`의 `t_*`가 pytest에 아예 안 잡혀 이 버그가
   드러날 기회가 없었다 — **이 이슈 자체가 만드는 배선**(결함 1)이
   처음으로 이 버그를 같은 pytest 세션에 노출시킨 것이므로, 고치지
   않으면 제안의 "How you'll know it worked" 1번 기준("기존 실패 외
   회귀 없음")을 이 write set 안에서 충족할 수 없었다. `test_gates.py`는
   이미 frozen write set 안이라 write set 확장은 아니다. `saved =
   os.environ.pop(...)` → try/finally 로 원래 값(있었다면 그 값, 없었다면
   부재)을 정확히 복원하도록 고쳤다.
2. **저장소 루트에서 맨몸 `python3 -m pytest -q`는 여전히 클린하지
   않다 — 그러나 원인이 이 write set 밖(`test_approve_scope.py`)이라
   손대지 않았다.** `test_approve_scope.py`(write set 밖, 이슈 본문도
   언급 안 함)의 여러 테스트가 `spawn.subprocess.run = fake_run`으로
   **전역** `subprocess` 모듈의 `run`을 패치하고 복원하지 않는다 —
   `spawn.subprocess`는 별도 객체가 아니라 프로세스 전체가 공유하는
   같은 `subprocess` 모듈이라, 이 파일이 먼저 수집·실행되면(맨몸
   `pytest -q`는 알파벳 순으로 `test_approve_scope.py`를 가장 먼저
   돈다) 이후 `test_gates.py`/`test_spawn.py`의 실제 git subprocess
   호출이 전부 가짜 성공을 돌려받아 무더기로 깨진다. `git status`/
   `git diff --stat`로 이 브랜치가 `test_approve_scope.py`를 전혀 건드리지
   않았음을 확인했고(따라서 이 이슈가 만든 결함이 아니라 사전 존재),
   `pytest -q test_approve_scope.py test_spawn.py`(내 write set 어느
   파일도 안 낀 조합)만으로도 10건이 재현돼 이슈 #222와 무관함을
   실측 확인했다. write set 밖이라 고치지 않았다 — 대신 검증 방식을
   `python3 -m pytest -q test_flows.py test_gates.py test_spawn.py`(이
   write set이 실제로 손댄 파일 + 그 회귀 표면)로 좁혀 "기존 실패
   1건 외 회귀 없음"을 확인했다. 별도 이슈로 다룰 가치가 있는 사전
   결함이지만, 이슈를 여는 것은 사용자 몫이라 여기서 만들지 않는다.

## Doc-placement ladder (완료 항목)

- [x] env var / config key / new dep / migration / setup step →
  handbook: `pytest.ini`는 새 setup step(`python3 -m pytest`가 이제
  `test_gates.py`도 돈다)이라 `README.md` "## Self-check"(이 프로젝트의
  handbook)에 한 줄로 반영(위 §What was done 항목 2) — 별도
  `docs/handbooks/` 신설 불필요.
- [x] library-or-format 선택 / 시그니처·wire format 변경 →
  `docs/issue-222/decisions/`: 해당 없음 — `_stage_for`의 시그니처
  확장(`issue_state=None` 추가)은 내부 헬퍼(`_` 접두)이고, 그 결과인
  `flows --json`의 5값 stage enum은 `docs/specs/flows-schema.md`가 이미
  약속해 둔 것을 채운 것뿐 새 결정이 아니다(제안 Constraints).
- [x] benchmark/investigation 수치 → `docs/issue-222/reports/`: 완료 —
  위 §검증의 테스트/라이브 실행 결과가 이 파일(프론트매터
  `closed_checks` + 본문)에 있음.
- [x] Phase 1 survey: `docs/issue-222/reports/implementation/survey.md`
  (PR #226으로 이미 제출)
- [x] Phase 1 proposal: `docs/issue-222/proposals/test-wiring-hygiene.md`
  (PR #226으로 이미 제출)
- [x] Phase 2 record: `docs/issue-222/reports/implementation.md`(this file)
- [x] Hunt record: `docs/reports/2026-08-03-hunt-issue-222-test-wiring-hygiene.md`
- [x] Tests: `test_gates.py`에 신규 회귀 1건 + 기존 1건 버그 수정,
  `test_flows.py` 신규 8건(유닛 6 + 통합 2)(위 §What was done 항목 4/6).

## Open finding resolution path

현재 열린 blocking finding 없음 — Hunt 절의 4개 벡터 모두 disposition을
마쳤고, write-set 확장이 필요한 미해결 항목은 남지 않았다.
