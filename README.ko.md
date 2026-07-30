# tokenmaxxxer / on-the-record

*[English](README.md)*

## 혼자 AI 로 코딩하다 보면 반드시 만나는 다섯 개의 벽

1. **바이브 코딩은 표류한다.** 긴 채팅 세션 하나로 몇 시간을 이어가다 보면
   맥락이 썩고, 초반에 정했던 요구사항은 잊히고, 코드베이스는 어느새 만든
   사람조차 더 이상 이해 못 하는 상태가 된다.
2. **품질은 동전 던지기다.** 어떤 세션은 훌륭하고 어떤 세션은 엉망인데,
   검증 안 된 작업이 그대로 커밋되는 걸 막는 장치가 어느 쪽에도 없다.
3. **매번 처음부터 다시 가르친다.** "테스트 먼저", "코드 전에 설계 문서부터"
   같은 작업 규칙을 세션마다 처음부터 다시 알려줘야 한다 — 아무것도 이어지지
   않기 때문이다.
4. **아무것도 인계할 수 없다.** 요구사항, 결정, 히스토리가 전부 채팅 로그
   안에만 있다. 팀원도, 미래의 나 자신도 그 작업에 올라타거나 감사할 방법이
   없다.
5. **에이전트를 병렬로 돌리면 서로 부딪힌다.** 격리도, 머지 규율도 없어서
   여러 에이전트를 동시에 돌리면 서로의 작업을 밟는다.

## 다른 AI 는 기록에 안 남고 일한다. 당신 것은 기록에 남기고 일한다.

on-the-record 가 만드는 모든 작업물은 공식 git 기록이 된다.
**요구사항은 이슈, 작업은 PR, 결정은 기록된 승인, 규칙은 버전 관리되는
룰북이다.** 여기서는 어떤 것도 채팅 로그 안에만 머물지 않는다.

이것이 AI 산출물을 데모용이 아니라 믿고 넘길 수 있는, 인계 가능한,
판매 가능한 등급으로 만드는 이유다.

- **역할 전문가, 태스크마다 깨끗한 맥락.** 역할마다 그 역할의 룰북만 깔린
  자기만의 샌드박스 세션이 뜬다 — QA 룰북 맥락이 코딩 세션으로 새는 일도,
  그 반대도 없다.
- **프로세스 자산이 git 안에 산다.** 룰북은 버전 관리되는 파일이라, 더 나은
  모델이 와도 아무것도 다시 가르칠 필요 없이 바로 집어 쓴다.
- **사용자가 유일한 승인자로 남는다.** 사용자 본인 GitHub 계정이 승인하지
  않으면 아무것도 머지되지 않는다 — 방관자가 아니라 CEO 자리다.
- **자기 완결적이다.** 플러그인 하나가 시스템 전체를 설치한다. 따로 연결할
  것이 없다.

아래부터는 이 약속이 실제로 어떻게 구현되는지에 대한 이야기다 —
설득이 아니라 뒷받침하는 세부사항이다.

역할을 소집한다 — 그 역할의 룰북만 깔린 샌드박스 세션 하나를 띄운다.

배차 기사가 아니라 콘센트가 있는 컨시어지다: contract v3 에서는 오케스트레이션
세션(이 마켓플레이스의 `on-the-record` 플러그인)이 사용자와 대화하고, 사용자가
불러주는 이슈를 작성하고, 역할 세션을 띄우고, 돌아온 PR 을 설명하고, 사용자의
결정 — 코멘트, 리뷰 Approve, 머지 — 을 사용자 본인 계정으로 대신 전달한다.
역할 세션은 AGENT 계정(`MUSTER_AGENT_GH_TOKEN`)으로 돌고, `issue-<n>/<role>`
브랜치에서 작업하며, 모든 결과는 PR 로 돌아온다. **각 역할이 자기 상태를 갖고,
on-the-record 는 읽기만 한다.**

```
protocol.md   규약 — on-the-record 가 하는 일 셋, 상태 노출 계약, 격리
roles/        역할 하나 = 파일 하나. 룰북 번들 + 샌드박스 경계
spawn.py      상태를 읽고, 역할 환경으로 세션을 띄운다
              (--issue <n> 가 브랜치를 만들고 프롬프트를 고정한다)
on-the-record/  그걸 대화에서 부르는 플러그인 (/on-the-record:run)
gates/        결정론 검사. 세션이 끝나면 spawn.py 가 부른다. LLM 0회
ledger/       성적표
```

