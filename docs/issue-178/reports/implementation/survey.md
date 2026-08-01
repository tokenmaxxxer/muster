---
role: implementation
subject: issue-178
loop_state: survey
---

# Current-state survey — spawn.py flows 구역 분할 (issue #178)

## 대상 구역 (spawn.py:1978-2277, 300줄)

정확히 이슈가 지목한 범위. AST 로 구역 내부에서 정의된 이름과, 구역
바깥에서 참조하는 이름을 직접 갈라 봤다(spawn.py 전체를 `ast.parse` 해
`lineno` 로 필터링, 재현 가능).

- **구역 안에서 정의**: `FLOWS_SCHEMA_VERSION`, `_STAGE_MAP`,
  `_BRANCH_RE`, `_BOARD_DELTA_ISSUE_RE`, `_stage_for`, `_pr_list_all`,
  `_pr_approved`, `_ledger_read`, `_ledger_issue`,
  `_activity_tool_summary`, `_session_last_activity`, `flows_payload`,
  `_age_hours`, `flows` — 이슈가 나열한 14개와 일치.
- **구역이 참조하는, 구역 밖 spawn.py 심볼**: `board`, `_approvers`,
  `_issue_comments`, `_repo_slug`, `_front_role`, `_roster_load`,
  `_alive`, 그리고 모듈 전역 `ROOT` — **7개 함수 + 전역 1개**.
  이슈 본문은 "8개 함수"(`status` 포함)라고 적었지만, `status` 는
  `flows_payload` 의 docstring 안 문장("`status()`'s own invariant")에만
  나오고 실제 호출은 없다 — 실측으로 정정. `board`/`closure_sweep`
  둘만 실제로 함수 호출 형태로 쓰이고 나머지는 각자 한 번씩.
- **구역이 참조하는 구역 밖 모듈**: `closure_sweep`
  (`flows_payload` 안에서 `sys.path.insert` 후 `import closure_sweep`,
  spawn.py:2219-2221 — closure_sweep 쪽도 자기 `main()` 안에서 동일한
  패턴으로 spawn 을 되돌려 부른다: 순환 관계지만 둘 다 함수 본문 안
  지연 import 라서 모듈 로드 시점 순환은 없음, 이미 오늘 시점에도
  성립).
- **구역 밖에서 구역 안 이름을 참조**: `flows()` 딱 하나, `main()` 의
  3줄(spawn.py:2315/2317-2318)뿐 — 이슈 서술과 일치.

## 선례 — gates/closure_sweep.py (153줄)

이미 반쯤 적용된 패턴: 자기 모듈 최상단에서
`sys.path.insert(0, str(Path(__file__).parent.parent))` 후
`import spawn` — 이후 `spawn.board(root)`, `spawn._pr_for_branch(...)`,
`spawn._issue_comments(...)`, `spawn._repo_slug(...)` 로 **전부 qualified
접근**(bare-name import 없음). `spawn.py` 의 `main()` 은 `closure-sweep`
분기에서 `sys.path.insert` 후 `import closure_sweep` 로 지연
import(spawn.py:2319-2325) — `flows` 분기에도 그대로 옮길 수 있는 모양.

## 실측 1 — 재export 가 test_spawn.py 를 무변경으로 두는가 (이슈 확인 항목 1)

`test_spawn.py` 의 `FlowsPayload`/`SessionLastActivity` 두 클래스
(1554-1749행, 15개 `spawn.` 참조)를 그대로 세어보면:

- `self._patch(spawn, "_pr_list_all", ...)` — 2회 (setUp 기본값 1,
  `test_decision_queue_from_open_pr` 오버라이드 1). `_pr_list_all` 은
  **구역 안에서 정의**되어 함께 옮겨가는 이름이다.
- `self._patch(spawn, "_repo_slug"/"_issue_comments"/"_roster_load", ...)`
  — 3회, 전부 **구역 밖**(spawn.py 에 남는) 함수.
- `spawn.flows_payload(...)` / `spawn._session_last_activity(...)` 직접
  호출 — 9회.
- `spawn.ROOT = self.root` (setUp), `spawn.BOARD`, `spawn.ledger_write(...)`
  — spawn.py 에 그대로 남는 이름들.

별도 재현으로 메커니즘을 직접 확인했다(`$TMPDIR` 에 `a.py`/`b.py`
2모듈, `b.py` 가 `from a import f, _x` 로 재export):

