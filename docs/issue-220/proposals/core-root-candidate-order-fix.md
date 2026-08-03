files:
- spawn.py
- test_spawn.py

## Request

#220: `core_root()`(spawn.py:1781-1801)의 로컬 오버라이드 후보 목록
(`_core_candidates()`)에 있는 후보 3("형제 디렉터리",
`ROOT.parent / "tokenmaxxxer-core"`) — 마켓플레이스 설치의 부산물이며
개발자가 의도한 오버라이드가 아님 — 이 관리 클론(후보 4,
`runs/rulebooks/tokenmaxxxer-core`)보다 먼저 매치되어, 이 개발 머신처럼
후보 3이 항상 존재하는 환경에서는 관리 클론(원격과 항상 동기화되는 유일한
경로)이 영구히 도달 불가능해진다. 실측(2026-08-01~03): 후보 3이 origin
대비 8→10커밋 뒤진 채 이틀간 고정돼 역할 세션들이 이미 고쳐진 board-gate
오탐에 반복 차단됐고, 같은 계열 사고로 세션 하나가 gate-lib 부재 상태로
$4.63을 태우고 죽었다(#218 본문). 이슈는 후보 3을 제거하거나 후보 4 뒤로
내리는 것을 요구사항으로 명시한다.

## Constraints

- 후보 1(`TOKENMAXXXER_CORE`)·후보 2(`$TOKENMAXXXER_RULEBOOKS/
  tokenmaxxxer-core`)의 순서·동작은 그대로 유지 — 강제 pull 금지도 그대로
  (이슈 요구사항 2).
- `core_root()`의 halt 계약(모든 후보+관리 클론+원격 clone까지 다 실패하면
  `sys.exit`)과 외부 시그니처(`() -> Path`)는 불변 — `test_spawn.py`의
  `test_core_dir_resolves_or_halts`가 이미 검사한다(이슈 요구사항 3).
- #218이 넣은 `core_version() -> str` 보고(읽기 전용, pull/clone 없음)는
  그대로 살린다 — 오버라이드 사용 시 진단용으로 계속 유효해야 한다(이슈
  요구사항 4).
- 새 환경변수·의존성·마이그레이션 없음.
- #219(이슈 #218)이 이미 머지됐으므로 이 write set은 그 위에서 작업한다
  (이슈 본문 "착수 시점").

## Rationale

**대안(rejected) — 후보 3을 제거하지 않고 관리 클론(후보 4) 뒤로 재배치**:
이슈가 명시적으로 허용한 두 옵션 중 하나. `core_root()`/`core_version()`
양쪽의 순회 순서를 "env 둘 → 관리 클론(pull) → 형제 디렉터리(재배치, pull
없음) → 원격 clone 시도 → halt"로 바꾸는 안. 이 안은 이슈의 최소 요구는
충족하지만, survey에서 확인한 이 저장소의 유일한 대칭 사례
(`rulebook_checkout()`이 쓰는 `_path(spec)`/`registered().get(
"installLocation")`)가 로컬 후보를 **설정 파일 명시 또는 호스트 등록부
값**으로만 인정하고 "런타임 값으로 조립한 디렉터리 이름 관례"는 애초에
후보로도 넣지 않는다는 원칙과 계속 어긋난다. 재배치해도 "관리 클론이
없고 형제 디렉터리만 있는" 드문 조합에서는 여전히 그 추측 조립 경로가
살아남아, 이슈가 지목한 결함의 근본 패턴(디렉터리가 우연히 존재한다는
사실만으로 오버라이드 취급)을 완전히 제거하지 못하고 발생 조건만 좁힌다.
또한 이 경로를 실제로 쓰고 싶은 개발자는 `TOKENMAXXXER_CORE`로 그 디렉터리를
직접 가리키면 되므로(능력 손실 없음), 재배치로 남겨 둘 실익이 없다.
considered and rejected: 결함의 근본 패턴을 남긴 채 발생 빈도만 낮춘다.