## 시작하기 (사용자가 실제로 해야 할 설정)

기계당 한 번:

1. `gh auth login` — 본인 계정(이게 승인하고 머지하는 계정이다).
2. 대화 세션 안에서:
   `claude plugin marketplace add tokenmaxxxer/on-the-record` +
   `claude plugin install on-the-record@tokenmaxxxer`.
   clone 필요 없다 — 마켓플레이스 add 자체가 clone 이고, on-the-record
   플러그인이 그 안에서 spawn.py 를 돌린다. 수동 checkout 은 on-the-record
   자체를 개발할 때만 필요하다.
(`spawn.py doctor` — 플러그인 훅이 현재 CLI 버전에서 headless 로 실제로
발화하는지 확인하는 프로브 — 는 CLI 업데이트 뒤 첫 스폰에서 자동으로 돈다.
작은 프로브 세션 하나. 수동 실행은 선택.)

선택 강화: 별도 에이전트 계정(머신 계정 PAT — `export
MUSTER_AGENT_GH_TOKEN=<pat>` — 또는 GitHub App)을 두면 사람/에이전트 구분이
세션 계층(gh-guard)에서 계정 계층으로 올라간다. 기본값은 둘 다 필요 없다 —
계정 하나로, 전부 대화 안에서.

선택: `export MUSTER_ROLE_MODEL=<model>` 은 스폰되는 역할 세션이 쓰는
모델을 고정한다(예: `sonnet`, `opus`). 기본은 미설정 — 이 경우 역할
세션은 CLI 기본 모델로 돈다. `doctor()` 의 haiku 프로브에는 영향 없다 —
이건 항상 자기 전용 저가 모델을 하드코딩해 쓴다.

명령마다 환경변수 설정을 기억하지 않아도 되는 지속적인 레포 전역
기본값을 원하면, 레포 루트의 `role_model.txt` 에 모델 이름을 한 줄로
적는다(예: `sonnet`). 우선순위는 `MUSTER_ROLE_MODEL`(env) >
`role_model.txt`(config) > 없음이다: env 변수가 설정돼 있으면 항상
이기고, config 파일은 env 변수가 없을 때만 쓰이며, 두 계층 모두에서
비어 있거나 공백뿐인 값은 미설정과 동일하게 처리한다(`--model` 플래그
없음, 오늘의 기본값). `--dry-run` 은 같은 우선순위 체인을 통해 완전히
해석된 값을 그대로 보여준다.

룰북과 tokenmaxxxer-core 는 수동 clone 이 전혀 필요 없다: spawn 이
`on-the-record/runs/rulebooks/` 아래에 자동으로 받아오고 ff-update 한다
(로컬 checkout 이 있으면 그쪽이 이긴다 — 개발용 override).

프로젝트(표적 레포)당 한 번 — 뭔가 빠진 게 있으면 오케스트레이터가
대화 중에 알아서 다 해주겠다고 제안한다:

1. GitHub remote(로컬뿐이면 `gh repo create --private --source . --push`).
2. `docs/specs/approvers.md` — 승인자 allowlist(이자 보드 opt-in).
   `python3 on-the-record/spawn.py init -C <repo>` 가 사용자 gh 로그인으로
   써주거나, on-the-record 세션이 확인 후 대신 만들어준다.
3. (권장) main 에 branch protection: PR 필수. (선택적 에이전트 계정을
   쓸 때만: 그 계정을 협업자로 초대.)

그 다음부터는 전부 대화다: `/on-the-record:run`.

v3 참고: 보드는 표적 레포의 `docs/issue-<n>/reports/<role>.md`, `main`
머지분만; 정본 계약은 tokenmaxxxer-core 안에만 있다 — 레포는 사본을
갖지 않는다; 보드 마커는 docs/specs/approvers.md (`spawn.py init` 가
써준다); `spawn.py approve` 는 사라졌다 — 승인은 오케스트레이터가
전달하는 GitHub 행위다; core 의 플러그인 넷(core/terse/freelunch/scout)
은 --plugin-dir 로 모든 역할 세션에 붙는다.