```
before patch, b.f() = 1
after patching b._x, b.f() = 1      # 재export 쪽만 패치 — 효과 없음
after patching a._x, b.f() = 3      # 정의된 곳을 패치 — 반영됨
```

`f`(≈`flows_payload`) 의 자유변수 조회는 `f.__globals__`(정의된 모듈의
네임스페이스)를 보지, 호출자가 어느 이름으로 불렀는지는 안 본다 —
pytest 공식 문서의 "patch 는 실제로 쓰이는 곳을 타겟해야 한다" 원칙과
정확히 같다(scout-brief.md 참조).

**결론**: 재export 로 spawn.py 에 `from flows import flows_payload, ...`
를 둬도 위 4개 `_patch` 호출 중 `_pr_list_all` 2건은 여전히 깨진다 —
`_pr_list_all` 이 구역과 함께 새 모듈로 옮겨가고, `flows_payload` 가
그것을 자유변수로 참조하기 때문. 나머지 3개 `_patch`(`_repo_slug` 등,
구역 밖에 남는 함수)와 9개 직접 호출은 재export 만으로도 안 깨진다 —
그 함수들은 spawn.py 에 그대로 있고, 옮겨간 코드가 그것들을
`spawn.X(...)` 식 qualified 접근으로 부르는 한(선례와 동일한 방식)
`spawn.X` 패치가 여전히 유효하다.

그런데 이 구분은 실무적으로 무의미하다 — **수용 기준 자체가 재export
를 막는다**: "`spawn.py` 의 순감소 줄 수가 이동한 구역 크기와 일치"
조건은 재export 로 남기는 줄만큼 순감소가 이동 크기에서 벗어나게
만든다. 즉 재export shim 은 문법적으로는 가능해도 이 이슈의 수용
기준을 못 지킨다 — 따라서 "재export 로 무변경 가능한가"의 답은
이슈 본문 판단대로 **없다**이고, 실측이 그 판단을 확인했다. 다만
이유는 이슈가 짚은 메커니즘(자유변수 바인딩)에 더해 수용 기준 자체가
재export 옵션을 배제한다는 점까지 겹친다.

## 실측 2 — 보호 경로 갱신 비용 비교 (이슈 확인 항목 2)

`gates/gates.py:26-30`:

```python
# 파이프라인이 자기 규칙을 다시 쓸 수 없어야 한다.
PROTECTED_ROOT_FILES = {"protocol.md", "protocol.ko.md", "spawn.py",
                        "jenkinsfile", ".gitlab-ci.yml"}
# 역할 정의와 배선. 루트의 것만 — 앱의 src/roles/ 는 정상 자산이다.
PROTECTED_ROOT_DIRS = {"roles", "gates", "agents", "images", "profiles"}
```

`is_protected()`(gates.py:56-67) 판정: 경로의 첫 세그먼트가
`PROTECTED_ROOT_DIRS` 에 있으면(2단 이상 경로) 무조건 보호, 1단짜리
경로면 `PROTECTED_ROOT_FILES` 정확 일치로 보호. `gates` 는 이미
`PROTECTED_ROOT_DIRS` 에 있다 — `test_gates.py:365` 의
`t_protected_paths` 가 `"gates/gates.py"` 를 보호 긍정 케이스로 이미
검증하고 있다(같은 로직이 `gates/` 아래 모든 파일에 적용됨).

세 후보의 실제 비용:

| 위치 | `gates/gates.py` 변경 | `test_gates.py` 변경 | 비고 |
|---|---|---|---|
| `gates/flows.py` | **0줄** — 이미 `gates` 가 PROTECTED_ROOT_DIRS 에 있음 | `t_protected_paths` 긍정 목록에 `"gates/flows.py"` 1줄 추가(수용 기준이 명시적으로 요구) | closure_sweep.py 와 같은 디렉터리·같은 패턴 |
| 루트 `flows.py` | `PROTECTED_ROOT_FILES` 에 `"flows.py"` 1줄 추가 | 같은 1줄 추가 | 루트에 spawn.py 외의 보호 대상 모듈이 새로 생김 — 오늘은 전례 없음 |
| 새 디렉터리(예: `board/flows.py`) | `PROTECTED_ROOT_DIRS` 에 새 이름 1줄 추가 | 같은 1줄 추가 | 파일 하나를 위해 새 최상위 보호 디렉터리 개념을 만드는 과잉 |

