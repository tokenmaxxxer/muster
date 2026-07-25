# protocol — 에이전트 오케스트레이션 규약

*2026-07-25. `pipeline.md`(1판, 라우터 데몬 전제)를 대체한다. 사람과 에이전트가
같이 읽는 계약서. 설계 근거는 `orchestrator-design-2026-07.md`.*

## 이 문서가 정하는 것 / 안 정하는 것

**정한다**: 에이전트가 언제 깨어나는지, 무엇을 받고 무엇을 내놓는지, 다음으로
어떻게 넘기는지, 어떤 권한을 갖는지.

**안 정한다**: 각 에이전트가 *어떻게* 판단하는지. 그건 룰북(마크다운)에 있고,
룰북을 고치는 것만으로 행동이 바뀌어야 한다. 이 문서를 고쳐야 행동이 바뀐다면
설계가 샌 것이다.

---

## 1. 오케스트레이션 기전 — 허브 없이 어떻게 이어지나

중앙 배차자가 없다. 대신 GitHub 이벤트가 통로다. 여기에 **문서로 확인된 제약
하나**가 설계를 지배한다.

> 기본 `GITHUB_TOKEN` 으로 일으킨 이벤트는 새 워크플로 실행을 만들지 않는다.
> 예외는 `workflow_dispatch` 와 `repository_dispatch` — 이 둘은 **항상** 실행을 만든다.
> — [GITHUB_TOKEN — GitHub Docs](https://docs.github.com/en/actions/concepts/security/github_token)

즉 워크플로 A 가 라벨을 바꿔도 `issues.labeled` 를 듣는 워크플로 B 는 **깨어나지
않는다.** 재귀 폭주를 막으려는 의도적 설계다. 우회로는 PAT 이나 GitHub App 토큰인데,
둘 다 수명 긴 광범위 자격증명이라 "워커는 라벨을 못 바꾼다"는 불변식을 무너뜨린다.

### 채택: 상태는 라벨, 신호는 dispatch

```
에이전트 N 이 끝나면
  ① 산출물을 남긴다        (아티팩트 / 코멘트 / 커밋)
  ② 라벨을 옮긴다          ← 상태. 사람이 읽고 손으로 고칠 수 있다
  ③ repository_dispatch    ← 신호. GITHUB_TOKEN 으로도 항상 전달된다
       ↓
에이전트 N+1 이 깨어나서
  ④ 라벨을 다시 읽어 자기 차례가 맞는지 확인한다  ← 멱등성
```

**두 트리거를 함께 단다.** 각 워크플로는 이렇게 듣는다:

| 트리거 | 누가 일으키나 | 왜 필요한가 |
|---|---|---|
| `repository_dispatch` | 앞 에이전트 | GITHUB_TOKEN 으로도 전달되는 유일한 경로 |
| `issues: [labeled]` | **사람** | 사람이 손으로 라벨을 되돌려 개입하는 경로. 사람 행동은 억제 대상이 아니다 |

두 경로가 동시에 울려도 ④의 라벨 재확인과 concurrency group 이 중복을 흡수한다.
**폴링은 없다.**

### 락 — 손으로 만들지 않는다

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.client_payload.issue }}
```

같은 그룹은 한 번에 하나만 돈다. 1판의 `pipeline:<stage>:running` 라벨 락과
stale 회수 로직은 **전부 삭제한다** — 이게 이 규약에서 가장 많은 코드를 지우는 항목이다.

기본 동작은 `queue: single`: 실행 중인 것은 그대로 두고, **대기 중이던 것은 새 요청이
밀어낸다**(최신 상태가 이긴다). 파이프라인에서는 이게 옳다 — 낡은 상태로 도는 것보다
낫다. 모든 요청이 반드시 실행돼야 하는 스테이지가 생기면 `queue: max`(최대 100)로
바꾼다. `queue: max` 와 `cancel-in-progress: true` 는 함께 못 쓴다.

---

## 2. 권한 — 에이전트 job 은 쓰기 권한 0

**확인된 제약**: 이슈 코멘트와 라벨 변경은 **둘 다 `issues: write`** 한 스코프다.
GitHub 은 이 둘을 분리하지 않는다. 따라서 "코멘트만 되고 라벨은 못 바꾸는" 토큰은
표준 `permissions:` 모델로는 만들 수 없다.

1판이 이 문제를 "게시는 라우터가 한다"로 풀었다. 2판은 **job 분리**로 푼다 —
`permissions:` 는 job 단위로 지정할 수 있다.

```yaml
jobs:
  agent:                        # 판단하는 job
    permissions:
      contents: read            # ← 읽기만. 이슈도 PR도 못 건드린다
    steps: [ … 산출물을 아티팩트로 업로드 … ]

  publish:                      # 게시하는 job
    needs: agent
    permissions:
      issues: write             # ← LLM 이 돌지 않는 job
    steps: [ … 아티팩트를 받아 게시하고 라벨을 옮기고 dispatch … ]