## 왜 필요한가

레포의 `.claude/settings.json` 을 고치면 그 레포에서 일하는 **모든** 에이전트에
적용된다 — 코딩 에이전트가 QA 룰북까지 읽는다. 플러그인 스코핑의 경계는 **세션**
이므로, 역할마다 세션을 따로 띄우는 수밖에 없다. 그게 on-the-record 다.

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
/plugin marketplace add tokenmaxxxer/on-the-record
/plugin install on-the-record@tokenmaxxxer
```

`on-the-record` 는 이게 설치의 전부다. on-the-record 자체 마켓플레이스에는 아홉 개 역할
룰북의 플러그인도 전부 올라 있고, 각각 자기 github repo 에서 바로 소스된다
(`{"source": "github", "repo": "tokenmaxxxer/<repo>"}`) — 그래서 `claude plugin
install <플러그인>@tokenmaxxxer` 로 아무거나(예: `coding-cycle`,
`freelunch`, `qa-cycle`) 바로 설치된다. 아홉 개 룰북 레포를 하나씩 마켓플레이스로
추가할 필요가 없다. 여기에도 룰북 로컬 clone 은 필요 없다 — 룰북을 손으로 clone
하지 **않는다**: 역할 파일이 자기 repo 를 적고 있고, 그 역할을 처음 띄울 때 없으면
받아온다. 비공개 레포도 된다(이미 있는 git 자격증명을 쓴다).

on-the-record 마켓플레이스로 설치하는 이 경로는 위의 `spawn.py` 자체 역할별 fetch 와는
별개의, 선택적인 경로다 — `spawn.py` 는 첫 스폰에서 자기 마켓플레이스 등록을
알아서 하므로 마켓플레이스 add 가 아예 필요 없다. `claude plugin install
<플러그인>@tokenmaxxxer` 는 `spawn.py` 밖에서 룰북 플러그인을 설치하고
둘러보고 싶을 때만 쓴다.

**이 목록은 설치를 풀어줄 뿐, 계속되는 갱신을 풀어주지 않는다.** 아래 실측대로
`claude plugin update` 는 고정된 `version` 문자열만 비교하고 룰북 아홉 개가 전부
0.1.0 에 머물러 있으므로, `tokenmaxxxer` 로 설치해도 `claude plugin
update` 가 github 원격 최신으로 갱신해주지 않는다. 설치된 룰북을 갱신하려면
여전히 `spawn.py update <역할>` (또는 재설치)을 거쳐야 한다.

로컬 체크아웃이 있으면 그쪽이 이긴다. `roles/<역할>.json` 의 `path` 는 선택이고,
그 디렉터리에 `.claude-plugin/marketplace.json` 이 있으면 원격 대신 그걸 쓴다 —
룰북을 고쳐가며 on-the-record 로 돌려볼 때 커밋·푸시를 먼저 하지 않아도 된다.

그 경로는 `$TOKENMAXXXER_RULEBOOKS/<레포>` 로 적혀 있고 `~` 와 `$VAR` 를 펴서
푼다. 룰북 체크아웃들이 모여 있는 디렉터리를 이 변수에 넣으면 된다:

    export TOKENMAXXXER_RULEBOOKS=~/src/tokenmaxxxer

안 넣으면 모든 역할이 github 에서 풀린다 — 룰북을 고치지 않는 사람에게는 그게
맞는 기본값이다. 안 풀린 변수는 리터럴 디렉터리 이름이 아니라 **경로 없음**으로
취급한다. 없는 경로를 가리키는 것은 "설정 안 함"이 아니라 "잘못 설정함"이고,
둘은 정반대 처분을 받아야 한다.

`TOKENMAXXXER_RULEBOOKS` 는 **선택적 개발용 override** 이지 스폰 시점의 필수
조건이 아니다: `spawn.py` 의 역할 스폰은 로컬 체크아웃이 없으면 이미 github 에서
룰북을 풀어오고, 위의 `claude plugin install <플러그인>@tokenmaxxxer` 도
마찬가지다. github 왕복 없이 룰북 소스를 직접 고칠 때만 이 변수를 넣는다.

**아무것도 스스로 갱신되지 않고, 클론만 갱신해서는 안 된다.** 세션은 마켓플레이스
클론이 아니라 `~/.claude/plugins/cache/` 의 설치본을 읽고, 이 둘은 갈라진다.
`claude plugin update` 는 plugin.json 의 `version` **문자열**만 보는데 룰북 아홉 개가
전부 0.1.0 에 머물러 있어서, 캐시가 몇 커밋 뒤처져 있든 "이미 최신"이라고 답한다.
실측 2026-07-27: 클론 2018d54 / 캐시 7107a49 — 몇 분 전에 머지한 게이트 수정이
세션에 안 붙어 있었다.

`spawn.py` 는 매 스폰마다 **설치본**의 sha 를 찍고, 클론과 다르면 다르다고 말한다.
`spawn.py update [역할]` 이 그 간격을 메운다 — 지우고 다시 까는 것이 캐시를 움직이는
유일한 길이다.

`update` 로도 안 움직이는 경우가 둘 있고, 둘 다 조용히 넘어가지 않고 보고된다:

- **유령 등록 항목.** 캐시 디렉터리를 지워도 `installed_plugins.json` 의 항목은
  남는다. "설치됨"으로 남은 항목은 재설치를 건너뛰게 하므로 캐시가 영영 안 돌아오고,
  세션은 룰북 0개로 도는데 on-the-record 는 붙었다고 보고한다. 지목된 항목을 지운다.
- **local scope 설치.** 어느 프로젝트의 `.claude/settings.local.json` 에 깔린 번들이
  자기 의존 플러그인들을 그 커밋에 묶어 둔다. user scope 의 uninstall 은 성공했다고
  답하면서 항목을 그대로 남긴다. 그 프로젝트에서 `--scope local` 로 번들을 지운다.

### 첫 실행 전 — 표적 레포에 보드 opt-in 이 있어야 한다

모든 역할이 보드(`docs/issue-<n>/reports/…`)를 읽고 쓰고, core 의 게이트는
레포가 `docs/specs/approvers.md` 를 갖고 있길 요구한다 — "이 레포는 보드다"를
선언하고 사람 승인자 목록을 적는, 사용자가 직접 쓰는 파일이다. 없으면 역할
세션의 보드/실행 쓰기가 거부되므로(fail-closed), `spawn.py` 는 실패할 세션을
태우는 대신 아예 시작을 거부한다:

```
$ python3 spawn.py product "…" -C ~/work/new-app
대상 레포에 docs/specs/approvers.md 가 없다: …
```

프로젝트당 한 번 심는다(`init` 은 사용자 gh 로그인을 쓰거나 `--login` 을 받는다):

```bash
python3 spawn.py init -C ~/work/new-app
```

이것이 **on-the-record 가 남의 레포에 쓰는 유일한 것**이다 — 보드 기록은
여기서 절대 쓰지 않는다. 그건 역할의 것이고 밖에서 고치면 그 역할의 게이트를
우회하는 셈이다. 정본 role-handoff 계약은 tokenmaxxxer-core 안에만 있고,
레포는 사본을 갖지 않는다.

정본과 다른 계약은 덮어쓰지 않는다: 그 레포가 의도적으로 다른 판일 수 있고,
조용히 갈아치우는 것은 포크와 같은 종류의 손상이다. `spawn.py` 가 내용 해시로
갈라짐을 보고한다 — 계약 frontmatter 에 버전 필드가 없어서 그게 유일한 판별
수단이다. `status: final` 두 개가 188줄 다를 수 있다. 2026-07-26 실측으로
룰북 셋은 345줄판, 셋은 533줄판이었다.

`--no-contract` 로 건너뛸 수 있다. 보드를 안 쓸 작업(코딩 역할에 단발 수정을
맡기는 것 같은)에만 쓴다. 경고가 아니라 플래그인 이유는 이 검사가 막는 실패가
조용하기 때문이다 — 헤드리스에서 stderr 경고는 아무도 안 읽는다.

### 루프

한 번 부르면 한 역할이 돈다. 끝나면 다음이 누구인지는 표 조회가 아니라 —
오케스트레이션 대화가 보드(`docs/issue-<n>/` 아래 기록, 각 기록의 `loop_state`)를
직접 읽고 내리는 판단이다.

```bash
python3 spawn.py product "세차 타이밍 앱을 기획해라" -C ~/work/new-app
python3 spawn.py                              -C ~/work/new-app
#   docs/issue-<n>/reports/*.md 를 읽고 loop_state 로 다음을 판단한다
python3 spawn.py feasibility "보드를 읽어라: …" -C ~/work/new-app
```

사람 전용 게이트(승인, scope, 라운드 종료)는 영향 없다 — 애초에 wake 로
자동화된 적이 없다.

승인의 정본 위치는 **이슈 댓글**이다: `gh issue comment <issue-n> --body
"APPROVE issue-<n>/<역할>"`. PR 리뷰 Approve 는 에이전트 계정을 분리한
2계정 하드닝 구성에서만 쓰는 대안이다 — 기본(1계정) 구성에서는 자기 PR 에
리뷰 Approve 를 달 수 없어 이슈 댓글이 유일한 경로다(contract v3 s19).

### 대화에서

대화에서 부르는 것이 기본이다. 트리거를 따로 만들지 않는다 — 일을 맡기는 자리가
이미 대화이기 때문이다.

```
/plugin marketplace add tokenmaxxxer/on-the-record
/plugin install on-the-record@tokenmaxxxer

