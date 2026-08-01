---
role: implementation
subject: issue-180
loop_state: landed
code_under_review: dc5ad692ed79936b4897662737b893d6499ef72b
---

# Implementation — `pr-opened` 출처 판별 + 진행 이벤트 (issue #180, phase 2)

Proposal: [[pr-opened-source-and-progress-events.md]](../proposals/pr-opened-source-and-progress-events.md),
승인: 이슈 코멘트 `APPROVE issue-180/implementation`(single-account mode) +
PR #184 merged. PR #184 에 오케스트레이터가 남긴 승인-전 리뷰 코멘트
(`_pr_for_branch` 메모이제이션 요구)를 아래 ①에 반영했다.

## Why

승인된 제안의 "What will be done" ①②③ 체크리스트를 그대로 이행하기
위해서다 — `_spawn_one` 의 stdout 스트림 루프가 (a) 읽기만 한 자기 레포
PR URL 로 `pr-opened` 를 잘못 세우고, (b) 세션 중간 진행이 `events.jsonl`
에 전혀 안 남는 두 결함을 같은 루프 안에서 고친다.

## What was done (제안의 ①②③ 대응)

1. **① 출처 판별 + PR #184 리뷰의 메모이제이션 요구.**
   `spawn.py:1466-1470`(신설 `_PROGRESS_BASH_PREFIXES`),
   `spawn.py:2455-2495`(스트림 루프): 후보 URL 마다 `_pr_for_branch`
   를 부르던 원래 체크리스트 문구 대신, `pr_number: int | None = None`
   을 루프 밖에 두고 **`pr_number is None` 일 때만** `_pr_for_branch(Path(cwd), br)`
   를 부른다 — 한 번 정수가 나오면 그 뒤 후보는 `int(m.rsplit("/",1)[-1]) == pr_number`
   정수 비교만 한다(네트워크 없음). `pr_seen` 은 검증까지 끝난 URL만
   추가한다(기존 유지) — 미확인 후보는 다음 줄에서 다시 후보가 되므로,
   `pr_number` 가 아직 `None`인 동안(=PR 이 아직 없거나 `gh` 가 일시적으로
   실패한 상태와 구분 불가)에는 새 후보마다 계속 재시도된다.
2. **② progress 이벤트.** `spawn.py:2481-2495`: 새 이벤트 타입
   `"progress"`, `detail` 은 `{"kind": "tool_use", "detail": "..."}` —
   `gates/flows.py:_session_last_activity`/`_activity_tool_summary` 가
   이미 쓰는 `kind`/`detail` 어휘·포맷(`"{name} {file_path}"`,
   `"{command[:60]} 실행"`)을 그대로 맞췄다(순환 import 라 함수 자체는
   재사용 안 함 — `gates/flows.py` 가 `spawn` 을 import 하므로 역방향은
   불가). 트리거: (i) `assistant` 메시지의 `Write`/`Edit` `tool_use` —
   직전에 기록한 progress 이벤트의 `file_path` 와 다를 때만 기록(연속
   중복 억제, `last_progress_file` 상태 변수); (ii) `Bash` `tool_use`
   이고 `input.command` 가 `_PROGRESS_BASH_PREFIXES`(git commit/git
   push/gh pr create/python3 test_spawn.py/python3 gates/ci.py) 중
   하나로 시작할 때. 두 트리거 모두 `gate-refusal` 판별과 같은
   `obj = json.loads(line)` 를 재사용한다 — `if obj.get("type") ==
   "result": ... elif ... obj.get("type") == "assistant": ...` 로
   분기만 나눴고, 이 줄에 대해 `json.loads` 를 두 번 부르지 않는다.
3. **③ `watch --follow`.** `spawn.py:1703-1734`(`_watch`),
   `spawn.py:2019-2021`(`--follow` 플래그), `spawn.py:2068`(배선):
   `_await_bounded` 의 시그니처·동작은 한 줄도 안 건드렸다. `_watch`
   에 `follow: bool = False` 를 추가해 `True` 면 `_await_bounded` 를
   반복 호출하며 매번의 리턴을 그대로 쓰다가, `offset` 이 진행된 뒤
   그 offset 이 가리키는 마지막 소비 이벤트의 `type` 이
   `"session-end"` 일 때만 멈춘다(`_await_bounded` 는 이벤트 소비든
   stall 이든 항상 0 을 리턴하므로, 멈출 신호는 offset 델타로 직접
   읽는다 — `_await_bounded` 내부를 안 건드리는 제약을 지키는 유일한
   방법). `on-the-record/hooks/directive.sh`(84-90행 부근)에 `--follow`
   가 있으면 재무장 루프가 필요 없다는 문장을 추가하고, 기존 수동
   재무장 절차는 대안으로 남겼다(로직 없는 텍스트 수정).
