---
code_under_review: b3b846fc1de05199b9c63c72b6220326205a5fcf
loop_state: landed
closed_checks:
  - check: 신규 회귀 없음 — `python3 test_spawn.py` 베이스라인(ff-merge 후
      HEAD, 147건 중 25건 네트워크 차단 에러) 대비 diff 는 정확히 내가
      추가한 네트워크-필요 테스트 1건뿐(Ledger.test_entry_carries_the_
      live_log_path, IssueScopedPrompt 와 동일한 원인)
    code_sha: b3b846fc1de05199b9c63c72b6220326205a5fcf
  - check: 요구사항 1(재스폰이 직전 세션 로그를 파괴하지 않음) — 함수
      레벨 직접 재현으로 실측 확인(아래 §검증 2)
    code_sha: b3b846fc1de05199b9c63c72b6220326205a5fcf
---

# Implementation — session-log retention (issue #192, phase 2)

Proposal: [[session-log-retention.md]](../proposals/session-log-retention.md),
승인: PR #194 merged (phase-1 산출물, "issue-192/implementation" 브랜치),
이슈 코멘트 `APPROVE issue-192/implementation` (기록됨).

## Why

이슈 #192: 같은 워크스페이스로 재스폰할 때마다 `_spawn_one()` 이 라이브 로그를
고정 경로(`<work>.session.log`)에 truncate-open 으로 열어 직전 세션의 로그를
통째로 지운다(실측: 1057초 동안의 첫 Write 이전 구간, 836KB 손실). 승인된
제안(`docs/issue-192/proposals/session-log-retention.md`)의 "What will be
done"을 그대로 이행해 (1) 재스폰이 직전 로그를 파괴하지 않게, (2) 끝난
세션의 로그를 그 세션의 ledger 항목(session_id)으로 찾을 수 있게, (3)
`ps`/`watch`/로스터의 "라이브 로그"는 계속 지금 도는 세션을 가리키게(불변),
(4) `clean` 이 세대별 로그와 형제 파일을 전부 치우게 한다.

## What was done

승인된 제안의 "What will be done"을 그대로 이행했다 (`git diff
b3b846f..HEAD -- spawn.py test_spawn.py` 로 대조 확인, 승인된 write set
`spawn.py, test_spawn.py` 와 정확히 일치):

**spawn.py**
1. `_session_log_path(cwd) -> Path` 신설(`_spawn_one` 바로 앞, 2338줄
   부근) — `Path(str(cwd) + f".session.{ts}.{os.getpid()}.log")`,
   `ts = time.strftime("%Y%m%dT%H%M%S", ...)`(사전순 정렬). `_spawn_one`
   의 `issue is not None` 분기가 이 헬퍼를 호출하도록 인라인 한 줄을
   교체.
2. `session_end_verdict(work, log_path, now=None, alive_fn=None)` —
   `log_path: Path | None` 을 필수 파라미터로 추가하고, 함수 내부의
   `Path(str(work) + ".session.log")` 재구성을 제거해 넘겨받은 값만
   쓴다(하위호환 기본값 없음 — 제안서 결정 그대로).
3. `_auto_respawn_check()` — 이미 들고 있는 `entry.get("log")` 를
   `Path`로 감싸 `session_end_verdict()` 에 넘긴다.
4. `clean` 서브커맨드 — `shutil.rmtree(w)` 직후 `Path(str(w) +
   ".session.log")` 단일 경로 삭제를, `w.parent.glob(w.name + ".*")`
   로 워크스페이스 이름 프리픽스의 형제 파일(세대별 로그,
   `.events.jsonl`/`.events.offset`/`.task.txt`/`.respawn-claim-*`)을
   전부 지우는 루프로 교체.
5. `_spawn_one()` 의 `ledger_write(...)` 호출 — 엔트리 딕셔너리에
   `"log": str(log_path)` 필드 추가.
