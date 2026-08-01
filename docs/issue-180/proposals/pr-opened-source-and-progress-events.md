---
role: implementation
subject: issue-180
loop_state: scope-proposed
---

# Proposal — `pr-opened` 출처 판별 + 진행 이벤트 (issue #180)

files: `spawn.py`(`_spawn_one` 스트림 루프의 `pr-opened` 판별 교체,
진행 이벤트 추가, `_watch`/`main()` 에 `--follow` 배선),
`test_spawn.py`(`EventExitScope`/`EventReporting` 확장 + 신규 진행-이벤트
테스트 클래스), `on-the-record/hooks/directive.sh`(재무장 지시 문구를
`--follow` 존재에 맞춰 갱신 — 텍스트만, 로직 없음),
`docs/issue-180/reports/implementation.md`(phase 2 기록, Approve
게이팅 이후에만 작성).

## Request (paraphrased, secrets stripped)

`_spawn_one` 의 stdout 스트림 파싱 루프(현재 좌표 spawn.py:2429-2449)가
두 가지를 잘못하고 있다. 하나, `pr-opened` 이벤트를 "세션이 PR 을
열었다"가 아니라 "세션 출력에 자기 레포 PR 처럼 생긴 문자열이
있었다"로 세운다 — 실측(2026-08-01, issue-178 phase 1): 세션이 자기
테스트 파일(`test_spawn.py`)을 읽었을 뿐인데, 그 파일의 fixture
문자열(`.../tokenmaxxxer/on-the-record/pull/142`, 실존하지 않는 PR)이
`pr-opened` 를 세워 `_await_bounded` 를 조기 복귀시켰다. 둘, 세션이
15~70분 동안 파일을 읽고 쓰고 테스트를 돌리고 커밋해도 `events.jsonl`
에는 아무것도 안 남아 `watch` 로는 그 구간이 통째로 안 보인다 —
오늘 오케스트레이터가 이걸 우회하려 만든 바깥 재파싱 스크립트가 그
자체로 두 파서 문제·로그 포맷 결합·기계 종속성 비용을 실측시켰다.
비슷한 종류의 오탐(자기 레포 URL 판별 실패)이 오늘 **두 번** 독립
재현됐다(`_spawn_one` 자신, 그리고 그 임시 바깥 스크립트가 `git push`
안내 URL `.../pull/new/<branch>` 를 pr-opened 로 오인) — 이슈는 이
두 결함이 같은 루프 안에서 나므로 하나로 묶어 고치라고 요청한다.

## Constraints

- `_spawn_one` 의 기존 스트림 루프 안에서 해결한다 — 새 파서, 새
  프로세스, 새 룰북 훅을 추가하지 않는다.
- `offset` 기전(`_read_offset`/`_write_offset`/`_event_count`,
  1606-1636)은 변경하지 않는다 — 이슈 #142 수정 이후 정상 동작이
  실측으로 확인돼 있다(survey.md).
- 동시성 구간 두 곳은 이번 변경이 건드리지 않는다: 로스터 파일락
  (`_roster_locked`, 1267-1290)과 포크/setsid/dup2(2366-2398, 이슈
  본문의 옛 좌표로는 `L2680-2710` — flows 이동으로 314줄 당겨졌다).
  `_watch()` 의 `--follow` 는 `_await_bounded` 자체를 바꾸지 않고
  그 호출을 반복하는 방식으로만 구현한다(아래 Rationale).
- `python3 test_spawn.py` 통과, 개수 감소 없음. `python3 gates/ci.py .`
  통과.
- 이 PR 은 조사와 제안까지만 담는다 — 코드 변경은 사람의 Approve
  이후 phase 2 에서만(contract v3 s19).

## Rationale

