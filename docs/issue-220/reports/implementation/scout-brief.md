# Scout brief — issue #220

**모드:** 내부 prior-art 조사 1건 (병렬 웹 스윕 없음) — 이유는 세그먼트
판단 아래에 명시. #218과 같은 모드.

**세그먼트 판단:** product-shaped 아님. `_core_candidates()`/`core_root()`는
사용자가 보지 못하는 내부 오케스트레이션(spawn.py)의 로컬 오버라이드 해석
로직이다 — 비교할 외부 "카테고리 best-in-class" 제품이 없다. 대신 이
저장소 안의 동종 해법을 prior art로 읽었다.

**Prior art: `rulebook_checkout()`의 로컬 후보 해석** (`spawn.py:126-198`)

`_path(spec)`(spawn.py:126-134)가 "로컬 후보"로 보는 것은 딱 둘뿐이다:
(a) `roles/<role>.json`에 명시적으로 적힌 경로, (b) `registered(marketplace)
.get("installLocation")` — Claude Code 자신의 마켓플레이스 등록부 값. 둘 다
사람 또는 호스트가 실제로 기록한 정보고, **디렉터리 이름 관례를 추측해서
조립한 경로가 없다.**

**Must-be (이 prior art가 강제하는 것):** "로컬 오버라이드"로 인정되려면
설정 파일 또는 호스트 등록부처럼 **명시적 신호**가 있어야 한다 — 런타임
값으로 조립한 경로가 우연히 존재한다는 사실만으로는 오버라이드로 취급하지
않는다.

**성능축(이 저장소의 두 경로가 갈리는 지점):** core_root()의 후보
1·2(env 변수)는 이 must-be를 이미 충족한다(사람이 명시적으로 설정해야만
존재). 후보 3(`ROOT.parent / "tokenmaxxxer-core"`)만 예외 — `ROOT.parent`라는
런타임 값으로 조립한 디렉터리 이름 관례이고, 존재 여부가 사람의 의도가
아니라 "마켓플레이스를 설치했는가"라는 무관한 사실에 좌우된다.

**GAP LINE:** must-be 중 "설정/등록부 기반 후보만 오버라이드로 인정"은
후보 1·2에서 이미 충족. 후보 3만 위반 — 이 저장소에서 로컬 후보 해석
로직이 이 관례를 어기는 유일한 자리이고, 이슈 #220이 지목한 결함(후보 3이
관리 클론을 영구히 가림)의 근원이 정확히 이 위반이다.

**Adopt:** 후보 1·2와 `rulebook_checkout()`의 "명시적 신호만 오버라이드"
원칙을 그대로 유지 — env 변수 둘은 손대지 않는다.
**Skip:** 후보 3을 관리 클론 뒤로 재배치하는 대안(제거 대신 순서만 조정) —
근거는 proposal의 Rationale에 기록(재배치는 이 저장소 어디에도 없는 "추측
조립" 패턴을 그대로 남겨 두는 것이라 must-be를 완전히 충족하지 못함).

**Sources:** 전부 이 저장소 내부 파일 — `spawn.py:126-134`(`_path`),
`spawn.py:174-198`(`rulebook_checkout`), `spawn.py:1781-1860`
(`_core_candidates`/`core_root`/`core_version`), `README.md:121-123`,
`git log --follow -- spawn.py`(aa59f97, 후보 3의 최초 도입 커밋 확인).
외부 웹 소스 없음(위 세그먼트 판단 사유).

**스테이지:** 1스테이지(내부 prior-art 정독), 판단점 1회 후 즉시 포화 —
`rulebook_checkout()`의 후보 해석 방식을 읽은 시점에 이미 "후보 3만 추측
조립 패턴"이라는 결론이 명확해져 추가 라운드가 결정을 바꾸지 않는다고
판단, 조기 종료.
