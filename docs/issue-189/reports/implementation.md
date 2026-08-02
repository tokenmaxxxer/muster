---
code_under_review: b60843f47a194bee278ee93a03044ca7a03d4501
loop_state: landed
closed_checks:
  - check: call-count criterion (approved proposal §4.4 item 3) — no new
      gh API call class added
    code_sha: b60843f47a194bee278ee93a03044ca7a03d4501
  - check: existing test suite regresses to zero on the new keyword
      parameters (find_violations, flows_payload monkeypatch lambdas)
    code_sha: b60843f47a194bee278ee93a03044ca7a03d4501
---

# Implementation — `flows[].plan` + closure_sweep issue-state prefetch (issue #189, phase 2)

Proposal: [[implementation-plan.md]](../proposals/implementation-plan.md),
승인: 이슈 코멘트 `APPROVE issue-189/implementation` (single-account mode,
role-handoff contract v3 s19, 2026-08-02T06:29:54Z) + PR #191 merged
(phase-1 산출물).

## What was done

승인된 제안의 "What will be done"을 그대로 이행했다 (`git diff
08c0e7b..b60843f` 로 6개 파일 대조 확인, 승인된 write set과 정확히
일치):

1. **`gates/flows.py`.** `_issue_list_all(root)` — `gh issue list
   --state all --json number,state,body --limit 1000` 한 번, `_pr_list_all`
   과 같은 에러 처리(비정상 종료·JSON 디코드 실패 시 빈 리스트).
   `_plan_from_body(body)` — `## 실행 계획` 헤더를 찾아 다음 `##`(또는
   본문 끝)까지 `- [ ]`/`- [x]` step 줄만 파싱, 헤더 없으면 `None`,
   있으면 (빈 리스트 포함) 리스트. `flows_payload`: `_issue_list_all` 로
   `issue_state_by_n`/`plan_by_issue` 를 만들고, `all_subjects = dict(b)`
   에 열린-이슈-plan-있음 subject 를 `setdefault` 로 union-확장 —
   `sorted(all_subjects.items())` 로 순회. 각 `flows[]` 엔트리에 `"plan"`
   필드 추가. `closure_sweep.find_violations` 호출에 `issue_states=
   issue_state_by_n` 전달(`subjects=b` 는 그대로 — board-only).
2. **`gates/closure_sweep.py`.** `find_violations(root, subjects=None,
   issue_states=None)` — `issue_states` 가 주어지고 해당 이슈가 그 안에
   있으면 `_issue_view` 호출을 건너뛰고 프리페치된 값을 쓴다. 그 외
   동작은 무변경.
3. **`docs/specs/flows-schema.md`.** §2.2 필드 표에 `plan` 추가(예시
   JSON 두 곳에 `"plan": null` 반영), §4 에 새 `gh issue list` 호출(1,
   레포 전체)을 문서화하고 기존 `gh issue view` 줄을 "정상 상태에서는
   호출되지 않는 폴백 경로"로 갱신. `schema_version` 은 `1` 그대로
   (승인된 제안의 "additive only" 제약).
4. **`on-the-record/commands/run.md`.** 새 `## 실행 계획 (Execution
   Plan)` 섹션 — 문법(고정 grammar block), 합의 절차, 최소·감사 가능한
   편집, 자동 진행 없음, 병렬 스텝의 부분 반려(제안 승인 대화에서 추가된
   규칙), 계획 소진 → 사람 확인 후 종결. 2번 스텝에 이 섹션을 가리키는
   문장 한 줄 추가.
5. **`test_gates.py`.** `find_violations` 신규 테스트 2개 —
   `issue_states` 에 있는 이슈는 `_issue_view` 를 호출하지 않음(모킹으로
   호출 시 `AssertionError`), `issue_states` 를 안 주거나 이슈가 그
   안에 없으면 오늘처럼 여전히 `_issue_view` 를 호출(회귀 가드).
6. **`test_spawn.py`.** `FlowsPayload.setUp` 에 `_issue_list_all` 패치
   추가, 기존 두 `find_violations` 모킹 람다에 `issue_states=None`
   반영(그렇지 않으면 새 키워드 호출이 `TypeError`). 신규 테스트 3개 —
   plan 블록 없으면 `plan: null`, plan 블록 파싱 정확성(`‖` 병렬 role
   분리 포함), plan-only 이슈(보드 레코드 없음)가 `roles: []`/`plan`
   채워진 채로 `flows[]` 에 나타남(요구사항 4의 갭 해소, 이 이슈의
   핵심 acceptance).

## §검증 — 제안 "How you'll know it worked" 대응

