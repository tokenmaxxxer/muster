# Survey — issue #204: 역할 세션 테스트의 네트워크 의존 제거

## 스카우트 스킵 기록

스킵 조건 1(순수 버그픽스에 준함) 적용. `spawn.py` 의 프로덕션 동작은 전혀
바뀌지 않는다 — 테스트 하네스가 이미 지원되는 로컬 오버라이드
(`$TOKENMAXXXER_RULEBOOKS`, `$TOKENMAXXXER_CORE`)를 픽스처로 채우는 테스트
설정 작업이다. 제품-형 표면(사용자가 보는 UI/API)이 아니라 내부 CI
하네스이므로 외부 best-in-class 제품 비교 대상이 없다. 이슈 #201의 survey와
동일한 종류의 스킵. scout-brief.md는 작성하지 않는다.

## 재현 방법론 — 이 세션의 Bash 샌드박스가 "네트워크 차단"과 등가인 이유

이 세션(`implementation` 역할, issue-204) 자체가 이슈가 말하는 "역할 세션의
샌드박스"다. `unset TOKENMAXXXER_RULEBOOKS TOKENMAXXXER_CORE` 뒤
`rulebook_checkout`(`spawn.py:175`)이 실제 `git clone`을 시도하면, 저장소 경로
밑에 클론하려다 git hook 템플릿 복사가 샌드박스에 막힌다:

```
fatal: cannot copy '.../commit-msg.sample' to
  '.../runs/rulebooks/execution-observation-rulebook/...': Operation not permitted
```

이슈 #201의 survey가 이미 기록한 것과 같은 종류의 증상(D2) —
진짜 DNS/방화벽 차단이 아니라 저장소 경로 하위 쓰기 제약이지만, **결과는
이슈가 말하는 것과 동일하다**: `rulebook_checkout`이 `SystemExit`으로 죽는다.
이 세션에서는 이 경로가 "네트워크 차단 환경"의 실측 대리자 역할을 한다 —
실제 DNS 차단이든 이 hook-copy 거부든, `rulebook_checkout`을 실패시킨다는
점에서 동등하다.

## 전수 조사 — `test_spawn.py`

`TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE` 미설정 상태에서
`python3 -m pytest test_spawn.py test_gates.py -q`:

```
18 failed, 134 passed in 7.20s
```

18건 전부 아래 두 함수 중 하나가 예외를 던진다 — **다른 실패 원인은
하나도 없다**:

- `spawn.py:207` `rulebook_checkout`의 `sys.exit(...)` (git clone 실패, 위 절 참고)
- `spawn.py:2550` `finally: if not is_parent_return:` 의 `UnboundLocalError`
  (원인은 `spawn.py:1807` `core_root()`의 `sys.exit` — `tokenmaxxxer-core`도
  못 받으면 `is_parent_return`이 대입되기 전에 함수를 벗어난다. 이슈 #201
  survey가 "샌드박스 확인 사항"에 기록한 것과 같은 실패 클래스, 다른 전조.)

18건 전부 **역할 하나**(`execution-observation`)로 `spawn._spawn_one(...)`을
직접 부른다 — 다른 역할을 쓰는 실패는 없다:

| 클래스 | 테스트 | 줄 | 범위 |
|---|---|---|---|
| `Ledger` | `test_entry_carries_the_live_log_path` | 800 | **범위 밖 — 이슈 #201** |
| `IssueScopedPrompt` | `test_preparation_and_preamble_happen_once` | 940 | **범위 밖 — 이슈 #201** |
| `EventReporting` | `test_end_turn_result_is_not_a_gate_refusal` | 1065 | (a) |
| `EventReporting` | `test_echoed_source_mentioning_denied_is_not_a_gate_refusal` | 1074 | (a) |
| `EventReporting` | `test_real_denial_still_reported` | 1085 | (a) |
| `EventReporting` | `test_pr_opened_does_not_refire_across_respawns` | 1091 | (a) |
| `EventReporting` | `test_read_only_repo_url_does_not_fire_pr_opened_when_no_pr_exists` | 1104 | (a) |
| `EventReporting` | `test_read_only_repo_url_does_not_fire_pr_opened_when_different_pr_open` | 1112 | (a) |
| `EventReporting` | `test_pull_new_branch_url_does_not_fire_pr_opened` | 1119 | (a) |
| `EventReporting` | `test_actually_opened_pr_fires_pr_opened` | 1129 | (a) |
| `EventReporting` | `test_pr_for_branch_call_count_not_proportional_to_candidate_urls` | 1138 | (a) |
| `EventReporting` | `test_pr_for_branch_keeps_retrying_while_unresolved` | 1156 | (a) |
| `ProgressEvents` | `test_write_tool_use_fires_progress` | 1179 | (a) |
| `ProgressEvents` | `test_consecutive_writes_to_same_file_are_deduped` | 1191 | (a) |
| `ProgressEvents` | `test_writes_to_different_files_both_fire` | 1202 | (a) |
| `ProgressEvents` | `test_verification_and_commit_commands_fire_progress` | 1213 | (a) |
| `ProgressEvents` | `test_exploratory_bash_does_not_fire_progress` | 1226 | (a) |
| `ProgressEvents` | `test_gate_refusal_parsing_still_works_alongside_progress` | 1238 | (a) |

