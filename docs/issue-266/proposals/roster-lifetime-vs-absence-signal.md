files:
- spawn.py
- test_spawn.py
- docs/issue-224/decisions/watch-crash-exit-code.md

## Request

#266(신청자 jjongkwann): `spawn.py watch --follow`가 정상 종료 중인 세션을 크래시로 오보하는 결함(#224 관찰 finding). `_spawn_one()`의 후처리 꼬리(실제 `git push`, 게이트/소유권 리포트, `classify`, `ledger_write`) 동안 명부(roster) 엔트리가 이미 지워져 있어, 동시 실행 중인 `--follow`가 "엔트리 없음"을 사망으로 오판해 `WATCH_CRASH_RC`를 리턴한다. 이슈가 제시한 두 후보 — (a) 명부 삭제를 session-end 기록 뒤로 이동, (b) 엔트리 부재를 사망 신호에서 제외 — 중 하나를 트레이드오프와 함께 선택하는 phase 1 제안. 구현은 phase 2.

## Constraints

- `_watch(issue, role, stall_timeout_min, follow=False) -> int` 시그니처·반환형 불변.
- #224가 랜딩한 session-end 우선 드레인 순서, `WATCH_CRASH_RC = 2` 상수, `wrapper_pid` 필드는 그대로 유지 — 이 이슈는 사망 판정의 첫째 갈래(`roster_entry is None`)와 명부 엔트리 수명만 다룬다(이슈 본문 요구 3).
- 회귀 테스트는 엔트리-부재 꼬리 상태(session-end 미기록 + 명부 비어 있음 + 프로세스는 후처리 중)를 실제로 구성해 수정 전 실패(red) → 수정 후 통과(green)를 증명해야 한다(이슈 본문 요구 2).
- phase 1이므로 이 문서는 제안뿐이다 — spawn.py/test_spawn.py에는 어떤 코드 변경도 없다.

## Rationale

**대안 (a)(rejected) — `roster_remove(roster_key)`(spawn.py:2995)를 `_append_event(..., "session-end", ...)`(spawn.py:3097) 뒤로 옮겨, 명부 엔트리 수명이 후처리 꼬리(`ensure_pushed`의 실제 `git push`, 게이트/소유권 리포트, `classify`, `ledger_write`) 전체를 덮게 한다.** 이슈 제목이 지목한 근본 원인(삭제가 기록보다 먼저 실행)을 문자 그대로 고치고, `_watch`의 사망 판정 조건(:1903)은 전혀 안 건드리므로 진짜 크래시에서 `WATCH_CRASH_RC`가 즉시 뜨는 기존 신호도 그대로 유지된다 — 장점은 분명하다.

기각 근거: 같은 명부 키를 지우는 호출부가 `_spawn_one` 말고 둘 더 있고(survey.md), 둘 다 `wrapper_pid`가 아니라 이미 죽어 있는 `pid`(claude 서브프로세스)로 생사를 판정한 뒤 무조건 `roster_remove`를 부른다 — `roster_kill()`(:1909-1924, 사람이 `spawn.py kill`로 호출, dead 분기가 무조건 `roster_remove(key)`를 부름, :1921-1923)과 `roster_ps()`(:1336-1356, `spawn.py ps` 조회가 부수효과로 dead 엔트리를 전부 지움, :1355)다. `_spawn_one` 자신의 삭제 시점만 미뤄도, 같은 후처리 꼬리 도중 사람이 `spawn.py kill`이나 `spawn.py ps`를 그 세션에 대해 실행하면(예: "느려 보이는데 죽었나" 확인차 ps를 돌리는 흔한 운영 동작) 두 함수 중 하나가 똑같은 키를 먼저 지워, `_watch --follow`의 손 안 댄 `roster_entry is None` 갈래가 그대로 다시 켜진다 — 이슈가 "이동이 roster_kill, flows_payload 등 다른 소비자에 주는 영향을 검토할 것"이라고 못박은 지점이 실제로 걸린다. 완전히 닫으려면 `roster_kill`·`roster_ps` 두 함수도 `wrapper_pid` 기준으로 바꿔야 하는데, 그건 한 줄 이동이 아니라 세 호출부 + 대응 테스트로 write set이 넓어지는 별도 설계 결정이고, 이슈 본문은 이걸 "검토"로만 위임했지 "같이 고쳐라"로 요구하지 않았다. considered and rejected: 이슈가 명시적으로 요구한 자체 검토가 바로 이 결합(coupling)을 드러내고, 그 결합을 실제로 끊으려면 이번 이슈의 스코프(요구 3: "첫째 갈래와 엔트리 수명"만)를 넘어선다.

**대안 (b)(adopted) — `_watch()`의 사망 판정(spawn.py:1903)에서 `roster_entry is None` 갈래를 뺀다: 엔트리 부재는 "불명, 스톨 안전망까지 계속 대기"로 처리하고, 엔트리가 있고 `wrapper_pid`가 죽어 있을 때만 크래시로 본다.**

