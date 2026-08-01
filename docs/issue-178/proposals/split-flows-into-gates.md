---
role: implementation
subject: issue-178
loop_state: scope-proposed
---

# Proposal — spawn.py flows 구역을 gates/flows.py 로 분리 (issue #178)

files: `gates/flows.py`(신규 — flows 구역 300줄, 로직 무변경 그대로
이동), `spawn.py`(해당 구역 삭제, `main()` 의 `flows` 분기를
closure-sweep 과 동일한 지연 import 모양으로 교체), `test_spawn.py`
(`FlowsPayload`/`SessionLastActivity` 두 클래스의 patch 대상·import 를
새 모듈로 갱신), `test_gates.py`(`t_protected_paths` 긍정 목록에
`"gates/flows.py"` 1줄 추가), `docs/issue-178/reports/implementation.md`
(phase-2 기록, Approve 게이팅). `docs/specs/flows-schema.md` 는
건드리지 않는다 — 그 문서 자체가 "flows 의 구현을 기술하지 않는다"고
명시하고 있어 이동과 무관하다.

## Request (paraphrased, secrets stripped)

spawn.py(2845줄) 는 43개 역할이 각자 격리 클론에서 PR 을 여는 구조에서
가장 자주 충돌하는 단일 파일이다(최근 30일 368커밋 중 87건, 24%).
그중 L1978-2277(~300줄, `FLOWS_SCHEMA_VERSION`부터 `flows()` 까지)은
다른 레포(`repo-status-board`, issue #172)를 위한 읽기 전용 JSON
계약이고, spawn 기전과 관심사를 공유하지 않으며, 구역 밖에서
참조되는 것은 `flows()` 하나뿐(`main()` 의 3줄)이라 측정상 가장 깨끗한
분리 후보다. `gates/closure_sweep.py` 가 이미 같은 모양(밖으로 빼고
`import spawn` 으로 되돌려 쓰기, `main()` 은 지연 import)을 쓰고
있어 새 패턴이 아니라 반쯤 적용된 패턴을 마저 하는 것. 이 PR 은 그
이동 자체가 아니라 — 이동 방식(재export 가능 여부), 새 파일 위치,
"아무것도 안 한다" 안, "repo-status-board 로 통째 이관" 안, 이 네
가지를 phase 1 에서 조사해 제안하는 것까지만 다룬다.

## Constraints

- 이 PR 에는 코드 변경이 없다 — phase 2 는 이 제안에 대한 사람의
  Approve 이후에만 연다(contract v3 s19).
- 로직 변경 일절 없음(이슈 본문 "안 한다" 절, 순수 이동만).
- `L2680-2710`(fork/setsid/dup2), `L1267-1290`(fcntl.flock roster),
  `L1606-1637`(events offset) — 테스트가 못 잡는 동시성 버그가 실측된
  세 구간은 이번에 안 건드린다.
- watchdog+respawn(~470줄), verdict(~150줄), 룰북 해결(~500줄) 등
  다른 구역 분할은 이 조각이 실제로 개선을 냈는지 본 뒤 별건으로
  판단 — 이번 스코프 밖.

## Rationale

**재export shim 을 스폰에 남기는 안 — considered and rejected**:
문법적으로는 가능하지만(survey.md 실측 1) 구역과 함께 옮겨가는
`_pr_list_all` 같은 내부 심볼을 patch 하는 테스트 2건은 재export
만으로는 여전히 깨진다 — `flows_payload` 가 그 이름을 옮겨간 모듈의
`__globals__` 로 조회하지, 재export 한 spawn.py 의 이름공간을 안
보기 때문(별도 재현 스크립트로 직접 확인, pytest 공식 문서의 "patch
는 쓰이는 곳을 타겟해야 한다" 원칙과 일치). 게다가 재export 로
남기는 줄만큼 수용 기준의 "순감소=이동 크기" 등식이 깨진다 —
매커니즘과 수용 기준 둘 다 재export 를 배제한다. 그래서
closure_sweep.py 와 동일하게 **clean cut**(재export 대신, instead of
a shim): spawn.py 는 아무것도 재export 하지 않고, `main()` 이 지연
import 로만 새 모듈을 부른다.

**대안 1(아무것도 안 한다) — considered and rejected**: 이슈가 든
87/368(24%) 수치를 그대로 받아들이지 않고 재검증했다 — flows 구역
자체를 건드린 커밋은 87건 중 2건(2.3%, issue-172 의 phase-2 커밋과
FEEDBACK 커밋)뿐이라, 이 수치는 "spawn.py 전체가 핫스팟"의 근거는
되지만 "flows 를 옮기면 충돌이 준다"의 직접 근거는 못 된다(flows 를
옮겨도 나머지 85건은 그대로 남는다). 아무것도 안 해도 flows 자체의
단기 충돌 비용은 낮다는 뜻이라, 대안 1 이 터무니없는 선택은
아니었다. 그럼에도 rejected 하는 이유는 이동 비용이 그만큼 낮기
때문이다: 순수 이동, 외부 호출 지점 1개, 기존 125개 테스트 + 바이트
동일성 비교로 기계적 검증 가능, 위치를 `gates/flows.py` 로 고르면
게이트 인프라 변경도 0줄. 그리고 이슈가 명시적으로 미룬 두 개의 더
크고 더 위험한 분할(watchdog+respawn, 룰북 해결)의 패턴 검증 파일럿
역할을 한다 — 실제 충돌 압력이 큰 영역(추정)에 손대기 전에, 가장 싼
후보로 "이 분리 패턴이 깨끗하게 통하는가"를 이 PR 로 먼저 확인한다.

**대안 2(repo-status-board 로 이관) — considered and rejected**:
이슈는 비용을 "board 읽기 8개 함수 복제"로 서술하지만 실측하면
(survey.md 실측 4) 그중 `_roster_load`/`_alive`/`_ledger_read` 는
함수가 아니라 **오케스트레이터를 실행 중인 머신의 로컬 파일**
(`runs/active.json`, `runs/ledger.jsonl`, 둘 다 gitignore 대상,
issue-172 survey.md 가 이미 "로컬 온-더-레코드 체크아웃 전용, 대상
보드 레포 아님"이라고 확인한 것)을 읽는다. repo-status-board 는
별도 레포/프로세스라 이 파일들에 접근할 통로가 오늘 존재하지 않는다
— "함수 복제"가 아니라 "로컬→원격 데이터 통로를 새로 설계"해야 하는
문제라 이번 이슈(순수 이동) 스코프를 훨씬 벗어난다. 게다가 복제된
board-read 로직은 온-더-레코드의 보드/roster/ledger 스키마가 바뀔
때마다 다른 레포에서 별도로 쫓아가야 하는 드리프트 부채를 영구히
남긴다. `gates/flows.py` 로의 저장소 내부 이동과 상충하지 않으며 —
원격 데이터 채널이 나중에 생기면 그때 다시 열 수 있는 선택지로
남는다.

**위치로 루트 파일·새 디렉터리 대신(rather than a root file or a new
directory) `gates/flows.py` 를 선택**: 세 후보를 보호 경로 갱신
비용으로 직접 비교했다(survey.md 실측 2) — `gates` 는 이미
`PROTECTED_ROOT_DIRS` 에 있어 `gates/flows.py` 는 `gates/gates.py`
변경이 0줄이고, `test_gates.py` 의 `t_protected_paths` 에 1줄만
추가하면 된다(이건 위치와 무관하게 수용 기준이 요구하는 최소
diff). 루트 파일(`PROTECTED_ROOT_FILES` +1줄)이나 새 디렉터리
(`PROTECTED_ROOT_DIRS` +1줄)는 둘 다 `gates/gates.py` 자체의 diff 가
하나 더 생긴다 — 그 파일은 "파이프라인이 자기 규칙을 다시 쓸 수
없어야 한다"는 주석이 붙은, 신뢰 경계에 가까운 코드라 diff 자체를
하나 줄이는 쪽이 낫다. 이 두 대안도 rejected — 위치 선택지로는
성립하지만 `gates/flows.py` 대비 이점이 없다. 또한 `gates/flows.py`
는 `closure_sweep.py` 와 같은 디렉터리·같은 지연 import 패턴·같은
"읽기 전용, 보드 전역, 아무것도 안 고치고 안 posting" 성격이라
선례와 가장 잘 맞는다(scout-brief.md).

## What will be done

phase 2(Approve 이후)에서, 로직 변경 없이:

1. `gates/flows.py` 신설 — spawn.py:1978-2277 을 그대로 옮긴다. 파일
   최상단에서 closure_sweep.py 와 동일하게
   `sys.path.insert(0, str(Path(__file__).parent.parent)); import spawn`
   을 두고, 구역이 참조하던 구역 밖 심볼(`board`, `_approvers`,
   `_issue_comments`, `_repo_slug`, `_front_role`, `_roster_load`,
   `_alive`, 전역 `ROOT`) 은 전부 `spawn.X` qualified 접근으로 고친다
   (지금 spawn.py 안에서는 bare-name 이던 것 — 유일한 텍스트 변경이지만
   로직은 동일). `closure_sweep` 호출도 `import closure_sweep` 그대로
   유지(같은 디렉터리라 sys.path 조작 불필요, closure_sweep.py 자신이
   이미 하는 것과 동일하게 맞춘다).
2. `spawn.py` — L1978-2277 삭제. `main()` 의 `flows` 분기
   (spawn.py:2315-2318)를 closure-sweep 분기(spawn.py:2319-2325)와
   같은 모양의 지연 import 로 교체:
   `sys.path.insert(...); import flows; return flows.flows(a.cwd, a.json)`.
   재export 없음(Rationale).
3. `test_spawn.py` — `FlowsPayload`/`SessionLastActivity` 두 클래스의
   `setUp`/개별 테스트에서 `spawn.` 을 타겟하던 것 중 옮겨간 구역
   내부 심볼(`_pr_list_all`, `flows_payload`, `_session_last_activity`
   등) 관련 참조를 새 모듈(`flows`, closure_sweep 테스트가 이미
   `import closure_sweep` 하듯 `sys.path.insert` 후 `import flows`)로
   재타겟. `_repo_slug`/`_issue_comments`/`_roster_load` patch 는
   여전히 `spawn` 대상(구역 밖에 남는 함수라 안 바뀜) —
   `self.closure_sweep` 패치도 무변경.
4. `test_gates.py` — `t_protected_paths` 긍정 목록에
   `"gates/flows.py"` 추가.
5. `docs/issue-178/reports/implementation.md` — phase-2 기록(net
   line-count 비교, 바이트 동일성 diff, 전체 테스트 실행 결과 첨부).

## Out of scope

- watchdog+respawn(~470줄), verdict(~150줄), 룰북 해결(~500줄) 분할 —
  이 PR 이 패턴 검증에 성공한 뒤 별건으로 판단.
- `L2680-2710`/`L1267-1290`/`L1606-1637` 의 동시성 버그 — 이번에
  손대지 않음(이슈 본문 "안 한다").
- repo-status-board 로의 flows 이관(대안 2) — 로컬 roster/ledger
  파일에 대한 원격 접근 통로가 없어 이번 스코프를 벗어남; 별도
  이슈로 그 통로부터 설계해야 성립.
- `docs/specs/flows-schema.md` 수정 — 구현 위치와 무관한 데이터
  계약 문서라 안 건드림.

## How you'll know it worked

체크리스트(2단계에서 무엇이 어느 수용 기준을 충족하는지 추적):

- [ ] `python3 test_spawn.py` → 125개 통과, 감소 없음 — 이슈 수용
  기준 1. (현재 베이스라인과 동일 — survey.md 의 베이스라인 실행이
  이미 125개를 확인했다; 이 체크아웃 샌드박스에서 보이는 5건의
  무관한 네트워크 에러는 phase 2 검증 시 네트워크 있는 환경에서
  재확인)
- [ ] `python3 spawn.py flows --json -C <레포>` 출력이 이동 전후
  바이트 동일(diff 로 확인, 커밋에 첨부) — 이슈 수용 기준 2.
- [ ] `python3 spawn.py flows -C <레포>` (사람용 표) 출력도 바이트
  동일 — 이슈 수용 기준 3.
- [ ] `spawn.py` 순감소 줄 수 == `gates/flows.py` 로 옮긴 줄 수
  (재export 없음의 직접 증거) — 이슈 수용 기준 4.
- [ ] `python3 gates/ci.py .` 통과 — 이슈 수용 기준 5 전반.
- [ ] `t_protected_paths` 에 `gates/flows.py` 긍정 케이스가 있고
  통과 — 이슈 수용 기준 5 후반("새 파일이 보호 경로에 걸리는 것이
  테스트로 확인됨").

실패 신호: 위 여섯 중 하나라도 어긋나면 이동이 순수하지 않았다는
신호 — 롤백하고 무엇이 달라졌는지 phase-2 기록의
"## Rationale for deviations" 에 남긴다(이슈 본문의 실패 신호 그대로
계승).
