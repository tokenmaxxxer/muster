---
role: implementation
subject: issue-180
loop_state: survey
---

# Current-state survey — `_spawn_one` 스트림 루프의 `pr-opened` 출처 판별 + 진행 이벤트 (issue #180)

PR #181(issue-178) 머지로 flows 구역이 `gates/flows.py` 로 빠지면서
`spawn.py` 는 2545줄이 됐다. 이 조사는 그 이후의 현재 `main` 을
기준으로 한다 — 이슈 본문이 인용한 줄 번호(`L2740-2765`,
`L2680-2710`, `L1267-1290`)는 flows 이동 전 좌표라 실제와 어긋난다.
아래는 실측으로 정정한 좌표다.

## 1. `pr-opened` 판별 경로 (① 실측)

- `_PR_URL_RE`(spawn.py:1466): `https://github\.com/[^\s"'\\]+/pull/\d+`.
  숫자 접미사가 필수다 — `pull/new/<branch>` 형태(뒤가 숫자가 아닌
  `new/...`)는 **이 정규식 자체는 애초에 안 잡는다**. 이슈 본문이
  말한 두 번째 실측(임시 감시 스크립트가 `pull/new/...` 를
  `pr-opened` 로 오인)은 `spawn.py` 안이 아니라 오케스트레이터가 오늘
  따로 만든 **바깥** 스크립트에서 난 일이다 — 그 스크립트는 아마
  `/pull/` 부분 문자열만 봤을 것이다(코드를 못 봤으니 추정이지만,
  이슈 본문의 "‘/pull/ 이 들어간 문자열’만으로는 못 가른다"는 결론과
  일치). 즉 phase 2 가 만들 새 로직이 **이 정규식보다 느슨해지면**
  안 된다는 뜻이고, 회귀 테스트에 `pull/new/<branch>` fixture 를 넣어
  이 경계를 고정해야 한다(이슈가 요청한 그대로).
- 실제 스트림 루프(spawn.py:2429-2439):
  ```
  with open(log_path, "w", encoding="utf-8") as lf:
      for line in proc.stdout:
          lf.write(line); lf.flush()
          if issue is not None:
              for m in _PR_URL_RE.findall(line):
                  if pr_prefix and not m.startswith(pr_prefix):
                      continue
                  if m not in pr_seen:
                      pr_seen.add(m); _append_event(events_path, "pr-opened", m)
  ```
  `_PR_URL_RE.findall(line)` 이 **raw JSON 한 줄 전체**(stream-json
  이벤트 하나를 문자열째)에 대고 돈다 — 그 줄이 assistant 의 진짜
  Bash tool_result 인지, 세션이 `Read` 로 띄운 파일 내용인지, 그냥
  텍스트 설명인지 전혀 구분하지 않는다. `_origin_pr_prefix`(1621-1631)
  는 owner/repo 접두사만 거르는 필터라 **같은 레포 안에서 난 오탐**은
  못 막는다 — 이슈 본문이 실측한 정확한 구멍이다.
- `test_spawn.py:1544-1551`(`test_foreign_pr_url_is_not_this_repos_pr`)
  이 이슈가 인용한 바로 그 트리거다: 이 테스트 자신의 fixture 문자열
  (`...tokenmaxxxer/on-the-record/pull/142`)이 `test_spawn.py` 를 읽는
  세션의 stdout 스트림에 그대로 실려 `_PR_URL_RE` 에 잡히고,
  `_origin_pr_prefix` 는 같은 레포라 통과시킨다.
- 이미 있는 "raw-text 스캔 → 구조화 필드 파싱"으로 옮긴 선례가 이
  파일 안에 있다: `gate-refusal` 판별(2440-2449)은 `obj =
  json.loads(line)` 로 파싱한 뒤 `obj.get("type") == "result"` 인
  레코드의 `permission_denials` **필드**만 본다 — 이슈-126 이 고친
  "raw-text 로 `permission_denial|denied` 를 스캔하다 이 파일 자신의
  정규식 소스 줄에 오탐"(test_spawn.py:986-995,
  `test_echoed_source_mentioning_denied_is_not_a_gate_refusal`)의
  결과물이다. `pr-opened` 는 아직 그 이전 세대(raw-text 정규식) 그대로
  남아 있다 — 같은 종류의 결함을, 같은 파일 안에서, 이미 한 번 고쳐본
  방식이 있다는 뜻.
- `gates/flows.py:107-157`(`_session_last_activity`)에 stream-json
  한 줄을 구조적으로 파싱해 `tool_use`/`text`/`result` 로 분류하는
  코드가 **이미 있다**(board 상황판의 "마지막 활동" 표시용, pull 방식
  — flows 조회 시점에 로그 tail 을 읽는다). `_activity_tool_summary`
  (~95-104)가 `tool_use` 블록의 `name`/`input`(`command`,
  `file_path` 등)에서 사람이 읽을 요약을 뽑는다. `_spawn_one` 의 push
  방식 이벤트 기록과는 소비 시점이 다르지만(전자는 언제든 조회, 후자는
  발생 즉시 `events.jsonl` 에 append), **한 줄을 tool_use/tool_result
  구조로 분류하는 로직 자체는 이미 이 저장소에 구현돼 있다** — 새로
  만들 필요가 없다.

