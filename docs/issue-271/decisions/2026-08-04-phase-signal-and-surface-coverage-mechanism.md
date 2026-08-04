---
name: phase-signal-and-surface-coverage-mechanism
kind: decision
---

# phase 신호 분리 메커니즘과 표면 커버리지 방법 (issue #271)

승인된 제안
(`docs/issue-271/proposals/2026-08-04-closing-trigger-surface-coverage-and-phase-predicate-separation.md`)
의 Rationale 두 가지를 실행 시점 결정으로 기록한다. 둘 다 phase 2 실행
중에도 그대로 유지됐다 — 아래는 왜 그 선택이 맞았는지와, 제안 문서
자체가 몰랐던 구현 디테일 하나(`flows._pr_approved` 재사용)를 덧붙인다.

## 1. phase 신호: 승인 이벤트로 유도한다 (closing 키워드도, 브랜치명도, 계획 상태도 아니다)

### 채택: `APPROVE issue-<n>/<role>` 이벤트

`gates/ci.py`의 `--autodetect` 경로에서 phase 를 더 이상 PR 본문의
closing 키워드에서 유도하지 않는다. 대신 role-handoff contract v3 s19가
이미 phase-2 개시 조건으로 정의한 바로 그 신호를 재사용한다:

- single-account: 승인자(`docs/specs/approvers.md`) 계정이 정확한 문자열
  `APPROVE issue-<n>/<role>` 코멘트를 이슈 또는 PR 에 남긴다.
- two-account: PR author 와 다른 승인자 계정의 PR 리뷰 Approve.

이 신호가 있으면 phase2, 없으면 phase1 — closing 키워드 유무는 이 판정에
전혀 관여하지 않는다. 이렇게 분리하면 requirement 2 가 요구한 상태
("phase1 로 판정되면서 본문에 closing 키워드가 있는" 상태)가 실제로
관측 가능해진다: pre-fix 에서는 closing 키워드가 있으면 그 자체로
phase 가 phase2 로 튀어 phase1-mismatch 검사가 도는 분기(`phase ==
"phase1"`)에 도달할 수 없었다(#245 관찰 F1). 승인 이벤트는 closing
키워드와 독립이므로, "승인 전인데 본문에 키워드가 있다"가 이제 실제로
일어날 수 있는 상태가 되고, 검사가 그 상태에 도달한다.

### 구현 디테일: `flows._pr_approved` 재사용 — 제안서가 몰랐던 기존 함수

제안서의 Rationale 은 `spawn._issue_comments`/`spawn._approvers` 를 손으로
엮어 이 판정을 새로 짜는 그림이었다(`approve_scope`의 idiom을 복사).
phase 2 실행 중 코드를 직접 읽어보니 `gates/flows.py:130`
`_pr_approved(pr, comments, approvers, subject, role)` 이 정확히 이
계약(코멘트 경로 + PR 리뷰 경로, 둘 다)을 이미 구현하고 있었다 —
상황판(`flows.status()`)이 미승인 PR 을 판별하는 데 이미 쓰는, 실사용
검증된 코드다. 새로 손으로 짜는 대신 이걸 재사용하기로 실행 시점에
바꿨다: 같은 로직을 두 벌 유지할 이유가 없고, 기존 함수 쪽이 이미 두
경로(코멘트/리뷰) 모두를 다뤄 제안서가 서술한 "코멘트 경로만 먼저 짜고
리뷰 경로는 나중"보다 완전하다. `gates/ci.py`는 `flows`를 새로 import
한다(`pr_reference.py`가 이미 `flows`를 쓰는 것과 같은 층 — 새 의존성
방향이 아니다). 이 스왑은 제안서의 Rationale 이 고른 **신호**(승인
이벤트)를 바꾸지 않는다 — 그 신호를 읽는 **코드**를 새로 짜지 않고
재사용한 것뿐이라, phase-2 record 의 "Rationale for deviations"가 아니라
이 결정 문서 쪽 각주로 남긴다.

### 기각한 대안 (제안서 원문 그대로, 실행 후에도 유효함이 재확인됨)

- **브랜치명**: `issue-<n>/<role>` 은 phase 1/2 동안 동일하므로 phase를
  구분할 신호가 못 된다.
- **계획(plan) 체크박스 상태만으로**: "마지막 스텝만 미완"은 phase-1
  제안 PR 과 phase-2 인도 PR 모두에서 나올 수 있는 모양이라, 신호로 쓰면
  requirement 2 가 닫으려는 바로 그 모호성을 계획-파싱 함수 쪽으로 옮길
  뿐이다.
- **phase 분기 밖에서 무조건 검사**: phase-2 인도 PR 은 원래
  closing 키워드를 **요구**하므로(`pr_reference.check_body`), 무조건
  금지하면 정상적인 phase-2 인도 머지를 오탐 차단한다.

## 2. 표면 커버리지: 각 표면을 직접 읽는다 (`closingIssuesReferences`로 대체하지 않는다)

`gates/ci.py`가 PR 제목(row B)과 브랜치 커밋 메시지 각각(row C)을
`gh pr view --json title`/`gh api repos/<slug>/pulls/<n>/commits`로 직접
읽어 기존 `_CLOSES_REF` 정규식을 적용한다 — GitHub의 GraphQL
`closingIssuesReferences` 필드로 대체하지 않는다.

**근거(실측)**: survey.md §4b — 실물 커밋-메시지 사고 PR 에
`closingIssuesReferences,body`를 질의하면 **빈 리스트**가 나온다. 그
머지가 실제로 이슈를 자동으로 닫힌 바로 그 머지인데도다. 이 필드는
본문-파생/수동-링크 관계만 반영하고 커밋 메시지 파생 종결은 반영하지
않는다 — 이 이슈가 존재하는 이유인 바로 그 구멍을, "더 GitHub-네이티브해
보이는" 방법으로 대체했다가 조용히 재현할 뻔했다. row H(수동 링크,
텍스트 신호 자체가 없는 유일한 표면)에 대한 보완 신호로만 이름을
남기고(제안서 표), 주 메커니즘으로는 채택하지 않는다.

## 3. row G — 사람이 머지 시점에 직접 타이핑하는 커밋 메시지

pre-merge 게이트는 이 표면을 원리적으로 못 본다(그 텍스트가 아직
존재하지 않는다) — 제안서의 Out of scope대로 별도 완화책을 이 PR 에
추가하지 않는다. 기존 `gates/closure_sweep.py`의 사후 보드 스윕이 이미
이 클래스 전체(사전 게이트가 못 보는 모든 경우)의 유일한 회수 경로다.