채택 근거 셋:
1. **결합이 없다.** `_spawn_one`(:2995)·`roster_kill`(:1923)·`roster_ps`(:1355) 세 삭제 호출부를 하나도 안 건드린다 — 판정부 한 곳(spawn.py:1903)과 그 테스트만 바뀐다. 대안 (a)가 만드는 3-함수 결합 문제 자체가 존재하지 않는다.
2. **이 파일 자신의 비용 비대칭과 일치한다.** spawn.py:1819의 기존 주석이 "스폰이 리턴했다"와 "세션이 끝났다"를 혼동하는 걸 "이 저장소가 가장 비싸게 치는 실패"라고 이미 못박아 뒀다 — 부재를 곧장 사망으로 읽지 않고 "불명 → 계속 대기"로 완화하는 쪽이 그 값어치와 같은 방향이다.
3. **업계 선례와 일치한다(scout-brief.md).** 우아한 종료 도중 헬스체크가 응답 없음을 곧장 사망으로 해석해 오탐을 내는 건 인정된 실패 계열이고, 그 대응으로 "등록 해제를 정리 완료 뒤로 미룬다"(≈ 대안 a)와 "장애 탐지기는 원래 불완전하니 무응답/부재를 확정 사망이 아니라 불명으로 다룬다"(≈ 대안 b) 둘 다 실제 관행으로 확인된다 — 우열이 정해진 카테고리가 아니라, 이 저장소의 결합도 구조가 (b) 쪽 비용을 더 낮게 만든다.

비용(정직하게 남긴다): 명부 엔트리가 (예: `roster_ps`/`roster_kill`에 의해, 또는 `roster_register` 호출 전 극히 짧은 창에서) 실제로 사라진 채로 세션이 진짜 크래시하면, `--follow`는 더 이상 즉시 `WATCH_CRASH_RC`를 리턴하지 않고 기존 `stall_timeout_min`(기본 5분) 안전망을 거쳐 `0`(stall)으로 리턴한다 — 대기는 유한하지만(행 아님), 이슈 #224가 도입한 "크래시와 정상 종료를 구분하는 별도 종료 코드"라는 신호는 이 경로에서 약해진다. `docs/issue-224/decisions/watch-crash-exit-code.md:25-26`가 트리거를 "pid is dead (or its roster entry is gone)"라고 적어 뒀으므로, (b)가 랜딩하면 이 문구도 phase 2에서 갱신 대상이다(Out of scope 아님 — What will be done 4).

## What will be done

1. `spawn.py:1903`의 `if roster_entry is None or not pid or not _alive(pid):`를 `if pid is not None and not _alive(pid):`로 좁힌다 — 엔트리가 있고 그 안의 `wrapper_pid`가 죽어 있을 때만 크래시로 본다. 엔트리 부재(`roster_entry is None`) 또는 엔트리는 있지만 `wrapper_pid` 필드가 없는 경우(`pid is None`)는 더 이상 즉시 사망 신호로 안 쓰고, `_await_bounded`의 기존 stall 루프로 자연히 계속 대기한다(`stall_timeout_min` 안전망이 커버).
2. `test_spawn.py::WatchFollow`에 엔트리-부재 꼬리 상태 회귀 테스트를 추가한다: `roster_register`를 호출하지 않은 채(엔트리 완전 부재) 가짜 `_await_bounded`가 몇 차례 stall을 흉내 내다가 나중에 `session-end`를 내는 시나리오를 구성 — 수정 전 코드로 이 테스트를 먼저 돌려 `WATCH_CRASH_RC`가 리턴됨(red)을 확인하고, 수정 후 `_watch`가 stall 경로를 따라 결국 `session-end`에서 정상 `0`을 리턴함(green)을 확인해 기록에 남긴다.
3. 기존 `test_follow_detects_dead_session_and_returns_crash_rc`(엔트리는 있고 `wrapper_pid`가 `_alive`로 거짓인 경우)가 회귀 없이 그대로 통과하는지 명시적으로 확인한다.
4. `docs/issue-224/decisions/watch-crash-exit-code.md:25-26`의 트리거 문구("pid is dead (or its roster entry is gone)")를 갱신해, 엔트리 부재만으로는 더 이상 트리거가 아님을 각주로 남긴다.

## Out of scope

- 대안 (a) — `roster_remove(roster_key)`의 위치 이동. Rationale에서 기각.
- `roster_kill()`/`roster_ps()`를 `wrapper_pid` 기준으로 바꾸는 일 — (b)를 채택하면 이 두 함수는 애초에 이번 결함과 무관해져 손댈 필요가 없다(이것 자체가 (b)의 장점, Rationale 참고).
- `gates/flows.py::flows_payload()`의 대시보드 표시 로직 변경 — 명부를 읽기만 하는 소비자라 이번 판정부 변경과 무관.
- #224가 랜딩한 session-end 우선 드레인 순서, `WATCH_CRASH_RC` 상수, `wrapper_pid` 필드 자체의 변경 — 유지(이슈 본문 요구 3).

## How you'll know it worked

- 신규 회귀 테스트가 수정 전 실행에서 fail(`WATCH_CRASH_RC` 리턴, red), 수정 후 실행에서 pass(`0` 리턴, green) — 두 실행 결과를 phase 2 기록에 남긴다(이슈 본문 요구 2).
- `python3 -m unittest test_spawn.py -v`의 `WatchFollow` 전체(기존 5건 + 신규 1건 이상)가 통과하고, 특히 `test_follow_detects_dead_session_and_returns_crash_rc`가 회귀 없이 통과.
- `docs/issue-224/decisions/watch-crash-exit-code.md` 갱신 여부를 phase 2 기록의 doc-placement ladder 항목으로 확인.