```

**불변식: LLM 이 도는 job 과 쓰기 권한을 가진 job 은 절대 같은 job 이 아니다.**
이게 지켜지면 프롬프트 인젝션이 성공해도 피해 반경이 "틀린 산출물"에 머문다.
게시 job 은 LLM 이 없으므로 인젝션 대상이 아니다.

### 예외 하나 — PR 리뷰

PR **리뷰 제출**(`POST /pulls/{n}/reviews`)은 `pull-requests: write` 로 되고,
이 스코프에는 라벨 변경 권한이 없다. 일반 코멘트(`POST /issues/{n}/comments`)와
경로가 다르다. **리뷰 에이전트는 코멘트가 아니라 리뷰를 제출한다** — 그러면 job 을
쪼개지 않아도 라벨을 건드릴 수 없다.

> 방증: `anthropics/claude-code-action` 의 공식 PR 리뷰 예제가 `contents: read` +
> `pull-requests: write` 만 주고 인라인 코멘트를 단다. 다만 이 스코프 매핑은 GitHub
> Apps 권한 레퍼런스에서 유도한 것이기도 해서, 1호 첫 실행에서 실증한다.
> 403 이 나면 job 분리로 되돌린다.

---

## 3. 라벨 어휘

| 라벨 | 의미 | 누가 붙이나 |
|---|---|---|
| `pipeline:<stage>` | 그 스테이지 차례 | 앞 에이전트의 publish job, 또는 사람 |
| `attempt:N` | 루프 예산. 초과 시 정지 | publish job |
| `pipeline:human` | 사람 호출. **어떤 워크플로도 이 라벨을 듣지 않는다** | 게이트 실패·예산 소진·타임아웃 |
| `pipeline:done` | 종료 | 마지막 스테이지 |

1판의 `pipeline:<stage>:running` 은 없다 — concurrency group 이 대체한다.

**진행 여부는 이슈의 열림/닫힘이 아니라 라벨로만 판정한다.** `Closes #N` 이 달린 PR
이 머지되면 이슈가 닫히는데, 열린 이슈만 보면 그 시점부터 파이프라인이 끊긴다
(1판 E2E 에서 실제로 끊겼다).

---

## 4. 에이전트 6종 — 계약표

승격 조건(트리거가 다르다 / 신뢰 도메인이 다르다 / 독립성이 필요하다) 중 하나
이상을 만족해야 에이전트다. 셋 다 아니면 같은 룰북의 커맨드다.

