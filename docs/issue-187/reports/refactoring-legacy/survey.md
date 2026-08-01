---
role: refactoring-legacy
subject: issue-187
loop_state: survey
---

# Current-state survey — spawn.py 기능별 모듈 분리 (issue #187)

## 대상 파일

spawn.py, 2625줄, 최상위 함수 87개(이슈의 "~90개"와 일치), 클래스 없음,
모듈 전역 `ROOT`(spawn.py:34)·`ROLES`. 정규식(`^def `)으로 함수 경계를
잡아 라인 범위를 산출했다(재현 가능 — `grep -n "^def "` 후 인접 def
사이 구간).

## 이슈 제안 4구역 대비 실측 라인 분포

이슈가 예시로 든 이름들을 그대로 채택하고, 각 구역에 이름이 명시되지
않은 나머지 함수들은 같은 관심사로 실측 배정했다(예: 그룹1은
`registered`/`rulebook_*`/`ensure_installed`/`update`/`doctor` 외에
`core_root`/`core_plugin_dirs`/`resolved_role_model` 등 룰북·플러그인
해석에 쓰이는 헬퍼 전부).

| 그룹 | 대표 함수(이슈 원문) | 실측 함수 수 | 실측 줄 수 |
|---|---|---|---|
| 0 (미분류 공유 헬퍼) | — (`go_proxy_layer`, `_mkt`, `_path`) | 3 | 42 |
| 1 (rulebook/플러그인) | `registered`, `rulebook_*`, `ensure_installed`, `update`, `doctor` | 21 | 693 |
| 2 (board/기록 읽기) | `board`, `status`, `frontmatter`, `gate_report`, `approve_scope` | 24 | 599 |
| 3 (roster/watchdog/watch) | `roster_*`, `watchdog_*`, `_watch`, `_append_event` | 29 | 517 |
| 4 (스폰·워크스페이스) | `spawn_cmd`, `issue_workspace`, `checkout_issue_branch`, `_spawn_one`, `main` | 6 | 684 |

합 87함수/2535줄(≈ 2625줄 중 나머지는 import·docstring·빈 줄).

## 교차-그룹 호출 그래프 (실측 — 각 함수 본문에서 다른 그룹 함수를 직접 호출하는지 정규식으로 스캔)

```
group0 -> group1: 1   (go_proxy_layer -> role_settings)
group1 -> group0: 10  (rulebook_source/dir/checkout/checkout_version/plugin_dirs/_plugin_names -> _mkt/_path)
group2 -> group3: 2   (session_end_verdict -> _alive, _events_path)
group3 -> group2: 3   (_post_crash_comment -> _issue_comments/_repo_slug; _auto_respawn_check -> session_end_verdict)
group3 -> group4: 1   (_auto_respawn_check -> _spawn_one)
group4 -> group0: 1   (_spawn_one -> go_proxy_layer)
group4 -> group1: 12  (spawn_cmd/main/_spawn_one -> doctor/resolved_role_model/core_plugin_dirs/require_doctor/update/role_settings/plugin_dirs/checkout_version)
group4 -> group2: 15  (main/_spawn_one -> approve_scope/require_no_repo_config/status/init_board/require_board/ownership_report/_is_new_commit/board_snapshot/classify/gate_report/_pr_for_branch/fail_closed_downgrade/_git_head; issue_workspace -> slug; checkout_issue_branch -> _base)
group4 -> group3: 20  (main/_spawn_one -> _watch/roster_kill/roster_ps/drive/_alive/_roster_load/roster_watchdog/_origin_pr_prefix/roster_register/_await_bounded/_append_event/_event_count/_events_path/_prior_event_details/roster_remove/ledger_write/_write_offset/_workspace_index_put/_offset_path)
```

group1(0→1 안 들어옴)·group2(3에서만 2건 들어옴)·group3(4에서만 1건
들어옴)은 서로 거의 독립적인 "리프"다 — 1↔2, 1↔3, 2↔4, 3↔1 방향
엣지는 **0건**. 반면 group4(`main`/`_spawn_one`)는 나머지 전부를
부르는 "허브"다(1+12+15+20=48엣지). 이 비대칭이 분리 순서와 위치
결정의 핵심 근거다(제안서 참조).

**순환 의존 2건 실측**(선행 이슈-178 분리 대상이던 flows/closure_sweep은
둘 다 spawn.py로 단방향이라 이런 순환이 없었다 — 이번이 처음 겪는
패턴):

