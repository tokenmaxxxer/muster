# Operations

This is the day-to-day operations/reference handbook for on-the-record, carrying the installation, isolation, gate, and self-check material out of the README (linked from there).

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

### 방치된 미커밋 작업 — 자동 재스폰 (이슈 #132, #247)

헤드리스 역할 세션이 `Agent`/`Task` 서브에이전트로 일을 쪼갠 뒤 "워커가
끝나면 이어가겠다"고 말하고 자기 턴을 끝내면, 그 프로세스는 정상 종료한다
(`rc=0`, 크래시 아님) — 하지만 다음 턴은 없다. 워커가 남긴 편집물은
워크스페이스에 미커밋인 채로 남고, 커밋할 프로세스는 이미 없다.

이 모양은 `errored`/`progressed`/`waiting-on-human`/`silent-failure` 와
갈라지는 두 개의 별도 처분으로 잡힌다:

- **`uncommitted-work`.** `silent-failure`(exit 0, 보드 무변화, 거부도
  없음)로 분류됐어야 할 세션인데, 워크스페이스에 `git status --porcelain`
  으로 잡히는 미커밋 변경이 있으면 여기로 재분류된다.
- **`failed-no-commit`.** 세션이 스스로 `progressed` 라고 보고했지만
  (보드 변화가 있었지만) 새 커밋도 없고 미커밋 변경도 없으면(또는 있으면
  `progressed-dirty-tree`) `fail_closed_downgrade()` 가 여기로 깎는다.

두 outcome 모두 **크래시가 아니다** — `roster_watchdog()`/
`session_end_verdict()` 의 `crashed`/`stalled` 3분법은 절대 이 경우를
잡지 못한다: 프로세스가 정상 종료하며 `session-end` 이벤트를 스스로 남기고,
`roster_remove()` 가 로스터 엔트리를 동기적으로 지우기 때문에, 어떤
`spawn.py watchdog` 틱도 "죽었는데 등록만 남은" 엔트리를 볼 기회가 없다.

이슈 #132 가 `crashed` 에만 걸어 둔 상한부(2회) 자동 재스폰/캡-코멘트
기계를, 이슈 #247 이 이 두 outcome 에도 그대로 연결했다 — 워치독 틱을
기다리지 않고, `_spawn_one()` 자기 프로세스가 outcome 을 확정하는 바로 그
자리에서 즉시 재스폰을 시도한다. 상한(2회)에 닿으면 `crashed` 때와 같은
이슈 코멘트가 남는다(어느 트리거가 상한을 채웠는지 본문에 적힌다). 상한을
기다리지 않고 더 일찍 개입하고 싶거나, 상한이 이미 소진됐다면 같은
워크스페이스/브랜치로 수동 재스폰한다:

```bash
python3 spawn.py <역할> "<맡길 일>" --issue <n>
```

`issue_workspace()` 가 새로 클론하지 않고 기존 워크스페이스를 fetch 해
이어받으므로, 미커밋 변경이 그대로 남아 있으면 세션이 커밋부터 끝낼 수
있다.

### 일부러 멈추는 자리

두 정지는 계약이 지켜지는 것이지 우회할 실패가 아니다:

- **coding, `proposed → approved` 에서.** 계약 §8 이 범위 변경 승인을 사람에게
  유보한다. 헤드리스는 거기서 서서 기다린다.
- **어느 역할이든, upstream 산출물의 첫 읽기에서.** 계약 §12 가 그것을 근거로
  움직이기 전에 한 번 묻게 하고, 답을 **추측하는 것을 금지한다.**

## Using it

### Installing

```
/plugin marketplace add tokenmaxxxer/on-the-record
/plugin install on-the-record@tokenmaxxxer
```

That is the whole install for `on-the-record`. `on-the-record`'s own marketplace also lists
every rulebook plugin from all nine role rulebooks, each sourced straight from its
own GitHub repo (`{"source": "github", "repo": "tokenmaxxxer/<repo>"}`) — so
`claude plugin install <plugin>@tokenmaxxxer` resolves any of them (say
`implementation-cycle`, `freelunch`, `execution-observation-cycle`) directly, without adding all nine
rulebook repos as separate marketplaces one at a time. No local clone of any
rulebook is required for this: the rulebooks are **not** cloned by hand — each
role file names its repo, and the first spawn of a role fetches that rulebook's
marketplace if it is not already on the machine. Private repos work — the fetch
uses the git credentials already in place.

