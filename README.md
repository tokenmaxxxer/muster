# harness

tokenmaxxxer 의 하네스 — 에이전트를 감싸서 쓸모 있고 안전하게 만드는 장치.
에이전트도 룰북도 아니고, **배선 + 경계 + 성적표**다.

모델(실력)은 사면 된다. 조직 지식은 못 산다. 이 레포는 후자를 담는다.

```
protocol.md   규약 — 에이전트의 모양·조율·격리 등급 (본체)
agents/       에이전트 하나 = 파일 하나. 대상 레포에 복사해 쓴다
gates/        결정론 검사. LLM 0회, 비용 0
ledger/       성적표. 수용률·비용·응답시간·revert율
images/       에이전트가 도는 컨테이너
```

## 모양

```
   지식                배선                 경계
룰북 플러그인   ←   agents/*.yml   →   container + permissions
"어떻게 판단"      "언제 어디로"        "무엇을 만질 수 있나"
```

**워크플로에 프롬프트가 없다.** 룰북의 `commands/<name>.md` 가 절차와 도구
권한(`allowed-tools`)과 판단 기준을 다 갖고, 워크플로는 `/plugin:command` 만 부른다.
리뷰 규칙을 바꾸려면 룰북만 고친다 — harness 를 건드릴 일이 없다.

```yaml
plugin_marketplaces: https://github.com/tokenmaxxxer/review-agent-rulebook.git
plugins: review@tokenmaxxxer-review
prompt: "/review:review ${{ github.repository }}/pull/${{ ... }}"
```

## 무엇을 하지 않는가

- **코드를 쓰지 않는다.** 생성(이슈→PR)은 이미 제품이다. 벤더 것을 쓴다.
- **머지하지 않는다.** 사람 게이트는 원장이 근거를 낼 때까지 유지한다.
- **상주하지 않는다.** 데몬이 없다. 이벤트가 없으면 아무것도 돌지 않는다.
- **판단을 담지 않는다.** 판단은 룰북에.
- **에이전트를 늘리지 않는다.** 원장이 지목할 때까지 하나다.

## 격리

에이전트마다 등급이 다르다. 전부를 같은 경계에 넣지 않는다.

| 등급 | 대상 | 러너 | 경계 |
|---|---|---|---|
| A | 입력이 우리 레포뿐 | hosted | `container:` — 이미지 고정, 비루트 |
| B | 신뢰할 수 없는 외부 입력 / 프로덕션 크리덴셜 | self-hosted | container + iptables default-deny |

**hosted 러너는 egress 를 제한할 수 없다** — `container.options` 의 `--network` 가
미지원이고 네이티브 egress 방화벽은 GA 가 아니다. 그래서 egress 통제가 필요한
research·diagnose 는 등급 B 이고, 그 에이전트를 실제로 만들 때 self-hosted 를 세운다.

## 쓰기

```bash
# 1. 구독 토큰 (1년, 추가 비용 0 — 구독 한도에서 차감)
claude setup-token
gh secret set CLAUDE_CODE_OAUTH_TOKEN -R <owner/repo>

# 2. 이미지 발행 (harness 에서 1회, images/ 가 바뀌면 자동)
cp agents/image.yml .github/workflows/ && git push

# 3. 에이전트 배치
cp agents/review.yml agents/gates.yml <대상레포>/.github/workflows/

# 4. gates 를 필수 체크로 등록 — 안 하면 빨간 불이 떠도 머지되므로 장식이다

# 5. 성적 확인
python3 ledger/collect.py <owner/repo>
```

`ANTHROPIC_API_KEY` 로 바꾸려면 시크릿만 교체한다. 구독 토큰은 대화형 사용과
한도를 공유하므로 볼륨이 커지면 전환한다.

## 자체 점검

```bash
python3 test_orchestrator.py     # 게이트·순수함수. 네트워크·GitHub 불필요
```

## 미해결

- **`container:` 안에서 `claude-code-action` 이 도는지 미실증.** 공식 지원 여부가
  문서화되어 있지 않고, git dubious-ownership 회피가 필요하다는 열린 이슈가 있어
  미리 넣어 두었다. 1호 첫 실행에서 확인한다.
- **플러그인 설치 실패 이슈.** 설치가 조용히 실패하는 열린 이슈가 있어 CLI 를
  이미지에 박고 `path_to_claude_code_executable` 로 가리켜 우회했다. 역시 미실증.
- **게이트 배포** — `gates/` 는 워크플로가 도는 레포에 있어야 한다. 벤더링하거나
  이 레포를 공개로 돌려야 한다. 게이트 로직에 비밀은 없다.
- **수용률 자동 판정** — 원장의 `accepted` 는 지금 사람이 채운다. 표본이 쌓이기 전에
  대리지표를 정답으로 쓰면 원장이 거짓말을 시작한다.

## 은퇴 예정

`src/main.py` 는 1판의 상시 라우터 데몬이다. 폴링·락·stale 회수·고아 워커 처리가
전부 Actions 가 이미 하는 일의 재구현이었고, 재점검 결함이 거의 전부 그 250줄에서
나왔다. `adapters.yml`·`adapters.e2e.yml`·`e2e/workers/`·`images/run.sh` 도 함께 은퇴한다.

지우지 않는 이유는 실측 기록이기 때문이다 — 실제 LLM 으로 이슈→spec→PR→머지→
테스트 전 구간을 돌려 얻은 발견이 `orchestrator-design-2026-07.md` §9 에 있고,
그 교훈은 워크플로에도 그대로 적용된다.
