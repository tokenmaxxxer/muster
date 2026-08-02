---
code_under_review: ee0c74067102a57702d740b7657b385b29269875
loop_state: landed
closed_checks:
  - check: FailClosedDowngrade + Clean 격리 실행 — pytest test_spawn.py -k
      "FailClosedDowngrade or Clean" -v — 13 passed(기존 12건 + 신규 1건),
      실패 0
    code_sha: ee0c74067102a57702d740b7657b385b29269875
  - check: 전체 스위트 python3 -m pytest test_spawn.py -q — 135 passed, 18
      failed(survey가 실측해 둔 샌드박스 rulebook-clone 네트워크 아티팩트
      18건과 정확히 일치, 신규 실패 0, collected 152→153로 신규 테스트
      1건만큼 증가)
    code_sha: ee0c74067102a57702d740b7657b385b29269875
  - check: .warrant-hunt.count/.warrant-hunt.lock 수동 생성 후 git status
      --porcelain — 빈 출력(gitignore 적용 확인), 확인 후 파일 삭제
    code_sha: ee0c74067102a57702d740b7657b385b29269875
---

# Implementation — 세션 종결 처리 결함 3건 (issue #205, phase 2)

Proposal: [[session-end-defects.md]](../proposals/session-end-defects.md),
승인: PR #206 merged `de0f873`, APPROVE issue-205/implementation.

## Why

승인된 제안의 세 결함을 그대로 이행한다: (1) `fail_closed_downgrade()`가
커밋 유무보다 dirty 검사를 먼저 봐서 실제 커밋+PR이 있던 세션 2건이
`failed-no-commit`으로 오분류됐다, (2) `.warrant-hunt.count`(훅 상태
파일)가 gitignore에 없어 워크스페이스를 dirty하게 만든다, (3) `clean`의
형제 삭제가 디렉터리를 만나면 예외로 전체 순회가 멈춘다(현재는 잠복).

## What was done

승인된 제안의 "What will be done" 5개 항목을 그대로 이행했다 — write set
(`spawn.py`, `.gitignore`, `test_spawn.py`) 밖으로 나가지 않았다:

1. `spawn.py` `fail_closed_downgrade()`(`:1234-1267`) — 기존
   `if uncommitted: return "failed-no-commit"` 줄 바로 앞에
   `if new_commit and uncommitted: return "progressed-dirty-tree"` 한 줄
   추가. 재분류 우회층 없음. 그 아래 기존 로직은 무변경 —
   `new_commit=False`인 dirty tree(진짜 커밋 없음)와 `already_delivered`+dirty는
   그대로 `"failed-no-commit"`을 받는다.
2. `spawn.py:2594-2609` 호출부 — `downgraded != outcome` 로그 블록을
   `downgraded == "progressed-dirty-tree"` 여부로 분기: 새 값이면 "새 커밋은
   있지만 워크스페이스에 정리 안 된 변경이 남았다" 취지의 새 문구, 그 외
   (`"failed-no-commit"`)면 기존 문구 그대로.
3. `.gitignore`에 `.warrant-hunt.*` 한 줄 추가 — 추적 해제는 `1c230db`
   (issue-197 phase 1)가 이미 부수 효과로 끝냈음을 `git ls-files`로
   재확인(빈 결과), 남은 일은 gitignore 패턴 하나였다.
4. `spawn.py:2125-2127` — `sibling.unlink()` 앞에 `if sibling.is_file():`
   가드. 디렉터리 형제는 건너뛰고 다음 순회로 넘어간다.
5. `test_spawn.py`:
   - `FailClosedDowngrade::test_new_commit_dirty_tree_is_still_downgraded`
     (구 `:600-606`)를 `test_new_commit_dirty_tree_is_promoted_not_downgraded`로
     개명하고 기대값을 `"failed-no-commit"`에서 `"progressed-dirty-tree"`로
     변경 — 결함을 단언하던 테스트라 수정 허용 대상(제안 Constraints).
     `FailClosedDowngrade`의 나머지 8개 테스트(특히
     `test_already_delivered_with_dirty_tree_still_downgrades`)는 한 줄도
     건드리지 않았다.
   - `Clean`에 `test_directory_sibling_does_not_abort_the_clean_loop` 신규
     추가 — 죽은 워크스페이스 두 개(`issue-51-review`, `issue-52-review`)를
     만들고 첫 워크스페이스의 형제 글롭 안에 디렉터리(`.somedir/`, 안에 파일
     하나)와 파일(`.events.jsonl`)을 같이 둔 뒤 `clean` 실행 — 예외 없이
     끝나고, 두 워크스페이스 모두 삭제되고(다음 워크스페이스도 정상 처리됨을
     증명), 파일 형제는 지워지고, 디렉터리 형제는 가드만 추가했으므로 그대로
     남는다는 것을 단언. 기존 `Clean`의 2개 테스트는 무변경.

## 검증 — 제안 "How you'll know it worked" 대응