This install-from-`on-the-record`'s-marketplace path is a separate, optional route from
`spawn.py`'s own per-role fetch above — `spawn.py` warms its own marketplace
registration on first spawn and needs no marketplace add at all. Use `claude
plugin install <plugin>@tokenmaxxxer` only when you want a rulebook
plugin installed and browsable outside of `spawn.py`.

**This listing resolves the install, not ongoing updates.** Per the measured
behavior below (`claude plugin update` compares only the pinned `version`
string and every rulebook sits at 0.1.0 forever), installing through
`tokenmaxxxer` does not make `claude plugin update` refresh a
GitHub-sourced rulebook from remote HEAD either. Refreshing an installed
rulebook still goes through `spawn.py update <role>` (or a reinstall).

A local checkout still wins when one exists. `roles/<role>.json` keeps an optional
`path`, and if that directory holds a `.claude-plugin/marketplace.json` it is used
instead of the remote — so editing a rulebook and running it through on-the-record does
not require a commit and a push first.

That path is written as `$TOKENMAXXXER_RULEBOOKS/<repo>` and is resolved through
`~` and `$VAR` expansion. Set the variable to the directory holding your rulebook
checkouts:

    export TOKENMAXXXER_RULEBOOKS=~/src/tokenmaxxxer

Leave it unset and every role resolves from GitHub, which is the right default for
anyone who is not editing the rulebooks. An unexpanded variable is treated as *no
path* rather than as a literal directory name — a path that does not exist is
"misconfigured", not "unconfigured", and the two deserve opposite handling.

`TOKENMAXXXER_RULEBOOKS` is an **optional dev override**, not a spawn-time
requirement: `spawn.py` role-spawning already resolves each role's rulebook
from GitHub when no local checkout exists, and so does `claude plugin install
<plugin>@tokenmaxxxer` above. Set it only to work on a rulebook's own
source locally without round-tripping through GitHub.

**Nothing updates itself, and updating the clone is not enough.** A session loads
plugins from `~/.claude/plugins/cache/`, not from the marketplace clone, and the two
drift apart: `claude plugin update` compares the `version` *string* in plugin.json,
and every rulebook sits at 0.1.0 forever, so it answers "already at the latest
version" however many commits behind the cache is. Measured 2026-07-27: clone
2018d54, cache 7107a49, and a gate fix merged minutes earlier was not what ran.

`spawn.py` prints the **installed** sha on every spawn and says so when it differs
from the clone. `spawn.py update [role]` closes the gap by uninstalling and
reinstalling, which is the only route that moves the cache.

Two things can pin a rulebook where `update` cannot move it, and both are reported
rather than silently tolerated:

- **A ghost registry entry.** `installed_plugins.json` keeps the entry when the
  cache directory is deleted. An entry that says "installed" makes the installer
  skip the plugin, so the cache never comes back and the session loads no rulebook
  at all while on-the-record reports it as present. Delete the named entry.
- **A local-scope install.** A bundle installed into some project's
  `.claude/settings.local.json` holds its dependencies at that commit; the
  user-scope uninstall reports success and leaves the entry in place. Uninstall the
  bundle with `--scope local` from that project.

### Before the first run: the target repo needs its board opt-in

Every role reads and writes the board (`docs/issue-<n>/reports/…`), and
core's gates require the repo to carry `docs/specs/approvers.md` — the
user-authored file that both declares "this repository is a board" and
lists the human approvers. Without it, a role session's board and
execution writes are refused (fail-closed), so `spawn.py` refuses to
start rather than burn a doomed session:

```
$ python3 spawn.py product-discovery "…" -C ~/work/new-app
대상 레포에 docs/specs/approvers.md 가 없다: …
```

Seed it once per project (`init` uses your gh login, or pass `--login`):

```bash
python3 spawn.py init -C ~/work/new-app
```

This is **the only thing on-the-record writes into someone else's repository** —
board records are never written from here, because those belong to a role
and editing them from outside routes around its gate. The canonical
role-handoff contract lives only in tokenmaxxxer-core; repos carry no
copy.

It refuses to overwrite a contract that differs from canonical: a repo may be
deliberately on another version, and replacing it silently would be the same
damage as the fork. `spawn.py` reports drift by content hash, which is the only
handle there is — the contract's frontmatter carries no version field, so two
files can both say `status: final` and differ by 188 lines. Measured 2026-07-26:
three rulebooks carried a 345-line contract and three a 533-line one.

