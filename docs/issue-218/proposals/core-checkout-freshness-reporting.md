files:
- spawn.py
- test_spawn.py

## Request

#218: `core_root()`(spawn.py:1781)가 tokenmaxxxer-core 체크아웃 후보에서
`plugin.json` 파일 존재만 확인하고 그 체크아웃의 sha·신선도는 확인도 보고도
하지 않는다. 실측: 로컬 머신의 마켓플레이스 클론이 2026-08-01 이후 2일간
같은 sha(52bdc15, origin 대비 10커밋 뒤)로 멈춰 있었는데 아무 로그에도 안
남아 역할 세션들이 계속 그 stale 게이트로 돌았고, 같은 원인 계열로 다른
세션 하나는 gate-lib 부재 상태에서 $4.63을 태우고 죽었다. 이슈는 (a) 신선도
확인+갱신 또는 최소 sha 보고, (b) 룰북과 같은 관리 경로로의 통일 검토를
제안이 다뤄야 한다고 명시한다.

## Constraints

- 로컬 체크아웃 우선순위(`TOKENMAXXXER_CORE` → `$TOKENMAXXXER_RULEBOOKS/
  tokenmaxxxer-core` → `ROOT.parent` 형제 → 관리 클론)는 개발용 오버라이드
  라는 기존 주석 의도(spawn.py:1798-1799)를 그대로 존중해야 한다 — 순서를
  바꾸거나 로컬 오버라이드를 강제로 pull해서는 안 된다.
- `core_root()`의 외부 시그니처·halt 동작(3후보+관리클론 다 없으면
  `sys.exit`)은 바꾸지 않는다 — `core_plugin_dirs()`를 거쳐
  `spawn_cmd()`까지 이어지는 기존 호출 경로가 이 계약에 의존한다
  (test_spawn.py:59-96에 이미 이 계약을 검사하는 테스트가 있다).
- 새 환경변수·의존성·마이그레이션은 없다.
- ledger(`runs/ledger.jsonl`)는 gitignore 대상 측정 데이터이므로 필드
  추가는 자유롭지만, 기존 필드(`rulebook` 등)는 이름·의미를 바꾸지 않는다
  (추가만, 제거·변경 없음).

## Rationale

**대안 1(rejected) — core_root()를 룰북처럼 완전히 통일**: 로컬 오버라이드
후보 셋을 없애고 항상 관리 클론(매 spawn `git pull`)만 쓰도록 바꾸는 안.
이슈 본문의 "관리 경로로의 통일 검토" 문구가 가리키는 가장 직접적인 해석이지만,
survey에서 확인한 `spawn.py:1798-1799`의 "로컬 우선은 개발용 오버라이드일
뿐이다" 주석 및 `rulebook_checkout()`의 동일 패턴(로컬 오버라이드는 pull하지
않음)과 정면으로 어긋난다. 개발자가 의도적으로 로컬 tokenmaxxxer-core를
특정 커밋에 고정해 두고 오프라인으로 작업 중일 수 있는데, 이 안은 그 상태를
매 spawn마다 강제로 움직이거나(네트워크 필요) 아예 그 경로를 없애 버린다.
considered and rejected: 로컬 오버라이드 존중이라는 기존 계약을 깬다.

**대안 2(rejected) — origin 대비 "몇 커밋 뒤"를 수치로 보고**: `git fetch` 후
`git rev-list --count HEAD..origin/main`으로 정량적 지연 커밋 수를 보고하는
안. `git fetch`는 로컬 오버라이드 경로에도 네트워크 접근을 강제해 대안 1과
같은 문제를 다시 끌어들이고, fetch 없이 기존 원격 추적 ref만 쓰면 그 ref
자체가 stale해서 오히려 잘못된 안심을 줄 수 있다. 또한 이 저장소의 기존
비교 대상(`checkout_version()`/`rulebook_version()`)도 원격 비교 수치 없이
sha+상태만 보고하는데, 이 정도로도 이슈가 실제로 stale함을 알아챈 방법
(같은 sha가 이틀간 안 바뀜)을 그대로 재현할 수 있다. rejected instead of
채택: 네트워크 강제 없이도 목적을 달성하는 더 단순한 대안(아래 "채택")이
있다.