### `gh` 로 실존 확인하는 기존 선례

- `_pr_for_branch`(spawn.py:815-820): `gh pr list --head <branch>
  --state all --json number -q .[0].number`. 이미 두 곳에서 쓰인다 —
  `approve_scope`(911)와 `_spawn_one` 자신의 `already_delivered`
  판정(2492, **stdout 루프가 끝난 뒤** `proc.wait()` 다음 위치).
- `ensure_pushed`(2243-2287)는 `--state open` 변형을 인라인으로 한 번
  더 쓴다(2268-2271) — "PR 있음"과 "OPEN 인 PR 있음"을 이슈 #60 회귀
  때문에 의도적으로 갈랐다는 주석이 붙어 있다.
- 즉 이 함수 안에 이미 `gh pr` 존재-확인 호출이 두 가지 모양으로
  있다 — 여기에 `pr-opened` 확인용 세 번째 모양을 새로 만들면 임시
  변형이 늘어난다; `_pr_for_branch` 를 그대로 재사용하는 편이
  기존 관성과 맞는다.
- **실측: `gh pr view 142` 는 존재하지 않는 PR 에
  `GraphQL: Could not resolve to a PullRequest with the number of
  142` 를 낸다**(이슈 본문에 이미 실측돼 있음) — `_pr_for_branch` 류의
  존재-확인은 이 정확한 사고를 URL 정규식 정교화 없이도 막는다: 존재하지
  않는 PR 번호는 애초에 `_pr_for_branch` 가 `None` 을 돌려준다.

### 놓치는 지점 — `ensure_pushed` 의 relay 는 스트림 루프 밖에 있다