`--no-contract` skips the check, for work that is not going near the board (asking
the implementation role for a one-off change, say). It is a flag rather than a warning
because the failure it prevents is silent, and a warning on stderr in a headless
run is not read.

### The loop

One call runs one role. After it, who runs next is not a table lookup — it is a
judgment call the orchestrating conversation makes by reading the board directly
(the records under `docs/issue-<n>/`, each one's `loop_state`).

```bash
python3 spawn.py product-discovery "build me a car-wash timing app" -C ~/work/new-app
python3 spawn.py                              -C ~/work/new-app
#   read docs/issue-<n>/reports/*.md; decide who's up next from loop_state
python3 spawn.py technical-feasibility "read the board: …" -C ~/work/new-app
```

Human-only gates (approval, scope, round-end) are unaffected by any of this —
they were never machine-routed to begin with.

The canonical approval location is the **issue comment**: `gh issue comment
<issue-n> --body "APPROVE issue-<n>/<role>"`. A PR review Approve is only an
alternative under a two-account, agent-account-separated hardening — in the
default (single-account) setup a PR review Approve on one's own PR is not
possible, so the issue comment is the only path (contract v3 s19).

When the human's decision is approve-with-feedback (conditional approval),
the recipe is two separate issue comments, in order: comment A's body is
the exact token string `APPROVE issue-<n>/<role>` and nothing else, ever;
comment B, posted immediately after, carries the feedback and points back
at comment A instead of repeating any part of the token. Token-first
ordering means a valid approval already stands the instant comment A
lands — feedback arriving a moment later in comment B never puts that in
question.

If a near-miss comment appears — approval-shaped (contains the literal
substring `APPROVE`) but not whole-body-identical to the canonical token —
the session posts exactly one reply pointing at the two-comment recipe
above and keeps waiting; it never treats the near-miss as approval, and
never posts more than one such reply per near-miss. (Two related code
defects — `approve-scope`'s `/scope`-vs-`/role` literal mismatch and the
30-comment pagination cap on issue-comment fetch — are issue #224's, not
fixed here.)

### From a conversation

Calling it from a conversation is the default. No separate trigger was built — the
place where work gets handed over is already the conversation.

```
/plugin marketplace add tokenmaxxxer/on-the-record
/plugin install on-the-record@tokenmaxxxer

/on-the-record:run                          just show the current state
/on-the-record:run execution-observation /testrun:testrun smoke
```

### Every command

```bash
python3 spawn.py                              # read the board (read-only)
python3 spawn.py <role> "<task>" -C <repo>    # bring up that role
python3 spawn.py <role> "x" --dry-run         # print the merged settings only
python3 spawn.py <role> "x" --no-contract     # skip the contract precondition
python3 spawn.py <role> "x" --unattended      # human absent, human gates still stand
python3 spawn.py doctor                       # measure hook firing on this CLI (once per version)
python3 spawn.py drive -C <repo>              # no auto-routing table exists; stops immediately
```

Authentication uses whatever is already logged in. No token, no secret.

### When a session ends

Every spawn captures the session's result JSON, appends one line to on-the-record's
`runs/ledger.jsonl` (session id, cost, turns, board delta, gate report) and
names the outcome: `errored` / `progressed` (the board changed) /
`waiting-on-human` (a §19 row stands) / `silent-failure` (exit 0 and an
unchanged board — the measured silent-death mode, now loud).

Every spawned session is stamped `TOKENMAXXXER_SPAWNED=1`: its prompts are
orchestrator-authored text, not a human turn, so core's mint hook must never
mint an approval from them. A human's approval is minted only in the human's
own session. And because rulebook enforcement rests on hooks firing in
headless sessions — a fact measured, not documented — `spawn.py doctor` must
re-measure it once per CLI version before any role spawns.

### Abandoned uncommitted work — automatic respawn (issues #132, #247)

When a headless role session splits work across `Agent`/`Task` subagents,
says "I'll continue once the workers finish," and ends its own turn there,
the process exits normally (`rc=0`, not crashed) — but there is no next
turn. Whatever a worker already wrote lands on disk uncommitted, and there
is no process left to commit it.

Two outcomes, distinct from `errored`/`progressed`/`waiting-on-human`/
`silent-failure`, name this shape:

- **`uncommitted-work`.** A session that would otherwise classify as
  `silent-failure` (exit 0, unchanged board, nothing blocked) gets
  reclassified here when the workspace has uncommitted changes visible to
  `git status --porcelain`.
- **`failed-no-commit`.** A session that self-reported `progressed` (the
  board did change) but left neither a new commit nor uncommitted changes
  (or left both — that case is `progressed-dirty-tree` instead) gets
  downgraded here by `fail_closed_downgrade()`.

Neither outcome is a **crash** — `roster_watchdog()`/
`session_end_verdict()`'s `crashed`/`stalled` trichotomy can never catch
this case: the process exits normally and appends its own `session-end`
event, and `roster_remove()` deletes the roster entry synchronously, so no
`spawn.py watchdog` tick ever gets a chance to see a dead-but-registered
entry.

Issue #132's capped (2 attempts) auto-respawn and cap-comment machinery,
previously wired only to `crashed`, now also fires for these two outcomes
(issue #247) — without waiting for a watchdog tick, `_spawn_one()` itself
triggers the respawn attempt the moment it finalizes its own outcome. On
hitting the cap, the same issue comment as the `crashed` case appears
(naming which trigger filled the cap). To intervene sooner than the cap,
or once the cap is already exhausted, respawn the same
workspace/branch manually:

```bash
python3 spawn.py <role> "<task>" --issue <n>
```

`issue_workspace()` fetches into the existing workspace rather than
re-cloning, so any uncommitted changes are still there for the resumed
session to commit.

### Where a run stops on purpose

Two halts are the contract working, not failures to route around:

- **implementation, at `proposed → approved`.** Contract §8 reserves approving scope
  changes for a human. A headless run stops there and waits.
- **any role, on a first read of an upstream artifact.** Contract §12 makes the role
  ask once, by name, before acting on it — and forbids guessing the answer.

## 격리 — 컨테이너가 아니라 샌드박스

Claude Code 의 Bash 샌드박스가 우리에게 필요한 것을 더 잘 준다. macOS 는 Seatbelt 라
설치할 것이 없다.

| 필요한 것 | 컨테이너(hosted CI) | Bash 샌드박스 |
|---|---|---|
| egress 통제 | **불가** (`--network` 미지원) | `network.allowedDomains` |
| 자격증명 격리 | 시크릿 명시 주입 | `credentials.envVars` 마스킹 + `injectHosts` |
| 파일시스템 경계 | 컨테이너 경계 | `filesystem.denyRead/allowWrite`, OS 강제 |
| 인증 | 별도 토큰 시크릿 필요 | **로그인된 것 그대로** |

## Isolation — a sandbox, not a container

Claude Code's Bash sandbox gives us more of what we need than a container does, and on
macOS it is Seatbelt, so there is nothing to install.

| requirement | container (hosted CI) | Bash sandbox |
|---|---|---|
| egress control | **not possible** (`--network` unsupported) | `network.allowedDomains` |
| credential isolation | secrets injected explicitly | `credentials.envVars` masking plus `injectHosts` |
| filesystem boundary | the container edge | `filesystem.denyRead/allowWrite`, enforced by the OS |
| authentication | needs its own token secret | **whatever is already logged in** |

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

## Three traps, each one measured

**① `--settings` merges, it does not replace.** A role file naming only the execution-observation rulebook
still drags in all 17 of the user's global plugins. `spawn.py` reads the global list and
overrides everything the role did not enable to `false`. Without that, the isolation is
a label.

**② The first spawn runs zero rulebooks.** It registers the marketplace; plugins attach
from the next run onward. It looks like a success, so it contaminates an ablation
wholesale. `spawn.py` checks `installed_plugins.json` and **stops** if anything is
missing.

**③ The sandbox permits fallback by default.** When a command hits the boundary the
agent simply turns the sandbox off and runs it again — in testing it read `~/.claude`
that way, through a `denyRead` that was supposedly blocking it. `spawn.py` forces
`allowUnsandboxedCommands: false`.

**Why not isolate wholesale with `CLAUDE_CONFIG_DIR`**: it separates configuration
completely, but the macOS keychain entry is tied to the config directory, so
authentication breaks.

### Package-registry access (issue #38)

A fresh sandboxed workspace has no package cache, so `go build`/`npm
install`/`pip install`/etc. hit the network boundary on the very first
dependency fetch. `role_settings()` addresses this two ways:

1. **Read-only host cache mount (default path).** If a well-known host
   package-cache directory exists (Go modules, npm, pip, cargo, Maven), it is
   added to `sandbox.filesystem.allowRead` — read-only, never write. This
   mount is only actively consulted by the ecosystem tooling for **Go**: an
   issue-scoped spawn also layers a `file://<host GOMODCACHE>/cache/download`
   source in front of `GOPROXY`, so `go build`/`go test` reads already-cached
   modules from the host without a write attempt against the read-only mount
   (`GOMODCACHE` itself stays workspace-local and writable, per the existing
   `.muster-cache` redirection below). npm/pip/cargo/Maven cache directories
   are still added to `allowRead` when present, but those tools' own cache
   env vars (`npm_config_cache`, `PIP_CACHE_DIR`, ...) are unconditionally
   redirected to the empty workspace `.muster-cache/` — their host caches are
   mounted but not yet wired into an active read path, so for those
   ecosystems the registry allowlist below is what actually avoids a
   network-denial failure today.
2. **Registry allowlist (fallback for cache misses).** `PACKAGE_REGISTRY_HOSTS`
   (a fixed list of official registry hostnames — npm, PyPI, Go module proxy,
   crates.io, Maven Central) is merged into every sandboxed role's
   `sandbox.network.allowedDomains`, so a role no longer needs to hand-curate
   these per `roles/*.json`.

### Web access (issues #58, #65)

Every role's sandbox allowlist only covered 3 hosts (`api.anthropic.com`,
`*.github.com`, `github.com`) plus the registry hosts above, so `WebSearch`
and `WebFetch` were silently denied for every role — the target of a search
or an in-context URL is not knowable in advance, so no fixed host list can
cover it (issue #43 hit this: 3/6 survey targets went unverified).

Web access is gated by **two independent layers**, and both have to be open
or the tool call is denied. `role_settings()` addresses each the same way it
addresses the registry case — additive, dedup-safe merges, applied to all
roles uniformly (operator decision: option B, not a per-role opt-in):

1. **Sandbox network layer (issue #58).** `WEB_ACCESS_DOMAINS` (a single
   `["*"]` entry — confirmed against the running Claude Code sandbox's
   domain matcher, which treats a literal `"*"` as matching every host) is
   merged into every sandboxed role's `sandbox.network.allowedDomains`, the
   same way `PACKAGE_REGISTRY_HOSTS` is merged just above. This governs
   whether the sandbox lets the *network connection* out.

2. **Tool-permission layer (issue #65).** Fixing layer 1 alone was not
   enough: a live session still saw every `WebSearch` call denied with
   "Permission to use WebSearch has been denied." Headless role sessions
   run with `--permission-mode acceptEdits` and nobody to answer a
   permission prompt, so a tool with no matching rule in
   `permissions.allow` is auto-denied regardless of what the network layer
   allows. `role_settings()` adds `WebSearch` and `WebFetch` to
   `permissions.allow` for every role (merged, not replacing a role's own
   `permissions.allow` entries) so headless sessions never hit that prompt
   for these two tools.

### Default-open posture (issue #72)

Issues #38, #58, #65, and #69 each opened one restriction switch at a time,
whack-a-mole style. #72 flips that: the sandbox now defaults **open** on
every restriction switch the schema exposes, except two things that stay
restricted — `sandbox.filesystem.allowWrite`/`denyWrite` (workspace write
scoping) and the board-gate/gh-guard hooks (enforced entirely outside the
sandbox schema, by `.claude/hooks/*`). `role_settings()` merges
`allowAllUnixSockets`, `allowLocalBinding`, `allowMachLookup`,
`enableWeakerNetworkIsolation`, `allowAppleEvents`, and
`enableWeakerNestedSandbox` open for every sandboxed role, additive and
no-clobber, the same merge site and pattern as the pre-existing registry/
web-domain allowlist merges above (`PACKAGE_REGISTRY_HOSTS`,
`WEB_ACCESS_DOMAINS`).

The sandbox itself stays `enabled: true` regardless of how many internal
switches are opened: headless Bash's auto-allow (trap ① above) depends on
the sandbox *existing*, not on any of its internal restriction settings, so
turning the sandbox off would remove that protection even though every
individual switch is now open. `sandbox.allowUnsandboxedCommands` also stays
`false` — that is what keeps the sandbox mandatory rather than advisory (see
trap ③ above); opening the restriction switches inside the sandbox doesn't
change whether the sandbox itself can be bypassed.

This one posture statement replaces the per-restriction trade-off notes that
used to sit under Package-registry access and Web access above — those two
merges are still real (and still worth naming, since they are the two
pre-#72 exceptions to the fully-restrictive default), but they are no longer
special cases against a "default-deny except this" backdrop. They are just
two more entries in an otherwise fully open sandbox.

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

## Gates

After a session ends, look deterministically at **what that session touched.** Zero LLM
calls.

```
[gate] needs a look:
  - protected path changed: .env
  - package does not exist: lodahs (package.json)
```

**It does not block** — the writes already happened and cannot be taken back, and on-the-record
does not adjudicate. It also does not wave anything through. When the check itself is
impossible (not a git repository, no default branch) it reports **"cannot check"**, not
"nothing found" — those two deserve opposite treatment.

The comparison base is the default branch `origin/HEAD` points at. `GATE_BASE` overrides it.

## 머지 게이트 (CI)

`.github/workflows/plan-aware-closes-gate.yml`(issue #245)이 PR 이벤트마다
`gates/ci.py --pr <n> --autodetect --closes-only`를 돌려 계획-인지 Closes
게이트(`gates/pr_reference.py`, issue #228)를 강제한다 — 위 "게이트"와 달리
이건 **막는다**: `--closes-only`는 write_scope/protected-path/deps/record
검사는 건너뛰고 Closes 게이트만 돈다. 이슈 번호는 PR 본문이 아니라 head
브랜치명(`issue-<n>/<role>`)에서, phase는 본문의 closing 키워드 유무에서
끌어낸다 — 추출 실패는 fail-closed(차단). 근거는
`docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`.

**2026-08-04 부로 실제로 막는다** — main 브랜치 보호 규칙에 `closes-gate`가
필수 상태 체크로 등록돼 있고(`required_status_checks.contexts:
["closes-gate"]`) `enforce_admins`도 켜져 있다 — `gh api
repos/tokenmaxxxer/on-the-record/branches/main/protection`으로 직접
확인된다. 검증용 일회용 PR #263(머지 안 됨)이 closing 키워드가 있는
상태에서의 차단과 제거 후 통과를 양방향으로 실측했다. 활성화 경과는
`docs/issue-245/reports/implementation.md`("Activation completed").

## Merge gate (CI)

`.github/workflows/plan-aware-closes-gate.yml` (issue #245) runs
`gates/ci.py --pr <n> --autodetect --closes-only` on every PR event to
enforce the plan-aware Closes gate (`gates/pr_reference.py`, issue #228)
— unlike the "Gates" section above, this one **does** block:
`--closes-only` skips the write_scope/protected-path/deps/record checks
and runs only the Closes gate. The issue number is derived from the head
branch name (`issue-<n>/<role>`), not the PR body; phase from whether the
body has a closing keyword. Extraction failure is fail-closed. Rationale:
`docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`.

**Blocking for real as of 2026-08-04** — `closes-gate` is registered as a
required status check on main's branch protection rule
(`required_status_checks.contexts: ["closes-gate"]`) and `enforce_admins`
is on too — verify directly with `gh api
repos/tokenmaxxxer/on-the-record/branches/main/protection`. A throwaway
verification PR (#263, never merged) measured both directions: blocked
with the closing keyword present, passing once it was removed.
Activation history: `docs/issue-245/reports/implementation.md`
("Activation completed").

## 자체 점검

```bash
python3 test_gates.py
```

## Self-check

```bash
python3 test_gates.py
```

`python3 -m pytest`도 `pytest.ini`(`python_functions = test_* t_*`) 덕분에
`test_gates.py`의 `t_*` 케이스를 포함해 전체 스위트를 수집·실행한다.

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

## Open

- **Who runs next is orchestrator judgment, not a routing table.** (issue #120)
  `spawn.py drive` no longer picks a role automatically — it stops immediately,
  every time. Carrying a subject end to end means the orchestrating conversation
  reads the board (`docs/issue-<n>/reports/*.md`, each one's `loop_state`) and
  spawns the next role itself.
- **Six gate families still live once per rulebook.** `state-gate.sh` exists seven
  times and all seven differ. core holds consent and the board gate today; lifting
  the rest in, with their transition tables as data, has not started.
- **Scoring is manual.** Whether a finding hit an answer-key entry is adjudicated by
  a person (the key's adjudication clause). The runner only builds the scoresheet —
  imitating automatic adjudication is how the ledger starts lying.
</content>