/on-the-record:run                          지금 상태만 본다
/on-the-record:run qa /testrun:testrun smoke
```

### 명령 전부

```bash
python3 spawn.py                              # 보드 조회 (읽기 전용)
python3 spawn.py <역할> "<맡길 일>" -C <레포>   # 그 역할을 띄운다
python3 spawn.py <역할> "x" --dry-run          # 합쳐진 설정만 본다
python3 spawn.py <역할> "x" --no-contract      # 계약 전제조건을 건너뛴다
python3 spawn.py <역할> "x" --unattended       # 사람 부재: mint 없음, 휴먼 게이트는 선다
python3 spawn.py doctor                       # 이 CLI 에서 훅 발화를 실측 (버전마다 한 번)
python3 spawn.py drive -C <레포>               # 자동 라우팅 표가 없다 — 즉시 멈춘다
python3 spawn.py approve <kind> --subject <s>  # 사람이 직접 승인 토큰을 발행 (TTY 필요)
```

인증은 로그인된 것을 그대로 쓴다. 토큰도 시크릿도 필요 없다.

### 세션이 끝나면

스폰마다 결과 JSON 을 받아 on-the-record 의 `runs/ledger.jsonl` 에 한 줄을 남기고
(세션 id, 비용, 턴 수, 보드 변화, 게이트 보고) 처분을 말한다 — `errored` /
`progressed`(보드 변화) / `waiting-on-human`(§19 대기) / `silent-failure`
(exit 0 인데 보드 무변화 — 실측된 침묵-사망 모드가 이제 소리를 낸다).

모든 스폰 세션에는 `TOKENMAXXXER_SPAWNED=1` 도장이 찍힌다: 그 세션의
프롬프트는 오케스트레이터가 쓴 텍스트이지 사람 턴이 아니므로, core 의 mint
훅은 거기서 승인을 발행하면 안 된다. 사람의 승인은 사람의 세션에서만
발행된다. 그리고 룰북 집행은 훅이 headless 세션에서 돈다는 — 문서가 아니라
실측이 보증하는 — 사실 위에 서 있으므로, `spawn.py doctor` 가 CLI 버전마다
한 번 그 실측을 다시 해야 스폰이 열린다.

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

### 패키지 레지스트리 접근 (issue #38)

새로 뜬 샌드박스 워크스페이스에는 패키지 캐시가 없어서, `go build`/`npm
install`/`pip install` 등이 첫 의존성 fetch 부터 네트워크 경계에 막힌다.
`role_settings()` 는 이걸 두 방식으로 다룬다:

1. **읽기 전용 호스트 캐시 마운트(기본 경로).** 잘 알려진 호스트 패키지
   캐시 디렉터리(Go 모듈, npm, pip, cargo, Maven)가 존재하면
   `sandbox.filesystem.allowRead` 에 추가된다 — 읽기 전용, 쓰기는 절대
   안 된다. 이 마운트를 실제로 적극 활용하는 생태계 도구는 **Go** 뿐이다:
   이슈 스코프 스폰은 `GOPROXY` 앞에 `file://<host GOMODCACHE>/cache/
   download` 소스를 한 겹 더 얹어서, `go build`/`go test` 가 읽기 전용
   마운트에 쓰기를 시도하지 않고도 호스트에 이미 캐시된 모듈을 읽게
   한다(`GOMODCACHE` 자체는 아래의 기존 `.muster-cache` 리다이렉션대로
   워크스페이스 로컬에 쓰기 가능 상태로 남는다). npm/pip/cargo/Maven
   캐시 디렉터리도 존재하면 `allowRead` 에 추가되긴 하지만, 그 도구들
   자신의 캐시 환경변수(`npm_config_cache`, `PIP_CACHE_DIR` 등)는 무조건
   빈 워크스페이스 `.muster-cache/` 로 리다이렉트된다 — 호스트 캐시는
   마운트돼 있지만 실제 읽기 경로에는 아직 연결이 안 된 상태라서, 이
   생태계들에 대해서는 아래 레지스트리 allowlist 가 오늘 기준으로
   네트워크 거부 실패를 실제로 막아주는 수단이다.
2. **레지스트리 allowlist(캐시 미스 대비).** `PACKAGE_REGISTRY_HOSTS`
   (npm, PyPI, Go 모듈 프록시, crates.io, Maven Central 등 공식
   레지스트리 호스트명 고정 목록)가 모든 샌드박스 역할의
   `sandbox.network.allowedDomains` 에 병합돼, 역할마다 `roles/*.json`
   에 이걸 손으로 큐레이션할 필요가 없다.

### 웹 접근 (issue #58, #65)

역할별 샌드박스 allowlist 는 원래 호스트 3개(`api.anthropic.com`,
`*.github.com`, `github.com`)와 위 레지스트리 호스트만 덮었기 때문에,
`WebSearch` 와 `WebFetch` 는 모든 역할에서 조용히 거부되고 있었다 — 검색
대상이나 맥락 속 URL 은 미리 알 수 없으니 고정 호스트 목록으로는 커버가
안 된다(issue #43 이 이걸 맞았다: 서베이 대상 6개 중 3개가 검증 못 됨).

웹 접근은 **독립된 두 계층**으로 막혀 있고, 둘 다 열려야 도구 호출이
통과한다. `role_settings()` 는 레지스트리 케이스와 같은 방식으로 각 계층을
다룬다 — 추가적이고 중복 안전한 병합을, 모든 역할에 균일하게 적용한다
(운영 결정: 옵션 B, 역할별 opt-in 이 아니다):

1. **샌드박스 네트워크 계층 (issue #58).** `WEB_ACCESS_DOMAINS`(리터럴
   `["*"]` 하나 — 실제로 돌아가는 Claude Code 샌드박스의 도메인
   매처가 리터럴 `"*"` 를 모든 호스트에 매치하는 것으로 확인됨)가
   위의 `PACKAGE_REGISTRY_HOSTS` 와 같은 방식으로 모든 샌드박스 역할의
   `sandbox.network.allowedDomains` 에 병합된다. 이건 샌드박스가
   *네트워크 연결*을 내보내는지를 결정한다.

2. **도구 권한 계층 (issue #65).** 계층 1만 고쳐서는 부족했다: 실제
   세션에서도 모든 `WebSearch` 호출이 "Permission to use WebSearch
   has been denied." 로 거부됐다. 헤드리스 역할 세션은
   `--permission-mode acceptEdits` 로 돌고 권한 프롬프트에 답할 사람이
   없어서, `permissions.allow` 에 매치되는 규칙이 없는 도구는 네트워크
   계층이 뭘 허용하든 자동 거부된다. `role_settings()` 는 모든 역할의
   `permissions.allow` 에 `WebSearch` 와 `WebFetch` 를 추가한다(역할
   자신의 `permissions.allow` 항목을 대체하지 않고 병합) — 그래서
   헤드리스 세션이 이 두 도구에 대해서는 그 프롬프트를 절대 만나지
   않는다.

### 기본 개방 태세 (issue #72)

issue #38, #58, #65, #69 는 각각 두더지잡기 식으로 제한 스위치를 하나씩
열었다. #72 는 그걸 뒤집는다: 이제 샌드박스는 스키마가 노출하는 모든
제한 스위치에서 기본이 **개방**이고, 제한 상태로 남는 건 딱 둘 —
`sandbox.filesystem.allowWrite`/`denyWrite`(워크스페이스 쓰기 범위)와
board-gate/gh-guard 훅(샌드박스 스키마 밖, `.claude/hooks/*` 로 전적으로
강제됨)이다. `role_settings()` 는 모든 샌드박스 역할에 대해
`allowAllUnixSockets`, `allowLocalBinding`, `allowMachLookup`,
`enableWeakerNetworkIsolation`, `allowAppleEvents`,
`enableWeakerNestedSandbox` 를 열어 병합한다 — 추가적이고 덮어쓰지
않으며, 위의 레지스트리/웹 도메인 allowlist 병합(`PACKAGE_REGISTRY_HOSTS`,
`WEB_ACCESS_DOMAINS`)과 같은 병합 지점, 같은 패턴이다.

샌드박스 자체는 내부 스위치를 몇 개나 열든 `enabled: true` 로 남는다:
헤드리스 Bash 의 자동 허용(위 함정 ①)은 샌드박스가 *존재한다*는 것에
의존하지 그 내부 제한 설정 중 무엇에도 의존하지 않는다 — 그래서 개별
스위치가 전부 열렸다 해도 샌드박스를 꺼버리면 그 보호가 사라진다.
`sandbox.allowUnsandboxedCommands` 도 여전히 `false` 로 남는다 —
그게 샌드박스를 권고가 아니라 필수로 유지하는 것이다(위 함정 ③ 참고);
샌드박스 내부 제한 스위치를 여는 것과 샌드박스 자체를 우회할 수
있는지는 별개다.

이 태세 선언 하나가 예전에 Package-registry access 와 Web access 아래에
있던 개별 트레이드오프 설명들을 대체한다 — 그 두 병합은 여전히
실재하고(여전히 이름 붙여둘 가치가 있다 — #72 이전의 "기본 전면 제한"
배경에 대한 유이한 예외였으니까), 다만 더 이상 "기본 거부, 이것만 예외"
배경 위의 특수 케이스가 아니다. 이제는 완전히 열린 샌드박스 안의 두
항목일 뿐이다.

## 게이트

세션이 끝나면 그 세션이 **무엇을 건드렸는지** 결정론적으로 본다. LLM 0회.

```
[게이트] 확인 필요:
  - 보호 경로 변경: .env
  - 존재하지 않는 패키지: lodahs (package.json)
```

**막지는 않는다** — 이미 쓴 뒤라 되돌릴 수 없고, on-the-record 는 판정하지 않는다.
대신 조용히 넘어가지도 않는다. 검사 자체가 불가능하면(git 아님, 기본 브랜치 부재)
"이상 없음"이 아니라 **"검사 불가"**로 보고한다 — 둘은 정반대 처분을 받아야 한다.

비교 기준은 `origin/HEAD` 가 가리키는 기본 브랜치를 찾아 쓴다. `GATE_BASE` 로 덮을 수 있다.

## 자체 점검

```bash
python3 test_gates.py
```

## 미해결

- **다음이 누구인지는 라우팅 표가 아니라 오케스트레이터의 판단이다.**(이슈 #120)
  `spawn.py drive` 는 더 이상 역할을 자동으로 고르지 않는다 — 매번 즉시
  멈춘다. subject 하나를 끝까지 몰아가려면 오케스트레이션 대화가 보드
  (`docs/issue-<n>/reports/*.md`, 각 기록의 `loop_state`)를 직접 읽고 다음
  역할을 스스로 띄워야 한다.
- **게이트 여섯 종이 아직 룰북마다 따로 산다.** `state-gate.sh` 는 일곱 벌이고
  일곱이 전부 다르다. core 가 지금 들고 있는 것은 승인과 보드 게이트뿐이고,
  전이 표를 데이터로 받는 형태로 올리는 일은 시작 전이다.
- **채점이 수동이다.** 발견이 정답 키를 맞혔는지는 사람이 판정한다(키의 adjudication
  조항). 러너는 채점표만 만든다 — 자동 판정을 흉내 내면 원장이 거짓말을 시작한다.
