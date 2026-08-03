---
subject: issue-246
role: implementation
phase: 1
---

# Scout brief — issue #246

**모드:** Stage 1 sweep, 2 angles, 병렬 `WebSearch` 단일 메시지(parallel
모드, 배치-순차 폴백 아님). Judge point 1회 후 즉시 포화 판단 — 2회차
딥닝 없이 종료. 소요: 검색 2콜 + 판단 1회, 5스테이지·3분 예산 안에서
종료.

**세그먼트 판단:** product-shaped 아님 — `spawn.py`의 refusal 분류기는
사용자가 보는 제품이 아니라 내부 오케스트레이션 스크립트다. 비교할 외부
"카테고리 best-in-class 제품"이 없어, survey.md가 찾은 두 개의 열린
결정(S1-S3 처리 방식, dedup granularity)에 대응하는 **공학 관용구**를
스윕 대상으로 삼았다.

## Angle 1 — 버퍼-후-flush 구조의 크래시 안전성 (결함 1 대상)

Write-ahead logging의 원칙은 "먼저 기록하고 나중에 반영"이다 — 커밋을
확정하기 **전에** 로그 레코드를 먼저 디스크에 쓰고, 크래시 후에는 그
레코드로 재생(replay)한다. 이 저장소의 buffer-then-flush 구조는 정확히
반대 순서(상관관계 확정 후에야 기록)를 issue #235가 의도적으로 선택한
것이고(`docs/issue-235/reports/implementation.md:94-115`), 그 대가로
크래시 구간의 내구성을 잃는다는 것이 이미 그 기록의 Hunt finding 1이다.
**Must-be:** 진짜 내구성(크래시 후에도 이벤트가 살아남음)을 되찾으려면
상관관계 확정 **전에** 기록해야 하는데, 그건 이 이슈의 제약("buffer-then-
flush 구조 유지", "새 계측 금지")과 정면으로 부딪힌다 — 구조 자체를 WAL
방식으로 바꾸는 것은 이번 이슈의 스코프 밖이다.
**적용:** 구조를 바꾸는 대신, 스트림이 터미널 `result` 줄 없이 끝나는
경우(EOF)에 한해 아직 상관관계가 안 된 `pending_refusals`를 확정
`gate-refusal`/`harness-refusal`/`sandbox-refusal`이 아닌 별도 라벨(예:
issue 본문이 직접 제시하는 `unverified-refusal`류)로 플러시하는 것은
WAL이 요구하는 "사전 기록"을 흉내 내지 않으면서도 완전한 침묵-손실을
막는 절충이다 — 크래시 시점에 이미 분류까지 끝난 텍스트를 "미확인"으로
표시해 내보내는 것이지, 상관관계 검증 자체를 앞당기는 것이 아니다.

## Angle 2 — 에러 dedup 의 fingerprint granularity (결함 2 대상)

Sentry의 이슈 그룹핑 관용구: 기본값은 굵은 단위(스택트레이스 기반)로
묶지만, 그 굵기가 실제로 다른 사건을 뭉갤 때(예: 같은 스택트레이스를
공유하는 RPC 호출인데 대상 엔드포인트가 다른 경우) fingerprint 규칙으로
**더 가는 단위**로 오버라이드하도록 권장한다 — 실제로 갈리는 내용을
키에 반영하라는 것이 이 관용구의 핵심.
**Must-be:** 굵은 키(레이어 단위)가 실제로 다른 두 사건을 뭉갤 수 있다는
것이 확인되면, 기본값을 그대로 유지하는 것보다 **실제로 갈리는 내용
(detail/reason 텍스트)을 키에 포함**해 세분화하는 쪽이 표준적으로
권장된다.
**적용:** 이 저장소의 dedup 키(`("gate", stem)` / `("harness",)` /
`("sandbox",)`)를 detail(또는 그 정규화된 형태)까지 포함하도록 세분화하는
쪽이 Sentry 관용구와 같은 방향 — "층당 1회"에서 "동일 detail 당 1회"로.

## Adopt / Skip

- **Adopt:** 결함 1 — EOF/크래시로 상관관계가 끝내 안 된 버퍼는 별도
  라벨로 플러시(issue 자신이 예시로 든 방향), `denials`에 `isinstance`
  가드 추가. 구조는 그대로 두고 손실 폭만 좁힌다.
- **Adopt:** 결함 2 — dedup 키를 레이어 단위에서 detail 단위로 세분화.
  Sentry 관용구와 같은 방향이고, 마스킹 픽스처로 고정 가능.
- **Skip:** 결함 1 — "명시적으로 버리는 결정을 문서화"만 하고 코드는
  안 바꾸는 대안. WAL 관용구가 보여주듯 이 손실은 흔한 실패급(크래시)에서
  발생하고 감사 대상 이벤트(거부 기록)라 손실 허용의 대가가 크다 — 근거는
  proposal의 Rationale에 기록.
- **Skip:** 결함 2 — "전체 유지"(현재 레이어 단위 그대로) 대안. Sentry
  사례가 보여주는 "굵은 키가 실제로 갈리는 사건을 뭉갠다"는 신호가 이미
  이 저장소 자체 구조(첫-기록-승리 + 레이어 단위 키)에 그대로 있다 — 근거는
  proposal의 Rationale에 기록.

**GAP 라인:** 두 must-be(사전 기록 내구성, 세분화된 fingerprint) 모두
현재 코드가 미충족 — 결함 1은 EOF 플러시 부재로, 결함 2는 레이어 단위
키로. 이슈가 이미 두 선택지를 이름 붙여 제시했으므로 스윕의 역할은 새
옵션을 발명하는 게 아니라 어느 쪽이 이 저장소의 실제 리스크(감사용
이벤트 손실, 잘못된 detail 로 뭉개짐)와 더 맞는지 공학 관용구로 뒷받침하는
것이었다.

**Sources:**
- [How Write-Ahead Logging Makes Databases Crash-Safe](https://medium.com/@vinodbokare0588/how-write-ahead-logging-makes-databases-crash-safe-7d420a03fca5)
- [Write-ahead logging and the ARIES crash recovery algorithm](https://sookocheff.com/post/databases/write-ahead-logging/)
- [Sentry — Event Fingerprinting](https://docs.sentry.io/platforms/javascript/enriching-events/fingerprinting/)
- [Sentry — Why Are My Events Grouped or Separated Incorrectly](https://sentry.zendesk.com/hc/en-us/articles/26184711712155-Why-Are-My-Events-Grouped-or-Separated-Incorrectly-in-Sentry)
- 내부: `docs/issue-235/reports/implementation.md:94-129`,
  `docs/issue-235/reports/execution-observation.md` Finding 1·2·3,
  `spawn.py:1491-1540,2748-2826`, `test_spawn.py:1576-1593`.