**출처 판별 — 후보 (a) tool_result 구조 상관관계 단독은 기각.**
Bash `tool_use`(명령 `gh pr create`/`git push`)와 이후 그 결과를 담는
`tool_result` 블록을 `tool_use_id` 로 짝짓는 방식은 이론적으로는 더
정밀하지만(survey.md 의 gate-refusal 구조화 선례, scout-brief.md 의
선례 2 원칙과 일치), 이 저장소가 오늘 실측한 두 사고 — 존재하지 않는
PR 번호(#142), `pull/new/<branch>` 오탐 — 둘 다 GitHub 에 직접 물어
확인하는 후보 (b) 하나로 이미 걸러진다(`gh pr view 142` 는 실측대로
`Could not resolve to a PullRequest` 를 낸다). 구조 상관관계 추적을
얹어도 막아내는 사고가 늘지 않는데, `assistant` 의 `tool_use` id 를
이후 `user` 메시지의 `tool_result` 와 맞추는 상태(대기 중인 tool_use
맵)를 스트림 루프 안에 새로 들고 있어야 해서 구현·유지 비용만
커진다 — spawn.py 는 이미 이슈-178 survey 가 "최근 30일 커밋의
24%가 손대는 최다 충돌 파일"이라고 실측한 곳이라, 여기 상태를 더
추가하는 안은 특히 불리하다. **채택은 (b) 단독** — 후보 URL에서 PR
번호를 뽑아 `_pr_for_branch(Path(cwd), br)`(기존 함수, 815-820, 이미
`_spawn_one` 자신이 2492에서 쓰고 있다)로 실제 열린(또는 열렸던) PR
번호와 대조한다. 새 `gh` 호출 모양을 만들지 않고 기존 관용구를 그대로
쓴다.

**진행 이벤트 — "매 tool_use 마다 기록"은 기각.** 이슈가 명시한
비용(`events.jsonl` 비대, 알림 폭탄)은 가정이 아니라 directive.sh
(74-87)의 기존 지시로 이미 정해져 있다: `watch` 가 `session-end` 가
아닌 이벤트로 리턴할 때마다 오케스트레이터는 반드시 즉시 재무장해야
한다 — 이벤트 하나가 오케스트레이터 왕복 하나다. 세션 하나가 내는
`tool_use` 는 수십~수백 건이라, 전부 기록하면 재무장 왕복이 그만큼
는다. **채택은 오늘 바깥 스크립트가 쓴 필터(산출물 쓰기 + 검증/커밋/
푸시 명령)를 그대로 시작점으로 삼되, 같은 파일에 연속으로 나는
Write/Edit 는 중복 억제한다** — 세션 하나의 전체 산출물 파일 수는
수십 개 규모로 이미 바운드돼 있다(이슈 하나의 phase 는 대개 파일
몇 개~십여 개를 건드린다).

**watch 모양 — "`_await_bounded` 자체를 스트리밍으로 바꾸고 단일-이벤트
모드를 없앤다"는 기각.** `_await_bounded` 는 `_watch()` 뿐 아니라
`_spawn_one` 자신의 포크-부모 조기 리턴 경로(2382-2386)도 그대로
쓴다 — 이 경로는 오케스트레이터가 스폰을 건 직후 빠르게 돌려받아야
하는, 명시적으로 out-of-scope 인 동시성 구간과 붙어 있는 코드다.
`_await_bounded` 의 계약(한 이벤트 또는 stall 에서 리턴)을 바꾸면
이 경로의 동작도 같이 바뀐다. **채택은 `_await_bounded` 를 그대로
두고, `_watch()` 에 `--follow` 플래그를 얹어 그 함수를 반복 호출하며
매번의 결과를 계속 찍다가 `session-end` 나 진짜 stall 에서만 멈추는
것** — 기존 단일-이벤트 모드(기본값, 사람이 한 번만 들여다볼 때)와
공존시킨다.

**대안 ④ — "①만 고치고 ②는 오케스트레이터 폴링으로 감당"은 기각.**
그 폴링은 가정이 아니라 오늘 실제로 만들어져 돌아갔고, 이슈 본문이
그 비용(이중 파서, 로그 포맷 결합, 기계 종속)을 실측으로 이미
적어놨다. 이슈의 "한다" 절도 진행 이벤트 기록을 명시적으로 포함한다
— ①만 하는 안은 이번 이슈가 이미 실측·확정한 비용을 그대로 남긴다.

## What will be done

### ① 출처 판별 (조항별 체크리스트)

- [ ] `_PR_URL_RE.findall(line)` 로 후보 URL 을 뽑는 기존 트리거는
  유지한다(정규식 자체를 느슨하게 만들지 않는다 — `pull/new/...` 를
  잡지 않는 현재의 숫자-접미사 anchor 가 이미 막고 있는 오탐이다).
- [ ] 후보 URL에서 PR 번호를 뽑아 `_pr_for_branch(Path(cwd), br)`
  (기존 세션 브랜치 변수 `br`, 2303 에서 이미 계산돼 있다)로 그
  번호가 이 세션 브랜치의 실제 PR 번호와 일치하는지 확인한 뒤에만
  `_append_event(events_path, "pr-opened", m)` 를 부른다.
- [ ] `pr_seen` 은 **확인된** URL만 추가한다 — 미확인 후보는 추가하지
  않아, `gh` 호출이 일시적으로 실패(네트워크)해도 같은 URL이 나중
  줄에서 다시 나오면 재시도된다(영구 억제 방지).
- [ ] `_origin_pr_prefix` 필터는 그대로 둔다(외국 레포 조기 배제,
  `gh` 호출 자체를 줄이는 값싼 1차 필터로 유지).
- 실패 신호: `test_foreign_pr_url_is_not_this_repos_pr` 류 fixture(자기
  레포 PR 번호를 텍스트로만 언급 — 실제 열린 PR과 다른 번호)에서
  `pr-opened` 가 서면 회귀. 반대로, `_pr_for_branch` 를 실제 열린
  PR 번호를 돌려주도록 몽키패치한 상태에서 그 번호가 포함된 URL이
  스트림에 나왔는데도 `pr-opened` 가 안 서면 **이슈 본문이 경고한
  "영원한 대기"** — 조기 복귀가 아니라 더 나쁜 상태다. 두 방향
  테스트가 모두 있어야 이 조항이 끝난 것이다.

### ② 진행 이벤트 (조항별 체크리스트)

- [ ] 새 이벤트 타입 하나: `"progress"`, `detail` 은
  `{"kind": ..., "detail": "..."}`(`gates/flows.py` 의
  `_session_last_activity` 가 이미 쓰는 `kind`/`detail` 어휘를
  그대로 맞춘다).
- [ ] 트리거는 스트림 루프가 이미 하는 `json.loads(line)` 파싱
  결과(`obj`)에서: (i) `assistant` 메시지의 `tool_use` 블록 중
  `Write`/`Edit` — 직전에 같은 `file_path` 로 기록한 `progress`
  이벤트가 없을 때만 기록(연속 중복 억제); (ii) `Bash` `tool_use`
  이고 `input.command` 가 `git commit`/`git push`/`gh pr create`/
  이 저장소의 검증 명령(`python3 test_spawn.py`, `python3
  gates/ci.py`) 중 하나로 시작할 때. 그 외 `Bash`(ls/grep/cat 등
  탐색성 호출)는 기록하지 않는다.
- [ ] `gate-refusal`/`pr-opened` 판별과 같은 파싱 결과(`obj`)를
  재사용한다 — 이 줄에 대해 `json.loads` 를 두 번 부르지 않는다.
- 실패 신호: 탐색성 Bash 호출(예: `ls docs/`)이 `progress` 를 세우면
  입도 실패(알림 폭탄 재현). 반대로 실제 커밋 명령이 한 세션에서
  0건의 `progress` 를 남기면 ②가 애초에 풀려던 "중간이 안 보인다"
  문제가 그대로 남은 것이다.

### ③ `watch` 모양 (조항별 체크리스트)

- [ ] `_await_bounded` 시그니처·동작은 변경하지 않는다.
- [ ] `main()` 에 `--follow`(불리언, `watch` 분기에서만 유효) 추가.
- [ ] `_watch()` 에 `follow: bool = False` 매개변수 추가 — `True` 면
  `_await_bounded` 를 반복 호출하며 매번 그 리턴값을 그대로 쓰다가,
  가장 최근 호출이 소비한 이벤트 타입이 `"session-end"` 였을 때만
  루프를 끝낸다(기존 `_await_bounded` 내부의 stall 처리·출력 형식은
  그대로 재사용 — 새 출력 포맷을 만들지 않는다).
- [ ] `on-the-record/hooks/directive.sh` 의 재무장 지시(74-87)에
  `--follow` 를 쓰면 매 이벤트 재호출이 필요 없다는 문장을 추가하되,
  기존 수동 재무장 절차는 대안으로 남긴다(로직 없는 문서성 수정).
- 실패 신호: `--follow` 세션이 `session-end` 이후에도 안 끝나면
  (오케스트레이터 쪽에서 그 백그라운드 호출이 영원히 안 끝난다)
  이슈가 경고한 "영원한 대기"의 또 다른 형태 — 반드시 테스트로
  종료 조건을 고정한다.

### ④ 대안 판단

앞의 세 조항을 모두 이번 phase 2 에서 함께 처리한다 — "①만" 안은
Rationale 에서 이미 기각.

## Out of scope

- `offset` 기전, 로스터 파일락, 포크/setsid/dup2 동시성 로직 —
  이슈가 명시적으로 막았다(Constraints).
- 룰북(43개) 쪽 훅 추가.
- `gh` 호출 실패 시 재시도 백오프/속도 제한 같은 운영 다듬기 — 지금은
  기존 `_pr_for_branch` 호출 실패 시 동작(빈 결과로 취급)을 그대로
  따르고, 별도 백오프는 이번 이슈 범위 밖(관측 후 필요하면 후속
  이슈).
- `ensure_pushed` 의 호스트 relay 경로(2260-2287, 스트림 루프
  **밖**, `proc.wait()` 이후)에서 열리는 PR 에 대한 `pr-opened`
  기록 — survey.md 가 실측한 사각 지대이지만, 이슈 본문의 범위
  선언("기존 스트림 루프 안에서 해결한다")을 문자 그대로 지키면 이
  경로는 스트림 루프의 일부가 아니다. `session-end` 는 이 경로가
  끝난 뒤에도 정상적으로 나므로 `watch`/`_await_bounded` 가 무한정
  블록하지는 않는다 — 다만 그 경로로 열린 PR은 `pr-opened` 자체는
  못 세운다는 점을 사각 지대로 명시만 해 둔다(후속 이슈 후보).
- `--follow` 를 쓰는 오케스트레이터 사용 패턴(하네스 `Monitor` 도구와
  결합하는 방식)은 spawn.py 코드가 아니라 오케스트레이터 운용 방식이라
  이 PR 산출물이 아니다 — directive.sh 문구 수정에만 반영한다.

## How you'll know it worked

- [ ] 세션이 자기 레포 PR URL 을 **읽기만** 했을 때 `pr-opened` 가
  서지 않는다 — 오늘 실측한 `test_spawn.py` 픽스처 케이스(존재하지
  않는 PR 번호) 그대로 회귀 테스트.
- [ ] `pull/new/<branch>` 형태 URL 이 스트림에 나와도 `pr-opened` 가
  서지 않는다(신규 테스트 케이스 — 이슈가 명시적으로 요청).
- [ ] 세션이 **실제로 PR 을 열었을 때는** `pr-opened` 가 선다
  (`_pr_for_branch` 몽키패치로 "실제 열림"을 흉내낸 회귀 방지
  테스트 — 이게 없으면 이 변경은 완료가 아니다).
- [ ] 외국 레포 URL 차단(#142)이 유지된다 — 기존 3개 테스트
  (test_spawn.py:1536-1551) 무변경 통과.
- [ ] 산출물 쓰기·검증/커밋/푸시 명령이 `events.jsonl` 에 `progress`
  로 남고, `spawn.py watch --issue N --follow` 로 세션 종료 전에
  관측된다.
- [ ] 탐색성 Bash 호출은 `progress` 를 세우지 않는다(입도 실패 방지
  테스트).
- [ ] `python3 test_spawn.py` 통과, 개수 감소 없음.
- [ ] `python3 gates/ci.py .` 통과.

**실패 신호(이슈 본문에서 계승)**: ① 수정 후 실제로 열린 PR 이
`pr-opened` 를 못 세우면, 이건 조기 복귀가 안 되는 정도가 아니라
**영원한 대기로 바뀐 것이다** — 이전보다 나쁘다. "읽기만 한 URL 은
무시" 방향과 "실제 연 PR 은 인식" 방향, 두 테스트가 모두 없으면 이
변경은 완료로 치지 않는다.
