---
code_under_review: 6a54d5a724d0f5c66ce647e3af01a0d0df16942d
loop_state: landed
closed_checks:
  - check: Ledger::test_entry_carries_the_live_log_path 개별 실행 — 1 passed
    code_sha: 6a54d5a724d0f5c66ce647e3af01a0d0df16942d
  - check: IssueScopedPrompt::test_preparation_and_preamble_happen_once
      개별 실행 — 1 passed
    code_sha: 6a54d5a724d0f5c66ce647e3af01a0d0df16942d
  - check: 전체 스위트 python3 -m pytest test_spawn.py -q — 152 passed,
      신규 실패 없음(기존 150건 그대로 통과)
    code_sha: 6a54d5a724d0f5c66ce647e3af01a0d0df16942d
---

# Implementation — 로스터 read observation point 수정 (issue #201, phase 2)

Proposal: [[roster-read-observation-point.md]](../proposals/roster-read-observation-point.md),
승인: 이슈 코멘트 `APPROVE issue-201/implementation` (single-account mode,
role-handoff contract v3 s19) + PR #202 merged (phase-1 산출물).

## What was done

승인된 제안의 "What will be done" 4개 항목을 그대로 이행했다 — write set
(`test_spawn.py` 단일 파일) 밖으로 나가지 않았고, `spawn.py`는 한 줄도
바꾸지 않았다(D1):

1. `Ledger::test_entry_carries_the_live_log_path`
   (`test_spawn.py:800-849`): `mock.patch.object(...)` 체인에
   `spawn.roster_register`용 call-through 스파이(`spy_roster_register`)를
   추가했다 — 원본 `roster_register`를 `orig_roster_register`에 저장해
   두고, 호출마다 `(key, dict(entry))`를 `roster_calls`에 담은 뒤 원본을
   그대로 호출한다. `json.loads(roster.read_text())["issue-9/execution-
   observation"]` 줄을 지우고, `roster_calls`에서 같은 키의 엔트리를 꺼내
   `roster_entry`로 썼다. 나머지 세 단언(`len(entries)`, `entries[0]["log"]
   == roster_entry["log"]`, 로그 파일 존재)은 손대지 않았다.
2. `IssueScopedPrompt::test_preparation_and_preamble_happen_once`
   (`test_spawn.py:940-1010`): 같은 call-through 스파이 패턴을 적용했다.
   `json.loads(roster.read_text())["issue-7/execution-observation"]["log"]`
   줄을 `roster_calls`에서 키 `"issue-7/execution-observation"`인 엔트리의
   `"log"`로 교체했다. 나머지 단언(프롬프트 중복 없음, workspace/branch
   준비 1회)은 손대지 않았다.
3. 두 테스트 모두 `spawn.ROSTER = roster` 재할당은 유지했다 — 실제
   `roster_register`/`roster_remove`가 여전히 임시 파일에 대해 온전한
   등록→삭제 사이클을 수행하도록(레포의 `runs/active.json`을 건드리지
   않도록) 하기 위해서다.
4. `spawn.py`는 변경하지 않았다.

## 검증 — 제안 "How you'll know it worked" 대응

survey에 기록된 대로, 이 저장소의 Bash 샌드박스에서 naive하게 돌리면
`rulebook_checkout`/`core_root`의 실제 git clone 시도가 저장소 경로 하위
쓰기 제약(git hook 템플릿 복사 거부)에 걸려 무관한 에러가 먼저 난다. 세
커맨드 모두 `TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE`를 유효한 로컬
체크아웃으로 가리킨 상태에서 실행해 실제 결과를 확인했다(D2 준수: 이
라우팅은 검증용 국지 조치이고 저장소에 반영하지 않았다 — 세 커맨드
실행 뒤 라우팅에 쓴 임시 `conftest.py`는 삭제하고 커밋에서 제외했다).

1. **개별 실행 1 — `test_entry_carries_the_live_log_path`:**
   ```
   $ python3 -m pytest test_spawn.py -k test_entry_carries_the_live_log_path -q
   .                                                                        [100%]
   1 passed, 151 deselected in 0.40s
   ```
