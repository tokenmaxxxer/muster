# harness

tokenmaxxxer 의 하네스 — 에이전트를 감싸서 쓸모 있고 안전하게 만드는 장치.
에이전트도 룰북도 아니고, **규약 + 게이트 + 원장**이다.

모델(실력)은 사면 된다. 조직 지식은 못 산다. 이 레포는 후자를 담는다.

```
protocol.md    규약 — 에이전트가 언제 깨어나고 무엇을 주고받는지 (본체)
workflows/     참조 워크플로. 대상 레포에 복사해 쓴다
gates/         결정론 게이트. LLM 0회, 비용 0
ledger/        성적표. 수용률·비용·응답시간·revert율
e2e/           워크플로 통합 테스트
```

## 무엇을 하지 않는가

- **코드를 쓰지 않는다.** 생성(이슈→PR)은 이미 제품이다. 벤더 것을 쓴다.
- **머지하지 않는다.** 사람 게이트는 원장이 근거를 낼 때까지 유지한다.
- **상주하지 않는다.** 데몬이 없다. 이벤트가 없으면 아무것도 돌지 않는다.
- **판단을 담지 않는다.** 판단은 룰북(마크다운)에 있다. 이 레포를 고치지 않고
  룰북만 고쳐서 행동이 바뀌어야 한다.
- **에이전트를 늘리지 않는다.** 원장이 지목할 때까지 하나다.

## 지금 상태

1호 `workflows/review.yml` 이 첫 출하 대상이다. PR 이 열리면
[review-agent-rulebook](https://github.com/tokenmaxxxer/review-agent-rulebook) 을
주입해 리뷰하고, 사람이 읽고 머지한다. 자율 머지는 없다.

**1호에는 상태기계가 필요 없다.** `protocol.md` 의 라벨 전이·dispatch 기전은
체인이 생기는 2호부터 적용된다.

## 쓰기

```bash
# 1. 구독 토큰 발급 (1년, 추가 비용 0 — 구독 한도에서 차감)
claude setup-token
gh secret set CLAUDE_CODE_OAUTH_TOKEN -R <owner/repo>

# 2. 워크플로 복사
cp workflows/review.yml <대상레포>/.github/workflows/
cp workflows/gates.yml  <대상레포>/.github/workflows/

# 3. gates 를 필수 체크로 등록 — 안 하면 빨간 불이 떠도 머지되므로
#    게이트가 아니라 장식이다

# 4. 성적 확인
python3 ledger/collect.py <owner/repo>
```

`ANTHROPIC_API_KEY` 로 바꾸려면 시크릿만 교체하면 된다 — 워크플로는 그대로다.
구독 토큰은 대화형 사용과 한도를 공유하므로 볼륨이 커지면 전환한다.

## 자체 점검

```bash
python3 test_orchestrator.py     # 게이트·순수함수. 네트워크·GitHub 불필요
```

## 미해결

- **게이트 배포** — `gates/` 는 워크플로가 도는 레포에 있어야 한다. 다른 레포에서
  쓰려면 벤더링하거나 이 레포를 공개로 돌려야 한다. 게이트 로직에 비밀은 없다.
- **수용률 자동 판정** — 원장의 `accepted` 는 지금 사람이 채운다. 표본이 쌓이기 전에
  대리지표를 정답으로 쓰면 원장이 거짓말을 시작한다.
- **PR 리뷰 권한 스코프** — `pull-requests: write` 만으로 리뷰 제출이 되는지 1호
  첫 실행에서 실증한다. 403 이면 job 분리로 되돌린다 (`protocol.md` §2).

## 은퇴 예정

`src/main.py` 는 1판의 상시 라우터 데몬이다. 폴링·락·stale 회수·고아 워커 처리가
전부 GitHub Actions 가 이미 하는 일의 재구현이었고, 재점검에서 나온 결함이 거의
전부 그 250줄에서 나왔다. `adapters.yml`·`adapters.e2e.yml`·`e2e/workers/`·
`pipeline.md` 도 같이 은퇴한다 (`pipeline.md` → `protocol.md`).

지우지 않고 두는 이유는 실측 기록이기 때문이다 — 실제 LLM 으로 이슈→spec→PR→
머지→테스트 전 구간을 돌려 얻은 발견들이 `orchestrator-design-2026-07.md` §9 에
있고, 그 교훈은 워크플로에도 그대로 적용된다.