1. **격리 실행 — `FailClosedDowngrade` + `Clean`:**
   ```
   $ python3 -m pytest test_spawn.py -k "FailClosedDowngrade or Clean" -v
   ...
   test_spawn.py::FailClosedDowngrade::test_new_commit_dirty_tree_is_promoted_not_downgraded PASSED
   test_spawn.py::Clean::test_directory_sibling_does_not_abort_the_clean_loop PASSED
   ...
   13 passed, 140 deselected in 1.52s
   ```
   `FailClosedDowngrade` 9건 전부 통과 — 8건은 문구까지 그대로(
   `test_already_delivered_with_dirty_tree_still_downgrades`가 여전히
   `"failed-no-commit"`을 리턴받는 것으로 통과), 수정된 1건은 새 기대값
   `"progressed-dirty-tree"`로 통과. `Clean` 3건(기존 2 + 신규 1) 전부 통과.
2. **전체 스위트:**
   ```
   $ python3 -m pytest test_spawn.py -q
   ...
   18 failed, 135 passed in 6.94s
   ```
   survey(§"기존 테스트 베이스라인")가 이 세션에서 실측해 둔 베이스라인과
   정확히 일치 — 18건 실패 전부 `rulebook_checkout`/`core_root`의 실제
   `git clone` 시도가 샌드박스 git-hook-템플릿 복사 제약에 걸리는 것으로,
   `SystemExit: ... 룰북을 받지 못했다 ... cannot copy
   '.../commit-msg.sample'` 트레이스로 개별 확인했다(이슈-201 survey가 이미
   문서화한 것과 같은 클래스의 샌드박스 아티팩트, 이 결함 3건과 무관).
   `Ledger::test_entry_carries_the_live_log_path`/
   `IssueScopedPrompt::test_preparation_and_preamble_happen_once`(이슈-201
   회귀로 지목된 2건)도 개별 실행해 같은 트레이스로 확인 — 내 변경이 만든
   회귀가 아니라 동일한 샌드박스 아티팩트다. `collected`가 152(survey 실측
   베이스라인) → 153으로, 신규 테스트 1건만큼 늘었다(개명한 테스트는 개수를
   바꾸지 않는다).
3. **수동 확인 — `.warrant-hunt.*` gitignore:**
   ```
   $ touch .warrant-hunt.count .warrant-hunt.lock
   $ git status --porcelain -- .warrant-hunt.count .warrant-hunt.lock
   (빈 출력)
   $ rm -f .warrant-hunt.count .warrant-hunt.lock
   ```
4. **수동 확인 — `clean` 디렉터리 형제:** 위 §1의
   `test_directory_sibling_does_not_abort_the_clean_loop`가 이 항목을
   자동화된 형태로 이미 실행·확인한다(디렉터리 형제를 낀 워크스페이스와
   그 다음 워크스페이스 둘 다 정상 처리, 예외 없음) — 별도 수동 재현은
   중복이라 생략.

## Hunt (before phase-2 completion)

phase-1(PR #206, 승인된 proposal)의 Rationale이 이미 결함별 rejected
alternative를 각 1-2건씩(결함 1: 재분류 우회층 / dirty_tree bool 필드,
결함 2: 리터럴 파일명 한 줄, 결함 3: `shutil.rmtree`로 디렉터리 형제까지
재귀 삭제) 조사해 기각 근거를 기록해 뒀다 — phase-2는 그 승인된 설계를
코드로 그대로 옮겼을 뿐 새 설계 결정을 내리지 않아 재-hunt 대상이 아니다.
phase-2 완료 시점의 확인은 위 §검증 1-4(실제 실행·수동 확인 결과)로
갈음했고, 그 결과를 이 레코드의 `closed_checks:`에 기록했다.

## What did not work

None.

## Rationale for deviations

None — phase-2 실행은 승인된 제안의 "What will be done" 5개 항목을 그대로
따랐다. 스코프 초과 중단도, 제안이 명시한 대안으로의 교체도 없었다.

## Doc-placement ladder (완료 항목)

- [x] env var / config / dependency / migration → handbook: 해당 없음 —
  새 환경변수·설정·의존성·마이그레이션 없음(제안 Constraints 그대로).
- [x] library-or-format 선택 / 시그니처·wire format 변경 →
  `docs/issue-205/decisions/`: 해당 없음 — 승인된 제안의 Rationale이 이미
  이 결정들(직접 교정 vs 재분류 우회층, 와일드카드 vs 리터럴 gitignore
  패턴, 파일 가드 vs rmtree 재귀 삭제)을 phase-1 proposal 문서에 기록했고,
  phase-2는 그 결정을 그대로 이행했을 뿐 새 결정을 내리지 않았다.
- [x] benchmark/investigation 수치 → `docs/issue-205/reports/`: 완료 — 위
  §검증의 실행 결과가 이 파일에 있다.
- [x] Phase 1 survey: `docs/issue-205/reports/implementation/survey.md`
  (PR #206으로 이미 merge)
- [x] Phase 1 proposal: `docs/issue-205/proposals/session-end-defects.md`
  (PR #206으로 이미 merge)
- [x] Phase 2 record: `docs/issue-205/reports/implementation.md` (this file)
- [x] Code: `spawn.py`
- [x] Config: `.gitignore`
- [x] Tests: `test_spawn.py`

## Open findings

None.