2. **개별 실행 2 — `test_preparation_and_preamble_happen_once`:**
   ```
   $ python3 -m pytest test_spawn.py -k test_preparation_and_preamble_happen_once -q
   .                                                                        [100%]
   1 passed, 151 deselected in 0.43s
   ```
3. **전체 스위트:**
   ```
   $ python3 -m pytest test_spawn.py -q
   ........................................................................ [ 47%]
   ........................................................................ [ 94%]
   ........                                                                 [100%]
   152 passed in 12.72s
   ```
   이슈 본문의 기대치(개별 2건 각각 `1 passed`, 전체 `152 passed`, 기존
   150건 그대로 통과, 신규 실패 없음)와 정확히 일치한다. 이 세 결과를
   개별로 기록하는 이유는 이슈 자체가 "전체 스위트 에러 목록 diff만으로는
   부족하다"(#198의 검증 실패 원인)는 교훈에서 나왔기 때문이다 — 개별
   실행 결과를 각각 실측·기록해 같은 실수를 반복하지 않는다.

## Hunt (before phase-2 completion)

phase-1(PR #202, 승인된 proposal)에서 이미 rejected-alternative 3건
(no-op 몽키패치, `_session_log_path` 재계산, 로스터 비교 제거)을 조사해
Rationale에 기각 근거를 기록했다 — 이 세 대안 모두 요구사항 1-3이 명시적으로
경계한 실패 패턴(검증력 제거, 명명 규약 재하드코딩, 교차검증 소실) 중 하나에
해당해 채택하지 않았다. phase-2는 그 설계를 코드로 그대로 옮겼을 뿐 새 설계
결정이 없어 재-hunt 대상이 아니다 — phase-2 완료 시점의 확인은 위 §검증
1-3(실제 실행 결과)으로 갈음했고, 그 결과를 이 레코드의 `closed_checks:`에
기록했다.

## What did not work

None.

## Rationale for deviations

None — phase-2 실행은 승인된 제안의 "What will be done"을 그대로 따랐다.
검증 커맨드 실행 시 샌드박스의 `rulebook_checkout` 네트워크 제약(D2, survey
"샌드박스 확인 사항" 절)을 피하려고 `TOKENMAXXXER_RULEBOOKS`/
`TOKENMAXXXER_CORE`를 로컬 체크아웃으로 가리키는 임시 `conftest.py`를
검증 중에만 사용했는데, 이는 제안이 "How you'll know it worked"에서 이미
예상하고 명시한 라우팅 방법이지 새로운 설계 결정이 아니며, 커밋에는
포함하지 않았다.

## Doc-placement ladder (완료 항목)

- [x] env var / config / dependency / migration → handbook: 해당 없음 —
  새 환경변수·설정·의존성·마이그레이션 없음(제안 Constraints 그대로).
  검증 중 사용한 `TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE` 라우팅은
  저장소에 반영하지 않는 국지 조치(D2)라 handbook 대상이 아니다.
- [x] library-or-format 선택 / 시그니처·wire format 변경 →
  `docs/issue-201/decisions/`: 해당 없음 — 승인된 제안의 Rationale이 이미
  이 결정(call-through 스파이 vs no-op 몽키패치 vs 재계산 vs 비교 제거)을
  phase-1 proposal 문서에 기록했고, phase-2는 그 결정을 그대로 이행했을
  뿐 새 결정을 내리지 않았다.
- [x] benchmark/investigation 수치 → `docs/issue-201/reports/`: 완료 —
  위 §검증의 세 커맨드 실행 결과가 이 파일에 있다.
- [x] Phase 1 survey: `docs/issue-201/reports/implementation/survey.md`
  (PR #202로 이미 merge)
- [x] Phase 1 proposal: `docs/issue-201/proposals/roster-read-observation-point.md`
  (PR #202로 이미 merge)
- [x] Phase 2 record: `docs/issue-201/reports/implementation.md` (this file)
- [x] Tests: `test_spawn.py`

## Open findings

None.