`ensure_pushed(cwd, issue, role)` 호출(2481)은 `proc.wait()`(2450) **이후**,
`for line in proc.stdout` 루프가 이미 끝난 지점에서 돈다. 세션이
샌드박스 egress 제한으로 스스로 push/PR 을 못 해 on-the-record 가
호스트에서 대신 push+`gh pr create` 를 하는 경로(2260-2287, 실제로
자주 타는 경로 — 주석에 "환경마다 다르게 막힌다"고 명시)는 **지금
구조상 절대로 `pr-opened` 이벤트를 못 낸다** — stderr 프린트
(2284-2285)만 있을 뿐 `_append_event` 호출이 없다. 이슈의 범위
("기존 스트림 루프 안에서 해결")를 문자 그대로 지키면 이 경로는 이번
수정 대상이 아니지만, 수용 기준("세션이 실제로 PR 을 열었을 때는
pr-opened 가 선다")을 relay 경로까지 포함해 읽으면 이 경로도 사각
지대로 남는다는 점은 제안서에서 명시적으로 판단해야 한다.

## 2. 진행 이벤트 재료 (② 실측)

- `events.jsonl` 에 지금 나는 이벤트는 넷뿐: `session-start`(2414),
  `pr-opened`(2439), `gate-refusal`(2449), `session-end`(2539,
  bounded 자식만). 세션이 파일을 읽고 쓰고 테스트를 돌리고 커밋하는
  중간 과정은 전혀 안 남는다 — 로그(`log_path`)는 계속 자라니까
  `_await_bounded` 의 stall 타이머(1683-1694, `log_path.stat().st_size`
  변화로 리셋)도 안 걸린다. 결과: 이벤트 0건인 채로 세션 전체 시간
  (실측 15~21분+) 동안 `_await_bounded` 호출 하나가 안 풀린다.
- 오늘 오케스트레이터가 만든 임시 바깥 스크립트가 걸렀다는 필터:
  산출물 경로 쓰기 + 검증/커밋/푸시 명령. `gates/flows.py` 의
  `_activity_tool_summary` 가 이미 `Write`/`Edit` 의 `file_path` 와
  `Bash` 의 `command` 를 뽑는 로직을 갖고 있어 참고할 분류 기준이
  있다 — 다만 그건 "마지막 활동 하나"만 원할 때고, 이번엔 매 이벤트를
  append 해야 하니 그대로 재사용은 못 하고 판단 기준만 빌린다.
- `on-the-record/hooks/directive.sh:74-87` 의 오케스트레이터 지시가
  이 입도 문제의 실제 비용을 정한다: "watch 가 session-end 아닌
  이벤트로 리턴할 때마다(`stall` 포함) 다른 일 하기 전에 반드시 watch
  를 다시 불러 재무장하라." 즉 이벤트 하나 = watch 재호출 하나 =
  오케스트레이터 세션의 왕복 하나. 이벤트가 너무 잦으면 `events.jsonl`
  파일 크기보다 이 재무장 왕복 횟수(그리고 사람에게 가는 완료 알림
  횟수)가 실제 비용이다.

## 3. `watch` 모양 재료 (③ 실측)

- `_await_bounded`(1652-1695)는 **이벤트 하나 또는 stall** 에서
  리턴하는 단일 함수이고, 두 호출자가 있다:
  1. `_spawn_one` 자신의 fork 부모 쪽 조기 리턴(2382-2386) — `os.fork()`
     직후 부모 프로세스가 `_await_bounded` 를 직접 불러 리턴한다. 이건
     이슈의 "안 한다" 절이 명시적으로 막은 fork/setsid 동시성 구간과
     바로 붙어 있다.
  2. 독립 CLI 서브커맨드 `_watch()`(1698-1714) — `spawn.py watch --issue
     N [--role R] [--stall-timeout M]` 로 호출되고, 워크스페이스
     인덱스(`_workspace_index_load`, 1638-1650)에서 `work`/`log`
     경로를 찾아 같은 `_await_bounded` 를 한 번 부른다.
- 두 호출자가 같은 함수를 그대로 공유한다 — `_await_bounded` 자체의
  "한 이벤트에 리턴" 계약을 바꾸면 1번(포크 부모)의 동작도 같이
  바뀐다. 1번은 의도적으로 빠르게 리턴해야 하는 경로(오케스트레이터가
  처음 스폰을 걸고 바로 다음 대화로 넘어가게)라, `_await_bounded` 를
  건드리지 않고 `_watch()` 쪽에서만 반복 호출로 감싸면 1번을 안전하게
  비켜간다.
- CLI 인자 배선: `--stall-timeout`(1995-1996)과 `--role`
  (1997-1998, dest=`watch_role`)이 이미 있고 `a.role == "watch"`
  분기(2038-2042)에서만 쓰인다 — `--follow` 같은 새 불리언 플래그를
  추가해도 다른 분기에 영향이 없다.
- 이 세션이 속한 실행 환경(하네스) 자체에 "백그라운드 프로세스의 매
  stdout 줄을 알림 하나씩으로 스트리밍"하는 도구(`Monitor`)가 있다 —
  `--follow` 로 매 이벤트를 한 줄씩 계속 찍게만 만들면, 오케스트레이터
  쪽은 `spawn.py watch --follow --issue N` 를 백그라운드로 한 번 걸고
  그 출력을 그 도구로 스트리밍 관측하는 식으로, directive.sh 의
  "매 이벤트마다 재호출" 지시를 "한 번 걸고 계속 듣기"로 단순화할 수
  있다. 이건 spawn.py 자체가 아니라 **오케스트레이터의 사용 패턴**
  쪽 이득이라, 제안서의 "watch 모양"과 "directive.sh 갱신"을 분리해서
  다뤄야 한다.

## 4. 대안 재료 (④ 실측)

이슈 본문이 그대로 실측을 적어 놨다: 오늘 만든 바깥 재파싱 스크립트는
"동작은 하지만" (1) `_spawn_one` 이 이미 같은 스트림을 줄 단위로 파싱
중이라 파서가 둘이 되고, (2) 로그 포맷이 바뀌면 바깥 파서만 조용히
깨지고, (3) 오케스트레이터를 실행한 그 기계에만 있어 다른 기계에는
없다. 이 세 비용은 "①만 고치고 ②는 오케스트레이터가 로그를 직접
폴링해서 감당한다"는 대안을 골랐을 때 그대로 남는 비용이다 — 이미
실측됐다는 점이 이 대안의 근거를 약하게 만든다(가정이 아니라 오늘
실제로 겪은 비용).

## 5. 수용 기준과의 교차 확인

- "세션이 자기 레포 PR URL 을 읽기만 했을 때 pr-opened 가 안 선다" —
  `test_foreign_pr_url_is_not_this_repos_pr` 류 fixture 로 회귀
  테스트 가능(이미 있는 fixture 재사용).
- "세션이 실제로 PR 을 열었을 때는 pr-opened 가 선다" — `EventReporting._run`
  (test_spawn.py:931-975)의 `spawn_cmd -> (["cat"], {})` 몽키패치가
  임의의 stdout 줄을 세션 출력으로 흘려보내는 하네스라, tool_use/
  tool_result 모양의 JSON 줄을 직접 구성해 넣으면 새 판별 로직을
  왕복 네트워크 없이 검증할 수 있다(`_pr_for_branch` 를 이 테스트
  안에서 monkeypatch, 이미 `EventReporting._run` 자체가
  `mock.patch.object(spawn, "_pr_for_branch", ...)` 를 쓰고 있다,
  965-966).
- "외국 레포 URL 차단이 유지된다" — `_origin_pr_prefix` 관련 3개
  테스트(1536-1551)는 로직을 안 건드리는 한 그대로 통과해야 한다.
- "세션 진행이 events.jsonl 에 남고 watch 로 세션 종료 전에 관측된다"
  — 새 이벤트 타입 + `_watch`(또는 `--follow`)가 그 타입도 소비하는지
  테스트 필요.
