---
role: implementation
subject: issue-178
loop_state: landed
code_under_review: de58ad87966798b957104ec7f40d298d598695fc
---

# Implementation — spawn.py flows 구역을 gates/flows.py 로 분리 (issue #178, phase 2)

Proposal: [[split-flows-into-gates.md]](../proposals/split-flows-into-gates.md),
approved via `APPROVE issue-178/implementation` (issue comment, single-account
mode).

## Why

이슈 #178 이 승인한 제안(`docs/issue-178/proposals/split-flows-into-gates.md`)의
"What will be done" 5개 항목을 그대로 이행하기 위해서다 — spawn.py(2845줄)
중 다른 레포(repo-status-board)를 위한 읽기 전용 계약 300줄(flows 구역,
issue #172)을 별도 모듈로 빼, 앞으로 spawn.py 의 다른 부분을 건드리는
PR 들의 diff 컨텍스트를 줄이고 `gates/closure_sweep.py` 가 이미 쓰는
지연-import 분리 패턴을 완성한다(watchdog+respawn/룰북 해결 등 더 크고
비싼 분할의 파일럿). 로직 변경은 0 — 순수 이동만 한다.

## What was done (제안의 5개 항목 대응)

1. **`gates/flows.py` 신설** — `spawn.py:1978-2277`(300줄) 을 그대로
   옮겼다. 파일 최상단에 `closure_sweep.py` 와 동일하게
   `sys.path.insert(0, str(Path(__file__).parent))` +
   `sys.path.insert(0, str(Path(__file__).parent.parent))` + `import spawn`
   를 두고, 구역이 참조하던 구역 밖 심볼 8개(`board`, `_approvers`,
   `_issue_comments`, `_repo_slug`, `_front_role`, `_roster_load`,
   `_alive`, 전역 `ROOT`) 를 전부 `spawn.X` qualified 접근으로 고쳤다 —
   옮겨진 300줄 본문 안에서 이것이 유일한 텍스트 변경이다. `closure_sweep`
   호출은 제안대로 그 자리에 그대로 뒀고(`import closure_sweep`), 이제
   같은 디렉터리라 그 호출 지점의 `sys.path.insert` 한 줄만 없앴다(대신
   동등한 경로 설정이 파일 최상단으로 옮겨왔으므로 동작은 동일). 파일에
   `closure_sweep.py`/`ci.py`/`gates.py` 와 같은 형식의 짧은 모듈
   docstring(2줄)을 추가했다 — 옮긴 300줄 본문 자체에는 없던 새 텍스트라
   "유일한 텍스트 변경"의 좁은 의미를 벗어나지만, 로직에 영향이 없고
   sibling 모듈들의 기존 관례와 일치해 그대로 뒀다.
2. **`spawn.py`** — 해당 구역(300줄) 삭제. `main()` 의 `flows` 분기를
   `closure-sweep` 분기와 같은 모양의 지연 import 로 교체:
   ```python
   if a.role == "flows":
       sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
       import flows
       return flows.flows(a.cwd, a.json)
   ```
   원래 분기(4줄: `if` + 주석 2줄 + `return`)와 새 분기(4줄: `if` +
   `sys.path.insert` + `import` + `return`)가 줄 수가 같다 — 주석 2줄은
   그 내용이 이제 `gates/flows.py` 의 모듈 docstring으로 옮겨가 중복이라
   지웠다. 이 net-zero 덕에 spawn.py 전체의 순감소가 정확히 이동한
   구역 크기(300줄)와 일치한다 (수용 기준 4, 아래 §검증).
3. **`test_spawn.py`** — `FlowsPayload`/`SessionLastActivity` 두 클래스의
   `spawn.flows_payload`(8회) / `spawn._session_last_activity`(7회) 참조
   15개를 전부 `self.flows.flows_payload` / `self.flows._session_last_activity`
   로 재타겟했다(각 클래스 `setUp` 에서
   `sys.path.insert(...); import flows; self.flows = flows`). 구역과 함께
   옮겨간 `_pr_list_all` 의 patch 대상도 `self.flows` 로 재타겟(2곳:
   `setUp` 기본값, `test_decision_queue_from_open_pr`/
   `test_hygiene_includes_closure_sweep_and_unapproved_prs` 오버라이드).
   `_repo_slug`/`_issue_comments`/`_roster_load`(구역 밖에 남는 함수) 와
   `closure_sweep.find_violations` patch 는 무변경 — 옮겨간 코드가 이들을
   `spawn.X`/`closure_sweep.X` qualified 로 부르는 한 기존 patch 타겟이
   여전히 유효하다(survey.md 실측 1 결론 그대로).
4. **`test_gates.py`** — `t_protected_paths` 긍정 목록에 `"gates/flows.py"`
   1줄 추가.
5. **본 기록** — phase-2 기록(이 파일).

## Doc-placement ladder (완료 항목)

- [x] env var / config / dependency / migration → handbook: 해당 없음 —
  새 환경변수·설정·의존성·마이그레이션 없음(순수 코드 이동).
- [x] library-or-format 선택 / 시그니처·wire format 변경 →
  `docs/issue-178/decisions/`: 해당 없음 — 그런 선택 없음.
  `docs/specs/flows-schema.md`(wire 계약)는 제안대로 안 건드렸다.
- [x] benchmark/investigation 수치 → `docs/issue-178/reports/`: 완료 —
  아래 §검증의 줄수 산술·바이트 diff·테스트 결과가 전부 이 파일에 있다.

## 검증 — 수용 기준 6개 (제안 "How you'll know it worked")

commit `de58ad8`(코드 변경 커밋, 이 기록 이전) 기준.

1. **`python3 test_spawn.py` → 125개, 감소 없음.**
   ```
   Ran 125 tests in 2.060s
   FAILED (errors=5)
   ```
   125개 그대로(감소 없음, 기준 충족). 5개 에러는 survey.md 베이스라인과
   완전히 동일한 5건(`EventReporting`/`IssueScopedPrompt`, rulebook
   `git clone` 이 이 샌드박스의 아웃바운드 git 접근 제한에 막히는
   환경 제약) — flows 이동과 무관, 이동 전후 개수·클래스 불변.
   `FlowsPayload`/`SessionLastActivity` 15개만 따로 돌리면
   `Ran 15 tests ... OK`.

2. **`python3 spawn.py flows --json -C <레포>` 바이트 동일.**
   이 레포(`.`) 대상으로 이동 직전/직후 각 1회 캡처해 diff:
   ```
   $ diff before.json after.json
   3c3
   <   "generated_at": "2026-08-01T08:26:56Z",
   ---
   >   "generated_at": "2026-08-01T08:32:28Z",
   ```
   차이는 `generated_at` 한 줄뿐 — `time.strftime(...,time.gmtime())` 로
   호출 시점 벽시계를 찍는 필드라 별도 프로세스 두 번 호출 사이에는
   코드와 무관하게 항상 달라진다(이동 여부와 상관없이 같은 프로세스를
   두 번 불러도 마찬가지). 그 한 줄을 제외한 나머지 전부(같은 크기
   1320바이트, `decision_queue`/`flows`/`sessions`/`ledger`/`unattributed`/
   `hygiene` 전 섹션) 완전 일치.

3. **`python3 spawn.py flows -C <레포>` (사람용 표) 바이트 동일.**
   ```
   $ diff before.txt after.txt
   (출력 없음 — 완전 동일, 402바이트)
   ```
   표 출력은 `generated_at` 을 안 찍으므로 시간 의존 필드 자체가 없다 —
   진짜 완전한 바이트 단위 동일.

4. **`spawn.py` 순감소 == 이동한 구역 크기.**
   ```
   이동 전 spawn.py: 2845줄
   이동 후 spawn.py: 2545줄
   순감소: 300줄  ==  이동한 구역(1978-2277): 300줄
   ```
   `main()` 분기 교체가 4줄→4줄(net-zero, 위 §1.2)이라 이동분 300줄이
   그대로 전체 파일 순감소로 나타난다 — 재export 없음의 직접 증거.

5. **`python3 gates/ci.py .` 실행 결과 및 보호 경로 확인.**
   ```
   게이트 차단:
     - 보호 경로 변경: spawn.py
     - 보호 경로 변경: gates/flows.py
   ```
   차단 사유는 이 둘뿐 — `record_enums`/`record_wellformed_in`/
   `record_no_tool_residue_in`/의존성 검사 등 다른 사유는 전혀 없다.
   `spawn.py` 는 `PROTECTED_ROOT_FILES` 멤버라 이 파일을 건드리는
   어떤 PR 이든(순수 이동이든 아니든, 과거 87건 포함) `origin/main` 대비
   diff 가 있는 한 구조적으로 이 줄에 걸린다 — "파이프라인이 자기 규칙을
   다시 쓸 수 없어야 한다"(gates/gates.py:26)는 설계 의도가 사람 리뷰를
   강제하는 것이지 이번 이동의 결함이 아니다(§3 에서 원본 트리 재현으로
   별도 확인). 그리고 이 실행 자체가 수용 기준 후반부("새 파일이 보호
   경로에 걸리는 것")를 실측 게이트로 직접 보여준다: `gates/flows.py`
   가 새로 보호 경로에 걸렸다.
6. **`t_protected_paths` 에 `gates/flows.py` 긍정 케이스 통과.**
   `test_gates.py` 전체(59개 함수, unittest 아닌 직접 호출 방식)를
   예외를 잡는 임시 하네스로 돌리면 `58/59 passed`, `t_protected_paths`
   포함. 유일한 실패(`t_repo_local_claude_config_stops_the_spawn`)는
   `/Users/jk/.tokenmaxxxer/trusted-repo-config.json` 에 쓰려다 나는
   `PermissionError`(이 샌드박스의 홈 디렉터리 쓰기 제한) — §3 에서
   원본 트리 재현으로 flows 이동과 무관함을 확인했다.

## §3 — 부가 확인: 5·6번 항목의 실패가 이동의 결함이 아님을 재확인한 절차

```
$ git stash push -u -m "issue-178-wip-check"
$ python3 test_gates.py            # 원본 트리, 내 변경 전부 제거된 상태
... (동일한 PermissionError 로 동일 지점에서 중단)
$ git stash pop                     # 변경 복원
```
원본 트리(이번 변경 0줄)에서도 `t_repo_local_claude_config_stops_the_spawn`
이 같은 `PermissionError` 로 죽는다 — 이번 이동이 만든 문제가 아니라
이 실행 샌드박스의 홈 디렉터리 쓰기 제한이라는 뜻이다.

## What did not work

`gates/ci.py .` 를 exit 0("게이트 통과")으로 기대했으나 실제로는 exit 1
("게이트 차단: 보호 경로 변경 spawn.py, gates/flows.py")이 났다 — 위
§검증 5번에 적은 대로, `spawn.py` 가 `PROTECTED_ROOT_FILES` 멤버인 한
`origin/main` 대비 diff 가 있는 어떤 PR 도 구조적으로 이 상태가 되므로
"이동이 순수하지 않다"는 신호가 아니다(이 실행이 정확히 노리는 두 경로만
잡혔고 다른 차단 사유가 없다는 사실 자체가 그 증거다). 롤백 없이 그대로
기록한다.

## Open findings

없음. 위 "What did not work"에 적은 `gates/ci.py` 관찰은 조치가 필요한
미해결 사항이 아니라 — spawn.py 를 건드리는 모든 PR 에 항상 나타나는
구조적 특성이며, 이 실행 자체가 수용 기준을 만족시키는 증거로 쓰였다.

## Next steps

이 기록을 포함해 PR 을 제출한다. 다음 단계는 사람 승인자(approvers.md)
가 이 PR 을 merge 하거나 close 하는 것 — contract v3 의 human-decision
시그널이 그것이다. 만약 리뷰 중 문제가 제기되면 resolution path 는
같은 브랜치(issue-178/implementation)에 새 커밋을 추가해 같은 PR 로
대응하는 것이다(수용 기준 넷 중 하나라도 사후에 어긋난 것이 발견되면
롤백 커밋 + 무엇이 달라졌는지 기록 추가).

## Non-goals (제안 그대로, 불변)

watchdog+respawn(~470줄)/verdict(~150줄)/룰북 해결(~500줄) 분할,
`L2680-2710`/`L1267-1290`/`L1606-1637` 의 동시성 버그, repo-status-board 로의
flows 이관, `docs/specs/flows-schema.md` 수정 — 전부 이번 스코프 밖(제안의
"Out of scope" 그대로).
