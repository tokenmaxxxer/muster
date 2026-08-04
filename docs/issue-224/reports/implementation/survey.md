# Survey — issue #224: 조회·감시 신뢰성 3건

착수 시점 확인: 전제 issue #223 은 PR #249 로 main 에 머지됨(git log:
`48266e7 Merge pull request #249 from tokenmaxxxer/issue-223/implementation`)
— 착수 제약 충족. 감사 시점 행 번호는 그 사이 머지들로 소폭 이동했다
(아래 각 결함에서 실제 행과 함께 표기).

## 결함 1 — 승인 코멘트 30개 한계 (`spawn.py:830-844` `_issue_comments`)

```python
def _issue_comments(root: Path, number: int) -> list[dict]:
    ...
    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{number}/comments"],
                       cwd=root, capture_output=True, text=True)
    ...
    data = json.loads(r.stdout)
    return [{"login": ..., "body": ...} for c in data]
```

`gh api` 호출(837행, 감사 기준 836행에서 1행 밀림)에 `--paginate`가 없다
— GitHub REST 는 `/issues/{n}/comments`를 페이지당 기본 30건으로 끊는다.
30번째 이후에 달린 코멘트는 이 호출로 영원히 안 보인다.

**호출부 3곳 전부 승인/멱등 판정에 이 함수를 쓴다** — 결함이 "감시"뿐
아니라 게이트 자체에 닿는다:
- `approve_scope()`(spawn.py:885-916, 922/924행) — phase-1 `APPROVE
  <subject>/scope` 코멘트 탐색. 30개 넘는 스레드에서 뒤늦게 단
  APPROVE 를 영원히 못 찾는다(이슈 본문이 지목한 정확한 사고).
- `gates/flows.py::_pr_approved()`(125-138행, `spawn._issue_comments`
  경유 284/287행) — phase-2 `APPROVE <subject>/<role>` 코멘트 탐색.
  상황판의 승인 검출이 같은 결함을 공유한다.
- `_post_crash_comment()`(spawn.py:1594-1607) — 재스폰 상한 코멘트의
  멱등 마커 탐색. 30개 넘으면 중복 코멘트를 다시 달 수 있다(부작용은
  작지만 같은 근본 결함).

**`--paginate` 단독 추가는 틀린 수정이다 — 실측 확인.** `gh api` 는
`--paginate`만 주면 페이지마다 별도 JSON 배열을 순차 출력한다(합쳐서
하나의 배열로 안 만든다) — `--slurp`를 같이 줘야 페이지들을 바깥
배열 하나로 감싼다. 이 저장소에서 직접 실행해 확인:

```
$ gh api repos/tokenmaxxxer/on-the-record/issues/224/comments --paginate --slurp
[[]]
```

댓글 0개인 이슈에서도 결과가 `[]`가 아니라 `[[]]`(페이지 1개를 감싼
바깥 배열)다 — 즉 `json.loads(r.stdout)`의 결과가 지금처럼 "코멘트
객체의 리스트"가 아니라 "페이지(코멘트 리스트)의 리스트"로 바뀐다.
`--slurp`를 빼면 다중 페이지 응답은 애초에 유효한 단일 JSON 이 아니라
`json.loads`가 `ValueError`로 죽는다(현재 코드의 `except ValueError:
return []`가 삼켜서 "코멘트 없음"으로 오판 — `--paginate`만 넣는
안은 결함을 고치기는커녕 다중 페이지에서 조용히 더 나쁜 실패로
바뀐다). 파싱 쪽에서 페이지 리스트를 평탄화하는 한 줄이 반드시
같이 가야 한다.

`gh --version`: 2.97.0 (설치본, 2026-07-31) — `--slurp`는 이 버전의
`gh api --help`에 문서화돼 있다.

## 결함 2 — PR 31건째부터 무음 누락 (`gates/flows.py:45-57` `_pr_list_all`)

```python
def _pr_list_all(root: Path) -> list[dict]:
    r = subprocess.run(["gh", "pr", "list", "--state", "open", "--json",
                        "number,headRefName,createdAt,body,reviews"],
                       cwd=root, capture_output=True, text=True)
```

`--limit`이 없으면 `gh pr list`는 기본 30건에서 끊는다(감사 기준
flows.py:41 — 그 사이 `_STAGE_MAP`/`_stage_for` 관련 편집으로 실제
호출부는 45-57행/48행으로 이동, 개수·순서 불변). `flows_payload()`가
이 결과로 `decision_queue`/`unapproved_open_prs`/`flows[].prs`를 전부
채운다(252-343행) — 31번째 이후 열린 PR 은 상황판·승인 대기열
어디에도 안 뜬다.

