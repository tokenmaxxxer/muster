# Survey — issue #266: 명부 삭제가 session-end 기록보다 앞서 실행

착수 시점 확인: 전제 issue #224(PR #255, 관찰 PR #261)가 이미 main 에 머지됨 — git log 상 `e4a760f Merge pull request #261 from tokenmaxxxer/issue-224/execution-observation` 가 HEAD. 이 이슈가 인용하는 Finding(`docs/issue-224/reports/execution-observation.md`)의 코드 좌표(`c71faba05` 기준)와 현재 워킹트리(HEAD) 좌표는 그 사이 머지 없이 스폰/watch 관련 코드가 그대로라 행 번호가 거의 안 밀렸다 — 아래는 전부 현재 워킹트리 실측.

## 결함 재확인 — 명부 엔트리 수명이 후처리 꼬리를 못 덮는다

`_spawn_one()`(spawn.py:2700-3098)의 후처리 꼬리:

```python
rc = proc.wait()                          # spawn.py:2994
roster_remove(roster_key)                 # spawn.py:2995 — 명부에서 즉시 삭제
if issue is not None:
    _release_spawn_claim(cwd, os.getpid())  # spawn.py:2997
...
if issue is not None:
    ...
    ensure_pushed(cwd, issue, role)       # spawn.py:3027 — 실제 git push
gates = gate_report(cwd) + ownership_report(cwd, role, delta)  # spawn.py:3028
outcome = classify(rc, result, delta, blocked)                # spawn.py:3029
...
ledger_write({...})                       # spawn.py:3060
...
if bounded and issue is not None:
    _append_event(events_path, "session-end", outcome)  # spawn.py:3097
```

`roster_remove(roster_key)`(:2995)는 `proc.wait()` 리턴 직후, 즉 claude 서브프로세스(명부의 `pid` 필드)가 죽는 순간 실행된다. `session-end` 이벤트는 `ensure_pushed`(실제 `git push`)·게이트/소유권 리포트·`classify`·`ledger_write`를 모두 거친 뒤 `:3097`에서야 남는다. `roster_key = f"issue-{issue}/{role}"`(:2782)는 `_watch()`가 조회하는 키(:1851)와 동일 — 이 구간 [:2995, :3097) 전체에서 `_roster_load().get(key)`는 `None`이다.

## `_watch --follow`의 사망 판정 (spawn.py:1847-1906)

```python
roster_entry = _roster_load().get(key) if key else None   # :1901
pid = roster_entry.get("wrapper_pid") if roster_entry else None  # :1902
if roster_entry is None or not pid or not _alive(pid):     # :1903
    print(...)
    return WATCH_CRASH_RC                                  # :1906, = 2 (spawn.py:1841)
```

이슈 #224 가 둘째·셋째 갈래(`pid` → `wrapper_pid`, `_alive`)만 고쳤다 — `wrapper_pid`는 `roster_register`(:2824-2840)에서 `os.getpid()`(:2839, fork-child 또는 non-bounded 경로의 현재 프로세스)로 심어지고 후처리 꼬리 내내 살아 있다. 하지만 첫째 갈래 `roster_entry is None`은 그대로다 — 위 구간에서 이 서브식이 참이라 `wrapper_pid` 값과 무관하게 `WATCH_CRASH_RC`가 리턴된다. 정상 진행 중인 세션이 크래시로 오보된다.

드레인 체크(:1890-1894, `session-end`가 이미 잔여로 남아 있으면 `continue`)는 이 구간을 못 막는다 — `session-end`는 `:3097`에야 디스크에 쓰인다.

## 이 명부 엔트리를 소비하는 다른 곳 — 이슈가 검토를 요구한 지점

명부(`ROSTER = runs/active.json`)를 읽거나 지우는 함수는 `_watch`(:1901) 말고 셋 더 있고, 그중 둘은 `pid`(claude 서브프로세스, 후처리 꼬리 시작 시점에 이미 죽어 있음) 필드로 생사를 판정한다 — `wrapper_pid`를 보지 않는다:

