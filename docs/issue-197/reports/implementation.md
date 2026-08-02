---
code_under_review: e7bfdcb1ddbcf1d67543c228f5c089621cdae507
loop_state: landed
closed_checks:
  - check: 기존 FlowsPayload 플랜 테스트 3개(펜스 없음·정확일치 헤더 케이스)
      회귀 없이 무변경 통과
    code_sha: e7bfdcb1ddbcf1d67543c228f5c089621cdae507
  - check: 이슈-189 실물 본문 회귀 픽스처 — 코드펜스 안 4-스텝 견본이 아니라
      변형 헤더 아래 실제 3-스텝(role 문자열의 em dash 접미사 포함)을
      정확히 낸다
    code_sha: e7bfdcb1ddbcf1d67543c228f5c089621cdae507
  - check: 라이브 확인 — 이 레포 자체에서 `spawn.py flows --json`을 실행,
      issue 189 항목의 plan이 실제 3-스텝으로 나옴을 직접 확인(합성 아님)
    code_sha: e7bfdcb1ddbcf1d67543c228f5c089621cdae507
---

# Implementation — `_plan_from_body` 코드펜스·헤더 전방일치 수정 (issue #197, phase 2)

Proposal: [[plan-parser-fix.md]](../proposals/plan-parser-fix.md), 승인:
이슈 코멘트 `APPROVE issue-197/implementation` (single-account mode,
role-handoff contract v3 s19) + PR #199 merged (phase-1 산출물).

## What was done

승인된 제안의 "What will be done"을 그대로 이행했다 — write set(`gates/flows.py`,
`on-the-record/commands/run.md`, `test_spawn.py`) 밖으로 나가지 않았다:

1. **`gates/flows.py`.** `_plan_from_body`의 헤더 탐색 루프와 스텝 수집
   루프 둘 다에 `in_fence` 토글을 추가했다 — ` ``` `로 시작하는 줄마다
   반전, `in_fence`인 동안 그 줄은 건너뛴다. `gates/gates.py:387-392`의
   `record_no_tool_residue_in`과 동일한 패턴, 새로 발명하지 않았다. 헤더
   비교를 `line.strip() == "## 실행 계획"` 단독에서
   `stripped == "## 실행 계획" or stripped.startswith("## 실행 계획 ")`로
   확장 — 뒤에 리터럴 공백을 요구해 `## 실행 계획서` 같은 동명 오매치를
   막는다. 반환 계약(`None`=블록 없음, 리스트=블록 있음)과
   `_PLAN_STEP_RE`는 손대지 않았다.
2. **`on-the-record/commands/run.md`.** `## 실행 계획 (Execution Plan)` →
   `### 문법` 절 바로 뒤에 `### 저작 규칙 (파서가 실제로 보는 것, issue #197)`
   신설 — (a) 견본·설명은 반드시 코드펜스 안, (b) 헤더는 `## 실행 계획`로
   시작하고 뒤에 공백+부가 설명 허용, (c) 본문에 펜스 밖 계획 헤더는
   정확히 하나여야 하며 여럿이면 첫 번째만 파싱되고 이는 저작 오류.
3. **`test_spawn.py`.** `FlowsPayload`에 회귀 테스트 3개 추가:
   - `test_flows_plan_skips_fenced_example_and_matches_variant_header` —
     주 증거. 이슈-189 실물 본문(`gh issue view 189 --json body`로 받은
     전문, 리터럴 문자열로 픽스처에 포함)을 그대로 써서 `plan`이 펜스 안
     4-스텝이 아니라 실제 3-스텝(role 문자열은 em dash 설명 접미사 포함
     그대로)을 낸다고 단언한다.
   - `test_flows_plan_fenced_only_body_has_no_real_plan` — 보조 합성
     케이스. 펜스 안에만 계획 헤더가 있고 펜스 밖 실제 헤더가 없으면
     `plan: None`.
   - `test_flows_plan_two_unfenced_headers_first_wins` — 보조 합성 케이스.
     펜스 밖 계획 헤더가 둘이면 첫 번째만 파싱된다(`break` 동작 무변경
     확인, run.md 저작 규칙의 문서화 대상 동작).

## 검증 — 제안 "How you'll know it worked" 대응