**같은 파일에 이미 있는 자매 함수가 정답 관용구를 갖고 있다.**
`_issue_list_all()`(60-73행, 바로 아래)은 "repo-wide, 한 번의 호출"
목적이 `_pr_list_all`과 동일한데 이미 `--limit 1000`을 쓴다:

```python
r = subprocess.run(["gh", "issue", "list", "--state", "all", "--json",
                    "number,state,body", "--limit", "1000"], ...)
```

`--limit`은 값 하나만 넣으면 되는 `gh` 자체 플래그라 결함 1의 페이지
평탄화 문제가 없다 — `--paginate --slurp`를 쓰지 않고도 단일 호출·단일
평탄 배열로 끝난다.

## 결함 3 — watch가 크래시 세션에서 무한 루프 (`spawn.py:1773-1808` `_watch`)

`_await_bounded()`(1729-1770행, 감사 기준 1741행 부근)는 그 자체로는
무한정 블록하지 않는다 — 이벤트 하나가 뜨거나 `stall_timeout_min`
(기본 5분)이 차면 반드시 리턴한다(1764-1766행 stall 처리). 진짜
문제는 `_watch()`의 `--follow` 분기(1789-1808행)다:

```python
while True:
    before = _read_offset(offset_path)
    rc = _await_bounded(events_path, offset_path, stall_timeout_min, log_path)
    after = _read_offset(offset_path)
    if after > before:
        ...
        if ev.get("type") == "session-end":
            return rc
```

stall 리턴은 offset 을 안 미루므로(`_await_bounded`의 stall 경로는
`_write_offset`을 안 부른다) `after == before`가 되고, 다음 줄에서
그대로 `_await_bounded`를 또 부른다 — stall 타임아웃마다 무한 반복.
세션 프로세스가 죽어서 로그가 더 이상 안 자라면 `session-end` 이벤트도
영원히 안 오므로 이 `while True`는 실제로 끝나지 않는다(issue 본문의
"오케스트레이터 영구 블록"). pid 를 전혀 안 본다 — 로그 정체와 "세션이
죽었다"를 구분할 신호가 이 루프 안에 없다.

**세션 사망을 판별할 기존 신호가 이미 이 파일에 있다.** `roster_key =
f"issue-{issue}/{role}"`로 `ROSTER`(runs/active.json)에 pid 가 등록돼
있고(`_spawn_one`, 2601-2727행, roster_register 호출 2725행) `_alive(pid)`
(1303-1309행, `os.kill(pid, 0)`)가 이미 `roster_ps()`/`roster_watchdog()`
에서 "죽었다" 판정에 쓰인다. `_workspace_index_load()`가 반환하는
`_watch()`의 entry(work/log 경로만 담음, 1713-1724행)에는 pid 가 없지만,
같은 키로 roster 를 한 번 더 찾으면 pid 를 얻는다 — 새 상태를 만들
필요가 없다.

**재스폰과의 상호작용도 이미 이 키로 맞물린다.** `_auto_respawn_check()`
(1621-1676행)가 크래시로 판정한 로스터 엔트리를 같은 `roster_key`로
`_spawn_one()`을 다시 불러(1676행) 새 pid 로 **같은 키**를 덮어쓴다
(`roster_register`가 dict 갱신). 즉 `--follow` 루프가 매 반복마다 로스터를
새로 조회하면: (a) 세션이 죽고 재스폰도 없으면 pid 죽음이 그대로
보이고, (b) 재스폰이 성공하면 다음 조회에서 새 pid(살아있음)를 보게
돼 자연히 새 세션을 계속 따라간다 — 별도 처리 없이 그냥 "매번 다시
읽기"만으로 두 경우 다 맞다.

**`_watch()`가 role 미지정 다중 매치 분기에서 resolved role 문자열을
버린다(1782-1787행)** — `matches[0][1]`(entry)만 쓰고 `matches[0][0]`
(키, 즉 "issue-N/role")은 버려진다. pid 조회에 실제 roster 키가
필요하므로, 이 분기에서 resolved 키를 지역 변수로 남겨야 한다(함수
시그니처·반환형 불변 — 내부 지역 변수 하나 추가일 뿐).

**대안(이슈가 제시한 두 번째 후보) — 순수 outer 타임아웃.** `--follow`
자체에 "이만큼 지나면 무조건 포기" 상한을 얹는 안도 이슈 본문이
후보로 언급한다. Rationale 에서 기각 근거를 다룬다(스카우트 결과와
함께).

## 참고 관찰 — "유의미 이벤트에서만 리턴" 계약, 실제로는 더 자주 리턴

이슈가 인용한 "계약 문서"는 `on-the-record/hooks/directive.sh:75-77`이다:

