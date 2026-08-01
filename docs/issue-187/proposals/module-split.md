---
role: refactoring-legacy
subject: issue-187
loop_state: scope-proposed
---

# Proposal — spawn.py 를 rulebook.py/board.py/roster.py 로 순차 분리 (issue #187)

files(phase 2, 순서대로): `rulebook.py`(신규), `board.py`(신규),
`roster.py`(신규), `spawn.py`(3개 구역 삭제 + 이동한 심볼을 qualified
접근으로 교체, `main()`은 무변경), `gates/gates.py`(`PROTECTED_ROOT_FILES`
에 3줄 추가), `test_gates.py`(`t_protected_paths` 긍정 목록에 3줄
추가), `test_spawn.py`(옮겨간 심볼을 patch/직접 호출하던 곳을 새 모듈로
재타겟 — 클래스 단위, survey.md의 그룹별 클래스 목록 참조),
`docs/issue-187/reports/refactoring-legacy.md`(phase-2 기록, Approve
게이팅).

## Basis

현상 조사는 `docs/issue-187/reports/refactoring-legacy/survey.md` —
spawn.py 87개 함수의 라인 범위·이슈 제안 4구역 대비 실측 배정·정규식
기반 교차-그룹 호출 그래프(엣지 실측)·보호 경로·테스트 베이스라인(144개,
25개 환경성 에러)을 직접 읽고 실행해 확인했다. 외부 선례 조사는
`docs/issue-187/reports/refactoring-legacy/scout-brief.md` — WebSearch
3건 동시 호출로 얇은 엔트리 패턴, 순환 import 처리, strangler fig를
확인했다(Sources: 해당 파일 하단 5개 URL + 저장소 내부 선례
`gates/flows.py`/`gates/closure_sweep.py`).

방법론: Feathers(*Working Effectively with Legacy Code*)의 특성화
테스트로 동작을 먼저 고정한 뒤 손대는 순서 — 이번엔 기존 `test_spawn.py`
144개(네트워크 무관 119개)가 이미 그 특성화 테스트 역할을 한다. Fowler
(*Refactoring: Improving the Design of Existing Code*) 카탈로그의
Extract Module을 반복 적용하되, 한 파일에 담기엔 순환 의존이 있어
(survey.md 실측) strangler fig 식으로 3단계에 걸쳐 점진적으로 뽑는다.

## Context