1. **group2 ↔ group3**: `session_end_verdict`(2) → `_alive`/`_events_path`(3),
   반대로 `_post_crash_comment`(3) → `_issue_comments`/`_repo_slug`(2),
   `_auto_respawn_check`(3) → `session_end_verdict`(2). 양방향.
2. **group3 → group4**: `_auto_respawn_check` → `_spawn_one` — 그룹3이
   허브(그룹4)를 역으로 호출.

## 선례 — gates/flows.py, gates/closure_sweep.py

이미 저장소 안에서 두 번 검증된 패턴(issue-172, issue-135, issue-178):
분리된 모듈 최상단에서 `sys.path.insert(0, str(Path(__file__).parent.parent))`
후 `import spawn`, 이후 전부 qualified 접근(`spawn.board(...)`,
`spawn._pr_for_branch(...)` 등) — bare-name import 없음. `spawn.py`의
`main()`은 해당 서브커맨드 분기에서 지연 import
(`sys.path.insert(...); import flows; return flows.flows(...)`,
spawn.py:2319-2325 부근 패턴)로 부른다. 재export shim은 issue-178의
survey.md가 별도 재현 스크립트로 확인한 이유(패치는 정의된 곳의
`__globals__`를 보지 재export 별칭을 안 봄, pytest 공식 문서와 일치)로
**기각된 전례**가 있다 — 이번에도 같은 결론을 재사용한다(재도출 불필요).

두 선례 모두 spawn.py로의 참조가 **단방향**(분리된 모듈 → spawn.py)
이었다 — 이번 이슈의 group2↔3, group3→4처럼 "spawn.py에 남는/다른
분리 모듈이 방금 옮긴 모듈을 되불러야 하는" 역방향 케이스는 이
저장소에 아직 전례가 없다(scout-brief.md가 외부에서 이 갭을 메운다).

## 외부 호출 지점 — 진입점 계약 확인

`python3 <checkout>/spawn.py <role> "<task>" --issue <n> -C <repo>`
계약을 참조하는 곳(전부 `subprocess`로 절대경로 실행, `import spawn`
아님 — 내부 모듈 구조와 무관):
`on-the-record/hooks/directive.sh`, `on-the-record/hooks/self-update.sh`,
`on-the-record/hooks/deliverable-guard.sh`, `on-the-record/commands/run.md`,
`bench/run.py`, `ledger/collect.py`. 이들은 spawn.py가 그 경로에 실행
가능한 파일로 남아 동일 CLI 동작(인자·종료코드·출력 포맷)만 내면
그만이다 — 이슈의 제약("절대경로 단일 진입 호출 계약 유지")과 정확히
일치, 내부 분리는 자유.

`import spawn`으로 **모듈 내부**를 직접 참조하는 곳(구조 변경에
민감): `test_spawn.py`, `test_gates.py`, `test_approve_scope.py`,
`gates/flows.py`, `gates/closure_sweep.py`.

## 보호 경로 (gates/gates.py:26-30)

```python
PROTECTED_ROOT_FILES = {"protocol.md", "protocol.ko.md", "spawn.py",
                        "jenkinsfile", ".gitlab-ci.yml"}
PROTECTED_ROOT_DIRS = {"roles", "gates", "agents", "images", "profiles"}
```

`is_protected()`(gates.py:56-67)는 1단짜리 경로면 `PROTECTED_ROOT_FILES`
정확 일치로만 보호한다 — 새 루트 형제 파일(예: `rulebook.py`)은 오늘
**보호되지 않는다**. `gates/` 아래는 이미 통째로 보호되지만, rulebook/
board/roster는 "게이트"가 아니라 오케스트레이터 핵심 서브시스템이라
`gates/`에 넣는 것은 의미상 어긋난다(제안서에서 대안으로 검토하고
기각).

## 테스트 베이스라인

```
$ python3 test_spawn.py
Ran 144 tests in 5.494s
FAILED (errors=25)
```

144개(issue-178 시점 125개에서 issue-180/182 작업으로 증가). 25건 전부
`rulebook_checkout`이 실제 `git clone`을 타는 경로(`EventReporting`/
`ProgressEvents`/`IssueScopedPrompt` 등)에서 나며, 이 샌드박스가 아웃바운드
git 접근을 막아 생기는 환경 제약이다 — 실측(단일 테스트 격리 실행,
`ProgressEvents.test_write_tool_use_fires_progress`)으로 확인: 트레이스백이
`rulebook_checkout`(spawn.py:207) 안에서 `git clone`이 로컬 git 템플릿
파일(`commit-msg.sample`) 복사에 실패하며 나는 `SystemExit`다 — 리팩터와
무관. phase 2 검증은 네트워크 있는 환경에서 144개 전부 재실행해 이
25건이 사라지는지 확인해야 한다(issue-178과 동일한 사전조건).