```
--issue <n>\` and \`spawn.py watch --issue <n>\` both return early, at
the first material event (PR opened, gate refusal, session end) or
after \`--stall-timeout\` minutes (default 5) with no session activity
```

"material event" 4종 = PR opened / gate refusal / session end / stall.
실제 `_await_bounded()`는 `events.jsonl`에 새로 append된 **어떤
타입이든** 리턴 트리거로 삼는다(1737-1744행, 타입 분기 없음). 이
파일의 전체 이벤트 타입 목록(`_append_event` 호출 지점 8곳):
`respawn-attempt`(1672) · `session-start`(2736) · `pr-opened`(2787) ·
`gate-refusal`/`harness-refusal`/`sandbox-refusal`(2804, `_classify_refusal_text`
분기) · `unclassified-refusal`(2812) · `progress`(2839, 2845) ·
`session-end`(2951).

`session-start`/`respawn-attempt`/`progress` 는 directive.sh 의 "PR
opened / gate refusal / session end" 어디에도 안 든다. 그 중
`progress`는 issue #180 phase 2 가 만든 것으로(docs/issue-180 참고),
그 프로포절 자신이 "매 tool_use 마다 기록"은 명시적으로 기각하고
Write/Edit 연속중복 억제 + 특정 Bash 접두사(`_PROGRESS_BASH_PREFIXES`,
spawn.py:1479-1483: `git commit`/`git push`/`gh pr create`/테스트
실행 2종)로 좁혔다 — 그런데도 코딩 세션 하나가 파일 여러 개를 쓰면
그때마다 `progress` 이벤트가 서고, directive.sh 의 재무장 지시(81-82행:
"session-end 가 아닌 이벤트로 리턴할 때마다... re-arm by calling
`spawn.py watch` again")가 그때마다 오케스트레이터를 재무장시킨다 —
이슈가 실측했다는 "재장전 사이클이 이벤트마다 반복돼 알림 소음화"와
정확히 부합한다.

**즉 이것은 "문서가 설명을 안 맞게 썼다"가 아니라 "코드가 문서보다
넓은 트리거 집합으로 동작한다"쪽 불일치다.** 정정 방향은 두 갈래:
(a) 문서(directive.sh)를 실제 동작에 맞춰 다시 쓴다, (b) 코드
(`_await_bounded`)를 문서의 4종으로 좁힌다. (b)는 issue #180 자신의
프로포절이 이미 명시적으로 검토·기각한 변경과 겹친다 — "`_await_bounded`
자체를 스트리밍으로 바꾸면 `_spawn_one`의 포크-부모 조기 리턴 경로
(2601행 근방)도 같이 바뀐다"는 이유로 그 계약(한 이벤트 또는 stall 에서
리턴)을 건드리지 않기로 이미 결정된 바 있다. 이 관찰의 스코프 판단은
proposal 의 Rationale 에서 다룬다.

## 같은 계열 후보 2건 — 이번 write set 밖 (판단 근거만 여기 기록)

이슈 본문이 "제안이 비용을 보고 판단"하라고 위임한 두 후보:

- **`events.jsonl` 무가드 `json.loads`** — `spawn.py:1746`
  (`_await_bounded` 내부, `ev = json.loads(lines[seen])`)과 `spawn.py:1805`
  (`_watch --follow` 내부, `ev = json.loads(lines[after - 1])`) 둘 다
  try/except 없이 파싱한다. 손상되거나 잘린 줄이 있으면 `_watch`/
  `_await_bounded` 자체가 `JSONDecodeError`로 죽는다.
- **`workspaces.json` 무락 read-modify-write** — `_workspace_index_put()`
  (spawn.py:1720-1724)이 `_workspace_index_load()`로 읽고 통째로
  다시 쓰는데, 로스터(`ROSTER`)의 `_roster_locked()`(1278-1288행,
  `fcntl.flock`)와 달리 락이 없다. 동시 스폰 2건이 겹치면 하나의
  엔트리가 유실될 수 있다.

둘 다 "조회·감시가 있는 걸 못 본다"는 이슈의 결함 3건과 같은 실패
계열(무가드 파싱 크래시, 동시성 유실)이지만, 결함 3건과 달리 **감사가
실측한 사고가 아니라 코드 형태로만 추정한 위험**이고, 고치려면 각각
독립적 설계 결정(파싱 방어 범위, 락 스코프)이 필요해 이번 3건의 frozen
write set 을 넓힌다. Out of scope 판단과 근거는 proposal 에서.

## 시그니처·계약 확인 (건드리면 안 되는 부분)

