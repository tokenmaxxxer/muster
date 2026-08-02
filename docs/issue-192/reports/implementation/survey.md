# Survey — issue #192: 재스폰이 직전 세션 로그를 덮어쓴다

phase: 1 (research). 구현 없음 — 다음 읽기만으로 확인한 현재 상태.

## 확인된 근본 원인

`spawn.py:2398-2399`, `_spawn_one()` 안:

```python
log_path = (Path(str(cwd) + ".session.log") if issue is not None
            else ROOT / "runs" / "last-session.log")
```

`issue is not None` 분기는 워크스페이스 경로(`cwd`)만으로 로그 경로를 결정한다 — 세션마다
달라지는 값(session_id, 시도 횟수, 시각)이 전혀 안 들어간다. 같은 워크스페이스로 몇 번을
재스폰해도 항상 같은 문자열이 나오고, 그 경로는 `open(log_path, "w", ...)`(2482줄)로
**트렁케이트 오픈**된다 — 이슈 배경의 836KB 손실이 정확히 이 지점이다.

`else` 분기(`runs/last-session.log`, issue 없는 애드혹 호출)는 원래부터 "최근 1건만"
스크래치 슬롯으로 설계된 별개 경로다 — 이슈가 말하는 "같은 워크스페이스 재스폰"은
`issue is not None` 경로에만 해당하므로 `else` 분기는 조사 대상에서 제외한다.

## 같은 규약을 공유하는 지점 — 이슈가 지목한 3곳 + 서베이로 찾은 1곳 더

이슈 프롬프트는 spawn.py:2398(생성), clean 2086-2120(삭제), `_await_bounded` 1657(stall
판정)을 지목했다. 코드를 실제로 추적하면 규약을 **재구성**(reconstruct)하는 지점과 그
값을 **전달받기만** 하는 지점이 갈린다 — 이 구분이 write set 을 정확히 정한다.

**규약을 독립적으로 재구성하는 지점 (고쳐야 할 곳):**
1. `spawn.py:2398-2399` — 생성 지점 (위).
2. `spawn.py:2117` — `clean` 서브커맨드, 죽은 워크스페이스 정리 시 `Path(str(w) +
   ".session.log")` 딱 한 경로만 지운다 (요구사항 4의 실측: 178/180 정리됐지만
   `.events.jsonl`/`.events.offset`/`.task.txt` 형제 파일은 그대로 남았다).