1. **`python3 -m pytest test_spawn.py test_gates.py -q` 통과, 기존
   assertion 무변경.**
   ```
   133 passed, 17 failed (baseline pre-existing failures) in 5.76s
   ```
   17개 실패는 이 워크스페이스에 `gh`/룰북 fetch 네트워크 접근이 없어
   생기는 기존 환경 실패(`IssueScopedPrompt`/`EventReporting`/
   `ProgressEvents`)로, 변경 전 베이스라인(`git stash` 후 같은 명령
   실행)에서도 동일하게 17개 실패·130 passed였다 — 이번 변경으로
   새로 깨진 테스트는 0개. `FlowsPayload` 클래스만 단독 실행
   (`-k FlowsPayload`)하면 14 passed(기존 11개 + 신규 3개), 전부
   통과 — `test_flows_plan_is_null_without_plan_block`,
   `test_flows_plan_parses_step_lines`,
   `test_flows_plan_only_issue_with_no_board_record_still_gets_entry`
   3개(제안 Constraints가 지목한 기존 케이스) 어설션 원문 그대로 통과
   확인.
2. **라이브 확인.** 이 저장소 자체에서 `python3 spawn.py flows --json -C .`
   실행, `flows[]`의 issue 189 항목:
   ```json
   "plan": [
     {"step": 1, "roles": ["product-discovery — 요구사항·수용기준 확정, 위 갭에 대한 접근 결정"], "done": true},
     {"step": 2, "roles": ["implementation — 확정된 스펙대로 구현"], "done": true},
     {"step": 3, "roles": ["execution-observation — 실제 동작 확인"], "done": true}
   ]
   ```
   펜스 안 4-스텝 견본(`architecture ‖ security-threat-model` 포함)이
   아니라 실제 3-스텝 — PR #195 코멘트가 실측했던 결함이 이 워크스페이스의
   고친 코드로 재현되지 않음을 직접 확인했다.

## Hunt (before phase-2 completion)

phase-1(PR #199, 승인된 proposal)에서 general-purpose 에이전트로 이미
adversarial hunt pass를 포그라운드 실행·완료했다 — 설계를 실제 파일과
이 레포 이슈 본문 64건 전체에 대조했고, 결과(펜스 미종료·펜스 없는
인용 오매치·틸드 펜스 미지원 3건, 전부 실측 없음 확인 후 의도적으로
범위 밖)는 proposal의 Rationale에 이미 기록돼 있다. phase-2는 그
설계를 코드로 그대로 옮겼을 뿐 새 설계 결정이 없어 재-hunt 대상이
아니다 — phase-2 완료 시점의 확인은 위 §검증 1·2(실제 실행 결과)로
갈음했고, 그 결과를 이 레코드의 `closed_checks:`에 기록했다.

## What did not work

None.

## Rationale for deviations

None — phase-2 실행은 승인된 제안의 "What will be done"을 그대로
따랐다. 유일한 편차 후보였던 보조 합성 테스트 2개(`test_flows_plan_
fenced_only_body_has_no_real_plan`)의 첫 시도는 이슈에 보드 레코드가
없어 `flows[]`에 아예 나타나지 않는 것을 놓쳐 `KeyError`로 실패했다 —
기존 `test_flows_plan_is_null_without_plan_block`과 같은 패턴
(`_write_record` 로 보드 레코드를 먼저 만듦)을 따라 즉시 고쳤다. 이는
테스트 구현의 실수 수정이지 승인된 제안 대비 설계·범위 편차가 아니다.

## Doc-placement ladder (완료 항목)

- [x] env var / config / dependency / migration → handbook: 해당 없음
  — 새 환경변수·설정·의존성·마이그레이션 없음(제안 Constraints: 새
  의존성 추가 금지, 그대로 지켰다).
- [x] library-or-format 선택 / 시그니처·wire format 변경 →
  `docs/issue-197/decisions/`: 해당 없음 — 승인된 제안의 Rationale이
  이미 이 결정(펜스 토글 재사용 vs 신규 마크다운 파서, 공백-경계
  전방일치 vs 좁은 괄호 정규식, 기존 break 유지 vs 새 게이트)을
  phase-1 proposal 문서에 기록했고, phase-2 는 그 결정을 그대로
  이행했을 뿐 새 결정을 내리지 않았다. `docs/specs/flows-schema.md`의
  `plan` 필드 형태도 무변경(제안 Out of scope 그대로).
- [x] benchmark/investigation 수치 → `docs/issue-197/reports/`: 완료 —
  위 §검증의 테스트 결과·라이브 확인 출력이 이 파일에 있다.
- [x] Phase 1 survey: `docs/issue-197/reports/implementation/survey.md`
  (PR #199 로 이미 merge)
- [x] Phase 1 scout-brief: `docs/issue-197/reports/implementation/scout-brief.md`
  (PR #199 로 이미 merge)
- [x] Phase 1 proposal: `docs/issue-197/proposals/plan-parser-fix.md`
  (PR #199 로 이미 merge)
- [x] Phase 2 record: `docs/issue-197/reports/implementation.md` (this
  file)
- [x] Code: `gates/flows.py`, `on-the-record/commands/run.md`
- [x] Tests: `test_spawn.py`

## Open findings

None.