1. **`roster_kill(issue, role)`**(spawn.py:1909-1924) — 사람이 `spawn.py kill`로 호출. `pid = e.get("pid", 0)`(:1916); `_alive(pid)`가 거짓이면 "이미 죽어 있다" 출력 후 무조건 `roster_remove(key)`(:1923) 호출 — 이 호출은 `_spawn_one`의 꼬리 상태와 무관하게 독립적으로 실행된다.
2. **`roster_ps()`**(spawn.py:1336-1356) — `spawn.py ps` 사람 조회 명령. 모든 엔트리를 순회하며 `_alive(e.get("pid", 0))`(:1345)가 거짓인 것을 `dead` 목록에 모았다가(:1352-1353) 전부 `roster_remove(k)`(:1355) 호출.
3. **`gates/flows.py::flows_payload()`**(:357-373) — `roster = spawn._roster_load()`(:357) 후 `spawn._alive(e.get("pid", 0))`(:362)로 `alive` 필드를 매겨 대시보드 `sessions[]`에 싣는다. 이쪽은 **삭제하지 않고 읽기만** 한다.

## 시그니처·계약 확인 (건드리면 안 되는 부분)

- `_watch(issue, role, stall_timeout_min, follow=False) -> int` — 시그니처·반환형 불변. `WATCH_CRASH_RC = 2`(spawn.py:1841, `docs/issue-224/decisions/watch-crash-exit-code.md`)와 `session_end_verdict()`가 이미 쓰는 "드레인 우선, pid 나중" 순서(PR #255 피드백 1) 둘 다 이슈 #224 소유물 — 이번 이슈는 첫째 갈래(`roster_entry is None`)와 명부 엔트리 수명만 다룬다(이슈 본문 요구 3).
- `roster_register`/`roster_remove`(spawn.py:1322-1333)의 시그니처 불변 — `roster_kill`(:1923), `roster_ps`(:1355), `_spawn_one`(:2995) 세 호출부가 그대로 재사용.
- `docs/issue-224/decisions/watch-crash-exit-code.md:25-26`는 `WATCH_CRASH_RC`의 트리거를 "pid is dead (or its roster entry is gone)"라고 명시한다 — 두 안 중 어느 쪽을 골라도 이 문서 문구가 실제 동작과 어긋나게 되므로 phase 2 가 doc-placement ladder 에 따라 이 결정 문서에 수정 각주를 남겨야 한다(이번 phase 1 write set 밖, phase 2 항목으로 표시).

## 테스트 현황

`test_spawn.py::WatchFollow`(:3399-이하)의 `setUp`(:3404-3428)은 모든 테스트에 명부 엔트리를 미리 등록해 둔다(:3425-3428, `wrapper_pid: os.getpid()`). `test_follow_tolerates_post_processing_tail_before_session_end`(:3512-3538)는 그 위에 다시 한 번 `roster_register`(:3521-3524)로 살아있는 엔트리를 심고서야 꼬리를 흉내 낸다 — 실제 프로덕션이 이 구간에서 만드는 상태(엔트리 완전 부재)를 한 번도 구성하지 않는다(execution-observation.md C3, 이 워킹트리에서도 그대로 유효 — 재확인함). 엔트리-부재 꼬리 상태를 구성하는 회귀 테스트는 이슈 요구 2가 명시한 대로 아직 0건.

## 쓸 파일 (write set 예상)

- `spawn.py` — 선택된 안에 따라 `_spawn_one()`의 `roster_remove(roster_key)` 위치(:2995) 이동, 또는 `_watch()`의 사망 판정 조건(:1903)에서 `roster_entry is None` 분기 제거·대체.
- `test_spawn.py` — `WatchFollow`에 엔트리-부재 꼬리 상태를 실제로 구성하는(즉 `roster_register`를 하지 않거나 명시적으로 `roster_remove`해 둔) 회귀 테스트 추가 — 수정 전 red, 수정 후 green을 증명(이슈 요구 2).
- `docs/issue-224/decisions/watch-crash-exit-code.md` — 트리거 문구(:25-26) 갱신, phase 2 항목.

## 스카우트 판단

이 이슈는 스킵 대상이 아니다 — 이슈 본문이 (a)/(b) 두 후보를 나란히 제시하고 "제안이 트레이드오프와 함께 선택"하라고 명시적으로 위임한 열린 설계 결정이다. 스카우트 실행, 상세·소스는 scout-brief.md.
