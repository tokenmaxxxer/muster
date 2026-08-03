# Scout brief — issue #218

**모드:** 내부 prior-art 조사 1건 (병렬 웹 스윕 없음) — 이유는 세그먼트 판단
아래에 명시.

**세그먼트 판단:** product-shaped 아님. `core_root()`는 사용자가 보지 못하는
내부 오케스트레이션(spawn.py)의 체크아웃 해석 로직이다 — 비교할 외부
"카테고리 best-in-class" 제품이 존재하지 않는다. 그래서 스윕 대신, 이슈
본문이 직접 지목한 **이 저장소 안의 동종 해법**을 prior art로 깊게 읽었다
(scout-directive의 "non-product roles scout the best of their own
deliverable's kind" 조항 적용).

**Prior art: 룰북(역할) 체크아웃의 신선도 3종 세트**
(`spawn.py:174-224`, `523-562`)
- `rulebook_checkout()`: 로컬 오버라이드는 그대로 반환(pull 없음) / on-the-record
  소유 클론만 반환 전 `git pull --ff-only`.
- `checkout_version()`: 어느 경로든 sha·branch·dirty·출처("로컬" vs "on-the-record
  클론")를 **읽기 전용**으로 문자열화 — pull도 mutate도 안 함.
- 이 값이 스폰 로그 줄(`spawn.py:2394`)과 ledger 레코드(`spawn.py:2628`)
  양쪽에 매 spawn마다 찍힌다.

**Must-be (이 prior art가 이미 강제하는 것):** 로컬 오버라이드 우선순위는
건드리지 않는다 — 신선도를 "강제 갱신"이 아니라 "보고"로 다룬다.

**성능축(이 저장소의 두 경로가 갈리는 지점):** (1) 신선도 *확인* — pull로
실제 최신화하는가, (2) 신선도 *보고* — sha/날짜를 로그·ledger에 남기는가.
룰북 경로는 관리 클론에서만 (1)을 하고, 모든 경로에서 (2)를 한다.
core_root()는 관리 클론에서만 (1)을 하고(이 부분은 이미 룰북과 같다),
**(2)를 아무 경로에서도 하지 않는다** — 이게 갭이다.

**GAP LINE:** must-be 중 "로컬 오버라이드 pull 안 함"은 core_root()가 이미
충족(변경 불필요). "신선도 보고"는 룰북 쪽엔 있고 core 쪽엔 전무 — 이번
제안이 메울 갭은 이것 하나.

**Adopt:** `checkout_version()`과 같은 모양(sha + 상태 + 출처, 읽기 전용
문자열, 스폰 로그·ledger 양쪽에 배선)을 core에도 만든다.
**Skip:** `rulebook_version()`의 설치본-vs-클론 비교(core는 `--plugin-dir`
직결이라 "설치본" 개념이 없어 해당 없음).

**Sources:** 전부 이 저장소 내부 파일 — `spawn.py:174-224`, `spawn.py:523-562`,
`spawn.py:1781-1831`, `spawn.py:2394`, `spawn.py:2628`, `spawn.py:1798-1799`
(로컬 우선=개발용 오버라이드 주석), `test_spawn.py:59-96`. 외부 웹 소스
없음(위 세그먼트 판단 사유).

**스테이지:** 1스테이지(내부 prior-art 정독), 판단점 1회 후 즉시 포화 —
룰북 쪽 3개 함수를 다 읽은 시점에 이미 갭(신선도 *보고* 부재)이 명확해져
추가 라운드가 결정을 바꾸지 않는다고 판단, 조기 종료.
