files: spawn.py, test_spawn.py

## Request

같은 워크스페이스로 재스폰(phase 1→2 승인, 미커밋 이어받기, watchdog 자동 재스폰)할
때마다 `_spawn_one()` 이 라이브 로그를 고정된 한 경로(`<work>.session.log`)에
truncate-open 으로 열어, 직전 세션의 로그를 통째로 지운다. 그 결과 "세션 시간의
91%(첫 Write 전 구간)에 무슨 일이 있었나"를 세션이 끝난 뒤 다시 물을 수 없다.
요구사항 1-4: (1) 재스폰이 직전 로그를 파괴하지 않는다, (2) 끝난 세션의 로그를 그
세션의 원장 항목(session_id)으로 찾아갈 수 있다, (3) `ps`/`watch`/로스터의 "라이브
로그"는 계속 지금 도는 세션을 가리킨다 — `_await_bounded` 의 stall 판정이 그 파일
크기 변화를 쓴다, (4) `clean` 이 늘어난 로그와 형제 산출 파일을 전부 치운다. D1(로그
보존까지만, 서베이 속도 조사는 별건) · D2(새 계측 없음, 보존만) · D3(진행중 ETA 범위
밖)는 확정 사항으로 그대로 둔다.

## Constraints

- D1-D3 를 뒤집지 않는다.
- 새 의존성·새 환경변수·마이그레이션 없음(순수 파일 경로/정리 로직 변경).
- `_await_bounded` 의 stall 판정, `roster_register`/`_workspace_index_put` 의
  최신-로그-포인터 갱신 매커니즘, watchdog 의 observe-only 계약(이슈 #90/#132) —
  기존 계약을 유지한 채 위에 얹는다. 특히 요구사항 3(라이브 로그가 지금 도는 세션을
  계속 가리킴)을 깨는 변경은 금지.
- 기존 `test_spawn.py` 스위트(144건)를 이 write set 이 건드리는 6개 클래스(Clean,
  SessionEndVerdict, Ledger, Watchdog, EventExitScope, WatchFollow) 기준으로 통과
  유지 — 서베이 확인: 이 6개는 현재 샌드박스에서 이미 깨끗이 통과하는 클린
  베이스라인이다.

## Rationale

**명명 규약 — 채택: 타임스탬프+PID 복합 접미사. Rejected alternative 1: PID 단독
접미사, rejected alternative 2: 이벤트 카운터 기반 세대번호.** 서베이 스카웃
(scout-brief.md)에서 확인: 재시작 간 파일 겹침 방지의 표준 관행은 타임스탬프 포함
명명이고, logrotate 류는 그 타임스탬프가 사전순 정렬 가능해야 한다고 명시한다.
**Rejected alternative 1 — PID 단독 접미사**(`.session.<pid>.log`): 이 저장소 안에
이미 선례(`adhoc/{role}/{os.getpid()}` 로스터 키)가 있어 구현이 가장 단순하지만,
스카웃이 찾은 자료가 "PID 포함은 사실상 표준(타임스탬프)에서 벗어난다"고 명시 —
사람이 디렉터리를 훑을 때 생성 순서를 알 수 없어 rejected. **Rejected alternative 2 —
`events.jsonl` 의 `session-start` 이벤트 개수를 세어 세대번호를 매기는 방식**
(`.session.N.log`): `log_path` 는 `_spawn_one` 이 `os.fork()` 하기 **전**에 계산되고,
이 워크스페이스에 대한 이번 세션 자신의 `session-start` 이벤트는 fork **후**(자식
프로세스, setsid 이후)에야 append 된다(spawn.py 2422-2455줄) — 그래서 두 프로세스가
fork 직전 거의 동시에 카운트를 읽으면 같은 N 을 계산해 같은 로그 파일에 동시에 쓰는
충돌이 가능하다. 이 저장소는 이미 동시 watchdog 재스폰 레이스를 실측·문서화하고
O_CREAT|O_EXCL 락으로 막아뒀다(1583-1594줄) — 카운터 방식은 그 레이스 클래스를 로그
파일 경로 계산에도 새로 들여오는 것이라 rejected. 채택안(타임스탬프+PID)은 정렬
가능성(must-be)과 충돌 안전성(이 저장소의 기존 패턴)을 동시에 만족하고, 추가 파일
읽기도 없다.

**요구사항 2 저장 위치 — 채택: `ledger.jsonl` 엔트리에 `log` 필드 추가. Rejected
alternative: 파일명에 session_id 인코딩(세션 종료 후 rename).** `session_id` 는
세션 프로세스가 끝나야 `result` 이벤트로 알 수 있는 값이라(2587줄) 로그를 열 때(세션
시작 시점) 파일명에 넣을 수 없다 — 세션 종료 후 파일명을 rename 하는 방식도
가능하지만, `_await_bounded` 가 도는 동안 파일 크기로 stall 을 판정하는 그 순간의
경로가 rename 으로 사라지면 안 된다(요구사항 3과 정면 충돌) — 그래서 rejected. 대신
`ledger_write()` 호출부는 이미 같은 스코프에 `log_path` 변수를 들고 있으므로, 그
값을 ledger 엔트리에 한 필드로 적는 쪽이 파일 재명명 없이 "session_id → 로그
위치"를 바로 잇는다. D2 저촉 여부: 이건 새 계측이 아니라 이미 계산된 값을 이미 쓰고
있는 append-only 기록에 한 줄 더 적는 것 — "문제는 수집이 아니라 보존"이라는 D2 의
취지 그대로다.

**`clean` 의 형제 파일 정리 — 채택: 워크스페이스-이름 프리픽스 글롭. Rejected
alternative: 접미사 하드코딩 나열.** 지금 정확히 `.session.log` 하나만 지우는 게
이슈의 문제(요구사항 1의 결과로 로그가 여러 개로 늘면 형제 파일 누락 클래스가 세대
수만큼 넓어짐)다. `.events.jsonl`/`.events.offset`/`.task.txt`/`.session.*.log` 를
하나씩 나열하는 대안도 가능하지만, 서베이에서 `.respawn-claim-<ts>` 락 파일(1589줄)
까지 이미 같은 계열로 새고 있는 걸 확인했다 — 나열식은 다음에 접미사가 하나 더
생기면 또 빠뜨리므로 rejected. `w.parent.glob(w.name + ".*")` 로 워크스페이스
디렉터리와 이름이 같은 프리픽스의 형제 파일을 전부 잡는 쪽이 이 누락 클래스 자체를
없앤다(logrotate 의 글롭 기반 정리 관행과 같은 방향).

## What will be done

**spawn.py**
- `_spawn_one()`(2398-2399줄 부근): `issue is not None` 분기의 로그 경로를 세션마다
  고유하게 만드는 작은 헬퍼로 뺀다 — 예: `_session_log_path(cwd) -> Path`,
  `Path(str(cwd) + f".session.{ts}.{os.getpid()}.log")` (`ts` 는 사전순 정렬되는
  `time.strftime` 포맷). 헬퍼로 빼는 이유는 단일 호출부라도 단위 테스트가 실제
  서브프로세스 기동 없이 명명 규약만 검증할 수 있게 하기 위함 — 새 추상화가 아니라
  기존 인라인 한 줄을 이름 붙여 테스트 가능하게 만드는 것.
- `session_end_verdict()`(1184-1226줄): 내부에서 `.session.log` 를 재구성하지 않고
  `log_path: Path | None` 파라미터를 받아 그 값을 쓰도록 시그니처를 바꾼다.
- `_auto_respawn_check()`(1552줄): 이미 들고 있는 `entry.get("log")` 를
  `session_end_verdict()` 호출에 넘긴다.
- `clean` 서브커맨드(2115-2120줄): `shutil.rmtree(w)` 직후 `w.parent.glob(w.name +
  ".*")` 로 남은 형제 파일(세대별 로그, `.events.jsonl`, `.events.offset`,
  `.task.txt`, `.respawn-claim-*` 등)을 전부 순회해 지운다.
- `_spawn_one()` 의 `ledger_write(...)` 호출(2585-2594줄 부근): 엔트리 딕셔너리에
  `"log": str(log_path)` 필드를 추가한다.
- `_await_bounded()`, `roster_register()`, `_workspace_index_put()`, `_watch()`,
  `gates/flows.py` 의 `_session_last_activity()` — 서베이에서 확인한 대로 이미
  로스터/워크스페이스-인덱스에서 그때그때의 `log_path` 값을 읽기만 하므로, 위 변경만
  으로 자동으로 새 규약을 따라간다. 코드 변경 없음(회귀 방지가 목적이므로 손대지
  않는 것 자체가 이 제안의 핵심 — 건드릴수록 요구사항 3 회귀 위험이 커진다).

**test_spawn.py**
- `SessionEndVerdict` 클래스(1380-1454줄): 새 시그니처에 맞춰 각 테스트가 `log_path=`
  를 명시적으로 넘기도록 고친다(하위호환 기본값 없이 — 유일한 실제 호출부도 항상
  넘기므로).
- `Clean` 클래스(1183-1241줄): 죽은 워크스페이스에 세대별 로그 2개 이상 +
  `.events.jsonl` + `.task.txt` 를 미리 만들어두고, `clean` 후 전부 사라졌는지
  확인하는 케이스를 추가. 기존 "살아있는 세션은 남긴다" 케이스는 그대로 유지.
- `Ledger` 클래스(786-798줄) 또는 `_spawn_one` 을 이미 exercise 하는 자리에, ledger
  엔트리의 `log` 필드가 실제 `log_path` 와 같은지 확인하는 케이스를 추가.
- `IssueScopedPrompt.test_preparation_and_preamble_happen_once`(933-940줄): 하드코딩된
  `Path(str(work) + ".session.log")` 대신, `_spawn_one` 호출 후 로스터에서 실제
  `log` 값을 읽어와 그 경로의 내용을 확인하도록 고친다 — 새 명명 규약을 테스트에
  다시 하드코딩하지 않기 위함.

## Out of scope

- D1/D2/D3 가 범위 밖으로 못박은 것(서베이 속도 원인, 새 계측, 진행중 ETA) — 전혀
  건드리지 않는다.
- `_await_bounded`, `roster_register`, `_workspace_index_put`, `_watch`,
  `gates/flows.py` 의 로직 변경 — 위 Rationale/What-will-be-done 에서 설명한 대로
  이미 파라미터로 값을 전달받으므로 변경 불필요, 그리고 건드리는 것 자체가
  요구사항 3 에 불필요한 회귀 위험을 더한다.
- `runs/` 아래 다른 정리 정책(보존 기간, 압축, 회전 개수 제한) — 이슈에 없고 D1 범위
  밖.
- `IssueScopedPrompt.test_preparation_and_preamble_happen_once` 를 포함한 25건의
  네트워크 차단 에러(`require_board`→`rulebook_checkout` 이 실제 GitHub 클론을
  시도)를 이 이슈에서 고치지 않는다 — 이번 write set 과 무관한 기존 환경 제약이다.

## How you'll know it worked

1. `python3 test_spawn.py` — 전체 스위트 실행. 이 write set 이 건드리는 6개 클래스
   (`Clean`, `SessionEndVerdict`, `Ledger`, `Watchdog`, `EventExitScope`,
   `WatchFollow`)와 갱신되는 `IssueScopedPrompt.test_preparation_and_preamble_
   happen_once` 는 통과해야 한다. 나머지 네트워크 차단 24건은 이 변경과 무관하게
   이 샌드박스에서 이미 에러였다는 서베이의 베이스라인과 비교해 신규 회귀가 없는지
   확인한다(가능하면 네트워크가 열린 환경/CI 에서 전체 144건 통과도 확인).
2. 이슈의 "확인 방법" 그대로 재현: 같은 워크스페이스로 두 번 스폰 후, 첫 세션의
   로그가 파괴되지 않고 남아 있는지(요구사항 1), 그 로그를 `ledger.jsonl` 의
   `session_id` 로 찾아갈 수 있는지(요구사항 2, `jq 'select(.session_id=="...")'`
   식으로), 그동안 `spawn.py ps` 와 `spawn.py watch --issue <n>` 가 계속 **두 번째
   (도는)** 세션을 가리키는지(요구사항 3) 손으로 확인한다.
3. `spawn.py clean` 을 죽은 워크스페이스(세대별 로그 여러 개 + `.events.jsonl` +
   `.task.txt` 보유)에 돌려, 워크스페이스 디렉터리뿐 아니라 형제 파일이 전부
   사라지는지 확인한다(요구사항 4) — 자동화된 케이스는 위 `Clean` 테스트가 커버.