이슈 본문이 범위 밖으로 못박은 두 건(`Ledger`, `IssueScopedPrompt`)은 이번
조사에서 손대지 않는다 — 이미 이슈 #201(PR #203, 커밋
`6a54d5a`)로 고쳐져 이 브랜치에 있고, 관측점(`roster_register` 스파이)
자체는 정상이다. 지금 실패하는 이유는 그 관측점에 도달하기도 전에
`_spawn_one`이 `rulebook_checkout`에서 죽기 때문이다 — 즉 이번 이슈가 걷어낼
바로 그 병목이 이 두 건도 같이 가리고 있다(§단일 병목점 참고).

`ProgressEvents`(1172줄)의 `_run`은 `EventReporting()._run`을 그대로
재사용한다(`test_spawn.py:1177`) — 두 클래스가 완전히 같은 코드 경로를 탄다.

## `EventReporting._run`/`ProgressEvents._run`이 이미 모킹하는 것

`test_spawn.py:1044-1054`:

```python
mock.patch.object(spawn, "issue_workspace", ...), \
mock.patch.object(spawn, "checkout_issue_branch", ...), \
mock.patch.object(spawn, "spawn_cmd", lambda *a, **k: (["cat"], {})), \
mock.patch.object(spawn, "ensure_pushed", ...), \
mock.patch.object(spawn, "ledger_write", ...), \
mock.patch.object(spawn, "_pr_for_branch", pr_for_branch):
    spawn._spawn_one(str(work), "execution-observation", task, unattended=True, issue=7)
```

`spawn_cmd`가 실제 `claude` CLI 커맨드 대신 `["cat"]`으로 바뀐다 — 즉
`plugin_dirs()`/`core_plugin_dirs()`가 돌려주는 **디렉터리 목록의 실제
내용물은 어차피 실행되지 않는다.** 이 두 함수가 필요로 하는 건 오직
"체크아웃이 있고 marketplace.json 이 최소 한 플러그인을 가리키며 그
플러그인 디렉터리에 `.claude-plugin/plugin.json` 이 있다"는 **구조** 뿐이다
— 목으로 살리는 게 아니라, 실제 함수(`rulebook_checkout`, `plugin_dirs`,
`core_root`, `core_plugin_dirs`)를 그대로 돌리면서 그 함수들이 찾는 자리에
최소 골격을 채워 넣는 것으로 충분하다.

## 단일 병목점 — 두 함수, 두 환경변수

`spawn.py:2379` `plugins = plugin_dirs(role, spec)` → `spawn.py:234`
`rulebook_checkout(role, spec)` → `spawn.py:190` `_path(spec)` →
`spec["path"]` = `roles/execution-observation.json`의
`"$TOKENMAXXXER_RULEBOOKS/execution-observation-rulebook"`(역할 파일 실측,
`roles/execution-observation.json:4`). 로컬에 `<path>/.claude-plugin/marketplace.json`
이 있으면 그걸 쓰고 끝 — 없으면 `sys.exit`(네트워크 클론 실패 시) 또는 실제
클론.

`_spawn_one` 안 어딘가(이번 조사로 정확한 줄은 특정하지 않음, 18건 모두의
공통 실패 지점이 `plugin_dirs`/`core_root` 둘 중 하나라는 사실만으로 배정에
충분함)에서 `core_plugin_dirs()`(`spawn.py:1813`) → `core_root()`
(`spawn.py:1773`)도 불린다. `core_root()`의 탐색 순서(`spawn.py:1780-1782`):

