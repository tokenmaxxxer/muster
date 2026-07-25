# protocol — 에이전트 규약

*2026-07-25 재설계. 사람과 에이전트가 같이 읽는 계약서.
설계 근거는 `orchestrator-design-2026-07.md`.*

## 한 장

```
        지식              배선                   경계
   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
   │ 룰북 레포     │  │ harness      │  │ container +      │
   │ (플러그인)    │  │ agents/*.yml │  │ permissions      │
   │              │  │              │  │                  │
   │ 무엇을 어떻게 │  │ 언제 깨어나고 │  │ 무엇을 만질 수   │
   │ 판단하는가    │  │ 어디로 넘기나 │  │ 있는가           │
   └──────────────┘  └──────────────┘  └──────────────────┘
```

**에이전트 하나 = 워크플로 파일 하나.** 워크플로는 판단을 담지 않는다 — 룰북
플러그인을 설치하고 커맨드 하나를 부른다. 룰북만 고쳐서 행동이 바뀌지 않으면
배선이 샌 것이다.

## 1. 에이전트의 모양

모든 에이전트가 같은 네 블록이다. 이 모양을 벗어나면 새 에이전트가 아니라
기존 룰북의 커맨드다.

```yaml
on:              # 언제 깨어나나
concurrency:     # 중복 실행 방지 (락을 손으로 만들지 않는다)
container:       # 어디서 도나 — 경계
permissions:     # 무엇을 만질 수 있나
steps:
  - 룰북 마켓플레이스 설치 → 커맨드 호출 → (필요하면) 다음 이벤트 발신
```

프롬프트가 워크플로에 있으면 잘못된 것이다. 룰북의 `commands/<name>.md` 가
절차와 `allowed-tools` 를 함께 선언하고, 워크플로는 `/plugin:command` 만 부른다.

## 2. 조율 — 규칙 셋

중앙 배차 프로세스가 없다. 조율은 규칙 세 개로 끝난다.

**① 상태는 라벨.** 사람이 읽고 손으로 고칠 수 있어야 한다. 라벨을 되돌리면
그 지점부터 재개된다.

| 라벨 | 뜻 |
|---|---|
| `pipeline:<agent>` | 그 에이전트 차례 |
| `attempt:N` | 루프 예산. 초과 시 정지 |
| `pipeline:human` | 사람 호출. **어떤 워크플로도 이 라벨을 듣지 않는다** |
| `pipeline:done` | 종료 |

