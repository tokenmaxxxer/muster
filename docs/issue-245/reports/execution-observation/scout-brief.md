---
name: execution-observation-scout-brief
kind: scout-brief
---

# Scout brief — "머지 게이트 신설 + 필수 체크 활성화" 부류를 강하게 감사할 때 무엇을 보는가

조준점: survey §4 의 G1(규칙 도달성) / G3(강제력 검증의 충분성). 판정
아님 — 이 부류의 감사 기준선(bar)만 모은다.

**Category must-bes** (이 부류의 감사가 당연히 요구하는 것)
- 양방향 실증: 위반 케이스가 실제로 막히고(negative/control-effectiveness
  test) *동시에* 클린 케이스가 통과하는 것 — 한쪽만은 통상 불충분으로 본다
  (false-negative + false-positive 양쪽 예산). [1][2]
- 게이트 스크립트의 변조 불가성: 검사 대상 PR 자신이 검사 로직을 고쳐
  통과시킬 수 있으면 통제로 인정되지 않는다(d-PPE / pwn request). 신뢰
  브랜치 체크아웃이 그 방어. [3][4]
- 규칙이 "존재"가 아니라 "발화 가능"함의 증거 — 도달 불가 규칙은 PASS 를
  보고하며 조용히 무의미해진다(vacuity / shadowing). red-green 픽스처나
  뮤테이션으로 발화를 보인다. [5][6][7]
- 필수 체크가 *트리거되지 않는* 경로 점검: GitHub 은 "이름이 목록에 있는
  체크"를 요구하지 [8], "트리거된 체크"를 요구하지 않는다 — 워크플로가 안
  돌면 `expected` 로 영구 대기, 잡 이름이 바뀌면 옛 컨텍스트가 영구 차단. [8][9]
- 본문 검사형 체크는 `pull_request` 기본 types 로는 본문 편집 시 재실행되지
  않는다 — `edited` 를 명시해야 한다. [10]
- `enforce_admins` 의 실제 범위: 규칙이 살아 있는 동안의 push/merge 만 막고,
  규칙 자체의 편집·삭제는 admin 이 여전히 할 수 있다(self-revocable). [11]

**성능 축(이 부류가 실제로 경쟁하는 2-3 차원)**: (1) 커버리지 — 사람이 웹
UI 로 만든/병합한 경로까지 잡는가, (2) 변조 저항 — 검사 대상이 검사기를
바꿀 수 있는가, (3) 자기 잠금 위험 — 필수화가 무관한 결함으로 저장소를
못 쓰게 만드는가(fail-closed 의 문서화된 비용: 웹훅 self-wedge). [12]

**Adopt**: 도달성(vacuity/shadowing) 을 관찰 체크리스트의 1급 항목으로
올린다 — 코드가 "있다"와 규칙이 "발화한다"를 분리해 본다. [5][6]
**Skip**: 뮤테이션 테스트·룰-히트 텔레메트리 도입 요구는 안 한다 — 관찰
역할은 관찰 대상 코드를 재실행·수정하지 않고, 이 규모의 게이트에 과잉이다.

**Segment fit**: 대상은 단일 저장소·저동시성·개인 소유 리포의 정책 게이트다
— 조직 통제(merge queue, CODEOWNERS 라우팅, custom role bypass 감사)는
같은 부류지만 상위 세그먼트라 기준선만 참고하고 요구하지 않는다.

**GAP LINE**: 현재 상태(survey §3)가 이미 충족한 must-be — 양방향 실증
(#263 FAILURE 02:06:49Z / SUCCESS 02:50:43Z), 신뢰 브랜치 체크아웃
(`ref: main`), `edited` 포함, `enforce_admins=true` 의 잔여 표면 문서화.
아직 대응이 확인되지 않은 must-be — (i) 규칙 발화 가능성(요구사항 2의
phase-1 mismatch 검사가 CI 경로에서 도달 가능한가, survey §4 G1), (ii)
필수 체크가 *안 도는* 경로에서 `expected` 로 남는지 vs 통과하는지, (iii)
잡 이름 `closes-gate` 와 보호 규칙 컨텍스트 문자열의 결합 취약성.

**이 패스**: 1 스테이지(sweep 만), 병렬 모드(Agent 3개 동시 dispatch),
deepening 없음 — judge point 1 에서 세 앵글이 G1/G3 위에서 겹쳐 saturation
판정.

Sources:
[1] https://nhimg.org/community/agentic-ai-and-nhis/ai-agent-guardrails-and-testing-are-your-controls-actually-working/
[2] https://www.mindbridge.ai/blog/sox-testing-procedures-a-strategic-guide-for-audit-leaders/
[3] https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/
[4] https://labs.cloudsecurityalliance.org/research/csa-research-note-megalodon-github-actions-cicd-supply-chain/
[5] https://docs.certora.com/en/latest/docs/prover/checking/sanity.html
[6] https://arxiv.org/pdf/1102.1237
[7] https://semgrep.dev/docs/writing-rules/testing-rules
[8] https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks
[9] https://github.com/orgs/community/discussions/63427
[10] https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
[11] https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
[12] https://kubernetes.io/docs/concepts/cluster-administration/admission-webhooks-good-practices/
