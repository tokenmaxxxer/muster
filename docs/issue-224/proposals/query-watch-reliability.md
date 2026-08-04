files:
- spawn.py
- gates/flows.py
- test_spawn.py
- test_flows.py

## Request

#224(신청자 jjongkwann): 조회·감시 신뢰성 결함 3건 — (1) `_issue_comments()`
(spawn.py:830-844)가 `gh api .../comments`에 페이지네이션 없이 호출해
30번째 이후 코멘트를 영원히 못 봄 — 승인 게이트(`approve_scope`, phase-2
`_pr_approved`, 재스폰 상한 코멘트 멱등 체크) 3곳이 공유하는 결함. (2)
`gates/flows.py::_pr_list_all()`(45-57행)이 `gh pr list`에 `--limit`
없이 호출해 기본 30건 초과 열린 PR 이 상황판에서 조용히 빠짐. (3)
`spawn.py::_watch()`의 `--follow` 분기(1789-1808행)가 세션 프로세스
사망을 판별할 신호가 없어, 크래시한 세션에서 `session-end` 이벤트가
영원히 안 와 오케스트레이터가 영구 블록됨.

## Constraints

- 착수 시점: 전제 issue #223 이 PR #249 로 main 에 머지됨 — 확인 완료
  (survey.md), 착수 가능.
- `_issue_comments(root, number) -> list[dict]` 반환형 불변 — 호출부
  3곳(`approve_scope`, `gates/flows.py::_pr_approved`,
  `_post_crash_comment`) 모두 지금처럼 평탄한 코멘트 dict 리스트를
  기대한다.
- `_pr_list_all(root) -> list[dict]` 반환형 불변 — `flows_payload()`가
  그대로 소비.
- `_watch(issue, role, stall_timeout_min, follow=False) -> int` 시그니처·
  반환형 불변 — `test_spawn.py::WatchFollow`가 `_await_bounded`를
  `mock.patch.object`로 대체해 호출 배선만 검사하므로, 특히
  `test_follow_ignores_stall_and_keeps_going`(pid 가 살아있는 상태에서
  stall 을 무시하고 계속 도는 회귀 보증)을 깨서는 안 된다.
- `_await_bounded()`의 시그니처와 "한 이벤트 또는 stall 에서 리턴"
  계약은 바꾸지 않는다 — issue #180 프로포절이 이미 이 계약을 건드리는
  안을 명시적으로 기각했다(`_spawn_one`의 포크-부모 조기 리턴 경로가
  같은 함수를 공유하기 때문). 이 이슈도 그 결정을 물려받는다.

## Rationale

**대안 1(rejected) — 결함 1을 `--paginate` 단독으로 고친다.** 이
저장소에서 직접 실행해 확인(survey.md): `gh api ... --paginate`는
페이지마다 별도 JSON 배열을 순차 출력해 다중 페이지 응답이 유효한
단일 JSON 이 아니게 된다 — `json.loads`가 `ValueError`로 죽고, 현재
코드의 `except ValueError: return []`가 그 실패를 삼켜 "코멘트
없음"으로 오판한다. 30개 넘는 스레드에서 지금은 "뒤쪽 코멘트를
못 본다"였던 게 이 안으로는 "코멘트가 전혀 없다고 오판한다"로
악화된다. considered and rejected: 실측으로 확인된 회귀.
채택안(instead of 대안 1): `--paginate --slurp`(페이지들을 바깥
배열 하나로 감싼다, 실측: `[[]]`형)로 호출하고, 반환 직전에
`[c for page in data for c in page]`로 평탄화한다.

