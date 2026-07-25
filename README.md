# muster

역할을 소집한다 — 그 역할의 룰북만 깔린 샌드박스 세션 하나를 띄운다.

배차 기사가 아니라 콘센트다. **상태는 각 역할이 갖고, muster 는 읽기만 한다.**

```
protocol.md   규약 — muster 가 하는 일 셋, 상태 노출 계약, 격리
roles/        역할 하나 = 파일 하나. 룰북 번들 + 샌드박스 경계
spawn.py      상태를 읽고, 역할 환경으로 세션을 띄운다
orchestrate/  그걸 대화에서 부르는 플러그인 (/orchestrate:run)
gates/        결정론 검사. LLM 0회
ledger/       성적표
```

*이름: 이전엔 `harness` 였는데, 이 조직에서 harness 는 이미 룰북 스택과
`qa-agent-rulebook/bench` 를 가리킨다. 겹치는 이름을 쓰면 문서가 서로를 가리키지
못한다.*

## 왜 필요한가

레포의 `.claude/settings.json` 을 고치면 그 레포에서 일하는 **모든** 에이전트에
적용된다 — 코딩 에이전트가 QA 룰북까지 읽는다. 플러그인 스코핑의 경계는 **세션**
이므로, 역할마다 세션을 따로 띄우는 수밖에 없다. 그게 muster 다.

## 역할

각 룰북이 자기 상태기계(`<role>-cycle`)와 원클릭 번들(`<role>-agent-env`)을 갖는다.
역할 파일은 그 번들 하나만 켠다 — 의존성이 나머지를 끌어오므로 룰북에 플러그인이
추가돼도 여기를 안 고쳐도 된다.

| 역할 | 룰북 | 무엇을 정하나 |
|---|---|---|
| product | tokenmaxxxer-product | 무엇을 만들지 |
| feasibility | tokenmaxxxer-feasibility | 될 일인지 (명세만 보고, 시장 논리 없이) |
| coding | tokenmaxxxer-coding | 만든다 (스티어링만, 상태기계 없음) |
| review | tokenmaxxxer-review | 명세대로인지 (요구사항별 판정) |
| qa | tokenmaxxxer-qa | 실제로 도는지 |
| ops | tokenmaxxxer-ops | 내보내고 지킨다 |

## 쓰기

대화에서 부르는 것이 기본이다. 트리거를 따로 만들지 않는다 — 일을 맡기는 자리가
이미 대화이기 때문이다.

```
/plugin marketplace add tokenmaxxxer/muster
/plugin install orchestrate@tokenmaxxxer-muster

/orchestrate:run                          지금 상태만 본다
/orchestrate:run qa /testrun:testrun smoke
```

셸에서 직접:

```bash
python3 spawn.py                              # 상태 조회 (읽기 전용)
python3 spawn.py qa "/testrun:testrun smoke" -C ~/work/some-repo
python3 spawn.py review "x" --dry-run         # 합쳐진 설정만 본다
```

인증은 로그인된 것을 그대로 쓴다. 토큰도 시크릿도 필요 없다.

## 격리 — 컨테이너가 아니라 샌드박스

Claude Code 의 Bash 샌드박스가 우리에게 필요한 것을 더 잘 준다. macOS 는 Seatbelt 라
설치할 것이 없다.

| 필요한 것 | 컨테이너(hosted CI) | Bash 샌드박스 |
|---|---|---|
| egress 통제 | **불가** (`--network` 미지원) | `network.allowedDomains` |
| 자격증명 격리 | 시크릿 명시 주입 | `credentials.envVars` 마스킹 + `injectHosts` |
| 파일시스템 경계 | 컨테이너 경계 | `filesystem.denyRead/allowWrite`, OS 강제 |
| 인증 | 별도 토큰 시크릿 필요 | **로그인된 것 그대로** |

## 실측으로 확인한 함정 셋

**① `--settings` 는 병합이지 교체가 아니다.** 역할 파일에 qa 룰북만 적어도 사용자
전역 플러그인 17개가 딸려온다. `spawn.py` 가 전역 목록을 읽어 역할이 켜지 않은 것을
전부 `false` 로 덮는다. 이걸 안 하면 격리가 이름뿐이다.

**② 첫 스폰은 룰북 0개로 돈다.** 마켓플레이스를 등록만 하고 플러그인은 다음
실행부터 붙는다. 겉보기엔 성공이라 ablation 결과를 통째로 오염시킨다. `spawn.py`
가 `installed_plugins.json` 을 확인해 미설치면 **멈춘다**.

**③ 샌드박스는 기본이 fallback 허용이다.** 명령이 경계에 막히면 에이전트가 그대로
샌드박스를 끄고 다시 돌린다 — 실측에서 `denyRead` 로 막은 `~/.claude` 를 그렇게
읽어냈다. `spawn.py` 가 `allowUnsandboxedCommands: false` 를 강제한다.

**`CLAUDE_CONFIG_DIR` 로 통째 격리하지 않는 이유**: 설정은 완전히 갈리지만 macOS
키체인 항목이 설정 디렉터리에 묶여 있어 인증이 끊긴다.

## 자체 점검

```bash
python3 test_gates.py
```

## 미해결

- **`warrant` 승인 게이트가 헤드리스에서 막힌다.** coding 룰북을 켜면 작업 시작 전
  승인에서 멈추는데 헤드리스에는 승인할 사람이 없다. `review-cycle`·`qa-cycle` 이
  답의 형태를 보여준다 — 작업 세션이 자기 승인을 못 만들고 사용자 턴에서 발행된
  일회용 토큰만 받는다. 같은 패턴을 warrant 에 적용하면 풀리지만 룰북 소유자의 결정이다.
- **coding 룰북에 상태기계가 없다.** 다른 다섯 역할은 `<role>-cycle` 로 승격됐다.
- **원장이 아직 리뷰 PR 기준이다.** `review-cycle` 이 `review-record.md` 로 판정을
  남기므로 거기 맞춰야 한다.
- **아무것도 재지 않았다.** `qa-agent-rulebook/bench` 가 준비돼 있고 한 번도 안 돌았다.