**채택 — sha+커밋날짜+출처를 읽기 전용으로 보고**: `checkout_version()`이
룰북 쪽에서 이미 하는 일(로컬 오버라이드는 건드리지 않고, 무엇이 도는지만
매 spawn 로그·ledger에 남긴다)을 core 쪽에 대칭으로 만든다. 로컬 오버라이드
우선순위·halt 계약은 완전히 그대로 두면서, "같은 sha가 며칠째 안 바뀐다"를
사람이나 로그 스캔이 바로 알아챌 수 있게 만드는 것이 이슈의 "최소한 sha
보고" 요구를 정확히 충족한다. 위 두 대안 대신(instead of) 이 쪽을 골랐다 —
읽기 전용이라 부작용이 없고, 이미 검증된 룰북 쪽 패턴을 그대로 재사용해
새로운 실패 모드를 만들지 않는다.

## What will be done

- `spawn.py`에 `_core_candidates()` 추가: `core_root()`의 기존 3후보
  (라벨, 경로) 목록을 만드는 로직을 이 함수로 뽑아낸다(우선순위·스킵 규칙
  변경 없음, 순수 리팩터).
- `core_root()`를 `_core_candidates()`를 쓰도록 다시 쓰되, 반환값·halt
  동작은 100% 동일하게 유지한다.
- `core_version() -> str` 신규 추가(1781행대, `core_root()` 옆): 읽기
  전용 — pull도 clone도 하지 않는다. `_core_candidates()`를 훑어 첫 매치를
  설명하거나, 없으면 관리 클론(`runs/rulebooks/tokenmaxxxer-core`)이
  있는지만 확인해 설명한다. 아무것도 없으면 "버전 불명(core 체크아웃
  없음)"류 문자열을 반환한다(halt하지 않음 — 로깅용이라 halt는
  `core_root()`의 몫으로 남긴다). 반환 형식은 `checkout_version()`과
  같은 모양: `"{sha}{dirty 표시} ({커밋날짜}, {출처 라벨})"`.
- `run_role()`의 스폰 로그 줄(spawn.py:2394 부근, 현재
  `"[{role}] 플러그인 {N}개, 룰북 {checkout_version(...)}, 작업 디렉터리 {cwd}"`)
  에 `core {core_version()}`을 추가한다.
- `ledger_write()` 호출부(spawn.py:2628 부근)의 레코드에 `"core":
  core_version()` 필드를 `"rulebook"` 필드 옆에 추가한다(기존 필드는 그대로).
- `test_spawn.py`에 단위 테스트 추가: (a) `TOKENMAXXXER_CORE`가 임시 git
  체크아웃을 가리킬 때 `core_version()`이 그 sha·커밋날짜·라벨을 담은
  문자열을 반환하는지, (b) 로컬 후보가 전혀 없고 관리 클론도 없을 때
  네트워크 접근(clone) 시도 없이 "버전 불명" 계열 문자열을 반환하는지, (c)
  기존 `test_core_dir_resolves_or_halts`가 리팩터 후에도 그대로 통과하는지
  (회귀 확인).

## Out of scope

- 로컬 오버라이드 자동 pull/갱신(대안 1, rejected).
- origin 대비 커밋 지연 수 계산(대안 2, rejected).
- tokenmaxxxer-core 레포 안의 "gate-lib 부재" 자체를 고치는 일 — 그
  레포는 이 write set 밖이고, 이번 변경은 그 사고를 다음번엔 로그로 바로
  진단 가능하게 만드는 것까지가 범위다.
- `rulebook_checkout()`/`checkout_version()`/`rulebook_version()`
  자체 수정 — 이미 올바르게 동작하는 참조 구현으로만 쓴다.

## How you'll know it worked

- `python3 -m unittest test_spawn.py -v`(또는 README가 적은
  `python3 test_spawn.py`)가 새 테스트 포함 전부 통과.
- 리팩터 후 기존 `test_core_dir_resolves_or_halts`가 그대로 통과 —
  `core_root()`의 halt 계약이 안 깨졌다는 증거.
- 수동 확인: 로컬 머신에서 `TOKENMAXXXER_CORE`를 실측에 쓰인 stale
  마켓플레이스 클론(`~/.claude/plugins/marketplaces/tokenmaxxxer-core`,
  sha 52bdc15)으로 가리키고 `python3 -c "import spawn;
  print(spawn.core_version())"`를 실행하면 결과 문자열에 `52bdc15`와
  `2026-08-01`이 나타난다 — 이슈가 요구한 "sha 보고"가 실제로 이 stale
  케이스를 잡아내는지 확인.