**대안 2(rejected) — 결함 2도 결함 1과 같은 `--paginate --slurp` +
평탄화로 고친다(일관성 우선).** 같은 파일의 자매 함수
`_issue_list_all()`(60-73행)이 정확히 같은 목적("repo-wide, 한 번의
호출", 이슈 #172 §3 rate-limit 설계)으로 이미 `--limit 1000`이라는
더 단순한 관용구를 쓰고 있다 — 단일 호출·단일 평탄 배열로 끝나
`--paginate --slurp`의 페이지-평탄화 처리가 애초에 필요 없다. PR
목록과 이슈 코멘트는 실패 모드의 크기가 다르다: 코멘트는 승인 왕복이
쌓이는 단일 스레드에서 무계획하게 늘어날 수 있어 고정 상한이 근본
해결이 안 되지만, 이 오케스트레이션 모델의 동시 열린 PR 수는 role
세션 동시 실행 규모에 매여 있어 1000 을 넘길 시나리오가 없다.
considered and rejected: 같은 파일 안에 이미 검증된 더 단순한
관용구가 있는데 굳이 더 복잡한(페이지 평탄화가 필요한) 패턴을
새로 들이는 건 불필요한 비일관성. 채택안(instead of 대안 2):
`_issue_list_all()`과 동일하게 `--limit 1000` 추가.

**대안 3(rejected) — 결함 3을 순수 outer 타임아웃(예: `--follow`
전체에 30분 같은 상한)으로 고친다.** 이슈 본문이 제시한 두 번째
후보이자 scout-brief.md 가 조사한 대안이기도 하다. 이 저장소는 이미
정확한 사망 신호(`_alive(pid)` + 로스터의 pid 등록, survey.md)를
갖고 있는데 그걸 버리고 근사 신호(경과 시간)만 쓰는 셈이다 — 느리지만
살아있는 세션(예: 큰 diff 검증에 시간이 걸리는 경우)을 조기에
포기하지 않으려면 타임아웃을 넉넉히 잡아야 하는데, 그러면 진짜 죽은
세션의 탐지도 그만큼 늦어진다. `docker logs -f`가 컨테이너 사망 시
즉시 리턴하는 업계 관행(scout-brief.md prior art 1)과도 반대
방향이다. considered and rejected: 이미 있는 정확한 신호를 버리고
오탐 위험이 있는 근사 신호로 대체. 채택안(instead of 대안 3):
`--follow` 루프가 매 반복 진입 시(`_await_bounded` 재호출 전) 로스터에서
같은 키(`issue-{issue}/{role}`)의 현재 pid 를 다시 조회해
`_alive(pid)`를 확인 — 죽었으면(엔트리 부재 포함) 루프를 즉시 끝내고
0 이 아닌 코드로 리턴(정상 `session-end` 종료와 구분되는 신호).
기존 `stall_timeout_min` 은 안전망으로 그대로 둔다(신호 자체가
드문 정상 경로에서도 무한정 걸리지 않도록) — 두 신호를 경합시키지
않고 pid 확인을 stall 리턴 직후의 "계속 기다릴지" 판단에 얹는다.

**대안 4(rejected) — "참고 관찰"(watch 가 문서상 4종 material
event 에서만 리턴해야 하는데 실제로는 모든 이벤트 타입에서 리턴한다,
directive.sh:75-77 vs `_await_bounded` 무분기)도 이번에 같이
고친다.** 정정 방향이 두 갈래인데 둘 다 이번 write set 밖으로
밀린다: 문서(directive.sh)를 실제 동작에 맞추는 안은 노이즈
문제(재장전 사이클 소음) 자체는 안 고치는 값싼 수정이라 이슈가
실측한 불편을 해결 못 하고, 코드(`_await_bounded`)를 4종으로 좁히는
안은 이 프로포절이 위에서 이미 "바꾸지 않는다"고 못 박은 계약(issue
#180 이 기각한 변경)과 정면으로 겹친다 — `_spawn_one`의 포크-부모
조기 리턴 경로까지 건드리는 더 넓은 설계 결정이라 결함 3의 pid 사망
판정과 독립적으로 검토해야 한다. considered and rejected: (a)안은
문제를 안 풀고, (b)안은 이번 이슈가 지키기로 한 계약과 충돌 —
둘 다 이번 3건(조회 누락 2건 + watch 무한 대기 1건)의 frozen write
set 밖.

**대안 5(rejected) — "같은 계열 후보 2건"(events.jsonl 무가드
json.loads, workspaces.json 무락 read-modify-write)도 이번에 같이
고친다.** 이슈 본문이 직접 위임한 판단이다. 둘 다 감사가 실측한
사고가 아니라 코드 형태로만 추정된 위험이고, 고치려면 각각 독립
설계 결정이 필요하다 — json.loads 방어는 "손상된 줄을 만나면
건너뛸지 중단할지"의 정책 결정, workspaces.json 락은 "로스터처럼
`fcntl.flock`을 새로 얹을지, 락 스코프를 얼마나 좁힐지"의 설계
결정. 둘 다 이번 3건(조회 누락 2건 + watch 무한 대기 1건)과는 다른
실패 계열(파싱 크래시, 동시성 유실)이라 같은 프로포절에 넣으면
write set 이 "감사가 실측한 3건"에서 "감사가 형태로만 추정한 2건"
까지 부정확하게 넓어진다. considered and rejected: 별도 설계 결정이
필요한 별개 실패 계열, 이번 3건의 frozen write set 밖.

## What will be done

1. `spawn.py::_issue_comments()`: `gh api` 호출에 `--paginate --slurp`
   추가, 파싱 직후 페이지 리스트를 평탄화(`[c for page in data for c
   in page]`)한 뒤 기존과 같은 dict 변환을 적용. `except ValueError`
   폴백은 그대로 유지(빈 리스트).
2. `gates/flows.py::_pr_list_all()`: `subprocess.run` 인자에
   `--limit`, `"1000"` 추가(위치는 `_issue_list_all()`과 동일하게
   `--json` 인자 뒤).
3. `spawn.py::_watch()`: role 미지정 다중 매치 분기(1782-1787행
   부근)에서 resolved 키(`matches[0][0]`)를 지역 변수로 보존. `--follow`
   분기의 `while True:` 루프 매 반복에서, `_await_bounded` 재호출
   직전에(즉 `after > before` 이면서 `session-end`가 아니었을 때,
   또는 stall 로 `after == before` 였을 때 모두) 로스터에서 같은 키의
   현재 엔트리를 다시 읽어 pid 를 얻고 `_alive(pid)`를 확인 — 엔트리가
   없거나 죽어 있으면 즉시 루프를 끝내고 0 이 아닌 코드로 리턴하며
   stderr 에 "세션 프로세스가 사라졌다"류 메시지를 남긴다(기존
   stall 메시지와 같은 자리에 추가하는 형태).
4. `test_spawn.py`: (a) `_issue_comments`에 대한 새 테스트 —
   `spawn.subprocess.run`을 mock 해 `--paginate --slurp` 응답 모양
   (`[[{...}], [{...}]]`, 2페이지 흉내)을 돌려주고 반환값이 평탄화된
   dict 리스트(2건)인지 확인. 구성한 `subprocess.run` 호출 인자에
   `--paginate`와 `--slurp`가 모두 있는지도 확인. (b) `WatchFollow`
   클래스에 pid 사망 감지 테스트 추가 — 가짜 `_await_bounded`가 매번
   stall(오프셋 불변)을 리턴하는 상황에서, 로스터에 죽은 pid(또는
   엔트리 없음)를 심어 두면 루프가 유한 반복 안에 0 이 아닌 코드로
   리턴하는지 확인. 기존 `test_follow_ignores_stall_and_keeps_going`
   (로스터에 살아있는 pid 를 심어 둔 채로 통과해야 함)은 그대로 두고,
   필요하면 `setUp`에 살아있는 pid(자기 자신의 `os.getpid()`) 로스터
   엔트리를 추가해 회귀를 명시적으로 지킨다.
5. `test_flows.py` (또는 대응하는 `test_spawn.py::FlowsPayload` 위치,
   기존 `_pr_list_all` 테스트가 어디 있는지 확인 후 같은 파일에):
   `flows._pr_list_all`의 `subprocess.run` 호출을 mock/spy 해 인자에
   `--limit`이 포함되는지 검사하는 테스트 1건 추가.

## Out of scope

- `on-the-record/hooks/directive.sh`의 "material event 4종" 문서
  정정, 또는 `_await_bounded`의 리턴 트리거를 4종으로 좁히는 코드
  변경 — Rationale 대안 4에서 기각. 이슈 #180 이 이미 지킨
  `_await_bounded` 계약과 겹치는 별도 설계 결정.
- `events.jsonl`의 무가드 `json.loads`(spawn.py:1746, 1805) 방어
  추가 — Rationale 대안 5에서 기각. 별개 실패 계열, 독립 설계 결정
  필요.
- `workspaces.json`의 무락 read-modify-write(`_workspace_index_put`,
  spawn.py:1720-1724)에 락 추가 — Rationale 대안 5에서 기각. 별개
  실패 계열, 독립 설계 결정 필요.
- `_await_bounded()` 자체의 시그니처·계약 변경 — Constraints 에서
  명시.

## How you'll know it worked

- `python3 -m unittest test_spawn.py -v`와 `python3 -m pytest
  test_flows.py`가 신규 케이스 포함 전부 통과, 기존
  `WatchFollow.test_follow_ignores_stall_and_keeps_going`도 그대로
  통과(회귀 없음 확인).
- `_issue_comments` 신규 테스트가 2페이지 흉내 응답에서 평탄화된
  dict 2건을 돌려주는지, 그리고 구성된 `gh api` 명령 인자에
  `--paginate`·`--slurp`가 모두 있는지 assert.
- `_pr_list_all` 신규 테스트가 구성된 `gh pr list` 명령 인자에
  `--limit`·`1000`이 있는지 assert.
- `WatchFollow` 신규 테스트가: 로스터에 죽은/부재 pid 상태에서
  `_watch(..., follow=True)`가 무한 루프 없이 유한 반복 안에 0 이
  아닌 코드로 리턴하는지 assert(실패 신호: 테스트 자체가 타임아웃 —
  루프가 여전히 안 끝난다는 뜻).
- 수동 확인: 이 저장소 자신의 이슈/PR 중 코멘트가 30개를 넘는 스레드가
  있으면(있다면) `python3 spawn.py approve-scope ...` 또는 직접
  `spawn._issue_comments(root, n)` 호출로 30개 이후 코멘트가 실제로
  보이는지 1회 확인 — 없으면 이 확인은 생략하고 위 mock 기반 테스트로
  충분하다고 본다(phase 2 구현 시점에 재확인).
