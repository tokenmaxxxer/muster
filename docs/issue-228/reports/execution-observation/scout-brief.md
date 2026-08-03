---
role: execution-observation
issue: 228
phase: 1
kind: scout-brief
---

# scout brief — "게이트 변경을 감사하는 리뷰"의 현장 기준

실행 방식: **병렬 fan-out**, sweep 1 스테이지만(각도 3개를 한 턴에 동시 디스패치), deepening 0 스테이지. 총 1/5 스테이지, 3분 예산 내. 포화 판정: 세 각도의 겹침이 아래 세 기준으로 수렴했고 추가 라운드가 phase-2 증거 계획을 바꾸지 않으므로 중단. sweep 각도는 survey 의 미지 S-1·S-3·S-4 에서 뽑았다.

## 이 부류(게이트 변경 감사)의 must-be

- **신규 테스트의 게이팅 력(力)은 "실행됐고 단언이 거짓이었나"로만 인정된다.** 시그니처 변경으로 인한 TypeError 는 "옛 코드에서 돌려볼 수 없었다"는 사실일 뿐 RED 증거가 아니다 — RED 는 assertion mismatch 여야 하고 syntax/TypeError 실패는 테스트를 고치라는 신호로 분류된다(industriallogic, ploeh). 변이 테스트(PIT/Stryker)가 이 부류의 표준 척도이며, 커버리지%가 아니라 "변형된/옛 구현에서도 초록이면 게이팅 력 없음"으로 판정한다.
- **fail-closed 게이트는 "평가 불가"와 "평가했고 위반"을 구분 가능한 신호로 내야 한다.** 구분 없는 fail-closed 는 장애를 정책 위반으로 위장한다는 것이 Gatekeeper 문서의 명시 비판이다.
- **fail-closed 는 위험 등급에 따라 선택되는 것이지 기본값이 아니다** — 보안·안전 임계 검사에만 정당화되고, 그 외에는 가용성 보호를 위해 fail-open 을 기대한다.
- **통제의 인과 귀속은 "그 시점에 통제가 실제로 돌았는가"를 먼저 증명한다** — SRE 포스트모템은 trigger 와 root cause 를 분리해, 논리 결함(돌았어도 못 잡음)과 배포·배선 결함(옳은 통제가 그 시점에 돌지 않음, 예: stale artifact/cache)을 갈라 놓는다. 강제 체크인지 advisory 인지(required status check 대 evaluate 모드)가 이 분기의 결정 증거다.

## 경쟁 축 (이 부류가 실제로 겨루는 2가지)

1. **증거 해상도** — "테스트가 늘었다"가 아니라 "어느 테스트가 어떤 근거로 옛 코드를 잡는가"까지 내려가는가.
2. **인과 분리도** — 사건을 통제 결함과 배포 경로 결함으로 나눠 각각에 다른 조치를 붙이는가, 한 덩어리로 뭉개는가.

## 채택 / 비채택

- **채택**: (1) 테스트별 실패 근거를 arity 대 assertion 으로 나눠 표로 적는 형식 — S-1/U-1 을 정직하게 해결한다. (2) fail-closed 평가를 "구분 가능한 신호 / 위험 등급 / 우회 경로 / 단계적 롤아웃" 네 질문으로 던지는 체크리스트 — S-3 을 겨눈다. (3) 사건 귀속 시 "그 시점에 어느 버전이 돌았나"를 timeline 으로 먼저 고정 — S-4 를 겨눈다.
- **비채택**: 변이 테스트 실제 실행(PIT/Stryker) — 이 role 은 관측 대상 코드 실행이 금지돼 있어 도구를 돌릴 수 없다. 변이 테스트의 *판정 기준*만 빌리고 실행은 하지 않는다. break-glass/override 설계 권고도 비채택 — 이 저장소 게이트는 GitHub 강제 체크가 아니라 사람이 돌리는 스크립트라 세그먼트가 다르고, 설계 처방은 이 role 의 산출물이 아니다.

## 세그먼트 적합성

참조한 사례는 대부분 강제형 admission control(Gatekeeper/PSA)과 required status check 다. 이 저장소의 게이트는 브랜치 보호도 워크플로도 없는 **비강제·수동 실행 스크립트**다. 따라서 위 기준은 "이 게이트도 그래야 한다"는 처방이 아니라, **판정 시 반드시 물어야 할 질문 목록**으로만 가져온다.

## GAP LINE

현재 상태가 이미 충족하는 must-be: 사건 timeline 이 API 로 완전히 남아 있어 "그 시점에 무엇이 돌았나"를 고정할 수 있다(각도 d 증거). 비어 있는 must-be: (i) 테스트별 실패 근거의 arity/assertion 구분이 어디에도 기록돼 있지 않다, (ii) "평가 불가" 차단과 "위반" 차단이 서로 다른 신호인지 확인된 바 없다, (iii) 새 fail-closed 경로가 warn 모드를 거쳤는지에 대한 기록이 없다. 이 세 칸이 phase-2 증거 계획이 겨눌 지점이다.

Sources:
- https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/
- https://www.industriallogic.com/blog/tdd-youre-doing-it-wrong/
- https://blog.ploeh.dk/2019/10/21/a-red-green-refactor-checklist/
- https://blog.ploeh.dk/2019/10/14/tautological-assertion/
- https://open-policy-agent.github.io/gatekeeper/website/docs/failing-closed/
- https://open-policy-agent.github.io/gatekeeper/website/docs/customize-admission/
- https://authzed.com/blog/fail-open
- https://kubernetes.io/docs/tasks/configure-pod-container/migrate-from-psp/
- https://sre.google/sre-book/postmortem-culture/
- https://sre.google/workbook/postmortem-analysis/
- https://medium.com/@warstories/how-a-stale-artifact-created-two-versions-of-the-same-system-888be562b2c3
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