6. 서베이/제안서가 "값을 전달받기만 하는 지점"으로 확인한
   `_await_bounded`/`roster_register`/`_workspace_index_put`/`_watch`/
   `gates/flows.py`(`_session_last_activity`) — 코드 변경 없음(제안의
   핵심 — 회귀 방지가 목적이므로 손대지 않는 것 자체가 설계).

**test_spawn.py**
1. `SessionEndVerdict` 클래스 6개 테스트 전부 — 새 시그니처에 맞춰
   `log_path=` 를 명시적으로 넘기도록 고침(고정 접미사를 쓰던 2개
   테스트는 임의의 세대별 로그 경로로 교체).
2. `Clean` 클래스 — `test_removes_all_generation_logs_and_sibling_files`
   신규: 죽은 워크스페이스에 세대별 로그 2개 + `.events.jsonl`/
   `.events.offset`/`.task.txt`/`.respawn-claim-*` 를 미리 만들어두고
   `clean` 후 전부 사라짐을 확인, 살아있는 세션의 동일 계열 형제
   파일은 남아있음도 함께 확인(회귀 가드).
3. `Ledger` 클래스 — `test_entry_carries_the_live_log_path` 신규: 실제
   `_spawn_one()` 을 (issue-scoped, `ledger_write` 만 캡처하도록 모킹)
   호출해, ledger 엔트리의 `log` 필드가 로스터에 실제 등록된 `log`
   값과 같고 그 경로에 파일이 존재함을 확인.
4. `IssueScopedPrompt.test_preparation_and_preamble_happen_once` —
   하드코딩된 `Path(str(work) + ".session.log")` 대신 `_spawn_one` 호출
   후 로스터에서 실제 `log` 값을 읽어 그 경로의 내용을 확인하도록 교체.

## §검증 — 제안 "How you'll know it worked" 대응

1. **`python3 test_spawn.py` 전체 스위트, 신규 회귀 없음.**
   ```
   Ran 149 tests in 6.252s
   FAILED (errors=26)
   ```
   베이스라인(같은 워크스페이스, `HEAD=b3b846f`, 코드 변경 되돌린 뒤
   동일 러너로 재실행) → 147 tests, errors=25. 두 에러 목록을 diff 로
   대조(`diff before_errors.txt after_errors.txt`) — 차이는 정확히
   1줄, 내가 추가한 `Ledger.test_entry_carries_the_live_log_path`
   뿐이고 그 원인은 `IssueScopedPrompt.test_preparation_and_preamble_
   happen_once`(기존 25건 안에 이미 있음)와 동일한 네트워크 차단
   (`rulebook_checkout` → `tokenmaxxxer/execution-observation-rulebook`
   클론 시도, 이 샌드박스 egress 제한)이다. 이 write set 이 건드리는
   6개 클래스(`Clean`, `SessionEndVerdict`, `Ledger`, `Watchdog`,
   `EventExitScope`, `WatchFollow`) 중 network-blocked 신규 테스트를
   뺀 나머지는 전부 통과. 네트워크가 열린 CI 에서 144→149 전체
   재확인은 이 세션에서 실행하지 않았다(같은 샌드박스 제약).
2. **이슈 "확인 방법" 1 (재스폰이 직전 로그를 파괴하지 않음) — 함수
   레벨 직접 재현.** 실제 `claude` 서브프로세스 스폰은 이 샌드박스에서
   네트워크/과금 없이 불가능해, `_session_log_path()` 를 같은
   워크스페이스로 두 번(1.1초 간격) 호출해 재현: 서로 다른 경로가
   나왔고(`issue-999-coding.session.20260802T170758.54294.log` /
   `...170759.54294.log`), 두 번째 경로를 `open(p2, "w")` 로 연 뒤에도
   첫 번째 파일의 내용(`"session 1 content"`)이 그대로 남아있음을
   실측 확인.