3. **`spawn.py:1221`, `session_end_verdict()`** — 이슈 프롬프트가 명시하지 않은 4번째
   지점. `Path(str(work) + ".session.log")`를 자체적으로 재구성해 그 mtime 으로
   `stalled` 대 `in-progress`를 가른다. 유일한 호출자는 `_auto_respawn_check()`
   (1552줄, watchdog 자동 재스폰 경로, 이슈 #90/#132)이며 `entry`(로스터 항목, `log`
   필드 보유)를 이미 들고 있으면서도 그걸 안 쓰고 고정 접미사를 다시 만든다. 생성
   지점(#1)의 명명 규약을 바꾸면 이 함수는 더 이상 존재하지 않는(또는 옛 세대의) 파일을
   보게 되어 watchdog 의 stalled 판정이 조용히 깨진다 — 요구사항 3과 같은 성격의
   회귀 위험이고, 셋만 고치면 이 넷째가 빠진다.

**규약 값을 전달받기만 하는 지점 (원시안 그대로면 손댈 필요 없음):**
- `_await_bounded()`(1657줄) — `log_path` 를 파라미터로만 받는다. 호출부는
  (a) `_spawn_one` 의 bounded-parent 분기(2426-2427줄, fork 직전에 계산한 바로 그
  `log_path` 변수를 그대로 넘김)와 (b) `_watch()`(1721/1723/1731줄, `workspace_index`
  에서 읽은 `entry["log"]`)뿐이다. 생성 지점 하나만 정확히 고치고 로스터/인덱스에 그
  결과를 계속 최신으로 채우면(이미 그렇게 되어 있다 — 아래), `_await_bounded` 자체는
  코드 변경 없이 새 규약을 자동으로 따라간다.
- `gates/flows.py:107` `_session_last_activity()` — `log_path` 를 파라미터로만 받고,
  유일한 호출자(240줄)는 로스터 항목의 `e["log"]`를 넘긴다. 상황판(`flows --json`)도
  동일하게 자동으로 새 규약을 따라간다.
- `roster_register()`(2444-2449줄)와 `_workspace_index_put()`(2408줄, 1650-1654줄) —
  둘 다 `_spawn_one` 이 매 스폰마다 그 시점에 계산한 `log_path` 값으로 **다시 쓴다**
  (덮어쓴다). 즉 "라이브 로그가 지금 도는 세션을 가리킨다"는 요구사항 3의 불변식은
  이미 이 재등록 매커니즘이 지키고 있다 — 생성 지점만 고유해지면 그 최신값이 그대로
  로스터/인덱스에 실린다. `_await_bounded`/`_watch`/`flows.py` 는 이 값을 읽기만 하므로
  별도 수정이 필요 없다는 것이 확인된다.

## 요구사항 2 (session_id 로 끝난 세션 로그 찾기) — 현재 이를 만족하는 저장소가 없다

`runs/ledger.jsonl`(`ledger_write()`, 2585-2594줄에서 호출)에는 세션마다 한 줄이
append 되고 `session_id`(`result.get("session_id")`, 2587줄)가 이미 들어있다. 하지만
그 줄에는 로그 경로가 없다 — `log_path` 는 같은 함수 스코프 안에 있는데도 ledger
엔트리 딕셔너리에 안 실린다. `WORKSPACE_INDEX`(`runs/workspaces.json`)는 `issue-<n>/
<role>` 키당 **최신 값 하나만** 덮어써서(1650-1654줄) 이전 세대를 못 찾는다. 로스터도
살아있는 세션만 들고 죽으면 지운다(`roster_remove`). 즉 세 저장소 다 "지금 도는
세션"이나 "가장 최근"만 가리키고, append-only 이면서 session_id 를 이미 키로 쓰는
`ledger.jsonl` 만이 "끝난 특정 세션"을 가리킬 수 있는 유일한 후보다.

## 요구사항 4 (clean 이 늘어난 로그 전부를 치운다)

`clean` 서브커맨드(2084-2123줄)는 워크스페이스 디렉터리를 `shutil.rmtree` 로 지운
직후 `<work>.session.log` 딱 하나만 확인해서 지운다(2117-2119줄). 형제 파일:
`_events_path`/`_offset_path` 가 만드는 `<work>.events.jsonl`/`<work>.events.offset`
(1463-1465, 1474-1479줄), `<work>.task.txt`(1595, 2349줄), 그리고 워치독 동시성 락
파일 `<work>.respawn-claim-<ts>`(1589줄)까지 — 전부 `clean` 이 안 건드린다. 생성별
로그가 여러 개로 늘어나면(요구사항 1의 직접 결과) 이 누락 클래스가 그대로 넓어진다:
지금 한 종류(정확히 한 경로) 빠뜨리던 게, 고치지 않으면 세대 수만큼 빠뜨리는 게 된다.

## 테스트 커버리지 (기존, 수정 전 베이스라인)

`python3 test_spawn.py` 를 이 샌드박스에서 그대로 돌리면 144건 중 25건이 **에러**로
끝난다 — 전부 `require_board()` → `rulebook_checkout()` 이 진짜 네트워크로 룰북
저장소를 클론하려다 이 샌드박스의 네트워크 제한에 막히는 동일한 원인이고
(`[역할] 룰북을 받지 못했다: ...`), 이번 이슈의 코드 경로와 무관하다. 이 write set 이
직접 건드릴 테스트 클래스 중:
- `Clean`(1183줄), `SessionEndVerdict`(1380줄), `Ledger`(786줄), `Watchdog`(1243줄),
  `EventExitScope`(1647줄), `WatchFollow`(1921줄) — **전부 25건 목록 밖**, 즉 이
  샌드박스에서 지금 깨끗이 통과한다. 수정 후 회귀 여부를 이 환경에서 바로 확인할 수
  있는 클린 베이스라인이다.
- `IssueScopedPrompt.test_preparation_and_preamble_happen_once`(933-940줄) 는 실제
  `_spawn_one()` 을 호출해 `Path(str(work) + ".session.log")` 를 직접 읽어 배달된
  task 내용을 확인한다 — **이미 25건 에러 목록에 있다**(네트워크 차단, 이번 변경과
  무관). 이 테스트는 고정 접미사를 하드코딩해서 읽으므로 명명 규약이 바뀌면 반드시
  같이 고쳐야 하지만(로스터에서 실제 `log` 값을 읽어오는 방식으로), 이 샌드박스에서
  네트워크 없이 통과 여부를 확인할 수는 없다 — 제안서에 이 한계를 그대로 적는다.
- `gates/flows.py` 관련 테스트(`FlowsPayload`, `SessionLastActivity`, 1793-1920줄
  부근)는 로스터 항목에 임의 경로를 직접 넣어 쓰므로(`self.log = ... / "wk.session.log"`
  같은 픽스처 문자열) 명명 규약 자체와 결합돼 있지 않다 — 영향 없음, 확인용.

## Out of scope 확인 (D1-D3, 뒤집지 않음)

- D1: 서베이가 왜 17.6분 걸렸는지는 안 본다 — 이 서베이도 로그 보존 write set 조사에만
  집중했다.
- D2: 로그 안 이벤트 스키마(timestamp/usage/duration_api_ms 등)는 손대지 않는다 —
  ledger 엔트리에 `log` 필드를 추가하는 건 세션 프로세스 안에서 **이미 계산돼 있는**
  `log_path` 변수를 한 줄 더 적는 것뿐, 새 계측이 아니다(수집 아니라 보존).
- D3: `progress` 이벤트가 Write/Edit + 커밋 계열만 세는 필터(`_PROGRESS_BASH_PREFIXES`,
  1470-1471줄)는 그대로 둔다 — 조사하지 않았다.