| 에이전트 | 트리거 | 입력 | 산출물(계약) | 다음 | 권한 | 모델 |
|---|---|---|---|---|---|---|
| **review** | PR 열림·갱신 | diff + spec(있으면) + 룰북 | PR 리뷰 (반증 통과분만) | 사람 머지 | `pull-requests: write` | opus |
| **gates** | PR 열림·갱신 | 커밋 범위 | 체크 성공/실패 | 필수 체크 | `checks: write` | 없음 (LLM 0회) |
| research | `pipeline:research` | 이슈 본문 | 출처 인용 브리프 → 코멘트 | `pipeline:plan` | agent: `contents: read` / publish: `issues: write` | sonnet |
| plan | `pipeline:plan` | 이슈 + 브리프 | `spec.md` — 검증 가능한 요구사항 + write-set | `pipeline:build` | agent: `contents: read` / publish: `contents: write` | opus |
| build | `pipeline:build` | spec | PR | (PR 이벤트 → review) | 벤더 제품에 위임 | sonnet |
| qa | 머지됨 | 브랜치/배포 | run record | `pipeline:done` 또는 버그 이슈 | agent: `contents: read` / publish: `issues: write` | sonnet |
| diagnose | `repository_dispatch` (외부 알럿) | 알럿 payload | 증거 인용 RCA → 이슈 | `pipeline:research` | agent: 프로덕션 read-only / publish: `issues: write` | opus |
| mine | `schedule` (주 1회) | 지난주 리뷰 코멘트 + 반영 여부 | 룰북 개정 이슈 | — | `issues: write` | opus |

모델 배정은 CLAUDE.md 의 라우팅 의도표를 따른다 — **판단은 opus, 작업은 sonnet.**
비용이 문제가 되면 DoorDash v3 패턴(sonnet 스카우트가 의심 지점만 추려 opus 딥
리뷰어에 전달)이 최적화 경로다.

### 모니터링이 다른 에이전트를 트리거하는 경로

원래 요구사항이었던 "모니터링 에이전트가 다른 플러그인의 에이전트를 트리거"는
버스에서 이렇게 성립한다:

```
알럿 시스템(Prometheus/Datadog)
  → POST /repos/{o}/{r}/dispatches   (event_type: alert, client_payload: 알럿 내용)
  → diagnose.yml 이 깨어나 RCA
  → 이슈 발행 + pipeline:research 라벨 + dispatch
  → research 가 깨어난다 …
```

외부 시스템은 REST 호출 하나만 하면 된다. 오케스트레이터를 거치지 않는다.

---

## 5. 스테이지 상세

### review (1호)

**1호에는 상태기계가 필요 없다.** PR 이 열리면 리뷰하고 끝이다. 라벨도, 라벨
전이도, attempt 예산도 쓰지 않는다. §1·§3 은 2호(chain)부터 적용된다.

- 트리거: `pull_request: [opened, synchronize]`
- 룰북: `review-agent-rulebook` 을 체크아웃해 프롬프트에 주입
- 판정 원칙 (DoorDash):
  - **precision over recall.** 게시 전 스스로 반증(disprove-it)에 실패한 지적만 낸다
  - **CI 가 잡는 것은 말하지 않는다.** 린터·타입체커·테스트가 이미 잡는 지적은 노이즈
  - 코드 품질 평론이 아니라 **결함 지적**
- 산출: PR 리뷰 1건. 지적 0건이면 리뷰를 남기지 않는다(침묵이 기본값)
- 원장 기록: PR 번호, 지적 수, 토큰 비용, 오픈→코멘트 소요 시간

**fork PR 은 시크릿을 받지 못한다.** 비공개 레포에서는 무관하고, 공개 레포로 확장할
때 `workflow_run` 분리 패턴이 필요해진다.

### gates (2호)

LLM 0회. 결정론적. 실패는 재시도가 아니라 정지다.

| 검사 | 막는 것 |
|---|---|
| writeset | 보호 경로(CI 설정·인증·시크릿·마이그레이션) 변경, spec 의 write-set 이탈 |
| deps | 존재하지 않는 패키지, 레지스트리 확인 불가 |
| (미구현) mutation | 테스트를 약화시켜 통과하는 치팅 |

**입력은 워크트리가 아니라 커밋 범위다** (`origin/main...HEAD` ∪ 워크트리).
1판은 `git status` 만 봐서 워커가 자가 커밋하면 게이트가 아무것도 못 봤다 — 재현 확인됨.