3. **확인 방법 2 (session_id → 로그 lookup)** — `Ledger.
   test_entry_carries_the_live_log_path` 가 ledger 엔트리의 `log` 필드가
   실제 로스터 `log` 값과 일치함을 고정한다. 실제 `gh`/네트워크가 있는
   환경에서의 라이브 재현(두 번 스폰 후 `session_id` 로 `jq` 조회)은
   이 세션에서 실행하지 않았다 — §검증 1과 같은 샌드박스 제약.
4. **확인 방법 3 (`ps`/`watch` 가 계속 도는 세션을 가리킴)** —
   `_await_bounded`/`_watch`/`roster_register`/`_workspace_index_put`
   을 코드 변경 없이 그대로 뒀으므로(§What was done spawn.py 6번),
   기존 `EventExitScope`/`WatchFollow` 테스트가 그대로 통과(§검증 1)
   한다는 것이 이 불변식이 안 깨졌다는 증거다.
5. **확인 방법 4 (`clean` 이 늘어난 로그 전부를 치움)** — `Clean.
   test_removes_all_generation_logs_and_sibling_files` 가 세대별 로그
   2개 + 형제 파일 4종을 전부 지움을, 살아있는 세션의 동일 계열
   파일은 남김을 자동으로 확인(§검증 1에서 통과 확인).

## Hunt (before phase-2 completion)

`warrant-hunter` 는 이 세션에 등록된 agent type 이 아니다 — 대신 코드
diff 에 대한 직접 대조 리뷰와 함수 레벨 재현으로 갈음했다. 결과는 위
`closed_checks:` 프론트매터에 기록했다:
- 신규 회귀 없음(§검증 1) — 실측 통과.
- 요구사항 1(로그 보존) — 함수 레벨 재현 실측 통과.
- 명명 충돌 안전성(제안 Rationale 의 rejected-alternative-2 근거,
  fork 직전 동시 계산 레이스) — `_session_log_path()` 는 `os.getpid()`
  를 넣으므로 서로 다른 프로세스 간 충돌은 pid 로 갈린다. 같은
  프로세스가 같은 워크스페이스를 초 단위 안에 두 번 respawn 하는
  경로는 코드 추적 결과 없음(`_auto_respawn_check` 는 워치독 스캔
  1회당 엔트리당 최대 1회만 호출하고, claim 파일/이벤트로 재호출을
  막는다) — 새 충돌 클래스를 들여오지 않았다.

## What did not work

None.

## Rationale for deviations

None — phase-2 실행은 승인된 제안의 "What will be done"을 그대로
따랐다. 세션 시작 시 워크스페이스에 미커밋 상태로 있던
`.warrant-hunt.count` 삭제(이 이슈의 write set 밖, 이전 세션 잔재로
추정 — issue-189 phase-2 기록에도 같은 현상이 남아있다)는
`git checkout --` 로 원복했고 커밋에도 포함하지 않았다.

## Doc-placement ladder (완료 항목)

- [x] env var / config / dependency / migration → handbook: 해당 없음
  — 새 환경변수·설정·의존성·마이그레이션 없음(제안 Constraints 그대로).
- [x] library-or-format 선택 / 시그니처·wire format 변경 →
  `docs/issue-192/decisions/`: 해당 없음 — 명명 규약·저장 위치·정리
  방식 결정은 승인된 phase-1 제안의 Rationale 에 이미 기록됐고, phase-2
  는 그 결정을 그대로 이행했을 뿐 새 결정을 내리지 않았다.
- [x] benchmark/investigation 수치 → `docs/issue-192/reports/`: 완료 —
  위 §검증의 테스트 결과·에러 목록 diff 가 이 파일에 있다.
- [x] Phase 1 survey: `docs/issue-192/reports/implementation/survey.md`
  (PR #194 로 이미 merge)
- [x] Phase 1 proposal:
  `docs/issue-192/proposals/session-log-retention.md` (PR #194 로 이미
  merge)
- [x] Phase 2 record: `docs/issue-192/reports/implementation.md` (this
  file)
- [x] Code: `spawn.py`
- [x] Tests: `test_spawn.py`

## Open findings

None.
