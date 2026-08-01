---
role: implementation
subject: issue-178
loop_state: scout
---

# Scout brief — spawn.py flows 구역 분할 (issue #178)

## 이 결정의 성격

외부 제품 비교가 성립하지 않는 순수 내부 리팩터 결정이다 — 대상은
on-the-record 자신의 오케스트레이터 스크립트고, "무엇을 만들지"가 아니라
"이미 만든 300줄을 어디로, 어떻게 옮기는가"만 남아 있다. issue-172 의
survey.md 자신도 같은 판단을 내렸다: "there is no comparable public
product to benchmark a two-person internal dashboard contract against."
이번에도 동일하다. 그래서 "동종 최고 제품"이 아니라 **선례**를 찾는 것으로
스코프를 좁혔다 — scout-directive 의 "prior art / 비교 가능한 시스템이
문제를 어떻게 풀었는가"에 해당.

## 선례 1 — 저장소 내부 (1차 소스, 가장 비교 가능)

`gates/closure_sweep.py` 가 이미 똑같은 모양이다: spawn.py 밖으로 빠진
읽기 전용, 보드 전역 스윕 모듈이고, 자기 모듈 최상단에서
`sys.path.insert` 후 `import spawn` 으로 되돌려 쓴다(`spawn.board`,
`spawn._pr_for_branch`, `spawn._issue_comments`, `spawn._repo_slug` 전부
qualified 접근, bare-name 아님). `spawn.py` 의 `main()` 은 `closure-sweep`
분기에서 이 모듈을 지연 import 한다(spawn.py:2322-2323). 이 저장소
안에서 이미 검증된, 유일하게 비교 가능한 선례다.
Source: gates/closure_sweep.py, spawn.py:2319-2325 (이 체크아웃에서 직접 읽음).

## 선례 2 — 외부, monkeypatch 의미론 (커뮤니티 정설과 대조 확인용)

"함수를 다른 모듈로 옮기면 monkeypatch 가 깨지는가"는 이 저장소만의
문제가 아니라 Python 전반의 잘 알려진 함정이다. pytest 공식 문서와
커뮤니티 설명이 일치해서 말한다: **patch 는 함수가 정의된 곳이 아니라
"실제로 쓰이는 곳"을 타겟해야 한다** — `from module import function` 로
재export 하면, patch 는 재export 한 이름을 바꿀 뿐 원본 함수의
`__globals__` (실행 시 조회하는 네임스페이스) 는 그대로다.
이 원칙을 이번 이슈의 `spawn.py` 재export 시나리오에 그대로 대입하면
issue 본문의 예측과 정확히 같은 결론이 나온다 — survey.md 에서 별도
실측(재현 스크립트)으로 직접 확인했고, 여기서는 그 실측이 낯선 특이
케이스가 아니라 커뮤니티에 문서화된 일반 규칙임을 확인하는 용도로만
쓴다.
Source: https://docs.pytest.org/en/stable/how-to/monkeypatch.html,
https://medium.com/@cini01/monkeypatching-subtleties-17e639fc3cd8

## Must-be / 채택·기각

- **Must-be**: 옮겨진 함수가 참조하는, 옮겨지지 않는 외부 심볼은 전부
  qualified 접근(`spawn.X`, `closure_sweep.X`)이어야 한다 — bare-name
  import 는 금지. 선례 1 이 이미 이 규칙을 지키고 있고, 선례 2 가 그
  이유(monkeypatch 가능성)를 설명한다.
- **채택**: closure_sweep.py 와 동일한 형태 — 같은 디렉터리
  (`gates/`), 같은 지연 import 패턴, 같은 "무엇도 안 고치고 안
  posting 한다" 성격.
- **기각**: spawn.py 에 재export shim 을 남기는 안 — 선례 2 의 원칙상
  테스트를 완전 무변경으로 만들지 못하는데도 shim 유지 비용(spawn.py
  줄 수 증가, 수용 기준의 "순감소=이동 크기" 등식 위반)만 남기 때문.

## 갭 라인

on-the-record 는 이미 이 정확한 문제(스폰 기전과 무관한 읽기 전용 보드
유틸리티를 spawn.py 밖으로 빼기)를 한 번 풀어봤다(closure_sweep.py) —
같은 패턴을 flows 에도 적용하면 되는 "이미 푼 문제의 반복"이라 새로
설계할 여지가 거의 없다. 남은 진짜 미해결 지점은 이 저장소에 없는
것: **위치 선택 시 보호 경로 갱신 비용의 명시적 비교**(closure_sweep
당시엔 이미 gates/ 안에 있었으므로 이 질문 자체가 없었다) — 이건
선례가 아니라 이번 survey.md 자체가 gates/gates.py 를 직접 읽어 채운다.

## 스테이지

1 스테이지(sweep) 로 포화 — judge point: 두 선례 모두 같은 결론(gates/
스타일 그대로 따르기)을 가리켜 추가 라운드가 결정을 바꾸지 않는다.
병렬 모드: WebSearch 2건 동시 호출(1턴), Agent 병렬 미사용(리서치
자체가 가벼워 서브에이전트 위임 불필요로 판단).

Sources:
- https://docs.pytest.org/en/stable/how-to/monkeypatch.html
- https://medium.com/@cini01/monkeypatching-subtleties-17e639fc3cd8
- gates/closure_sweep.py, spawn.py:2319-2325 (저장소 내부, 1차 소스)
