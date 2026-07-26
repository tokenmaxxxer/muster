# tokenmaxxxer / muster

*[English](README.md)*

역할을 소집한다 — 그 역할의 룰북만 깔린 샌드박스 세션 하나를 띄운다.

배차 기사가 아니라 콘센트다. **상태는 각 역할이 갖고, muster 는 읽기만 한다.**

```
protocol.md   규약 — muster 가 하는 일 셋, 상태 노출 계약, 격리
              (protocol.ko.md 가 같은 규약의 한국어판)
roles/        역할 하나 = 파일 하나. 룰북 번들 + 샌드박스 경계
spawn.py      상태를 읽고, 역할 환경으로 세션을 띄운다
orchestrate/  그걸 대화에서 부르는 플러그인 (/orchestrate:run)
wakes.py      계약 §3 의 WAKES-ON 표를 평가한다 — 보드가 누구를 깨우는가
bench/        ablation 러너 — 룰북 on/off 를 같은 표적에 돌린다
gates/        결정론 검사. 세션이 끝나면 spawn.py 가 부른다. LLM 0회
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

역할 파일은 마켓플레이스와 경계만 적는다. 플러그인 목록은 `spawn.py` 가 그 룰북의
`marketplace.json` 을 읽어 펼친다 — 룰북에 플러그인이 추가돼도 여기를 안 고쳐도 된다.

**`<role>-agent-env` 번들만 켜는 방식은 안 된다.** 번들의 `dependencies` 는
`--settings` 의 `enabledPlugins` 로 해결되지 않는다(A/B 실측: 번들만 켠 세션은
doctrine 의 SessionStart 훅이 안 돌아 `docs/` 버킷이 안 생겼고, 개별로 켠 세션은
생겼다). 번들이 켜졌다는 사실만 보고 넘어가면 **룰북 0개로 도는 세션을 성공으로
착각한다.**

| 역할 | 룰북 | 무엇을 정하나 |
|---|---|---|
| product | tokenmaxxxer-product | 무엇을 만들지 |
| feasibility | tokenmaxxxer-feasibility | 될 일인지 (명세만 보고, 시장 논리 없이) |
| coding | tokenmaxxxer-coding | 만든다 — `build-proposal`, `loop_state: proposed,approved,landed` |
| review | tokenmaxxxer-review | 명세대로인지 (요구사항별 판정) |
| qa | tokenmaxxxer-qa | 실제로 도는지 |
| ux-design | tokenmaxxxer-ux-design | 쓰는 모습이 어때야 하는지 |
| verify | tokenmaxxxer-verify | coding 과 qa 의 산출물이 서로 맞는지 |
| reflect | tokenmaxxxer-reflect | 착지한 라운드가 무엇을 가르쳤는지 |
| ops | tokenmaxxxer-ops | 내보내고 지킨다 |

## 쓰기

### 설치

```
/plugin marketplace add tokenmaxxxer/muster
/plugin install orchestrate@tokenmaxxxer-muster
```

설치는 이게 전부다. 룰북을 손으로 clone 하지 **않는다** — 역할 파일이 자기 repo 를
적고 있고, 그 역할을 처음 띄울 때 없으면 받아온다. 비공개 레포도 된다(이미 있는 git
자격증명을 쓴다).

로컬 체크아웃이 있으면 그쪽이 이긴다. `roles/<역할>.json` 의 `path` 는 선택이고,
그 디렉터리에 `.claude-plugin/marketplace.json` 이 있으면 원격 대신 그걸 쓴다 —
룰북을 고쳐가며 muster 로 돌려볼 때 커밋·푸시를 먼저 하지 않아도 된다.

**마켓플레이스 클론은 스스로 갱신되지 않는다.** `spawn.py` 가 매 스폰마다 룰북의
sha 를 찍으므로 낡은 클론으로 돈 실행이 짐작이 아니라 눈에 보인다. 갱신은
`/plugin marketplace update <이름>` 이다.

### 첫 실행 전 — 표적 레포에 계약 파일이 있어야 한다

모든 역할이 `docs/specs/role-handoff-contract.md` 가 정의한 공유 보드를 읽고 쓰며,
각 룰북의 게이트는 그 파일을 **작업 중인 레포에서** 찾는다. 없으면 역할은 그래도
돌고 그럴듯한 산출물도 낸다 — 다만 계약의 공통 헤더가 하나도 안 붙어서 보드에
아무것도 안 올라가고 다른 역할이 영영 안 깨어난다. 세션은 종료 0 이고 그 사실을
아무것도 말해주지 않는다.

그래서 `spawn.py` 가 아예 멈춘다:

```
$ python3 spawn.py product "…" -C ~/work/new-app
대상 레포에 docs/specs/role-handoff-contract.md 가 없다: …
```

프로젝트당 한 번 심는다:

```bash
python3 spawn.py init -C ~/work/new-app
```

정본은 muster 의 `contract/` 에 있고, 이것이 **muster 가 남의 레포에 쓰는 유일한
경우다** — 보드 기록은 여기서 절대 쓰지 않는다. 그건 역할의 것이고 밖에서 고치면
전이 게이트를 우회한다. 계약 파일은 상태가 아니라 **전제조건**이다.

정본과 다른 계약이 이미 있으면 덮어쓰지 않는다. 그 레포가 의도적으로 다른 판일 수
있고, 조용히 갈아치우는 것은 갈라짐과 같은 종류의 손상이다. `spawn.py` 가 내용
해시로 갈라짐을 알린다 — 계약 frontmatter 에 버전 필드가 없어서 그게 유일한
판별 수단이다. `status: final` 두 개가 188줄 다를 수 있다. 2026-07-26 실측으로
룰북 셋은 345줄판, 셋은 533줄판이었다.

`--no-contract` 로 건너뛸 수 있다. 보드를 안 쓸 작업(코딩 역할에 단발 수정을
맡기는 것 같은)에만 쓴다. 경고가 아니라 플래그인 이유는 이 검사가 막는 실패가
조용하기 때문이다 — 헤드리스에서 stderr 경고는 아무도 안 읽는다.

### 루프

한 번 부르면 한 역할이 돈다. 끝나면 보드에게 다음이 누구인지 묻는다. `wake` 가
계약 §3 의 WAKES-ON 표를 평가해 지목한다.

```bash
python3 spawn.py product "세차 타이밍 앱을 기획해라" -C ~/work/new-app
python3 spawn.py wake -C ~/work/new-app
#   [feasibility] hypothesis docs/proposals/…md — feasibility 가 아직 안 읽었다
python3 spawn.py feasibility "보드가 너를 깨웠다. …" -C ~/work/new-app
python3 spawn.py wake -C ~/work/new-app
#   선 것 없음 — feasibility 가 확인했고 지금 작업 중이다
```

**바뀌지 않은 보드는 아무도 깨우지 않는다**(계약 §6). qa↔coding 이 무한 핑퐁하지
않고 끝나는 것이 이 규칙 덕이다.

`wake` 는 보고만 하고 띄우지 않는다. 여섯 줄 중 둘은 내용 판단이라 —
product 의 "수용 기준을 흔드는가", ops 의 "내보낼 준비가 됐는가" — **"안 깨어남"이
아니라 "못 잼"으로 찍힌다.**

### 대화에서

대화에서 부르는 것이 기본이다. 트리거를 따로 만들지 않는다 — 일을 맡기는 자리가
이미 대화이기 때문이다.

```
/plugin marketplace add tokenmaxxxer/muster
/plugin install orchestrate@tokenmaxxxer-muster