1. `$TOKENMAXXXER_CORE` (환경변수, 직접)
2. `$TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core` (**RULEBOOKS 변수 재사용**)
3. `ROOT.parent/tokenmaxxxer-core` (레포 옆 디렉터리)

각 후보에 대해 `<candidate>/core/.claude-plugin/plugin.json`이 있어야
채택된다. 셋 다 없으면 `runs/rulebooks/tokenmaxxxer-core`로 실제 clone을
시도하고, 그것도 실패하면 `sys.exit`(`spawn.py:1807-1810`).

## 스파이크 검증 — 픽스처 하나로 18건 전부 해소되는지 실측

이 세션의 샌드박스 안에서 임시 디렉터리(레포 밖, `$TMPDIR` 하위)에 최소
골격 픽스처를 만들어 실측했다(레포에는 아무것도 커밋하지 않음 — 순수
가설 검증):

```
<fixture>/execution-observation-rulebook/.claude-plugin/marketplace.json
  {"plugins": [{"name": "execution-observation", "source": "./execution-observation"}]}
<fixture>/execution-observation-rulebook/execution-observation/.claude-plugin/plugin.json
  {"name": "execution-observation"}
<fixture>/tokenmaxxxer-core/core/.claude-plugin/plugin.json
  {"name": "core"}
```

`TOKENMAXXXER_RULEBOOKS=<fixture>`, `TOKENMAXXXER_CORE=<fixture>/tokenmaxxxer-core`
로 설정하고(둘 다 명시적으로 — §단일 병목점의 두 독립 진입점을 각각 직접
채움) `python3 -m pytest test_spawn.py -q`:

```
152 passed in 12.74s
```

**18건 전부 해소** — 범위 밖으로 못박은 2건(`Ledger`,
`IssueScopedPrompt`)도 부수적으로 통과한다(이미 존재하는 #201 수정이 이
병목 뒤에서 정상 동작함을 재확인하는 것일 뿐, 이번 이슈가 그 관측점 자체를
다시 손대는 것은 아니다). `spawn.py`는 전혀 건드리지 않았다 — 순수하게
기존에 지원되는 두 환경변수에 값을 채운 것만으로 전체 해소.

## `test_gates.py` 조사

### (1) 이슈 본문이 지목한 명령으로는 오늘 0건 실패 — 수집조차 안 됨

`test_gates.py`의 테스트 함수는 전부 `t_` 접두(`test_` 아님, 예:
`t_slug_is_directory_name`, `test_gates.py:32`) — pytest 기본 수집 규칙에
안 걸린다. 저장소에 `pytest.ini`/`conftest.py`/`pyproject.toml` 이 전혀 없어
(확인: 루트에 없음) 커스터마이즈도 없다. 실측:

```
$ python3 -m pytest test_spawn.py test_gates.py -q
18 failed, 134 passed in 7.20s   # test_gates.py 관련 실패/통과 항목 0건 — 애초에 안 걸림
```

즉 이슈 본문이 요구사항 1에 적은 그 명령으로는 `test_gates.py`가 오늘도
**항상 0건 실패**다(단 하나도 실행이 안 되므로). 이 파일의 자체 진입점
(`test_gates.py` 상단 docstring: "python3 test_gates.py")으로 돌려야 실제
내용을 볼 수 있다.

### (2) 자체 진입점으로 돌리면: 네트워크 실패 0건, 무관한 실패 1건

```
$ python3 test_gates.py     # TOKENMAXXXER_RULEBOOKS/CORE 미설정
  ok  t_board_absent_names_the_v1_location
  ... (43건 ok)
Traceback ...
  File "test_gates.py", line 128, in t_repo_local_claude_config_stops_the_spawn
    spawn.require_no_repo_config(str(root), True)
  File "spawn.py", line 777, in require_no_repo_config
    pins.write_text(...)
PermissionError: [Errno 1] Operation not permitted:
  '/Users/jk/.tokenmaxxxer/trusted-repo-config.json'
```