**채택 — 후보 3("형제 디렉터리")을 `_core_candidates()`에서 완전히 제거**:
`core_root()`/`core_version()`은 이미 `_core_candidates()`를 순회하는
구조이므로, 이 함수의 반환 목록에서 튜플 하나를 빼는 것만으로 두 호출부
모두에 자동 반영된다(호출부 자체는 수정 불필요). 결과 순서는 "env
1 → env 2 → 관리 클론(pull, 항상 동기화)"이 되어, 이슈 요구사항 1("기본
경로가 항상 원격과 동기화되는 관리 클론이 되게")을 재배치보다 더 직접
충족한다 — 조건부가 아니라 무조건. `rulebook_checkout()`의 검증된 원칙
(설정/등록부 기반 후보만 오버라이드로 인정)과도 일치시켜, 이 저장소
안에서 로컬 후보 해석 로직이 "추측 조립" 패턴을 쓰는 유일한 예외를
없앤다. instead of 위 재배치안 — 근본 패턴을 남기지 않고 완전히 제거하며,
코드 변경량도 더 적다(튜플 삭제 1줄 vs 순회 순서 재구성).

## What will be done

- `spawn.py`의 `_core_candidates()`(1781-1791행대)에서 `("형제 디렉터리",
  str(ROOT.parent / "tokenmaxxxer-core"))` 튜플을 제거 — 반환 목록이 env
  후보 둘만 남는다. 함수 docstring의 "후보 셋" 표현을 "후보 둘"로 갱신.
- `core_root()`(1794-1829행대)·`core_version()`(1832-1860행대) 본문은
  수정하지 않는다 — 둘 다 이미 `_core_candidates()`를 순회하는 루프이므로
  튜플 제거만으로 두 곳 다 새 순서를 자동으로 따른다(순수 삭제 리팩터,
  호출부 무변경).
- `test_spawn.py`에 회귀 테스트 추가:
  (a) 형제 디렉터리(`ROOT.parent / "tokenmaxxxer-core"`)와 관리 클론
  (`runs/rulebooks/tokenmaxxxer-core`)이 **둘 다 존재**하고 env 둘 다
  비어 있을 때 `core_root()`가 관리 클론 경로를 반환하는지(형제 디렉터리가
  아니라) — 이슈가 보고한 정확한 결함의 회귀 방지.
  (b) 같은 셋업에서 `core_version()`이 관리 클론 쪽 sha와 "on-the-record
  클론" 라벨을 반환하는지(형제 디렉터리 쪽이 아니라).
- 변경 후 `python3 -m unittest test_spawn.py -v` 1회 실행해 기존
  `test_core_dir_resolves_or_halts`·두 `core_version` 테스트·
  `test_flags` 등이 전부 그대로 통과하는지 확인(halt 계약·시그니처
  무변경의 증거).

## Out of scope

- 후보 1·2(env 변수)의 순서·pull 정책 변경 — 이슈가 명시적으로 유지를
  요구.
- 관리 클론의 pull-then-return 단계, 원격 clone 시도, halt 메시지 문구 —
  변경 대상 아님.
- 후보 3을 재배치하는 대안(위 Rationale에서 rejected).
- `rulebook_checkout()`/`checkout_version()`/`rulebook_version()` 자체
  수정 — 이미 올바른 참조 구현으로만 쓴다(#218과 동일 스코프 판단).
- README.md에 "형제 디렉터리가 더는 후보가 아니다"를 문서화하는 일 —
  애초 README가 이 관례를 문서화한 적이 없었으므로(survey 확인) 갱신할
  기존 문구가 없다.

## How you'll know it worked

- `python3 -m unittest test_spawn.py -v`가 새 회귀 테스트 둘 포함 전부
  통과.
- 기존 `test_core_dir_resolves_or_halts`가 리팩터 후에도 그대로 통과 —
  halt 계약이 안 깨졌다는 증거.
- 수동 확인: 임시 디렉터리에 형제 디렉터리(`ROOT.parent/tokenmaxxxer-core`,
  오래된 sha)와 관리 클론(`runs/rulebooks/tokenmaxxxer-core`, 최신 sha)을
  둘 다 만들고 env 둘 다 비운 상태에서 `python3 -c "import spawn;
  print(spawn.core_root()); print(spawn.core_version())"`를 실행하면
  관리 클론 경로와 그 최신 sha가 나온다 — 형제 디렉터리 쪽이 아니라.