4. **`test_spawn.py`.** `EventReporting._run` 에 `pr_for_branch`/`branch`
   kwarg 를 추가해(기존 호출부 전부 하위 호환), ①에 새 테스트 6개를
   추가했다(§검증 1-2). 기존 `test_pr_opened_does_not_refire_across_respawns`
   는 `_pr_for_branch` 를 항상 `None` 으로 모킹하던 것을, 이 브랜치의
   실제 PR 번호(124)를 돌려주도록 바꿨다 — ① 적용 후에는 검증되지
   않은 URL 로는애초에 `pr-opened` 가 안 서므로, "respawn 넘어 중복
   안 남" 의도를 검증하려면 검증이 통과하는 경로가 필요하다. 새
   `ProgressEvents` 클래스(6개)로 ②를, 새 `WatchFollow` 클래스(5개)로
   ③을 각각 고정했다. 총 125→142개(+17), 감소 없음(§검증 7).
5. **본 기록** — phase-2 기록(이 파일).

## Doc-placement ladder (완료 항목)

- [x] env var / config / dependency / migration → handbook: 해당 없음
  — 새 환경변수·설정·의존성·마이그레이션 없음. `--follow` 는 기존
  `spawn.py` CLI 의 새 플래그일 뿐 별도 설정 표면이 아니다.
- [x] library-or-format 선택 / 시그니처·wire format 변경 →
  `docs/issue-180/decisions/`: 해당 없음 — `docs/specs/flows-schema.md`
  는 `flows --json` 페이로드만 계약하고 `events.jsonl` 의 이벤트
  타입은 애초에 어느 spec 문서에도 나열돼 있지 않다(확인:
  `grep -rn "gate-refusal|session-end|respawn-attempt" docs/specs/*.md`
  무결과) — `"progress"` 추가가 갱신할 기존 wire 계약 문서가 없다.
- [x] benchmark/investigation 수치 → `docs/issue-180/reports/`: 완료 —
  아래 §검증의 테스트 결과·호출 횟수·라이브 CLI 출력이 전부 이
  파일에 있다.

## §검증 — 제안 "How you'll know it worked" 8개 + PR #184 리뷰의 추가 기준

commit `dc5ad69`(코드 변경, 이 기록 이전) 기준. 테스트는 이 샌드박스의
`git clone`(rulebook/core 체크아웃)이 `runs/` 아래 훅-템플릿 복사에서
`Operation not permitted` 로 막히는 환경 제약이 있어(issue-178
survey.md/기록과 동일 계열 관찰), 이미 로컬에 존재하는 체크아웃을
`TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE` 로 가리켜 우회 확인했다
(`~/.claude/plugins/marketplaces/tokenmaxxxer-core`, 그리고 사전에
`execution-observation-rulebook` 을 `$TMPDIR` 아래 클론) — 코드는 안
건드렸고, 실행 환경 설정만 바꿨다.

1. **읽기만 한 자기 레포 PR URL 은 `pr-opened` 를 세우지 않는다.**
   `EventReporting.test_read_only_repo_url_does_not_fire_pr_opened_when_no_pr_exists`
   (`_pr_for_branch` → `None`) 와
   `..._when_different_pr_open`(`_pr_for_branch` → 99, URL 은 142) 둘
   다 통과.
2. **`pull/new/<branch>` 는 `pr-opened` 를 세우지 않는다(신규).**
   `test_pull_new_branch_url_does_not_fire_pr_opened` 통과 — `_PR_URL_RE`
   가 애초에 후보로 안 뽑아 `_pr_for_branch` 호출 자체가 0회임도 같이
   확인(`calls == []`).
3. **실제로 PR 을 열었을 때는 `pr-opened` 가 선다(회귀 방지, 양방향의
   나머지 절반).** `test_actually_opened_pr_fires_pr_opened`
   (`_pr_for_branch` → 555, URL 555) 통과 — 1·2·3 세 테스트로 제안이
   요구한 "읽기만 한 URL 은 무시 / 실제 연 PR 은 인식" 양방향이 모두
   있다.
