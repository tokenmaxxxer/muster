files:
- spawn.py
- test_spawn.py

## Request

이슈 #223(2026-08-03 감사 신규 high): 같은 (issue, role) 조합의 동시
스폰을 막는 클레임이 `_spawn_one()`이 담당하는 **주 스폰 경로**
(`main()`이 직접 호출하는 경로, spawn.py:2322)에는 없다. 재스폰 경로
(`_auto_respawn_check()`, spawn.py:1653-1664)에는 이미 원자적
O_CREAT|O_EXCL 클레임이 있는데, 그건 그 함수가 `_spawn_one()`을
부르기 **전에** 독자적으로 쥐는 클레임이라 `_spawn_one()` 자체에는
없다. 같은 이슈·역할을 두 번 spawn하면 두 세션이 같은 워크스페이스의
`.git/index`를 공유해 서로의 커밋을 파괴하고, 이벤트 스트림 offset을
밀어 미소비 이벤트를 건너뛰고, 로스터 항목을 덮어쓴다. 요구사항 3가지:
(1) 주 경로에도 재스폰 경로와 같은 계열의 클레임을 넣어 이미 살아
있으면 명확히 거부, (2) 죽은 세션이 남긴 stale 클레임은 정리 가능,
(3) 거부 메시지는 어느 세션(pid/시작 시각)이 잡고 있는지 알려준다.

## Constraints

- spawn.py 수정은 #218/#220 머지 후 착수, #221(워크스페이스 동기화)과
  조율해 순차 진행 — 셋 다 이미 main 에 머지 완료(survey.md 확인),
  착수 가능.
