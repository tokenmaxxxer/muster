# Scout brief — issue #197: 계획 블록 파서 수정

Stage 1 (sweep, 3 angles, 병렬 `WebSearch` 단일 메시지 — parallel 모드, 배치-순차
폴백 아님), judge point 1회 후 수렴(2회차 딥닝 불필요 판단, 예산 내 조기 종료).
소요: 세 검색 각 1콜, 판단 1회 — 5스테이지·3분 예산 안에서 종료.

## Must-be (카테고리 공통 전제)

- 코드펜스 안 콘텐츠는 구조적 마크업(헤딩 포함)으로 해석되지 않는다 —
  CommonMark 스펙 자체의 우선순위 규칙(펜스드 코드 블록이 먼저 파싱되고 그
  안의 `#` 로 시작하는 줄은 리터럴로 취급된다, spec.commonmark.org 0.29/0.30
  Fenced code blocks·ATX headings 절). 이 레포가 지금 위반하고 있는 것이
  바로 이 must-be.
- 경량 라인 스캐너로 펜스를 다룰 때는 `` ``` `` 토글 방식이 표준 관용구다 —
  정규식 하나로 펜스 전체를 매치하려는 시도보다 상태 플래그 토글이 실제
  구현체(marked.js PR #1853 등)와 이 레포 자체 관용구(아래 gap 라인)에서
  공통으로 쓰인다.

## 성능 축 (경쟁하는 2~3 차원)

1. **정확도 vs 구현 비용** — 전용 마크다운 파서 라이브러리(CompreheMD 류)는
   중첩·인라인 코드까지 완전히 다루지만 새 의존성이 필요하다. 정규식/라인
   스캔은 이 레포가 다루는 좁은 구조(ATX 헤딩 + 체크박스 리스트)만 노리면
   충분하고 의존성이 없다.
2. **헤더 매칭 관용도** — 정확 일치(취약, 변형 헤더 다 놓침) vs 전방일치
   (관용적이나 우연한 동명 헤더를 오매치할 위험) — 경계 문자(공백/줄끝)
   요구로 위험을 낮추는 것이 표준적으로 언급되는 절충(`startsWith` 계열
   함수 문서, 정확 경계 필요성).

## 채택 / 스킵

- **채택**: 펜스 토글 상태 플래그 + 전방일치(공백 경계) 헤더 매칭. 이
  레포 자체에 이미 검증된 선례(`gates/gates.py:387-392`,
  `record_no_tool_residue_in`)가 있고, 위 must-be(CommonMark 우선순위 규칙)와
  정확히 같은 방향이다.
- **스킵**: 전용 마크다운 파서 라이브러리 도입. 이 레포가 다루는 구조가
  ATX 헤딩 + 체크박스 리스트뿐이라 라이브러리의 나머지 기능(인라인 파싱,
  링크, 표 등)이 전혀 안 쓰이고, no-footgun 방침("플랫폼이 이미 제공하는
  것에 새 의존성 금지")과도 충돌 — 이 레포에 마크다운 파서 의존성이
  현재 전혀 없다(grep 확인, 자체 정규식/라인스캔만 씀).

## 세그먼트 적합성 (한 줄)

이 결함은 사용자향 제품이 아니라 내부 CLI 데이터 계약(`flows --json`)의
파서다 — "베스트인클래스 경쟁 제품"이 아니라 "이 레포 자신의 기존
관용구"가 가장 적합한 비교 대상이었고, 실제로 그 관용구(`gates/gates.py`)가
이미 정확히 이 문제를 풀어 놓았다는 사실이 이번 스윕의 핵심 수확이다.

## Gap 라인

현재 상태가 이미 충족: "펜스는 토글 플래그로 스킵한다"는 관용구 자체는
`gates/gates.py`에 이미 있다 — **재발명이 아니라 재사용** 문제다.
현재 상태가 놓친 것: (1) 그 관용구가 `gates/flows.py`의 `_plan_from_body`에는
전혀 적용돼 있지 않다, (2) 헤더 매칭이 정확 일치뿐이라 must-be의 "전방일치
경계 안전성" 축을 아예 다루지 않는다, (3) 문법 정의(`run.md`)가 펜스/헤더
변형 규칙에 침묵해 위 두 갭을 스펙 차원에서 승인해 버렸다.

## 사용한 스테이지/모드

Stage 1 sweep 1회(3 angles, parallel), judge point 1회 후 saturation 판단으로
정지 — 추가 딥닝이 채택/스킵 판단을 바꾸지 않을 것으로 판단(내부 선례가
이미 결정적 증거였음).

Sources:
- https://spec.commonmark.org/0.30/
- https://spec.commonmark.org/0.29/
- https://spec.commonmark.org/0.12/ (Fenced code blocks)
- https://github.com/markedjs/marked/pull/1853 (fix: fix atx heading and make regex safe)
- https://www.smashingmagazine.com/2020/12/commonmark-formal-specification-markdown/