`test_spawn.py`는 31개 최상위 테스트 클래스가 있고, 여러 곳에서
`self._patch(spawn, "_x", ...)`로 특정 심볼을 직접 패치한다 — 심볼이
새 모듈로 옮겨가면 패치 대상도 그 모듈로 재타겟해야 한다(issue-178
survey.md가 이미 실측한 메커니즘 그대로: 패치는 정의된 곳을 타겟).
클래스별 소속 그룹은 대체로 이름으로 판별 가능하다(예:
`Watchdog`/`SessionEndVerdict`/`AutoRespawnClaim`/`PostCrashComment`/
`RosterConcurrency`/`EventExitScope` → group3; `BoardSnapshot`/
`SessionResult`/`Classify`/`FailClosedDowngrade`/`GitHead`/`IsNewCommit`/
`OwnershipReport` → group2; `SpawnCmd`/`DryRunModelReflection`/
`WebToolPermissionAccess`/`PackageRegistryAccess`/
`SandboxDefaultOpenAccess` → group1; 나머지는 group4 또는 여러 그룹에
걸침) — 정확한 목록은 phase 2 착수 시 해당 단계 대상 함수를 grep해
재확인한다.

## 동시성 리스크 구간 (issue-178 선례가 이미 지목, 이번에도 유효)

파일이 자란 만큼 줄 번호를 재확인했다:

- `spawn.py:2423-2438` — `os.fork()`/`os.setsid()`/`os.dup2()`
  (`_spawn_one` 안, group4).
- `spawn.py:1267-1278` — `fcntl.flock`(`_roster_locked`, group3).
- `spawn.py:1478-1642` 대 — events offset(`_offset_path`/`_read_offset`/
  `_write_offset`, group3).

이번 분리가 group3(roster.py)을 옮기는 단계에서 `_roster_locked`/
offset 함수들의 **텍스트를 그대로**(로직 무변경) 옮기게 되므로, 그
구간의 바이트가 이동 전후 동일한지 diff로 확인하는 것으로 충분하다 —
동시성 버그 자체를 고치는 건 이번 스코프 밖(이슈 "관찰 가능한 동작 안
바꾼다" 제약과 직접 충돌).

## 시사점

- group1은 들어오는 교차-그룹 엣지가 0이라 가장 안전한 첫 이동
  후보(issue-178이 flows를 고른 것과 같은 "측정상 가장 깨끗한 후보"
  논리).
- group4는 허브라 마지막에 남기는 쪽이 이동 횟수를 최소화한다(옮기면
  옮길수록 47개 호출부를 전부 qualified로 고쳐야 함 — group4를 안
  옮기면 그 47개 호출부는 spawn.py 안에서 qualified 접근으로 한 번만
  고치면 됨).
- group2↔3 순환과 group3→4 역참조는 지연 import(이미 저장소가 main()
  분기에서 쓰는 패턴)로 끊을 수 있다 — 새 메커니즘 도입이 아니라
  기존 패턴의 재적용(scout-brief.md가 외부 확인).

구체적 단계 순서·모듈 경계·기각한 대안은 proposals/module-split.md에서
확정한다.

## Sources

내부(1차 소스, 이 체크아웃에서 직접 읽고 실행): spawn.py 전체(함수
경계·교차-그룹 호출 스캔, 결과는 위 표), gates/flows.py,
gates/closure_sweep.py, gates/gates.py:20-30·56-67, test_gates.py
(`t_protected_paths`), test_spawn.py(클래스 목록·`_patch` 사용처),
`python3 test_spawn.py` 전체 실행 + `ProgressEvents.
test_write_tool_use_fires_progress` 단일 격리 실행, on-the-record/hooks/
directive.sh·self-update.sh·deliverable-guard.sh, on-the-record/commands/
run.md, bench/run.py, ledger/collect.py(진입점 계약 참조처),
docs/issue-178/proposals/split-flows-into-gates.md +
docs/issue-178/reports/implementation/survey.md(재export 기각 근거,
보호 경로 판정 로직 재사용).

외부(scout-brief.md 경유, 보조 확인용): 하단 scout-brief.md의 Sources
참조.
