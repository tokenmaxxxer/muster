---
role: execution-observation
issue: 228
phase: 1
kind: proposal
loop_state: proposed
---

# 제안 — issue #228 step 2 관측을 어느 층에서, 어떤 증거로 판정할 것인가

**이 문서는 판정을 담지 않는다.** 아래는 phase 2 에서 무엇을 어떤 증거에 대고 판정할지의 계획이며, 잠정 판정도 여기에 쓰지 않는다. 판정은 승인 후 `docs/issue-228/reports/execution-observation.md` 에서만 내린다.

관측 대상: role `implementation`, issue #228 실행 계획 step 1, PR **#231**, delivery 커밋 **923416d**, 자기 기록 `docs/issue-228/reports/implementation.md`. 현재 상태 조사는 `reports/execution-observation/survey.md`, 증거 적재는 `reports/execution-observation/research.md`, 감사 기준은 `reports/execution-observation/scout-brief.md`.

## 검사할 세 층과 각 층의 증거원

### 1. outcome — PR/기록이 이슈가 요구한 것을 실제로 실었는가

요구 4건(issue #228 본문 L16-19) 각각에 대해 **구현 hunk 의 file:line** 과 **그 hunk 를 실행하는 테스트의 존재 여부**를 짝지어 판정한다. 증거원: `git show 923416d` 의 `gates/pr_reference.py`·`gates/ci.py` hunk, `git show 923416d^:gates/pr_reference.py`(변경 전 대조), `923416d test_gates.py` 의 신규 테스트, `git grep -n "_plan_from_body" 923416d`.

판정 기준(문항 형태, 답은 phase 2 에서):

- R1(미완 스텝 시 차단·마지막 스텝만 요구)·R2(계획 없는 이슈 현행 유지)·R4(`_plan_from_body` 재사용): 요구된 동작이 코드에 있는가, 그리고 그 코드 경로에 도달하는 테스트가 있는가.
- R3(펜스 안 인용도 파싱됨): 요구가 명령한 **과소 계수 방지**(펜스 안 `Closes` 를 세야 한다)와, 요구가 명령하지 않은 **과대 계수**(GitHub 이 파싱하지 않는 `<!-- -->` 주석·인라인 코드 스팬) 중 어디까지가 이 이슈의 범위였는지를 이슈 문언과 결정 문서(923416d docs/issue-228/decisions/2026-08-03-check-body-plan-aware-closes.md:79-82)로 먼저 확정한 뒤 판정한다. 범위 밖으로 명시된 것을 미이행으로 세지 않는다.

### 2. trajectory — phase-1→phase-2 경로가 온전했는가

증거원: `docs/issue-228/proposals/implementation.md`(제안이 승인 전에 존재했는가·범위를 미리 선언했는가), `docs/issue-228/reports/implementation/survey.md`(제안 전에 현재 상태 조사가 있었는가, 실측 스캔이 있었는가), issue #228 코멘트 `APPROVE issue-228/implementation`(<https://github.com/tokenmaxxxer/on-the-record/issues/228#issuecomment-5161635406>, 승인이 정확문자열·approvers.md 계정이었는가), `docs/issue-228/reports/implementation.md` 의 hunt 처분(스스로 찾은 findings 를 숨겼는가 남겼는가), 그리고 PR #231 본문의 closing 키워드 처리.

판정 기준: (i) 승인이 계약 v3 s19 의 두 경로 중 하나를 문자 그대로 만족했는가, (ii) phase-1 산출이 phase-2 착수 **전에** 커밋됐는가(커밋 순서 2c84417 → 923416d 로 확인), (iii) 이슈가 제약으로 지목한 인접 결함(ci.py `--phase`)을 범위에 넣은 결정이 제안 단계에서 선언됐는가 아니면 사후 확장이었는가.

### 3. step — 어느 특정 아티팩트가 미흡한가

이 층은 아래 네 질문에 대해서만 열고, 각 질문은 scout-brief 가 정리한 현장 기준을 그대로 척도로 쓴다.

- **(a) 신규 테스트 9건의 변경 전 실패 근거**: 각 테스트를 `arity 로만 실패` / `assertion 이 옛 로직과 충돌` / `옛 로직에서도 통과` 세 칸으로 분류한 표(research.md 각도 a)를 근거로, "9건이 변경 전에 실패한다"는 명제가 어느 해상도에서 참인지 판정한다. 척도: 실패가 assertion mismatch 여야 RED 증거로 인정된다(scout-brief must-be 1). **제약 고지**: 이 role 은 관측 대상 테스트를 실행할 수 없으므로 판정은 blob 정독으로 연역 가능한 범위까지이며, 그 경계를 판정문에 명시한다.
- **(b) ci.py `--phase` 수정과 도달 가능성**: 변경 전 무음 경로가 "검사 없음"이었는지 "다른 약한 검사로의 대체"였는지를 923416d^ gates/ci.py:44,90 대 923416d gates/ci.py:49-53 로 확정하고, 그 수정이 이 게이트를 도달 가능하게 한 인과를 호출 사슬로 서술한다. 자동 호출 지점 부재(`.github/workflows` 공백, `--phase` grep 0건)가 "도달 가능"의 의미를 어떻게 한정하는지도 함께 판정한다.
- **(c) fail-closed 방향의 위해**: 신규 차단 경로 두 곳(923416d gates/ci.py:49-51, gates/pr_reference.py:98-100)에 대해 scout-brief 의 네 질문 — 평가 불가와 위반이 구분되는 신호인가 / 이 검사의 위험 등급이 fail-closed 를 정당화하는가 / 우회 경로가 있는가 / warn 단계를 거쳤는가 — 를 던지고, **정당한 phase-2 를 새로 막는 구체적 입력이 존재하는지**를 입력 열거로 답한다. 저장소 밖 호출자 가능성은 확인 불가로 남기고 가정으로 라벨한다.
- **(d) 실물 사건 귀속**: 사건 1(PR #231 자신이 closing 키워드 없이 머지돼 #228 자동 종결 없음)과 사건 2(PR #237 머지 직후 #235 자동 종결, 8번째 사례)를 **각각 따로** 귀속한다. 척도: "그 시점에 어느 버전의 통제가 실제로 돌았는가"를 timeline 으로 먼저 고정하고(1fc8e96 머지 시각 대 PR #237 머지 시각), 그 다음 통제 논리 결함인지 배포·배선 결함인지 가른다(scout-brief must-be 4). 증거원: issues/228·235 timeline API, #235 재오픈 코멘트, issue #221 본문, `spawn.py:2372-2375`, `spawn.py:1054-1064`, 브랜치 보호 부재.

## 미흡 findings 를 쓰는 형식

step 층에서 미흡이 확인되면 4부 blameless 형태로 적는다 — impact / timeline / root cause / action item, findings 1건 규모로 축소하고 전면 포스트모템 의식은 붙이지 않는다. 세 층 모두 해당 없는 경우에도 "해당 없음, 이유 X" 로 명시하고 침묵으로 생략하지 않는다.

## 이 role 이 하지 않는 것

관측 대상의 `src/`·`test/`·`docs/issue-228/` 중 이 role 의 기록 경로 밖은 읽기만 하고 편집하지 않는다. 관측 대상 코드·테스트를 실행하지 않는다. 이슈를 발행하지 않는다 — 확인된 미흡은 이 PR 의 기록에만 담고, 판단과 이슈화는 사람이 한다.

## phase 2 착수 조건

approvers.md 계정이 issue #228 에 본문 전체가 정확히 `APPROVE issue-228/execution-observation` 인 코멘트를 남기거나(단일 계정 모드), 이 PR 에 approvers.md 계정의 리뷰 Approve 가 달릴 때. 그 전까지 `docs/issue-228/reports/execution-observation.md` 는 쓰지 않는다.