- `_issue_comments(root: Path, number: int) -> list[dict]` — 반환형
  불변(코멘트 dict 리스트, 페이지 평탄화는 함수 내부에서 끝낸다).
  호출부 3곳(`approve_scope`, `gates/flows.py::_pr_approved`,
  `_post_crash_comment`) 모두 지금처럼 평탄 리스트를 기대 — 반환형이
  바뀌면 셋 다 깨진다.
- `_pr_list_all(root: Path) -> list[dict]` — 반환형 불변, `flows_payload()`
  가 그대로 소비.
- `_watch(issue, role, stall_timeout_min, follow=False) -> int` —
  시그니처·반환형 불변. `test_spawn.py::WatchFollow`가 `_await_bounded`를
  `mock.patch.object`로 완전 대체해 호출 배선만 검사하므로, pid 사망
  판정을 `_watch()` 쪽(또는 `_await_bounded` 호출 사이)에 넣으면 이
  기존 목이 깨지지 않는지 확인 필요 — 특히
  `test_follow_ignores_stall_and_keeps_going`은 "stall 을 무시하고
  계속 간다"는 이름 그대로 pid 가 안 죽은 상태에서의 회귀 보증으로
  남겨야 한다(§ below).
- `_await_bounded()` 자체의 시그니처·"한 이벤트 또는 stall 에서
  리턴" 계약은 이슈 #180 프로포절이 이미 "바꾸지 않는다"로 확정 —
  이 이슈도 그 결정을 따른다(참고 관찰 절 참고).

## 테스트 현황

- `_issue_comments`/`_pr_list_all` 둘 다 자신의 `subprocess.run` 호출
  인자를 직접 검사하는 테스트가 0건이다(grep 결과) — 모든 소비자
  테스트가 `mock.patch.object(spawn, "_issue_comments", ...)` /
  `self._patch(flows, "_pr_list_all", ...)`로 함수 자체를 완전
  대체해서 호출부 배선만 본다(test_spawn.py:2559/2575/2714,
  test_flows.py:72/74 등). `spawn.subprocess.run`을 직접
  mock/spy 하는 하우스 스타일은 이미 있다(test_spawn.py:207
  `mock.patch("spawn.subprocess.run")`, 233
  `wraps=subprocess.run` 스파이) — 이번 회귀 테스트가 이 패턴을
  가져다 쓴다.
- `test_spawn.py::WatchFollow`(3063-3157행)는 `_await_bounded`를
  가짜로 바꿔 `_watch(..., follow=True)`의 반복·정지 조건만 검사한다
  — pid 사망을 흉내 내는 테스트는 0건. 새 테스트가 필요하다: 가짜
  `_await_bounded`가 매번 stall(오프셋 불변)을 리턴하는 상황에서,
  로스터 pid 가 죽어 있으면 루프가 유한 반복 안에 리턴하는지(성공
  신호), 살아있으면 기존처럼 계속 도는지(회귀 방지,
  `test_follow_ignores_stall_and_keeps_going`이 이미 이 케이스를
  덮는다 — 건드리지 않는다).

## 쓸 파일 (write set 예상)

- `spawn.py` — `_issue_comments()`에 `--paginate --slurp` + 페이지
  평탄화, `_watch()`의 `--follow` 분기에 로스터 pid 사망 판정 추가
  (다중 매치 분기의 resolved 키 보존 포함).
- `gates/flows.py` — `_pr_list_all()`에 `--limit 1000` 추가.
- `test_spawn.py` — `_issue_comments`의 다중 페이지 파싱 테스트
  (mock 화 `subprocess.run`으로 `--paginate --slurp` 응답 모양
  `[[...], [...]]` 흉내), `WatchFollow`에 pid 사망 감지 테스트 1-2건
  추가.
- `test_flows.py` (또는 `test_spawn.py::FlowsPayload`, 기존 테스트가
  어느 쪽에 있는지에 따라) — `_pr_list_all()`의 `subprocess.run` 호출
  인자에 `--limit`이 있는지 검사하는 테스트 1건 추가.

## 스카우트 판단

결함 1·2는 "pure bugfix" 스킵 조건 적용: 둘 다 열린 설계 결정이
거의 없는 기계적 수정이다(각각 `gh` 자체 플래그 조합, 그리고 같은
파일 자매 함수가 이미 쓰는 관용구를 그대로 따라감) — 별도 외부 스카우트
없이 이 저장소 내부 prior art(`_issue_list_all`의 `--limit 1000`,
그리고 `gh api --help`/실측으로 확인한 `--paginate --slurp` 동작)로
충분. 결함 3(pid 사망 판정 vs 순수 타임아웃)은 이슈 본문이 두 후보를
나란히 제시해 열린 설계 결정이라 스킵하지 않고 스카우트 실행 —
상세·소스는 scout-brief.md.