이 실패는 **네트워크와 무관**하다 — `spawn.require_no_repo_config`
(`spawn.py:726`)이 레포 밖 `$HOME/.tokenmaxxxer/trusted-repo-config.json`
(`spawn.py:767`)에 쓰려다, 이 세션 Bash 도구의 샌드박스가 레포 경로 밖
쓰기를 막아서 난다(실제 파일은 존재하고 OS 퍼미션도 정상 — `ls -la`로
확인, 순수히 이 세션의 도구 경계 문제). `$HOME`을 쓰기 가능한 임시
디렉터리로 우회하면:

```
$ HOME=<tmp>  python3 test_gates.py   # (내부적으로 os.environ 재설정 후 실행)
  ok  t_rulebook_falls_back_to_github
  ok  t_new_roles_resolve_without_a_local_checkout
  ...
61 passed
```

**61건 전부 통과, 네트워크 호출 0건.** `t_rulebook_falls_back_to_github`
(`test_gates.py:167`)와 `t_new_roles_resolve_without_a_local_checkout`
(`test_gates.py:207`)은 이름과 달리 `spawn.rulebook_source(spec)`만 부른다
(`test_gates.py:179,215`) — 이 함수는 **순수 판단 함수**(`spawn.py:141`,
"로컬 체크아웃이 있으면 그쪽, 없으면 github 라고 판단만 하고 리턴")라 실제
clone을 하지 않는다. 파일 docstring이 스스로 적은 설계("네트워크·GitHub
없이 도는 것만", `test_gates.py:2`)가 실측으로 확인된다.

**결론: `test_gates.py`는 네트워크 의존 실패가 0건이다.** 유일한 실패
(`t_repo_local_claude_config_stops_the_spawn`)는 이 세션의 도구 경계가 만든
것이지 파일 자체의 문제가 아니고, 그마저도 이슈 본문의 pytest 명령으로는
애초에 실행되지 않는다.

### 발견 — pytest 미수집은 이번 이슈의 범위로 다루지 않는다

`test_gates.py`를 `python3 -m pytest ...`로 실제 수집·실행되게 만드는 것
(예: `t_` → `test_` 개명, 또는 `python_functions` 설정 추가)은 그 자체로
검토할 만한 별도 개선이지만, **네트워크 의존과 무관**하고 이슈 본문이
요구하는 것(요구사항 1: 그 명령이 실패 0)은 이미 참이다. 이번 제안의
쓰기 대상에 넣지 않는다 — 범위를 벗어난 재설계(테스트 발견 규칙 변경)이지
네트워크 제거가 아니다.

## 배정 결론

- **(a) 로컬 오버라이드 픽스처 주입 — 16건 전부.** `test_spawn.py`의
  `EventReporting`/`ProgressEvents` 두 클래스, 16개 테스트 메서드. 스파이크
  실측(§스파이크 검증)으로 최소 골격 픽스처 하나 + 환경변수 두 개
  (`TOKENMAXXXER_RULEBOOKS`, `TOKENMAXXXER_CORE`) 설정만으로 16건 전부
  해소를 확인. 개별 테스트를 건드릴 필요 없음 — 진입점(`conftest.py`)
  하나로 전부 해소된다.
- **(b) network 마커 + skip — 0건.** "검증 대상 자체가 네트워크 fetch"인
  테스트가 이 18건 중에 없다. `rulebook_source()`의 판단 로직을 검증하는
  두 테스트(`test_gates.py:167,207`)는 애초에 순수 함수라 네트워크를 타지
  않으므로 skip 대상도 아니다.
- **(c) 모킹 — 0건.** (a)로 전건 대체 가능해 최후 수단이 필요 없다.

## 쓰기 대상(write set) 예상

- `conftest.py` (신규, 레포 루트) — `TOKENMAXXXER_RULEBOOKS`/
  `TOKENMAXXXER_CORE`를 아래 픽스처로 `setdefault`(이미 설정된 환경은
  존중).
- `tests/fixtures/rulebooks/execution-observation-rulebook/.claude-plugin/marketplace.json` (신규)
- `tests/fixtures/rulebooks/execution-observation-rulebook/execution-observation/.claude-plugin/plugin.json` (신규)
- `tests/fixtures/rulebooks/tokenmaxxxer-core/core/.claude-plugin/plugin.json` (신규)

`spawn.py`, `test_spawn.py`, `test_gates.py` 본문 변경 없음 — 순수 추가.