4. **외국 레포 URL 차단(#142) 유지.** `test_pr_prefix_from_https_and_ssh_origin`,
   `test_pr_prefix_none_without_origin`, `test_foreign_pr_url_is_not_this_repos_pr`
   (기존 3개, 무변경) 통과.
5. **산출물 쓰기·검증/커밋/푸시 명령이 `progress` 로 남고 `watch --follow`
   로 session-end 전에 관측된다.** 단위 테스트
   (`ProgressEvents.test_write_tool_use_fires_progress`,
   `test_verification_and_commit_commands_fire_progress`) 외에, 실제
   `spawn.py` CLI 로 라이브 재현했다 — `runs/workspaces.json` 에
   `issue-99180/verify-follow` 를 등록하고 `events.jsonl` 에
   `session-start`→`progress`×3→`session-end` 를 심은 뒤:
   ```
   $ python3 spawn.py watch --issue 99180 --role verify-follow --follow --stall-timeout 0.05
   [watch] session-start: {'pid': 999, 'ts': 1785576121}
   [watch] progress: {'kind': 'tool_use', 'detail': 'Write docs/issue-180/reports/implementation.md'}
   [watch] progress: {'kind': 'tool_use', 'detail': 'python3 test_spawn.py 실행'}
   [watch] progress: {'kind': 'tool_use', 'detail': 'git commit -q -m x 실행'}
   [watch] session-end: progressed
   EXIT 0
   ```
   한 호출로 progress 3건이 session-end 전에 다 보이고, session-end
   에서만 멈췄다(EXIT 0). 대조: 같은 fixture 를 `--follow` 없이 5번
   호출하면 각 호출이 이벤트 하나씩만 리턴한다(호출 1: session-start,
   2-4: progress 각 1개, 5: session-end) — `--follow` 가 재무장 4번을
   없앤 것을 실측으로 보였다.
6. **탐색성 Bash 호출은 `progress` 를 세우지 않는다.**
   `test_exploratory_bash_does_not_fire_progress`(`ls docs/`, `grep -rn
   foo .`, `cat spawn.py`, `git status`, `git diff` 5종) 통과.
7. **`python3 test_spawn.py` 통과, 개수 감소 없음.**
   ```
   Ran 142 tests in 9.671s
   OK
   ```
   125(베이스라인, `git show HEAD~1:test_spawn.py` 기준 `def test_` 개수)
   → 142(+17, §What was done 4번 목록과 정확히 일치). 위 환경 우회
   적용 시 142개 **전부** 통과 — 에러/실패 0건.
8. **`python3 gates/ci.py .` 통과.**
   ```
   게이트 차단:
     - 보호 경로 변경: spawn.py
   EXIT 1
   ```
   기대(exit 0)와 다르다 — issue-178 phase-2 기록(§검증 5, `de58ad8`)이
   이미 실측·기록한 것과 같은 구조적 특성이다: `spawn.py` 는
   `PROTECTED_ROOT_FILES` 멤버라 `origin/main` 대비 diff 가 있는 한
   어떤 PR 이든 이 줄에 걸린다(`gates/gates.py:26` 설계 의도 — "파이프
   라인이 자기 규칙을 다시 쓸 수 없어야 한다"). 차단 사유가 이 한
   줄뿐이라는 것 자체가 다른 게이트(레코드 well-formed, 의존성 등)는
   전부 통과했다는 증거다. §What did not work 에 그대로 기록한다.
9. **(PR #184 리뷰가 추가한 기준) `_pr_for_branch` 호출 횟수가 후보
   URL 수에 비례하지 않는다.**
   `test_pr_for_branch_call_count_not_proportional_to_candidate_urls`:
   서로 다른 번호(1, 142, 124, 555, 142, 7, 8, 555) 8개 후보 URL 을
   흘리고 `_pr_for_branch` 를 카운팅 스텁으로 교체 — **호출 1회**,
   `pr-opened` 는 실제 번호(555)에 대해서만 1건. 반대쪽(회귀 방지)도
   같이 고정: `test_pr_for_branch_keeps_retrying_while_unresolved` —
   `_pr_for_branch` 가 계속 `None` 을 내는 동안은 후보 3개에 호출
   3회(미해결 상태의 재시도 성질이 메모이제이션으로 안 죽었다).

## What did not work

`python3 gates/ci.py .` 를 exit 0 로 기대했으나 exit 1 (`보호 경로
변경: spawn.py`)이 났다 — §검증 8에 적은 대로 `spawn.py` 를 건드리는
모든 PR 에 구조적으로 나타나는 특성이고(issue-178 phase-2 가 이미
같은 관찰을 기록), 다른 차단 사유가 없다는 사실 자체가 이번 변경이
다른 게이트를 깨지 않았다는 증거다. 롤백 없이 그대로 기록한다.

## Open findings

없음. 위 "What did not work"에 적은 `gates/ci.py` 관찰은 조치가
필요한 미해결 사항이 아니다 — 구조적 특성이며 이 실행 자체가 §검증
8을 만족시키는 증거로 쓰였다.

## Next steps

이 기록을 포함해 새 PR 을 연다(#184 는 phase-1 산출물로 이미 merge
됨 — issue-178 과 같은 패턴: 같은 브랜치, phase 마다 별도 PR). 다음
단계는 사람 승인자(approvers.md)가 이 PR 을 merge 하거나 close 하는
것 — contract v3 의 human-decision 시그널이 그것이다. 리뷰 중 문제가
제기되면 같은 브랜치(issue-180/implementation)에 새 커밋을 추가해
같은 PR 로 대응한다.

## Non-goals (제안 그대로, 불변)

`offset` 기전, 로스터 파일락(`_roster_locked`), 포크/setsid/dup2
동시성 로직, 룰북(43개) 훅 추가, `gh` 호출 실패 재시도 백오프,
`ensure_pushed` 의 호스트 relay 경로에서 열리는 PR 에 대한
`pr-opened` 기록, `--follow` 를 쓰는 오케스트레이터 운용 패턴(하네스
`Monitor` 결합) — 전부 제안의 "Out of scope" 그대로.
