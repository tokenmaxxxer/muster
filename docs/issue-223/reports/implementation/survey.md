# Survey — issue #223: 같은 (issue, role) 동시 스폰을 막는 클레임이 주 스폰 경로에 없다

착수 시점 확인: 이슈 본문의 제약은 "spawn.py 수정 — #218/#220과 파일이
겹치므로 그들 머지 후 착수(이슈 #221 워크스페이스 동기화 건과는 조율해
순차로)"다. #218/#220은 이미 #221 단계에서 확인된 대로 main 에 머지
완료. #221 자체도 `03b444f`(Merge pull request #240 from
tokenmaxxxer/issue-221/implementation)로 이미 main 에 머지 완료 — 이
서베이는 그 뒤의 spawn.py(2860줄)를 기준으로 한다. 순차 조율 제약
충족, 착수 가능.

## 대상 코드: `_spawn_one()` (spawn.py:2511-2856), 그리고 그 두 호출부

`_spawn_one()`의 독스트링이 이미 설계 원칙을 명시한다(spawn.py:2516-2517):
"main() 과 drive() 가 같은 몸통을 쓴다 — 드라이버가 따로 스폰 경로를
들고 있으면 둘이 갈라지고, 갈라진 쪽이 조용히 게이트 하나를
빠뜨린다." 실제로는 `drive()`(spawn.py:1933-1945)가 아직 아무 것도
스폰하지 않는 빈 스텁이라, 오늘 `_spawn_one()`을 부르는 곳은 정확히
둘뿐이다:

1. `main()` 직접 호출 — `spawn.py <role> "<task>" --issue <n>` (spawn.py:2322,
   `bounded=a.issue is not None`).
2. `_auto_respawn_check()` — watchdog 의 자동 재스폰 경로
   (spawn.py:1678, `bounded=True` 고정).

## 결함 확인: 재스폰 경로에만 O_EXCL 클레임이 있다