/orchestrate:run                          지금 상태만 본다
/orchestrate:run qa /testrun:testrun smoke
```

### 명령 전부

```bash
python3 spawn.py                              # 보드 조회 (읽기 전용)
python3 spawn.py wake                         # 보드가 누구를 깨우나 (계약 §3)
python3 spawn.py <역할> "<맡길 일>" -C <레포>   # 그 역할을 띄운다
python3 spawn.py <역할> "x" --dry-run          # 합쳐진 설정만 본다
python3 spawn.py <역할> "x" --no-contract      # 계약 전제조건을 건너뛴다
```

인증은 로그인된 것을 그대로 쓴다. 토큰도 시크릿도 필요 없다.

### 일부러 멈추는 자리

두 정지는 계약이 지켜지는 것이지 우회할 실패가 아니다:

- **coding, `proposed → approved` 에서.** 계약 §8 이 범위 변경 승인을 사람에게
  유보한다. 헤드리스는 거기서 서서 기다린다.
- **어느 역할이든, upstream 산출물의 첫 읽기에서.** 계약 §12 가 그것을 근거로
  움직이기 전에 한 번 묻게 하고, 답을 **추측하는 것을 금지한다.**

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

## 게이트

세션이 끝나면 그 세션이 **무엇을 건드렸는지** 결정론적으로 본다. LLM 0회.

```
[게이트] 확인 필요:
  - 보호 경로 변경: .env
  - 존재하지 않는 패키지: lodahs (package.json)
```

**막지는 않는다** — 이미 쓴 뒤라 되돌릴 수 없고, muster 는 판정하지 않는다.
대신 조용히 넘어가지도 않는다. 검사 자체가 불가능하면(git 아님, 기본 브랜치 부재)
"이상 없음"이 아니라 **"검사 불가"**로 보고한다 — 둘은 정반대 처분을 받아야 한다.

비교 기준은 `origin/HEAD` 가 가리키는 기본 브랜치를 찾아 쓴다. `GATE_BASE` 로 덮을 수 있다.

## 자체 점검

```bash
python3 test_gates.py
```

## 미해결

- **WAKES-ON 감시자를 실제로 돌리는 것.** `wake` 는 누구를 열지 말해줄 뿐 여는 것은
  사람이다. 계약 §3 이 "만들어진다면 미래의 자동 감시자"에게 그 자리를 남겨뒀다.
  다만 subject 하나를 손으로 끝까지 몰아본 다음에 만드는 게 맞다 — 지금까지 매
  단계마다 루프였으면 삼켰을 것이 하나씩 나왔다.
- **`feasibility-agent-rulebook` 게이트 스위트의 기존 9건 실패.** v1 경로인
  `feasibility-record.md` 에 대고 게이트를 때리는데, 소유 경로 규칙이 그 경로를 더는
  안 덮는다. 게이트가 그걸 계속 관할해야 하는지, 케이스를 옮겨야 하는지는 그 룰북의
  판단이다.
- **계약 §3 표와 §5 가 어긋난다.** §5 는 모든 역할이 자기 앞 finding 에 깨어난다고
  하는데, 표는 coding 줄에만 finding 을 적었다. `wakes.py` 는 §5 를 따랐다 — 표만
  따르면 coding 외 역할에게 온 finding 을 아무도 안 본다.
- **채점이 수동이다.** 발견이 정답 키를 맞혔는지는 사람이 판정한다(키의 adjudication
  조항). 러너는 채점표만 만든다 — 자동 판정을 흉내 내면 원장이 거짓말을 시작한다.