**② 신호는 `repository_dispatch`.** 기본 `GITHUB_TOKEN` 으로 일으킨 이벤트는
워크플로를 재트리거하지 않는다(재귀 폭주 방지). `repository_dispatch` 와
`workflow_dispatch` 만 이 규칙의 명시적 예외다 —
[GITHUB_TOKEN 문서](https://docs.github.com/en/actions/concepts/security/github_token).
그래서 라벨을 옮긴 뒤 dispatch 로 깨운다. 받는 쪽은 라벨을 다시 읽어 자기 차례가
맞는지 확인한다(멱등).

사람이 손으로 라벨을 바꾼 경우는 `issues: [labeled]` 가 받는다 — 사람 행동은
재트리거 억제 대상이 아니다. 두 경로를 함께 달면 **폴링이 필요 없다.**

**③ 동시성은 `concurrency`.** 락을 만들지 않는다.

```yaml
concurrency:
  group: <agent>-${{ 이슈 또는 PR 번호 }}
  cancel-in-progress: true
```

## 3. 격리 — 등급은 에이전트마다 다르다

전부를 같은 경계에 넣지 않는다. 필요한 곳에만 비용을 낸다.

| 등급 | 대상 | 러너 | 경계 |
|---|---|---|---|
| **A** | 입력이 우리 레포뿐 — review, gates, qa, plan, build | hosted | `container:` — 이미지 고정, 비루트, 호스트 FS 차단 |
| **B** | 입력이 신뢰할 수 없는 외부(research) 또는 프로덕션 크리덴셜(diagnose) | **self-hosted** | container + iptables default-deny egress |

**등급 B 가 따로인 이유**: GitHub hosted 러너는 egress 를 제한할 수 없다.
`container.options` 에서 `--network` 가 명시적으로 미지원이고, 네이티브 egress
방화벽은 아직 GA 가 아니며, Azure VNet 경로는 유료 larger runner 전용이다.
**컨테이너를 원했던 첫 이유가 egress 통제였으므로, 그게 필요한 에이전트는
hosted 에서 성립하지 않는다.** 그 에이전트를 실제로 만들 때 self-hosted 를 세운다.

등급 A 에서 컨테이너가 사주는 것: 툴체인 고정, 비루트 실행, 호스트 파일시스템
차단. 사주지 않는 것: egress 통제. **env 기본 차단은 Actions 가 이미 해결한다**
— 시크릿이 상속이 아니라 명시 주입이다(로컬 라우터에서 컨테이너가 필요했던
두 번째 이유가 여기서 소멸한다).

## 4. 권한 — 게시와 판단을 분리한다

이슈 코멘트와 라벨 변경은 **둘 다 `issues: write`** 다. GitHub 은 분리하지 않는다.
따라서 판단하는 job 에 게시 권한을 주면 그 job 이 `pipeline:human` 을 떼어내
자기 게이트를 무력화할 수 있다.

**규칙: LLM 이 도는 job 과 라벨을 바꾸는 job 은 같은 job 이 아니다.**
판단 job 은 산출물을 아티팩트로 넘기고, 게시 job(LLM 없음)이 읽어서 게시한다.

**예외 — PR 리뷰.** 리뷰 제출은 `pull-requests: write` 로 되고 이 스코프에는 라벨
권한이 없다. 리뷰 에이전트는 코멘트가 아니라 리뷰를 내므로 job 을 쪼갤 필요가 없다.
(벤더 공식 예제도 `contents: read` + `pull-requests: write` 만 준다.)

## 5. 에이전트

| 에이전트 | 트리거 | 룰북 | 격리 | 다음 |
|---|---|---|---|---|
| **review** | PR 열림·갱신 | review-agent-rulebook | A | 사람 머지 |
| **gates** | PR 열림·갱신 | 없음 (LLM 0회) | A | 필수 체크 |
| qa | 머지됨 | qa-agent-rulebook | A | `done` 또는 버그 이슈 |
| plan | `pipeline:plan` | coding-agent-rulebook | A | `pipeline:build` |
| build | `pipeline:build` | coding-agent-rulebook | A | PR → review |
| research | `pipeline:research` | (신규) | **B** | `pipeline:plan` |
| diagnose | 외부 알럿 dispatch | (신규) | **B** | 이슈 발행 → `pipeline:research` |
| mine | 주 1회 schedule | 없음 | A | 룰북 개정 이슈 |

모델은 CLAUDE.md 의 라우팅 의도표를 따른다 — **판단은 opus, 작업은 sonnet.**

### 외부 시스템이 에이전트를 깨우는 경로

```
알럿 시스템(Prometheus/Datadog)
  → POST /repos/{o}/{r}/dispatches   {event_type: alert, client_payload: {...}}
  → diagnose 가 깨어나 RCA → 이슈 발행 + pipeline:research + dispatch
  → research 가 깨어난다 → …
```

REST 호출 하나면 되고, 중앙 프로세스를 거치지 않는다.

## 6. 불변식

깨지면 설계가 샌 것이다. 워크플로 리뷰 시 이것부터 본다.

1. **워크플로에 프롬프트가 없다.** 판단은 룰북에.
2. **LLM job 과 라벨 변경 job 이 분리된다.** (예외: PR 리뷰 — §4)
3. **진행 판정은 라벨로만.** 이슈 열림/닫힘으로 하지 않는다 — `Closes #N` 이
   달린 PR 이 머지되면 이슈가 닫혀 파이프라인이 끊긴다(1판에서 실제로 끊겼다).
4. **게이트는 필수 체크다.** 등록하지 않으면 빨간 불이 떠도 머지되므로 장식이다.
5. **신뢰할 수 없는 값을 셸에 보간하지 않는다.** 이슈 제목을 `run:` 안에
   `${{ }}` 로 넣으면 제목 안의 `$(…)` 가 실행된다 — **이슈는 누구나 열 수
   있으므로 원격 코드 실행이다.** env 로 받아 인용한다.
6. **재시도는 멱등하다.** 매 시도를 base + 계약에서 새로 시작한다.
7. **`pipeline:human` 은 아무도 듣지 않는다.** 사람만 푼다.

## 7. 출하 순서

한 번에 하나. 다음을 늘릴지는 **원장이 정한다** — 멀티에이전트 파일럿의 40%가
6개월 내 실패하고, 단일 에이전트가 64% 벤치마크에서 동등 이상이다.

| 순 | 무엇 | 이 단계가 증명하는 것 |
|---|---|---|
| 1 | review + gates + ledger | 워크플로가 룰북 플러그인을 실행자로 부른다 (골격) |
| 2 | 첫 ablation | 룰북이 수용률을 올리는가 — 이 레포의 존재 이유 |
| 3 | mine | 룰북이 스스로 개정되는 루프 |
| 4 | plan → build 체인 | §2 의 조율 규칙이 실제로 도는가 |
| 5 | research / diagnose (등급 B) | self-hosted + egress 방화벽 |

1이 서면 2~5는 **같은 모양의 파일을 하나씩 더하는 일**이 된다. 그게 이 설계의 요점이다.

## 8. 미확정

- `claude-code-action` 을 `container:` 안에서 돌리는 것은 공식 지원 여부가 문서화되어
  있지 않다. git "dubious ownership" 회피(`safe.directory`)가 필요하다는 열린 이슈가
  있어 1호에 미리 넣어 두었다. 첫 실행에서 실증한다.
- 플러그인 설치가 조용히 실패하는 열린 이슈가 있다. 1호 첫 실행에서 확인한다.
- 헤드리스에서 확인된 것은 플러그인 **커맨드**까지다. 훅·에이전트도 로드되는지는
  미확인 — 룰북이 훅에 의존하면 그때 확인한다.
