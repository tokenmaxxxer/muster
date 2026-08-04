# Scout brief — issue #266

스테이지: 1 스테이지(WebSearch 2건, 같은 턴에 병렬 발사), 판단점 1회 후 종료 — 두 앵글의 결과가 이슈의 두 후보(a)/(b)에 정확히 대응해 추가 라운드가 결정을 못 바꿈(포화).

## Must-bes (카테고리 공통 관찰)
- 우아한 종료(graceful shutdown) 도중 헬스체크/레지스트리가 "응답 없음"을 곧장 "죽음"으로 해석하면 오탐이 난다 — 정상 종료가 느릴수록 이 창이 커진다. [Source 1]
- 레지스트리 등록 해제(deregistration)는 프로세스가 실제로 정리 작업을 끝낸 뒤에 일어나야 한다 — 순서를 암묵적 타이밍에 맡기면 부서지기 쉽다(fragile). [Source 1]
- 장애 탐지기(failure detector)는 근본적으로 불완전하다 — 응답 없음과 죽음을 항상 구분할 수 없으므로, 부재/무응답을 "확정 사망"이 아니라 "불명"으로 다루는 쪽이 오탐(false-down)을 줄이는 신중한 기본값이다. [Source 2]

## 성능 축
- **탐지 지연 vs 오탐률** — 이슈의 (a)/(b) 둘 다 이 축의 반대편에 선다: (a)는 지연을 안 늘리고 오탐만 없애려 하고(엔트리 수명 연장), (b)는 오탐을 확실히 없애는 대신 부재-상태의 탐지를 안전망(stall timeout) 지연으로 늦춘다.
- **결합도** — (a)는 같은 키를 지우는 다른 소비자(`roster_kill`, `roster_ps`, survey.md 참고)와 순서를 공유해야 닫힘이 보장된다(결합 高); (b)는 `_watch` 판정부 하나만 바꿔 다른 소비자와 무관하다(결합 低).

## Adopt / Skip
- **Adopt**: 부재를 불명으로 두고 기존 stall 안전망에 위임하는 패턴(Source 2) — 이 파일이 이미 `stall_timeout_min` 안전망을 갖고 있어 새 메커니즘이 필요 없다.
- **Skip**: preStop-hook류 "지연 삽입"(Source 1의 로드밸런서 사례) — 이 저장소엔 로드밸런서가 없고, 지연을 어디 얼마나 넣을지는 이슈가 이미 (a)로 구체화해 뒀다(모델을 그대로 빌려올 필요 없음).

## Segment fit / Gap line
사내 CLI 오케스트레이터의 프로세스 명부 — 클라우드 서비스 메시보다 훨씬 작은 스케일이지만 실패 모드(등록 해제 레이스)는 동일 카테고리. 이 저장소가 이미 갖춘 것: 안전망(stall timeout), 별도 생존 신호(wrapper_pid) — 필드가 이미 K8s의 readiness/liveness 분리와 유사한 모양. 이 저장소에 없는 것: 등록 해제를 "정리 완료 이후"로 미루는 명시적 순서(= 이슈의 (a)), 그리고 "부재 = 불명"으로 읽는 소비자 쪽 관용구(= 이슈의 (b)) — 카테고리가 둘 다 실제 관행으로 인정하므로 스카우트는 우열을 가리지 않고 이 저장소의 결합도 구조(survey.md)로 판단을 넘긴다.

Sources:
- https://www.momentslog.com/development/spring-boot-graceful-shutdown-on-kubernetes-build-a-termination-budget-that-actually-drains-traffic
- https://copyconstruct.medium.com/health-checks-in-distributed-systems-aa8a0e8c1672