`gates/flows.py` 만 `gates/gates.py` 자체를 건드리지 않는다 — 나머지
둘은 보호 목록 자체의 diff 가 하나 더 생긴다(리뷰 대상이 하나
늘어난다는 뜻이기도 하다: 보호 목록은 "파이프라인이 자기 규칙을 다시
쓸 수 없어야 한다"는 코멘트가 붙은, 신뢰 경계에 가까운 코드다).

## 실측 3 — 충돌 측정치 재검증 (이슈 확인 항목 3, 대안 1)

이슈가 든 수치를 이 체크아웃에서 그대로 재현:

```
$ git log --oneline | wc -l              → 368
$ git log --oneline -- spawn.py | wc -l  → 87   (24%, 이슈와 일치)
$ 최근 7일 spawn.py 일별 커밋 수: 7, 8, 10, 11, 12, 18, 21   (이슈의 "7~21건"과 일치)
```

수치 자체는 정확하다. 그런데 87건 중 **flows 구역 자체를 건드린
커밋은 몇 건인지**를 따로 셌다(`git log -S"FLOWS_SCHEMA_VERSION"`,
`git log --oneline | grep -i "172\|flows"`):

```
c02d693 issue-172: phase 2 — spawn.py flows --json + flows-schema.md + tests
8ecfe99 issue-172: FEEDBACK — sessions[].last_activity (ts/kind/detail) ...
```

**2건 / 87건 (2.3%)**. flows 구역 자체는 spawn.py 안에서 거의 안
바뀌는 영역이다 — 87건의 충돌 압력 대부분은 flows 가 아니라 spawn.py
의 다른 부분(스폰 기전, watchdog, 룰북 해석 등, 실제로 이슈의 "안
한다" 절이 지목한 영역들)에서 나온다.

**함의**: "87/368=24%" 라는 수치 자체는 flows 를 옮기는 근거로 직접
쓰기엔 약하다 — 그 수치는 spawn.py 전체가 핫스팟이라는 근거이지,
flows 가 그 핫스팟에 기여하고 있다는 근거가 아니다. flows 를 옮겨도
저 87건 중 87건이 그대로 남는다(2건만 사라졌을 사례). 이동의 실제
근거는 다른 데 있다:

1. **저비용·저위험 파일럿**: 이슈 자신이 "안 한다"에서 미룬 두 영역
   (watchdog+respawn ~470줄, 룰북 해석 ~500줄)이야말로 충돌 압력이
   실제로 큰 곳일 가능성이 높다(이번 조사 범위 밖 — 확인 안 함). 그
   두 영역은 구역 밖 참조가 훨씬 복잡할 것으로 추정되고, 동시성
   버그가 실측된 영역과 인접해 있어(fork/setsid, fcntl.flock,
   events offset) 분할 자체의 리스크도 크다. flows 는 외부 호출
   지점이 `main()` 의 3줄뿐이고 로직 변경이 0이라 가장 싸게 "이
   패턴이 통하는지" 검증할 수 있는 후보다.
2. **영구적 파일 크기 축소**: 2845줄 중 300줄(10.5%)이 spawn.py 의
   나머지 코드와 런타임 상태를 전혀 공유하지 않는다(구역 밖 참조는
   순수 함수 호출 7개뿐). 이 300줄을 영구히 빼면, flows 자체의 향후
   변경 빈도와 무관하게 spawn.py 의 다른 부분을 건드리는 모든 향후
   PR 의 diff 컨텍스트가 그만큼 줄어든다.
3. **비용이 실제로 낮다**: 순수 이동, 기존 125개 테스트 + 바이트
   동일성 비교로 기계적으로 검증 가능, 게이트 인프라(gates/gates.py)
   변경 없이(`gates/flows.py` 선택 시) 가능.

**아무것도 안 하는 안(대안 1)이 나쁜 선택은 아니다** — flows 자체의
충돌 빈도가 낮으므로 안 옮겨도 단기 비용은 작다. 다만 이동 비용도
비슷하게 작고, 향후 더 비싼 두 분할의 리허설 가치가 있어 순이익이
더 크다고 판단한다(제안서 §근거에서 결정).

## 실측 4 — 대안 2: flows 를 repo-status-board 로 이관 (이슈 확인 항목 4)

이슈는 비용을 "board 읽기 8개 함수를 그쪽이 복제해야 한다"로
서술한다. 그 8개(실측 7개, 위 참조) 중 실제 성격이 갈린다:

- **레포 콘텐츠 기반, 이식 가능**: `board`, `_approvers`,
  `_issue_comments`, `_repo_slug`, `_front_role` — git 체크아웃 +
  `gh` CLI/API 호출만 있으면 어느 프로세스에서든 재현 가능. `board()`
  는 `frontmatter()`, `ROLES`, `BOARD` 상수에도 의존(spawn.py:947-990
  대) — "8개 함수"가 아니라 그 전이 의존까지 옮기거나 재구현해야
  진짜로 이식된다.
- **로컬 오케스트레이터 프로세스 상태, 이식 불가능**: `_roster_load`
  (`ROOT / "runs" / "active.json"` 읽음, spawn.py:1263/1279),
  `_alive`(`os.kill(pid, 0)` — 그 PID 를 낸 프로세스와 같은 머신이어야
  의미가 있음), 그리고 flows 구역 자체 안에 있는 `_ledger_read`
  (`ROOT / "runs" / "ledger.jsonl"` 읽음, spawn.py:2029-2031). 이
  파일들은 git 에 커밋되지 않는다(issue-172 survey.md 가 이미
  같은 결론을 냈다: "`runs/ledger.jsonl` and `runs/active.json` are
  local to the on-the-record checkout that ran the sessions, not to
  the target board repo").

**함의**: "8개 함수 복제"는 실제 비용을 과소평가한 서술이다. 세션
(sessions[])·원장(ledger[]) 두 섹션은 함수를 복제하는 게 아니라,
오케스트레이터를 실행 중인 머신의 로컬 파일에 다른 레포/프로세스가
접근할 새 데이터 통로(파일 동기화, 원격 읽기 API 등 — 오늘 존재하지
않음)를 새로 설계해야 이관 가능하다. 이건 "옮기기"가 아니라 "새
인프라를 먼저 만들고 나서 옮기기"이고, 이번 이슈(순수 이동) 스코프를
한참 벗어난다. 게다가 복제된 board-read 로직은 on-the-record 의
보드/roster/ledger 스키마가 바뀔 때마다 다른 레포에서 별도로
따라가야 하는 드리프트 부채도 남긴다.

**결론**: 대안 2 는 지금 실행 가능한 대안이 아니다 — 실행하려면 이
이슈보다 훨씬 큰, 아직 설계되지 않은 별도 이슈(원격 데이터 접근
채널)가 선행돼야 한다. `gates/flows.py` 로의 저장소 내부 이동과
상충하지 않는다 — 그 원격 채널이 언젠가 생기면 그때 다시 검토할 수
있는 선택지로 남는다.

## 베이스라인 (수용 기준 검증용)

```
$ python3 test_spawn.py
Ran 125 tests in 2.098s
FAILED (errors=5)
```

125개라는 총 개수는 이슈의 수용 기준과 일치. 5개 에러는 전부
`EventReporting`/`IssueScopedPrompt` 클래스(`rulebook_checkout` 이
`git clone` 으로 실제 GitHub 네트워크를 타는 경로)에서 나며, 이
샌드박스가 아웃바운드 git 접근을 막아서 생기는 환경 제약이지 flows
와는 무관하다 — `FlowsPayload`/`SessionLastActivity` 15개는 개별
실행 시 전부 통과(`python3 -m unittest test_spawn.FlowsPayload
test_spawn.SessionLastActivity` → `Ran 15 tests ... OK`). phase 2
검증 시 네트워크 있는 환경에서 전체 125개를 다시 돌려 이 5건이
사라지는지 확인해야 한다 — flows 이동과 무관한 사전 조건임을
기록해 둔다.

## Sources

저장소 내부(1차 소스, 이 체크아웃에서 직접 읽고 실행):
spawn.py:1978-2277(flows 구역), spawn.py:796-1300대(구역 밖 의존
함수 7개 + ROOT/BOARD/ROLES), spawn.py:2278-2325(`main()` 분기),
gates/closure_sweep.py(전체), gates/gates.py:1-67(보호 경로 판정),
gates/ci.py(closure_sweep 이 CI 게이트 목록에 없음을 확인),
test_spawn.py:1554-1749(FlowsPayload/SessionLastActivity),
test_gates.py:360-372(`t_protected_paths`), docs/issue-172/reports/
implementation/survey.md, docs/issue-172/proposals/flows-json.md
(roster/ledger 가 오케스트레이터 로컬임을 이미 확인한 선행 조사),
`git log` 직접 실행(커밋 수·일별 분포·flows 관련 커밋 특정).

외부(scout-brief.md 경유, 보조 확인용):
https://docs.pytest.org/en/stable/how-to/monkeypatch.html,
https://medium.com/@cini01/monkeypatching-subtleties-17e639fc3cd8.