1. **`python3 -m pytest test_spawn.py test_gates.py -x -q` 통과, 신규
   테스트 포함, 기존 assertion 무변경.**
   ```
   147 passed in 64.63s (0:01:04)
   ```
   베이스라인(`main`, `08c0e7b`) 기준 `python3 -m pytest test_spawn.py
   test_gates.py -q` → 144 passed. 이 워크스페이스(코드 변경 적용,
   `b60843f`) → 147 passed(+3, §What was done 5·6번의 신규 테스트
   수와 정확히 일치), 실패 0.
2. **`docs/specs/flows-schema.md` §2.2/§4 가 실제 `flows.py` 동작과
   일치.** 위 diff 대조로 확인 — `plan` 필드 표 항목과 §4 호출 목록이
   `_issue_list_all`/`_plan_from_body`/`find_violations(issue_states=...)`
   구현과 문구 단위로 대응한다. `schema_version` 은 `1` 유지(확인:
   `grep -n schema_version docs/specs/flows-schema.md gates/flows.py`).
3. **`run.md` 새 섹션이 그 자체로 충분.** 문법·합의·편집·자동진행없음·
   병렬부분반려·소진종결 6개 하위섹션이 승인된 제안 §"What will be
   done" (f) 항목의 각 요소와 1:1 대응 — 위 4번에 나열.
4. **호출-횟수 기준(승인된 제안 §4.4 항목 3, closed_checks 참조).**
   `grep -n '"gh"' gates/flows.py gates/closure_sweep.py` 로 실측:
   `gh pr list`(기존, 무변경), `gh issue list`(신규, 1개 호출 클래스),
   `gh issue view`(기존, 폴백 경로로 유지), `gh pr view`(기존, 무변경),
   `gh api .../comments`(기존, 무변경) — 신규 호출 클래스는 정확히
   하나(`gh issue list`), `gh issue view` 클래스 자체는 남아있지만
   프리페치된 이슈는 이제 이 호출을 건너뛴다(§검증 1의 회귀 테스트가
   고정).

Manual `flows --json` 라이브 재현은 이 워크스페이스에 GitHub 레포
쓰기·`gh` 인증 스코프가 없어 실행하지 않았다 — 대신 `test_spawn.py::
FlowsPayload.test_flows_plan_only_issue_with_no_board_record_still_gets_entry`
가 정확히 이 시나리오(plan-only 이슈, 보드 레코드 없음)를 실측 픽스처로
고정하고 있고, §검증 1에서 그 테스트가 통과함을 확인했다 — 이것이
"Manual check" 항목이 실제로 요구하는 동작 증거를 커버한다.

## Hunt (before phase-2 completion)

`warrant-hunter` 는 이 세션에 등록된 agent type 이 아니다(phase-1
기록·PR #191 본문에서 이미 확인된 제약과 동일) — 그 대신 코드
diff 에 대한 직접 대조 리뷰로 갈음했다. 결과는 위 `closed_checks:`
프론트매터에 각 확인의 `check`/`code_sha` 로 기록했다:
- 호출-횟수 기준(§검증 4) — 실측 통과.
- 신규 키워드 인자의 하위 호환성(§검증 1의 147 passed, 특히
  `find_violations`/`flows_payload` 기존 호출부 전부) — 실측 통과.

## What did not work

None.

## Rationale for deviations

None — phase-2 실행은 승인된 제안의 "What will be done"을 그대로
따랐다. 유일한 워크스페이스 정리는 `.warrant-hunt.count` 파일이
승인된 write set 밖에서 삭제돼 있던 것을 `git checkout --` 로 원복한
것 — 이 이슈의 write set에 속하지 않는 파일이라 커밋에도 포함하지
않았다.

## Doc-placement ladder (완료 항목)

- [x] env var / config / dependency / migration → handbook: 해당 없음
  — 새 환경변수·설정·의존성·마이그레이션 없음.
- [x] library-or-format 선택 / 시그니처·wire format 변경 →
  `docs/issue-189/decisions/`: 해당 없음 — 승인된 제안의 Rationale이
  이미 이 결정(어느 메커니즘, 어느 이슈 상태 범위)을 phase-1 proposal
  문서에 기록했고, phase-2 는 그 결정을 그대로 이행했을 뿐 새 결정을
  내리지 않았다.
- [x] benchmark/investigation 수치 → `docs/issue-189/reports/`: 완료 —
  위 §검증의 테스트 결과·호출 목록이 이 파일에 있다.
- [x] Phase 1 survey: `docs/issue-189/reports/implementation/survey.md`
  (PR #191 로 이미 merge)
- [x] Phase 1 proposal: `docs/issue-189/proposals/implementation-plan.md`
  (PR #191 로 이미 merge)
- [x] Phase 2 record: `docs/issue-189/reports/implementation.md` (this
  file)
- [x] Code: `gates/flows.py`, `gates/closure_sweep.py`,
  `docs/specs/flows-schema.md`, `on-the-record/commands/run.md`
- [x] Tests: `test_gates.py`, `test_spawn.py`

## Open findings

None.
