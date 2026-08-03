# Survey — issue #220: core_root() 후보 순서 결함

## 대상 코드: `_core_candidates()` / `core_root()` / `core_version()` (spawn.py:1781-1860)

#218(PR #219)이 `_core_candidates()`로 뽑아낸 현재 후보 목록(spawn.py:1786-1791):

1. `TOKENMAXXXER_CORE` (env, 직접 경로)
2. `$TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core` (env, RULEBOOKS 변수 재사용)
3. `ROOT.parent / "tokenmaxxxer-core"` (라벨 "형제 디렉터리") — 마켓플레이스
   설치가 ROOT 옆에 clone 해 두는 부산물

이 셋을 순서대로 보고 `plugin.json` 파일 존재만 확인해 첫 매치를 즉시
반환한다(`core_root()` spawn.py:1801-1808, `core_version()` spawn.py:1849-1856
둘 다 같은 순회). 셋 다 없을 때만 관리 클론(`ROOT/runs/rulebooks/
tokenmaxxxer-core`)으로 떨어지는데, 이 관리 클론만 반환 직전에
`git pull -q --ff-only`를 돈다(spawn.py:1812-1815) — "항상 원격과 동기화"인
유일한 경로다.

## 결함 재현

이슈 실측(2026-08-01~03): 후보 3(형제 클론, `~/.claude/plugins/marketplaces/
tokenmaxxxer-core`류 위치가 아니라 정확히는 `ROOT.parent/tokenmaxxxer-core`)이
이 개발 머신에 **항상 존재**한다 — 플러그인 마켓플레이스를 설치하면 생기는
부산물이라 지우지 않는 한 없어지지 않는다. 후보 3이 `plugin.json`만 있으면
sha 비교 없이 즉시 반환되므로, 관리 클론(후보 4)은 후보 3이 존재하는 한
**영원히 도달 불가**다. #218이 이미 붙인 `core_version()` 보고 덕에 이
정체(같은 sha 52bdc15가 이틀간 안 바뀜)를 로그에서 볼 수는 있게 됐지만,
후보 순서 자체는 아직 안 고쳐졌다 — #218의 write set은 "보고"까지였고
"순서 결함"은 이 이슈(#220)로 명시적으로 미뤄졌다(이슈 본문 "착수 시점").

## 후보 3("형제 디렉터리")의 기원 — 문서화된 기능인가?

`git log --follow -- spawn.py`로 추적: 이 후보는 `aa59f97`("Restructure for
contract v3")에서 `core_dir()`(현 `core_root()`의 전신) 최초 작성 시점부터
`ROOT.parent / "tokenmaxxxer-core"`로 이미 있었다 — #218이 새로 추가한 게
아니라 애초 설계에 포함돼 있었다.

README.md:121-123 은 로컬 오버라이드를 일반적으로만 언급한다: "Rulebooks
and tokenmaxxxer-core need NO manual clones: spawn fetches and ff-updates
them ... (a local checkout, if present, wins — that is the development
override)." 이 문장은 **env 변수로 가리키는 로컬 체크아웃**을 말하는 것으로
읽힌다 — `ROOT.parent/tokenmaxxxer-core`라는 특정 디렉터리 관례를 명시적으로
가리키지는 않는다. `docs/handbooks/`, `docs/decisions/`를 grep해도 이
관례를 설명하거나 정당화하는 문서는 없다. 즉 후보 3은 "개발자가 의도적으로
선택하는 오버라이드 경로"로 어디에도 문서화돼 있지 않다 — 반면 후보 1·2는
README가 명시적으로 "development override"라 부르는 바로 그 메커니즘(env
변수)이다.

## Prior art — 이 저장소 안의 대칭 함수: `rulebook_checkout()`

`rulebook_checkout()`(spawn.py:174-198)은 룰북 쪽의 "로컬 우선, 없으면
관리 클론" 로직이다. 여기서도 "로컬 후보"가 있지만, 그 로컬 후보는
`_path(spec)`(spawn.py:126-134) — **`roles/<role>.json`에 명시적으로 적힌
경로**, 또는 `registered(spec["marketplace"]).get("installLocation")` —
**Claude Code 자신의 마켓플레이스 등록부**에서 읽은 값이다. 즉 룰북 쪽의
모든 "로컬 오버라이드" 후보는 (a) 설정 파일에 명시되거나 (b) 호스트가
실제로 추적하는 등록 정보에서 나온다 — **디렉터리 이름 관례를 추측해서
만든 경로가 하나도 없다.**

`core_root()`의 후보 1·2(env 변수)는 이 원칙과 일치한다: 둘 다 사람이
명시적으로 설정해야만 존재한다. 후보 3만 예외다 — `ROOT.parent`라는
런타임 값으로 경로를 **조립**해서, 그 자리에 뭔가 있으면 무조건 오버라이드로
취급한다. 이 저장소의 다른 어떤 로컬-후보 해석 로직도 이런 "추측 조립"
패턴을 쓰지 않는다 — 후보 3은 유일한 예외이자 이슈가 지목한 결함의 근원이다.

## halt 계약·시그니처 확인 (건드리면 안 되는 부분)

- `core_root()`: 반환형 `Path`, 아무 후보도 매치 안 되고 관리 클론도 없고
  원격 clone도 실패하면 `sys.exit(...)`(spawn.py:1826-1829). 이 계약은
  `test_spawn.py:60-78`(`test_core_dir_resolves_or_halts`)이 검사한다 — env
  둘 다 비우고 `ROOT`를 존재하지 않는 경로로 바꾼 뒤 halt를 기대한다. 이
  테스트는 후보 3을 직접 겨냥하지 않는다(가짜 `ROOT`라 후보 3 자리도
  자동으로 존재하지 않음) — 후보 3을 제거해도 이 테스트는 그대로 통과할
  것으로 예상된다(변경 후 실행으로 확인 예정).
- `core_version()`: 반환형 `str`, halt 없음, pull/clone 없음. #218이 붙인
  두 테스트(`test_core_version_reports_sha_date_and_label_for_local_override`,
  `test_core_version_reports_unknown_without_network_when_nothing_found`)가
  이미 있다 — 둘 다 후보 3에 의존하지 않는다(전자는 `TOKENMAXXXER_CORE` 지정,
  후자는 세 후보+관리 클론 전부 미스 케이스).
- `core_plugin_dirs()`(spawn.py:1863-1872)는 `core_root()`를 그대로 호출할
  뿐 후보 목록을 자체적으로 순회하지 않는다 — `_core_candidates()` 변경이
  이 함수에 새로 영향을 주지 않는다.

## 테스트 현황

`test_spawn.py`에 `_core_candidates()`나 "형제 디렉터리"를 직접 겨냥한
테스트는 없다(grep 결과 없음) — 즉 후보 3을 제거해도 깨질 기존 테스트가
없다. 이 결함(후보 3이 후보 4를 영구히 가린다) 자체를 재현·회귀 방지하는
테스트도 아직 없다 — 이번 write set에 추가해야 한다.

## 쓸 파일 (write set 예상)

- `spawn.py` — `_core_candidates()`(1781-1791행대)에서 후보 3 제거.
  `core_root()`/`core_version()` 본문은 `_core_candidates()`를 그대로
  순회하므로 추가 수정 불필요(순수 삭제 리팩터).
- `test_spawn.py` — 후보 3이 있어도 관리 클론이 우선한다는 회귀 테스트
  추가(`core_root()`, `core_version()` 양쪽).

## 스카우트 판단

product-shaped 아님 — #218과 동일 사유(내부 오케스트레이션 자기 일관성
버그, 비교할 외부 카테고리 제품 없음). 스킵하지 않고 #218과 같은 모드로
내부 prior-art 조사를 1건 수행함: `rulebook_checkout()`의 로컬 후보 해석
로직(위 "Prior art" 절). 상세는 `scout-brief.md`.
