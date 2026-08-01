---
role: implementation
subject: issue-180
loop_state: scout
---

# Scout brief — pr-opened 출처 판별 + 진행 이벤트 (issue #180)

## 이 결정의 성격

외부 제품과 비교할 대상이 아니다 — on-the-record 자신의 오케스트레이터
스크립트가 자기 하위 프로세스의 stdout 스트림에서 "실제로 일어난 일"과
"세션이 그저 읽거나 언급한 텍스트"를 가르는 내부 판별 로직이다.
issue-178 survey 가 이미 같은 판단을 내렸다("내부 리팩터엔 동종
최고 제품이 없다"). 그래서 스코프를 **선례** 찾기로 좁혔다 —
1차 소스는 이 저장소 내부(survey.md 에서 이미 확인), 2차로 외부
prior art 두 갈래를 확인했다.

## 선례 1 — 저장소 내부 (survey.md 재인용, 가장 비교 가능)

`gates/flows.py:107-157` 의 `_session_last_activity` 가 stream-json
한 줄을 `tool_use`/`text`/`result` 로 구조 분류하는 로직을 이미
갖고 있고, `_spawn_one` 자신도 `gate-refusal` 판별에서 이미 raw-text
정규식(이슈-126 이전)을 구조화 필드 파싱(`obj.get("permission_denials")`)
으로 바꾼 전례가 있다. `pr-opened` 만 raw-text 정규식 세대에 남아
있다. Source: 이 체크아웃 직접 읽음(gates/flows.py, spawn.py).

## 선례 2 — 외부, LLM 에이전트 관측성 (일반 원칙 대조용)

2026년 AI 에이전트 관측성 자료들이 공통으로 짚는 지점: 에이전트가
"도구를 호출했다"는 **텍스트**를 내는 것과 도구가 **실제로 실행되고
그 출력을 확인**하는 것은 다르고, 실패 모드 대부분이 조용하다(에러
코드 없이 그럴듯한 텍스트만 남는다). 권고되는 대응은 (1) 도구
입출력을 스키마 수준에서 100% 검증하고 (2) LLM 이 만든 텍스트가 아니라
실제 실행 결과에 대고 판정하는 것 — 이번 이슈의 "tool_result 구조로
가른다"(후보 a)와 "GitHub 에 직접 물어 확인한다"(후보 b) 둘 다 이
원칙의 구체화다.
Source: https://aidevdayindia.org/blogs/ai-agent-observability-agentops-playbook/ai-agent-observability-agentops-playbook.html,
https://www.confident-ai.com/blog/llm-agent-evaluation-complete-guide

## 선례 3 — 외부, `gh` CLI 스크립팅 정석

`gh pr create` 의 stdout URL 을 직접 파싱하는 대신 `gh pr list --head
<branch> --state open --json url` 로 존재를 구조적으로 재확인하는
것이 커뮤니티가 권하는 스크립팅 관행이다 — 이유로 든 것은 정확히
이 저장소의 `_pr_for_branch`(spawn.py:815-820)가 이미 하고 있는 모양
(`--head` + `--json` 필드 추출)과 같다.
Source: https://medium.com/neural-engineer/mastering-pull-requests-with-github-cli-6ddb357076b0

## Must-be / 채택·기각

- **Must-be**: URL 문자열이 어디서 왔는지와 무관하게, 최종 판정은
  GitHub 자신에게 물은 결과(존재 + head 브랜치 일치)여야 한다 — 세
  선례 모두 "텍스트 매칭만으론 부족하다"는 결론으로 수렴한다.
- **채택**: `_pr_for_branch` 재사용(선례 1·3) — 새 `gh` 호출 모양을
  또 만들지 않는다.
- **기각**: tool_result/tool_use 상관관계까지 구조적으로 추적하는
  안(후보 a 단독) — 선례 2 의 원칙엔 맞지만, 이슈 #142 실측(존재하지
  않는 PR 번호)과 `pull/new/` 오탐 둘 다 "GitHub 에 직접 확인"
  (후보 b) 하나로 이미 걸러진다. 구조 추적을 추가해도 막는 사고가
  늘지 않는데 구현 복잡도(assistant 의 tool_use id 를 이후 user
  tool_result 와 맞추는 상태 추적)만 커진다 — proposal.md 의
  Rationale 에서 비교.

## 갭 라인

on-the-record 는 "텍스트 매칭 → 구조화 필드/외부 확인"으로 옮기는
문제를 gate-refusal 에서 이미 한 번 풀었다(gap 없음, 반복). 이
저장소가 아직 안 가진 것: **진행 이벤트의 입도 기준**과 **watch 의
재무장 방식** — 둘 다 선례가 이 저장소 안에도, 찾은 외부 자료에도
없어 survey.md 의 실측(directive.sh 재무장 지시, `_await_bounded` 의
이중 호출자)에서 직접 판단해야 한다(proposal.md 로 이어짐).

## 스테이지

1 스테이지(sweep, WebSearch 2건 병렬 1턴)로 포화 — judge point: 세
선례 모두 "구조화/외부 확인이 텍스트 매칭보다 낫다"는 같은 결론을
가리키고, 이미 저장소 안에 재사용 가능한 구현(`_pr_for_branch`,
`_session_last_activity`)까지 있어 추가 라운드가 채택 결정을 바꾸지
않는다. 병렬 모드: WebSearch 2건 동시 호출.

Sources:
- gates/flows.py:107-157, spawn.py:815-820,2243-2287,2440-2449 (저장소 내부, 1차 소스)
- https://aidevdayindia.org/blogs/ai-agent-observability-agentops-playbook/ai-agent-observability-agentops-playbook.html
- https://www.confident-ai.com/blog/llm-agent-evaluation-complete-guide
- https://medium.com/neural-engineer/mastering-pull-requests-with-github-cli-6ddb357076b0