**원칙: 불확실하면 막는다.** 매니페스트를 못 읽었으면 "새 의존성 0개"가 아니라
"검사 불가"이고, 둘은 정반대 처분을 받는다.

### plan

산출물 `spec.md` 는 두 가지를 반드시 담는다:

1. **검증 가능한 요구사항** — 번호로. "잘 동작한다"가 아니라 판정 가능한 문장으로
2. **write-set** — `- write: <경로 glob>` 형식. 게이트가 이것과 대조한다

write-set 선언이 없으면 게이트는 fail closed 다. "범위를 말하지 않았으니 아무 데나
써도 된다"는 자율 파이프라인에서 성립하지 않는다.

### research

egress 가 가장 넓고(웹 전체) write 는 0인 조합. 산출물을 파일이 아니라 **코멘트**로
둔 이유가 이것이다 — 외부 콘텐츠를 읽는 에이전트가 레포에 쓸 수 없어야 인젝션
피해 반경이 "틀린 브리프"에 머문다.

---

## 6. 불변식

깨지면 설계가 새는 신호. 워크플로 리뷰 시 이것부터 본다.

1. **LLM job 과 쓰기 권한 job 은 분리된다.** (예외: PR 리뷰 — §2)
2. **에이전트는 라벨을 직접 바꾸지 않는다.** publish job 만 바꾼다.
3. **진행 판정은 라벨로만.** 이슈 열림/닫힘으로 하지 않는다.
4. **게이트는 건너뛸 수 없다.** 필수 체크로 등록되어야 한다.
5. **신뢰할 수 없는 값은 셸에 보간하지 않는다.** 이슈 제목·본문을 `run:` 안에
   `${{ }}` 로 넣으면 제목 안의 `$(…)` 가 실행된다 — **이슈는 누구나 열 수 있으므로
   이건 원격 코드 실행이다.** env 로 받아 인용한다.
6. **계약은 경로가 아니라 내용으로 넘긴다.** 샌드박스 밖 경로를 주면 워커가 읽지
   못한다(1판 E2E 에서 실제로 멈췄다).
7. **재시도는 멱등해야 한다.** 매 시도를 `origin/main` + spec 에서 새로 시작한다.
8. **`pipeline:human` 은 아무도 듣지 않는다.** 사람만 풀 수 있다.

---

## 7. 출하 순서

한 번에 하나씩. 다음을 늘릴지는 **원장이 결정한다** — 멀티에이전트 파일럿의 40% 가
6개월 내 실패하고, 단일 에이전트가 64% 벤치마크에서 동등 이상이다.

| 순 | 무엇 | 왜 이 순서 |
|---|---|---|
| 1 | `review.yml` + `ledger/` | 병목이 검토다(DORA). 코드를 안 쓰므로 가장 안전 |
| 2 | `gates.yml` | 리뷰어 판단력 밖의 방어선 |
| 3 | **첫 ablation** | 룰북 on/off 수용률 비교. 이 레포가 존재하는 이유 |
| 4 | `mine.yml` | 룰북이 학습하는 자산이 되는 지점 |
| 5 | 원장이 지목하는 것 | 확장 vs 리뷰어 개선을 데이터가 고른다 |

**이 표 전체를 한꺼번에 짓지 않는다.** §4 의 6종 계약표는 나중에 놀라지 않기 위해
미리 그려둔 지도이지, 지금 지을 목록이 아니다.

---

## 8. 미확정

- **§2 의 스코프 매핑** — PR 리뷰가 `pull-requests: write` 만으로 되는지 1호 첫
  실행에서 실증. 403 이면 job 분리로 되돌린다
- **`attempt:N` 의 증가 주체** — chain 이 생기는 2호 이후 결정
- **fork PR** — 공개 레포로 확장할 때 `workflow_run` 분리 패턴
- **build 위임처** — `claude-code-action` vs Copilot coding agent. 원장 비용 비교 후
