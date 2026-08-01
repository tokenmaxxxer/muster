---
role: refactoring-legacy
subject: issue-187
loop_state: scout
---

# Scout brief — spawn.py 기능별 모듈 분리 (issue #187)

## 이 결정의 성격

내부 리팩터 — "무엇을 만들지"가 아니라 "이미 있는 2625줄을 어떻게
쪼개는가". issue-178(스코프 300줄, 순환 없는 단일 클린 컷)과 이번
(스코프 3~4모듈·87함수, survey.md가 순환 의존 2건을 실측)의 차이는
규모와 결합도다. 그래서 이번 스카우트는 "동종 최고 제품 비교"가 아니라
(a) 대형 단일 파일 CLI를 형제 모듈+얇은 엔트리로 쪼개는 게 검증된
패턴인지, (b) 저장소가 이미 쓰는 지연 import 순환 회피가 커뮤니티
정설과 일치하는지, (c) 한 이슈 안에서 여러 작은 단계로 나누는 접근이
role directive의 strangler fig 요구와 맞는지를 확인하는 목적으로
좁혔다.

## 선례 1 — 저장소 내부 (1차, 가장 비교 가능)

`gates/flows.py`, `gates/closure_sweep.py` — 이미 이 저장소 안에서
두 번 검증된 패턴: 형제 디렉터리 모듈이 최상단에서 `sys.path.insert`
후 `import spawn`, 이후 전부 qualified 접근, 재export 없음(issue-178
survey.md가 monkeypatch 결합을 실측으로 확인·기각). `main()`은 지연
import로 분기. 단, 두 선례 모두 참조가 spawn.py로의 **단방향**이라
이번 group2↔3, group3→4 같은 역방향 케이스의 전례는 아니다(survey.md
갭).
Source: gates/flows.py, gates/closure_sweep.py, spawn.py (저장소 내부,
직접 읽음).

## 선례 2 — 외부, 얇은 엔트리 + 목적별 모듈 분리

커뮤니티 자료가 "스크립트를 호출하는 부분과 핵심 기능을 분리"하는
얇은 엔트리 패턴, "utils 안티패턴을 제거하고 목적별 모듈로 배분"하는
조직화를 표준으로 제시한다 — 이슈 본문의 "spawn.py를 얇은 엔트리로
남기고 형제 모듈을 임포트" 제안과 방향이 같다.
Source: https://realpython.com/python-script-structure/,
https://denyslinkov.medium.com/scaling-your-python-cli-87f74a0fb6cb

## 선례 3 — 외부, 순환 의존 처리

지연 import(함수 본문 안에서 import)가 "선호되는 해법"으로 문서화돼
있고, 대안으로 "공유 모듈 신설"도 같이 제시된다 — survey.md가 실측한
group2↔3 순환, group3→4 역참조 둘 다 이 두 해법(지연 import 우선,
필요시 공유 모듈)으로 커버된다. 지연 import의 트레이드오프(파일 상단이
아닌 곳의 import는 관례를 깨고 린터가 감점할 수 있음)도 문서화돼
있다 — 이 저장소는 이미 그 트레이드오프를 감수하고 쓰는 중(main()
분기)이라 새 비용이 아니다.
Source: https://medium.com/@denis.volokh/the-circular-import-trap-in-python-and-how-to-escape-it-9fb22925dab6,
https://stackabuse.com/python-circular-imports/

## 선례 4 — 외부, 단계적 분할

Fowler의 strangler fig(마이크로서비스 맥락이지만 "한 번에 안 바꾸고
독립적으로 추출 가능한 경계를 먼저 식별, 점진적으로 교체"라는 원칙은
role directive의 "너무 커서 한 카탈로그 스텝에 안 들어가면 strangler
fig" 요구와 정확히 같은 모양) — survey.md의 교차-그룹 호출 그래프가
이미 "어느 그룹부터 뽑아야 안전한가"(들어오는 엣지 0인 group1 먼저,
허브인 group4 마지막)를 보여주므로, 제안서는 이 순서를 한 PR 안의
순차 단계들로 구체화한다.
Source: https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig

## Must-be / 채택·기각

- **Must-be**: 새 형제 모듈은 옮기지 않는 심볼을 전부 qualified
  접근(`rulebook.X`, `board.X` 등)으로 부른다 — bare-name import
  금지(선례 1+3, 이미 이 저장소의 확립된 규칙).
- **Must-be**: 순환이 있는 두 지점(group2↔3, group3→4)은 함수 본문
  안 지연 import로 끊는다 — 모듈 병합이나 새 공유 모듈보다 이
  저장소의 기존 패턴(main() 분기의 지연 import)과 정확히 같은 모양
  이라 채택.
- **채택**: 들어오는 교차-그룹 엣지가 0인 그룹부터 먼저 옮기고, 허브
  (group4)는 이동 횟수 최소화를 위해 마지막(또는 이번 스코프에서
  아예 유지)으로 미룬다 — 선례 4 + survey.md 그래프.
- **기각**: group0(`_mkt`/`_path`/`go_proxy_layer`, 42줄) 전용
  `common.py` 신설 — 선례 3이 대안으로 제시하지만, 이 저장소 규모
  (소비자가 group1 하나뿐, group4는 `go_proxy_layer` 1개만 씀)에서는
  새 보호 파일 하나 늘리는 비용이 qualified 접근 비용보다 크다(제안서
  §대안에서 확정).

## 갭 라인

저장소는 이미 "빼내기 + 지연 import + qualified 접근" 패턴을 두 번
(flows, closure_sweep) 검증했다 — must-be 대부분은 이미 충족돼
있다. 이번이 처음 겪는 갭 둘: (1) 순환 의존이 있는 분할(선행 두
사례는 spawn.py로 단방향), (2) 한 이슈에서 여러(3~4개) 모듈을 순차
단계로 처리하는 규모. 외부 선례는 두 갭 모두에 "이미 알려진 해법이
있다"는 방향만 확인해줄 뿐, 정확히 어느 함수를 어느 단계에서 어떻게
끊는지는 survey.md의 실측 콜그래프를 기반으로 제안서가 직접 설계한다.

## 스테이지

1 스테이지(sweep)로 포화 — judge point: 4개 선례 전부 이 저장소가
이미 쓰는 패턴(지연 import, qualified 접근, 얇은 엔트리)과 같은
방향을 가리켜 추가 라운드가 결정을 바꾸지 않는다. 병렬 모드:
WebSearch 3건 동시 호출(1턴, 진짜 병렬 — Agent 서브에이전트는 리서치
자체가 가벼워(앵글당 1쿼리) 위임 불필요로 판단, SCALE GATE 미달).

Sources:
- https://realpython.com/python-script-structure/
- https://denyslinkov.medium.com/scaling-your-python-cli-87f74a0fb6cb
- https://medium.com/@denis.volokh/the-circular-import-trap-in-python-and-how-to-escape-it-9fb22925dab6
- https://stackabuse.com/python-circular-imports/
- https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig
- gates/flows.py, gates/closure_sweep.py, spawn.py (저장소 내부, 1차 소스)