`_auto_respawn_check()`(spawn.py:1611-1678)는 `_spawn_one()`을 부르기
**전에** 자기만의 원자적 클레임을 이미 갖고 있다(spawn.py:1653-1664,
이슈 #132에서 도입, 이슈 #223 본문이 인용하는 바로 그 메커니즘):

```python
claim_path = Path(str(work) + f".respawn-claim-{start_ts}")
try:
    fd = os.open(str(claim_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(fd)
except FileExistsError:
    return
```

그 위 주석(spawn.py:1653-1658)이 정확히 이슈 #223 이 말하는 위험을
이미 한 번 실측했다고 적어 둔다: "두 watchdog 프로세스가 동시에 이
지점에 도달하면 둘 다 통과한다(실측: warrant-hunter 리포트, 스레드
두 개로 재현)... 실제 락은 이 원자적 파일 생성 하나뿐이다." 이
클레임의 성질: **"이 특정 크래시(session_start_ts)의 재스폰 시도가
이미 청구됐는가"**를 묻는, 재시도-단위 마커다. pid 를 기록하지도
않고, 생존 여부를 검사하지도 않는다 — 같은 크래시에 대한 재스폰은
논리상 한 번만 필요하므로 생존 검사가 불필요하다.

반면 `main()`이 부르는 몸통(`_spawn_one()` 자체)에는 이 클래스의
검사가 전혀 없다. `_spawn_one()`은 `issue_workspace()`로 이슈+역할
결정 디렉터리를 얻고(spawn.py:2523, 아래 참고), `checkout_issue_branch()`로
브랜치를 갈아탄 뒤(spawn.py:2524), bounded 경로면 바로
`os.fork()`(spawn.py:2609)로 들어간다 — 그 사이 어디에도 "이
(issue,role) 이 이미 살아 있는가"를 묻는 코드가 없다. `roster_register()`
호출(spawn.py:2630)은 Popen 이후에 일어나는 **사후 기록**일 뿐,
스폰을 막는 게이트가 아니다.

**재현 가능한 실패 경로**: 사람(또는 오케스트레이터)이
`spawn.py implementation "..." --issue 223`를 두 번 연속 호출하거나,
watchdog 이 크래시로 판정해 재스폰을 시도하는 바로 그 순간 같은
(issue, role)로 직접 호출이 겹치면, 두 프로세스 모두 `_spawn_one()`을
통과해 같은 워크스페이스에 두 번째 `claude` 세션을 띄운다. 이슈 본문의
증상(같은 `.git/index` 공유, 이벤트 offset 상호 잠식, 로스터 항목
상호 덮어쓰기)은 정확히 이 지점에서 발생한다 — 셋 다 두 세션이
**동시에 실행 중**이어야만 일어나는 증상이지, `issue_workspace()`/
`checkout_issue_branch()`의 clone/checkout 단계 자체의 경합은 아니다.

## 인접 인프라: 이미 있는 두 락/생존검사 메커니즘

1. **ROSTER (`runs/active.json`, spawn.py:1275-1323)** — 키
   `issue-{issue}/{role}`(spawn.py:2589)로 pid/issue/role/ts/work/log 를
   기록한다. `_roster_locked()`가 `fcntl.flock`으로 프로세스 간
   load-mutate-save 를 직렬화한다(이슈 #139, `RosterConcurrency` 테스트로
   검증됨 — test_spawn.py:2435-2467). `_alive(pid)`(spawn.py:1303-1308,
   `os.kill(pid, 0)`)로 생존 여부를 판정하고, `roster_ps()`가 죽은
   엔트리를 "DEAD(정리됨)"으로 표시한다. **다만 이 등록은 항상
   `proc.pid`(Popen 이후의 실 세션 pid)로, 스폰을 막는 사전 게이트가
   아니라 사후 관측용 기록이다** — 오늘 이 저장소의 어떤 코드도
   ROSTER 를 "이미 떠 있으면 거부"에 쓰지 않는다.
2. **`.respawn-claim-{ts}`** — 위에서 다룸. `clean` 커맨드
   (spawn.py:2246-2252)가 워크스페이스 삭제 시 `w.parent.glob(w.name + ".*")`로
   형제 산출물을 전부 쓸어간다 — 새 클레임 파일도 이 글롭에 자동으로
   걸린다(접미사만 다르면 됨, 코드 변경 불필요).

## 알려진 함정 (이번 이슈 착수 프롬프트가 명시): fork-전 pid 기록

`_spawn_one()`의 bounded 분기(spawn.py:2593-2629)는 `os.fork()` 뒤
부모(`child_pid > 0`)가 `_await_bounded()`로 즉시 리턴한다(spawn.py:2610-2613) —
이 리턴값은 CLI 프로세스의 종료값이 되므로, `main()` 경로에서는 fork
직후 부모가 곧 죽는다. 자식만 `os.setsid()` 이후 실제 세션이 끝날
때까지 살아 있다가 `roster_remove()`→`os._exit()`로 마감한다
(spawn.py:2851-2855). **클레임을 fork 전에 기록한 pid(부모 자신의
pid, `os.getpid()`)로 써 두면, 부모가 죽는 순간 그 클레임은 죽은
pid 를 가리키게 되어 생존검사(`_alive`)가 "stale" 로 오판한다** —
실제로는 자식이 세션을 계속 몰고 있는데도. 이번 착수 프롬프트가
지목하는 대로, 이 실패는 로컬 독립 검증에서 이미 한 번 관측되고
"fork 직후 pid 재기록"으로 해소된 전례가 있다 — 새 구현은 같은 함정을
반복하면 안 된다.

## 클레임 거부 시 호출부별 실패 처리 차이 (신규 발견, 설계에 영향)

`_spawn_one()`의 기존 사전 검증 실패(`issue_workspace()`/
`checkout_issue_branch()`의 origin 없음, clone 실패, checkout 실패 등)는
전부 `sys.exit(...)`로 하드 실패한다(spawn.py:2374, 2399, 2450 등) —
이 파일의 기존 관용구(#221 스카우트 브리프가 이미 확인: "하드 실패는
sys.exit, 재시도 가능한 실패는 stderr 로그 후 조용히 리턴"). 그런데
`_spawn_one()`의 두 호출부는 실패 시 영향 범위가 다르다:

- `main()` 경로는 그 자체로 하나의 CLI 프로세스이므로, `sys.exit()`은
  그 프로세스 하나만 끝낸다 — 안전.
- `_auto_respawn_check()`는 `roster_watchdog()`의 `for key, e in
  sorted(d.items())` 루프(spawn.py:1456) **안에서** 죽은 로스터
  엔트리마다 호출된다(spawn.py:1459) — 한 워치독 프로세스가 크래시한
  엔트리 여러 개를 한 틱에 순회할 수 있다는 뜻이다. 이 루프 안에서
  `_spawn_one()`이 새 클레임 충돌로 `sys.exit()`하면, 그 틱에 남은
  다른 크래시 엔트리들이 전부 처리되지 않고 워치독 프로세스 자체가
  끝난다.

이건 이미 오늘도 존재하는 특성이다(`checkout_issue_branch()`의 기존
`sys.exit()`도 워치독 루프 도중 같은 영향을 준다) — #223 이 새로
만드는 위험이 아니다. 워치독은 10-15분 간격으로 반복 호출되므로
(spawn.py:1442 독스트링), 놓친 엔트리는 다음 틱에 다시 잡힌다 —
관찰-전용 계약(이슈 #132/#135) 자체가 이미 "다음 틱이 다시 본다"는
전제 위에 서 있다. 다만 이 사실은 새 클레임의 실패 처리 방식(하드
sys.exit vs 값 리턴)을 고를 때 참고해야 하는 실제 트레이드오프라
proposal 의 Rationale 에 넘긴다.

## 테스트 현황

`test_spawn.py`에 `AutoRespawnClaim`(2278-2392) 클래스가 이미
respawn-claim 의 정확한 회귀 재현 패턴을 갖고 있다 —
`test_concurrent_watchdogs_do_not_double_respawn`(2344-2372)이
`threading.Thread` 두 개로 `_auto_respawn_check()`를 동시에 불러
정확히 하나만 `_spawn_one`(모킹됨)에 도달함을 검증한다. **하지만
`_spawn_one()`의 bounded 분기(`os.fork()` 포함, spawn.py:2609)는
오늘 어떤 테스트에서도 `bounded=True`로 호출된 적이 없다** —
`grep -n "bounded=True"`는 spawn.py:1678 하나만 잡는다(정의부),
test_spawn.py 에는 0건. `IssueScopedPrompt`/`EventReporting`류 기존
테스트는 전부 `_spawn_one(..., issue=N)`을 `bounded` 인자 없이
불러(기본값 False) fork 를 우회한다(예: test_spawn.py:1211, 1365,
1420). fork-후-pid-재기록 경로는 이번 이슈가 처음으로 테스트를
요구하는 코드 경로다.

## 범위(write set) — 실제로 건드릴 파일

- `spawn.py` — `_spawn_one()`에 (issue,role) 클레임 취득/해제/fork-후
  재기록 추가.
- `test_spawn.py` — 새 클레임의 동시성 회귀 테스트(threading 재현,
  `AutoRespawnClaim`과 같은 패턴), stale 클레임 정리 테스트, 거부
  메시지 내용 검증.

새 의존성·환경변수·마이그레이션 없음 — handbook 갱신 대상 없음
(docs/handbooks/operations.md·on-the-record.md 확인, 클레임/로스터
관련 기존 문서화 없음).

## 스카우트 스킵 판단 (scout-directive)

이 이슈는 두 스킵 조건 중 "순수 버그픽스"에 해당한다: 기존에 이미
설계·구현되어 실전 검증된 메커니즘(`.respawn-claim-{ts}`, 이슈
#132)을 이슈 본문이 명시적으로 "재스폰 경로와 동일한 계열의 클레임
(O_EXCL 등)"이라고 지목하며, 그 계열을 주 경로에도 넣으라고
요구한다 — 새로운 제품 방향이나 사용자 대면 설계 결정이 아니라, 이미
결정된 메커니즘을 놓친 경로에 마저 적용하는 일관성 수정이다. 그럼에도
불구, 이 서베이가 찾은 gap(주 경로 무방비, fork-pid 함정, 워치독 루프
영향)을 근거로 클레임의 구현 방식(O_EXCL+pid 생존검사 vs flock)만은
가볍게 실측 조사했다 — 결과는 proposal.md 의 Rationale 에 있다
(WebSearch 1건, `Sources:` 포함). product-shaped 조사(카테고리
best-in-class 비교)는 대상이 없다 — 사용자가 보지 못하는 내부
오케스트레이션 프리미티브라 비교할 외부 제품이 없다(#221 스카우트
브리프의 동일 판단과 같은 근거).