spawn.py(2625줄·최상위 함수 87개)가 43개 역할이 각자 격리 클론에서
PR을 여는 구조에서 탐색·리뷰 비용이 큰 단일 파일로 자람 — AI 역할
세션이 일부만 수정할 때도 파일 전체를 읽어야 해 토큰 비용이 크고,
파일 경계가 영향 범위 경계가 안 돼 수정 정확도도 낮다. 이슈는 4개
하위 시스템 참고 경계(①rulebook/플러그인 ②board/기록 읽기
③roster/watchdog/watch ④스폰·워크스페이스)를 제시하되 "최종 구조는
역할 판단"으로 위임했고, `python3 <marketplace>/spawn.py <role>
"<task>" --issue <n> -C <repo>` 절대경로 단일 진입 호출 계약 유지를
제약으로 걸었다. 이 PR은 실제 이동이 아니라 — target 구조(4구역
그대로 갈지, 몇 개를 합칠지), 위치(형제 파일 vs 새 디렉터리), 순서
(어느 그룹부터), 순환 의존 처리 방식을 phase 1에서 조사해 제안하는
것까지만 다룬다.

### Constraints

- 이 PR에는 코드 변경이 없다 — phase 2는 이 제안에 대한 사람의
  Approve 이후에만 연다(contract v3 s19).
- 로직 변경 일절 없음(이슈 본문 "관찰 가능한 동작 안 바꾼다" 절, 순수
  이동 + qualified 접근 교체만).
- `spawn.py:2423-2438`(fork/setsid/dup2), `spawn.py:1267-1278`
  (fcntl.flock roster), `spawn.py:1478-1642`대(events offset) — 테스트가
  못 잡는 동시성 버그가 실측된(issue-178 선례) 세 구간은 이번에도 안
  고친다. `roster.py` 단계에서 텍스트째 옮기되 바이트 동일성으로만
  검증한다.
- `python3 spawn.py <role> "<task>" --issue <n> -C <repo>` 절대경로
  단일 진입 계약 무변경 — spawn.py는 그 경로에 실행 가능한 파일로
  계속 존재하고 동일 CLI 동작(인자·종료코드·출력 포맷)을 낸다
  (survey.md가 이 계약을 참조하는 6개 외부 호출 지점을 확인 — 전부
  `subprocess`로 절대경로 실행, 내부 모듈 구조와 무관).

## Options Considered

**group4(스폰·워크스페이스: `spawn_cmd`/`issue_workspace`/
`checkout_issue_branch`/`_spawn_one`/`main`, 684줄)를 이번엔 안 뽑는다
— considered and rejected(별도 파일로도 분리)**: survey.md의 교차-그룹
호출 그래프(실측)가 group4를 나머지 세 그룹 전부를 부르는 허브로
보여준다(1+12+15+20=48개 엣지, 들어오는 엣지는 group3에서 1개뿐).
group4를 5번째 형제 파일(예: `spawn_session.py`)로 뽑아도 spawn.py는
여전히 그 경로에 실행 파일로 있어야 하므로 결과는 "684줄이 이름만
바꿔 옮겨감 + `import spawn_session; sys.exit(spawn_session.main())`
3줄짜리 껍데기가 spawn.py에 남음"이다 — 전체 리뷰 대상 줄 수는 안
줄고(684줄은 어딘가에 그대로 있음), 간접 호출 한 단계만 늘어난다.
반면 group1/2/3 세 개만 뽑아도 spawn.py는 2625→약 774줄(70% 감소)로
이미 목표(탐색·리뷰 비용 감소)를 대부분 달성한다. group4 자체 분리는
이 PR이 성립시키는 패턴(형제 모듈 + qualified 접근 + 지연 import로
순환 끊기)이 실제로 깨끗하게 통하는지 확인한 뒤, 그 가치가 있다고
판단되면 별도 이슈로 다시 연다 — issue-178이 watchdog+respawn·룰북
해석 분할을 "패턴 검증 파일럿 이후 별건 판단"으로 미룬 것과 같은
논리.

**형제 파일(저장소 루트) — considered, 새 보호 디렉터리 대비
선택**: 이슈 본문이 "형제 모듈"을 직접 언급한다. 대안으로 새
디렉터리(예: `spawn_lib/`)를 만들면 `PROTECTED_ROOT_DIRS`에 1줄만
추가하면 돼 `gates/gates.py` diff가 더 작다(3파일 각각 대신 디렉터리
1개). 그런데 `rulebook.py`/`board.py`/`roster.py`는 "게이트"가 아니라
오케스트레이터 핵심 서브시스템이라 `gates/`(게이트 전용, closure_sweep/
flows/pr_reference/ci 넷 다 "훑고 보고만 한다" 성격)에 넣는 것은
의미상 맞지 않고, 새 목적 불명확한 디렉터리(`spawn_lib/` 류)를 3파일
때문에 만드는 것도 issue-178의 survey.md가 이미 "파일 하나를 위해
새 최상위 보호 디렉터리 개념을 만드는 과잉"이라 기각한 논리와 같다.
`PROTECTED_ROOT_FILES` 3줄 추가 비용을 감수하고 형제 파일을 선택한다
— diff는 더 크지만 위치가 의미와 맞아 리뷰어가 "왜 여기 있는가"를
안 물어도 된다.

**group1(rulebook) → group2(board) → group3(roster) 순서 —
considered and rejected(다른 순서/한 번에 다 옮기기)**: survey.md
그래프상 group1은 다른 그룹으로부터 들어오는 엣지가 0(가장 깨끗한
첫 이동, issue-178이 flows를 고른 논리와 동일). group2는 group3에서
2개 엣지만 들어오고 아직 옮기지 않은 group3(spawn.py에 남음)을
qualified로 부르면 그만이라 두 번째로 안전 — `board.py`의
`session_end_verdict`는 이 단계에서 `spawn._alive`/`spawn._events_path`
를 그대로 부른다(로직 무변경, 그룹3이 아직 spawn.py 안에 있으므로).
group3을 세 번째로 옮기며 두 가지를 동시에 처리: (a) `roster.py`가
최상단에서 `board.py`를 일반 import(순환 아님, roster→board 단방향),
(b) 방금 만든 `board.py`의 `session_end_verdict` 안 `spawn._alive`/
`spawn._events_path` 호출을 함수 본문 안 지연 `import roster`로
교체(이 저장소가 이미 main() 분기에서 쓰는 지연 import 패턴 재적용,
scout-brief.md 선례 3), (c) `roster.py`의 `_auto_respawn_check` 안
`_spawn_one` 호출도 함수 본문 안 지연 `import spawn`으로 교체
(group4가 spawn.py에 남으므로). 한 번에 4그룹을 다 옮기는 big-bang은
role directive의 "작게 나눠 매 단계마다 테스트"를 어기고, 순환 두
지점과 허브 재배선을 한 커밋에서 동시에 검증해야 해 실패 시 원인
분리가 안 된다 — 그래서 기각.

**group0(`go_proxy_layer`/`_mkt`/`_path`, 42줄)을 `rulebook.py`에
합침 — considered and rejected(전용 `common.py` 신설)**:
scout-brief.md가 외부 선례로 "공유 모듈 신설"도 제시하지만, 소비자가
`rulebook.py`(그룹1, `_mkt`/`_path` 10회) 하나와 `spawn.py`에 남는
`_spawn_one`(`go_proxy_layer` 1회)뿐이라 42줄 때문에 보호 파일을 하나
더 늘리는 비용이 `_spawn_one`에서 `rulebook.go_proxy_layer(...)`로
qualified 접근 1곳 고치는 비용보다 크다. `rulebook.py`가 이미
`_mkt`/`_path`의 주 소비자라 자연스러운 합류지다.

## Decision

phase 2(Approve 이후), 로직 변경 없이, 아래 순서로 — **각 단계 뒤
`python3 test_spawn.py` 전량 재실행, 네트워크 무관 119개(144−25) 통과
유지 확인**(role directive: "매 단계마다 테스트, 끝에서만이 아니라"):

1. **`rulebook.py` 신설**(735줄 = group1 693 + group0 42). 파일
   최상단에서 `import spawn`(같은 디렉터리라 sys.path 조작 불필요,
   closure_sweep.py의 지연 import 모양과 정신은 같되 위치가 같아
   더 단순) 후, 구역이 참조하던 구역 밖 심볼을 qualified 접근으로
   정리. `spawn.py`에서 group1+group0 삭제, 남은 `spawn_cmd`/`main`/
   `_spawn_one`/`issue_workspace`/`checkout_issue_branch`의 12개
   group1 호출부 + 1개 group0 호출부를 `rulebook.X(...)` qualified로
   교체. `spawn.py`에 `import rulebook` 추가(모듈 최상단, 순환 없음
   — group1은 spawn.py를 안 부름). `test_spawn.py`의 `SpawnCmd`/
   `DryRunModelReflection`/`WebToolPermissionAccess`/
   `PackageRegistryAccess`/`SandboxDefaultOpenAccess` 등 group1 관련
   클래스에서 `spawn.` patch 대상을 `rulebook.`로 재타겟.
   `gates/gates.py`의 `PROTECTED_ROOT_FILES`에 `"rulebook.py"` 추가,
   `test_gates.py`의 `t_protected_paths`에 긍정 케이스 1줄 추가.
2. **`board.py` 신설**(599줄 = group2). 같은 패턴으로 `import spawn`.
   `session_end_verdict`는 이 단계에서 `spawn._alive`/
   `spawn._events_path`를 그대로 부른다(group3이 아직 spawn.py 안).
   `spawn.py`에서 group2 삭제, 남은 group4의 15개 group2 호출부를
   `board.X(...)`로 교체, `import board` 추가. `test_spawn.py`의
   `BoardSnapshot`/`SessionResult`/`Classify`/`FailClosedDowngrade`/
   `GitHead`/`IsNewCommit`/`OwnershipReport` 등을 재타겟.
   `PROTECTED_ROOT_FILES`/`t_protected_paths`에 `"board.py"` 추가.
3. **`roster.py` 신설**(517줄 = group3). 최상단에서 `import spawn`
   **및** `import board`(일반 top-level — 이 방향은 순환 아님).
   `_post_crash_comment`는 `board._issue_comments(...)`/
   `board._repo_slug(...)`로 qualified. `_auto_respawn_check`는
   `session_end_verdict` 호출을 `board.session_end_verdict(...)`로,
   `_spawn_one` 호출은 함수 본문 안 **지연** `import spawn`으로(순환
   회피 — spawn.py가 이미 `roster.py`를 top-level import하므로
   반대 방향은 지연이어야 함). 동시에 **`board.py`의
   `session_end_verdict`를 수정**: `spawn._alive`/`spawn._events_path`
   직접 호출을 함수 본문 안 지연 `import roster`로 교체(같은 순환
   회피 원리 — `roster.py`가 `board.py`를 top-level import하므로
   반대 방향은 지연). `spawn.py`에서 group3 삭제, 남은 group4의 20개
   group3 호출부를 `roster.X(...)`로 교체, `import roster` 추가.
   `fcntl.flock`/`fork`/`setsid`/`dup2` 구간은 이동 후 바이트 diff로
   무변경 확인(Constraints 참조 — `fork`/`setsid`/`dup2`는 group4에
   남아 이동 대상 아님, `fcntl.flock`만 `roster.py`로 이동). 관련
   `test_spawn.py` 클래스(`Watchdog`/`SessionEndVerdict`/
   `AutoRespawnClaim`/`PostCrashComment`/`RosterConcurrency`/
   `EventExitScope` 등) 재타겟. `PROTECTED_ROOT_FILES`/
   `t_protected_paths`에 `"roster.py"` 추가.
4. **`docs/issue-187/reports/refactoring-legacy.md`** — phase-2
   기록(단계별 net line-count 비교, 이동 구간 바이트 동일성 diff,
   전체 테스트 실행 결과, 보드 읽기·spawn·watch 스모크 로그 첨부).

각 단계는 그 자체로 완결적이고(role directive: "each independently
completable and leaving the system working") 이전 단계의 산출물
위에서만 진행한다.

## Consequences

3단계 전부 끝나면 `spawn.py`는 2625줄에서 약 774줄(main + spawn_cmd +
issue_workspace + checkout_issue_branch + ensure_pushed + _spawn_one +
import/ROOT/argparse 설정, 70% 감소)로 줄어든다. 새로 생기는 리뷰
표면은 4개 파일(spawn.py 포함)로 나뉘어 각 PR/세션이 실제로 건드리는
모듈만 읽으면 되지만, `PROTECTED_ROOT_FILES`가 3줄 늘고 순환 회피용
지연 import 2곳(`board.session_end_verdict`, `roster._auto_
respawn_check`)이 새 유지보수 포인트로 남는다 — 둘 다 이 저장소의
기존 패턴 재적용이라 신규 개념은 아니다. group4(684줄)는 이번엔
spawn.py에 그대로 남아 있어 목표(파일당 크기 축소)를 부분적으로만
달성한다 — 나머지는 이 PR의 패턴이 통함을 확인한 뒤 별도 이슈로.

## Out of scope

- group4(`spawn_cmd`/`issue_workspace`/`checkout_issue_branch`/
  `_spawn_one`/`main`, 684줄) 별도 파일 분리 — 이 PR이 패턴 검증에
  성공한 뒤 별건으로 판단(Options Considered).
- `spawn.py:2423-2438`/`1267-1278`/`1478-1642`대의 동시성 버그 — 이번에
  손대지 않음(이슈 본문 "안 한다" 절, Constraints).
- 새 보호 디렉터리(`spawn_lib/` 류) 신설 — 형제 파일 채택으로 불필요
  (Options Considered).
- group0 전용 `common.py` 신설 — `rulebook.py`로 합류(Options
  Considered).
- `docs/specs/*` 수정 — 구현 위치와 무관한 계약 문서라 안 건드림.

## Verification

체크리스트(2단계에서 무엇이 어느 수용 기준을 충족하는지 추적,
이슈의 "보드 읽기·spawn·watch 스모크로 회귀 없음 확인" 검증 절과
연결):

- [ ] `python3 test_spawn.py` → 각 단계 후 및 최종, 네트워크 무관
  119개(144−25) 통과 유지, 감소 없음.
- [ ] `python3 test_gates.py` / `python3 test_approve_scope.py` 통과
  (이 두 파일도 `import spawn` — group1/2/3 심볼을 직접 참조하지
  않는지 확인하고, 참조한다면 재타겟).
- [ ] `python3 spawn.py -C <레포>`(board 읽기), `python3 spawn.py
  status -C <레포>`, `python3 spawn.py watch --issue <n> -C <레포>`
  스모크 — 이동 전후 출력 바이트 동일(이슈 검증 절 그대로).
- [ ] `python3 spawn.py <role> "<task>" --issue <n> -C <repo>` 절대경로
  단일 진입 계약 스모크 — 정상 기동 확인(네트워크 있는 환경).
- [ ] `spawn.py` 순감소 줄 수 == 이동한 3개 구역 크기 합(1851줄, 재export
  없음의 직접 증거) — group1/2/3 함수 정의부는 정확히 한 곳에만
  존재.
- [ ] `python3 gates/ci.py .` 통과.
- [ ] `t_protected_paths`에 `rulebook.py`/`board.py`/`roster.py` 긍정
  케이스 3건이 있고 통과.
- [ ] 순환 의존 두 지점(`board.session_end_verdict`↔`roster`,
  `roster._auto_respawn_check`→`spawn`)이 지연 import로만 끊겨 있고
  모듈 top-level import 순환이 없음(정적 확인: 각 신규 모듈을 단독
  `python3 -c "import rulebook"` 등으로 임포트 성공하는지).

실패 신호: 위 항목 중 하나라도 어긋나면 해당 단계만 롤백하고(단계별
독립 완결성 덕분에 이전 단계까지는 유지 가능) 무엇이 달라졌는지
phase-2 기록의 "## Rationale for deviations"에 남긴다.