- `_spawn_one()`의 독스트링이 명시하는 설계 원칙("main() 과 drive() 가
  같은 몸통을 쓴다")을 지킨다 — 새 클레임은 `_spawn_one()` 자체에
  넣어 두 호출부(main() 직접 호출, 재스폰)가 자동으로 같이 보호받게
  한다. 호출부 각각에 따로 클레임을 심지 않는다.
- fork-전 pid 함정 재발 금지: bounded 분기(spawn.py:2593-2629)는
  `os.fork()` 후 부모가 `_await_bounded()`로 곧바로 리턴하고 곧
  종료한다(spawn.py:2610-2613) — 클레임에 fork 전 pid를 기록한 채로
  두면 부모 종료 순간 그 클레임이 죽은 pid를 가리켜 생존검사가
  stale로 오판한다(로컬 독립 검증에서 실측되고 "fork 직후 pid
  재기록"으로 해소된 전례). 새 구현은 fork 직후 자식 분기에서 pid를
  자기 자신의 것으로 다시 써야 한다.
- 워치독 루프 보호: `_auto_respawn_check()`는 `roster_watchdog()`의
  `for key, e in sorted(d.items())` 루프 안에서 죽은 엔트리마다
  호출된다(spawn.py:1456-1459) — 한 틱에 크래시 엔트리 여럿을 순회할
  수 있다. 새 클레임의 거부를 `sys.exit()`로 하면, 한 (issue,role)의
  클레임 충돌이 그 틱에 남은 무관한 다른 크래시 엔트리 처리를 전부
  막는다. 기존 `issue_workspace()`/`checkout_issue_branch()`의
  `sys.exit()`도 이미 같은 특성이 있어(#223이 새로 만드는 위험이
  아님) 완전히 새 계약을 만드는 대신, 클레임 충돌만은 값 리턴으로
  다뤄 워치독 루프가 다음 엔트리로 계속 진행하게 한다(Rationale
  참고).
- 클레임 파일은 `clean` 커맨드의 기존 형제-파일 글롭
  (`w.parent.glob(w.name + ".*")`, spawn.py:2250)에 자동으로 걸리는
  이름을 쓴다 — `clean` 쪽 코드는 건드리지 않는다.
- `_spawn_one()`/`issue_workspace()`/`checkout_issue_branch()`의
  기존 시그니처는 바꾸지 않는다 — `test_spawn.py`의 여러 기존 테스트
  (`IssueScopedPrompt`, `EventReporting` 등)가 이들을
  `mock.patch.object`로 그대로 대체해 호출부만 검사한다.
- 새 의존성·환경변수·마이그레이션 없음.

## Rationale

**클레임의 정체성 판정 방식 — 대안 A(rejected): 파일에 pid+ts를 쓰고
매번 `_alive(pid)`로 생존을 검사한다(기존 ROSTER/`_alive()`와 같은
방식) vs 대안 B(채택): O_CREAT|O_EXCL로 파일을 만들되, 내용은
pid+ts를 담아 유지한다.**

둘 다 "생존 여부는 결국 기록된 pid를 검사해야 안다"는 점에서 근본적으로
같은 메커니즘이다 — 진짜 갈림길은 pid-생존검사 기반 클레임 자체를 쓸지,
아니면 OS 가 프로세스 생사와 자동으로 묶어 주는 `fcntl.flock()`
어드바이저리 락으로 전환할지였다. 실제로 flock 방식을 진지하게
검토했다: `fork()`는 파일서술자를 복제하면서 같은 "open file
description"을 공유하므로, 부모가 fork 직후 락을 쥔 fd를 자식에게
물려주고 자신은 종료해도 락은 자식이 그 fd를 닫을 때까지(정확히 세션
종료 시점까지) 유지된다 — pid 재기록이라는 조작 자체가 필요 없고,
pid 재사용(stale 오판의 원인)도 OS 커널이 원천 차단한다. 웹 조사가
이 방향을 뒷받침한다: "만약 서비스가 PID 파일을 (그냥 쓰는 대신)
POSIX 락으로 쥔다면 pid 를 원자적으로 조회할 수 있다 — 단순 파일
기반 pid 저장보다 더 견고하다고 여겨진다"(trbs/pid 프로젝트 문서 및
PyPI 설명 — 기본 모드가 파일 내용이 아니라 `fcntl` 락 자체로 이미
떠 있음을 판정한다). 그럼에도 flock 방식을 **채택하지 않았다**:
(1) 이슈 #223 본문이 명시적으로 "재스폰 경로와 동일한 계열의 클레임
(O_EXCL 등)"을 요구한다 — 이 저장소는 이미 `.respawn-claim-{ts}`라는
검증된 O_EXCL 관용구를 갖고 있고(이슈 #132), #221 스카우트 브리프가
확인한 이 저장소의 house style("새 관용구를 발명하지 않는다")과도
맞는다. (2) flock 은 `subprocess.Popen()`의 `close_fds` 동작, 자식
프로세스로의 fd 상속 경계를 새로 검증해야 하는 표면을 늘린다 — 이번
수정의 실제 요구사항(주 경로에 빠진 게이트 하나를 넣는다)에 비해
과한 신규 표면이다. (3) pid 재사용으로 인한 stale 오판은 이미 ROSTER의
`_alive()`가 안고 있는, 이 저장소가 이미 받아들인 위험 수준이다(이슈
#139 이후 별다른 사고 없이 운영됨) — 새 클레임만 이 위험을 없애려고
다른 메커니즘을 쓰면 오히려 두 락 계열(O_EXCL 계열 vs flock 계열)이
공존하게 되어 일관성이 떨어진다. 그래서 O_CREAT|O_EXCL + pid/ts
기록 + `_alive()` 생존검사(대안 A와 실질적으로 같은 성격이지만
`.respawn-claim`과 파일-생성 규약을 공유) — 즉 대안 B를 채택한다.
fork-직후 pid 재기록은 이 채택안에서 **필수**로 남는다(위 Constraints
참고) — flock 이었다면 불필요했을 단계지만, house-style 일치를
우선한 트레이드오프로 받아들인다.

**클레임 충돌 시 실패 전달 방식 — 대안(rejected): 기존 사전검증
실패와 동일하게 `sys.exit()`로 하드 실패 vs 채택: `_spawn_one()`이
값(거부 사유 문자열을 포함한 비정상 rc)을 리턴하고 호출부가 판단한다.**
`sys.exit()`이 이 파일의 확립된 house style(#221 스카우트 브리프가
이미 정리)과 더 일관되고 구현도 단순하지만, survey.md 가 찾은
구조적 사실 — `_auto_respawn_check()`가 `roster_watchdog()`의 루프
안에서 크래시 엔트리마다 반복 호출된다는 것 — 때문에 기각한다:
클레임 충돌은 (이 이슈가 고치려는 바로 그 상황이므로) 드문 예외가
아니라 **정상적으로 자주 마주칠 케이스**다. 이런 흔한 케이스로
워치독 프로세스 전체가 죽어 같은 틱의 다른 무관한 크래시 엔트리들까지
처리를 놓치게 하는 건, 기존 `sys.exit()` 관용구가 원래 겨냥한
"드문 하드 실패"의 성격과 다르다. 값 리턴은 `main()` 경로에서도
그대로 프로세스 종료 코드로 전파되므로(`return _spawn_one(...)`,
spawn.py:2322) 사람이 보는 최종 동작은 동일하다 — 워치독 루프만
추가로 보호받는다.

## What will be done

1. `spawn.py`에 헬퍼 두 개를 추가한다(이름 예정,
   `_acquire_spawn_claim(work, issue, role)` /
   `_release_spawn_claim(claim_path, pid)` 형태):
   - 클레임 경로: `Path(str(work) + ".spawn-claim")` —
     `.respawn-claim-{ts}`와 같은 형제-파일 명명 계열, `clean`의
     기존 글롭에 별도 코드 없이 걸린다.
   - 취득: `os.open(path, O_CREAT | O_EXCL | O_WRONLY)`로 시도 →
     성공하면 `{"pid": os.getpid(), "ts": int(time.time())}`를 써서
     클레임 확보. `FileExistsError`면 기존 내용의 pid를 읽어
     `_alive(pid)` 확인 — 죽었으면 stale로 보고 `unlink` 후 1회
     재시도(자기 치유, 요구사항 2), 살아있으면 pid/ts를 담은 거부
     사유를 리턴(요구사항 3).
2. `_spawn_one()`에서 `issue is not None`일 때만
   (`work = issue_workspace(cwd, issue, role)` 직후,
   `checkout_issue_branch()` 호출 전) 클레임을 취득한다. 거부되면
   그 사유를 stderr에 출력하고 비정상 rc를 리턴한다(`sys.exit()` 아님
   — Rationale/Constraints 참고) — 워크스페이스 clone/checkout에
   들어가기 전에 빠르게 실패한다.
3. bounded 분기의 `os.fork()`(spawn.py:2609) 직후, 자식 분기
   (`child_pid == 0`, `os.setsid()` 이전)에서 클레임 파일의 pid
   필드를 자식 자신의 `os.getpid()`로 즉시 다시 쓴다 — ts는
   유지한다. 이게 fork-전-pid 함정의 실제 수정 지점이다.
4. 클레임 해제는 `roster_remove(roster_key)`가 이미 있는 지점
   (spawn.py:2754, `proc.wait()` 직후 — bounded/unbounded 공통 경로)
   에 나란히 추가한다. 이 지점에 닿지 못하고 프로세스가 죽는 경우
   (kill -9 등)는 클레임이 남는데, 그건 요구사항 2의 stale-정리
   경로(다음 취득 시도가 `_alive()`로 감지)와 `clean` 커맨드의 글롭
   정리가 이미 흡수한다 — `.respawn-claim`도 동일한 한계를 이미
   받아들이고 있다.
5. `main()`이 이제 `_spawn_one()`의 리턴값(비정상 rc)을 그대로
   프로세스 종료 코드로 전파하므로 별도 수정 불필요
   (`return _spawn_one(...)`, spawn.py:2322).
6. `test_spawn.py`에 새 테스트 클래스(`SpawnOneIssueRoleClaim` 류)를
   추가한다 — `AutoRespawnClaim.test_concurrent_watchdogs_do_not_double_respawn`
   (test_spawn.py:2344-2372)과 같은 패턴으로 `threading.Thread` 두
   개가 실제로 동시에 `_spawn_one()`(`issue_workspace`/
   `checkout_issue_branch`/`spawn_cmd`/`ensure_pushed`/
   `roster_register`는 기존 `IssueScopedPrompt`류 테스트처럼 모킹,
   `bounded=False`로 fork 우회)을 호출해 정확히 하나만 통과함을
   검증한다. 별도 테스트로: (a) 죽은 pid를 담은 기존 클레임 파일이
   있을 때 새 취득이 성공하는지(stale 정리), (b) 거부 사유 문자열에
   기존 클레임의 pid/ts가 들어있는지(요구사항 3), (c) `os.fork`를
   모킹해 자식 분기(리턴값 0)를 강제하고 클레임 파일의 pid가 자식
   pid로 재기록되는지(fork-후-재기록 회귀 방지 — 오늘 이 분기는
   테스트 커버리지 0건, survey.md 확인).

## Out of scope

- `drive()`는 여전히 빈 스텁이다 — 실제로 역할을 고르는 로직이
  없으므로 새 클레임과 상호작용할 세 번째 호출부가 없다. `drive()`가
  나중에 실 스폰 로직을 갖게 되면 `_spawn_one()`을 그대로 쓰는 한
  이 클레임을 자동으로 물려받는다(설계 원칙 그대로).
- `issue_workspace()`/`checkout_issue_branch()` 자체의 clone/fetch
  단계에서 일어날 수 있는 (더 드문) 동시성 경합은 다루지 않는다 —
  이슈 #223의 증상(3가지 전부)은 두 `claude` 세션이 동시에 **실행
  중**이어야 발생하며, 클레임은 그 실행 진입 직전(브랜치 체크아웃
  전)에 걸려 이를 막는다.
- `checkout_issue_branch()`의 기존 `sys.exit()`이 워치독 루프
  전체를 끝내는 특성은 이번 이슈로 새로 만드는 문제가 아니므로
  고치지 않는다(survey.md에 기록).
- ROSTER를 스폰-게이트로 재활용하는 방향, `fcntl.flock()` 기반
  클레임(Rationale에서 검토 후 기각)은 채택하지 않는다.

## How you'll know it worked

- `python3 test_spawn.py`(또는 해당 테스트 클래스만)를 돌려, 새
  concurrency 재현 테스트가 "정확히 하나만 `_spawn_one` 본체를
  통과한다"를 실제로 통과시킨다 — `AutoRespawnClaim`의 기존 동시성
  테스트와 같은 신뢰 수준(진짜 스레드로 재현, 모킹으로 우연히
  안 걸리는 결과가 아님).
- stale-클레임 정리 테스트와 거부 메시지 pid/ts 포함 테스트가 통과한다.
- fork-후 pid 재기록 테스트가 통과해, 이번 이슈가 지목한 함정이
  코드에 다시 들어오면 즉시 빨간불이 뜬다.
- `spawn.py`의 기존 회귀 스위트(`IssueScopedPrompt`, `EventReporting`,
  `Drive` 등 — `_spawn_one`/`issue_workspace`/`checkout_issue_branch`를
  이미 모킹해 쓰는 클래스들)가 전부 그대로 통과해, 시그니처 불변
  제약이 실제로 지켜졌음을 확인한다.
