# Setup

This is the setup/installation reference handbook for on-the-record, linked from the README.

## 요구사항

**macOS 또는 Linux.** `PATH` 에 `bash`, `python3`, `git`, `gh`, 그리고
`gh auth login` 할 수 있는 GitHub 계정.

**Windows 네이티브는 지원하지 않는다 — WSL 을 쓴다.** 이식이 덜 된 게 아니라
구조적이다: 강제 평면 전체가 `.sh` 훅(`board-gate`, `approval-gate`,
`gh-guard`, `directive`)이고, `spawn.py` 는 `os.fork()` / `os.setsid()` /
`fcntl.flock()` 으로 역할 세션을 몬다. 시작해서 아무것도 강제하지 않는 대신
import 에서 실패하는데, 그쪽이 낫다 — 게이트 없이 도는 세션은 성공처럼 보인다.

macOS 의 샌드박스는 Seatbelt 라 이미 있다. **Linux 의 샌드박스와 자격증명
저장은 아직 실측하지 않았다** — `bash`·`fork`·`flock` 이 다 있으니 드라이버는
돌지만, 그걸 격리가 검증됐다는 뜻으로 읽지 마라.

## Requirements

**macOS or Linux.** `bash`, `python3`, `git`, and `gh` on `PATH`, and a
GitHub account you can `gh auth login` with.

**Native Windows is not supported — use WSL.** Two things make it structural
rather than a porting gap: the entire enforcement plane is `.sh` hooks
(`board-gate`, `approval-gate`, `gh-guard`, `directive`), and `spawn.py` drives
role sessions with `os.fork()` / `os.setsid()` / `fcntl.flock()`. It fails at
import rather than starting and enforcing nothing, which is the outcome to
prefer: a session that runs with no gates looks like success.

On macOS the sandbox is Seatbelt, already present. **On Linux the sandbox and
the credential store have not been measured** — `bash`, `fork` and `flock` are
all there, so the driver runs, but do not read that as a verified claim about
isolation.

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

## Getting started (what the user actually sets up)

Once, per machine:

1. `gh auth login` — your own account (this is what approves and merges).
2. In your conversational session:
   `claude plugin marketplace add tokenmaxxxer/on-the-record` +
   `claude plugin install on-the-record@tokenmaxxxer`.
   No clone needed — the marketplace add IS the clone, and the on-the-record
   plugin drives spawn.py from inside it. A manual checkout is only for
   developing on-the-record itself.
(`spawn.py doctor` — the probe that verifies plugin hooks actually fire
headless on the current CLI version — runs automatically on the first
spawn after a CLI update; one small probe session. Manual run optional.)

Optional hardening: a separate agent identity (machine-account PAT via
`export MUSTER_AGENT_GH_TOKEN=<pat>`, or a GitHub App) moves the
agent/human split from the session layer (gh-guard) to the account layer.
The default needs neither — one account, everything in conversation.

Optional: `export MUSTER_ROLE_MODEL=<model>` pins the model used by
spawned role sessions (e.g. `sonnet`, `opus`). Unset by default — role
sessions then run on the built-in default model (`sonnet`), not the
caller's own (possibly more expensive) session model. Does not affect the
`doctor()` haiku probe, which always hardcodes its own cheap model.

For a durable, repo-wide default that doesn't depend on remembering to
set the env var per command, write the model name to a repo-root
`role_model.txt` (one line, e.g. `opus`). Precedence is
`MUSTER_ROLE_MODEL` (env) > `role_model.txt` (config) > `sonnet` (built-in
default): the env var always wins when set, the config file is used only
when the env var is unset, and a missing or whitespace-only value at
either layer is treated the same as unset — falling through to the next
layer, terminating in the built-in `sonnet` default when both are unset
or blank. `--dry-run` reflects the fully resolved value through the same
precedence chain.

Rulebooks and tokenmaxxxer-core need NO manual clones: spawn fetches and
ff-updates them under `on-the-record/runs/rulebooks/` automatically (a local
checkout, if present, wins — that is the development override).

Once, per target repo — and the orchestrator offers to do all of it in
conversation when it finds a piece missing:

1. A GitHub remote (`gh repo create --private --source . --push` if
   local-only).
2. `docs/specs/approvers.md` — the approver allowlist (and board opt-in).
   `python3 on-the-record/spawn.py init -C <repo>` writes it from your gh login,
   or the on-the-record session creates it for you after confirming.
3. (Recommended) branch protection on main: PRs required. (Only with the
   optional agent account: invite it as a collaborator.)

Then everything is conversation: `/on-the-record:run`.

v3 notes: the board is `docs/issue-<n>/reports/<role>.md` in the target
repo, `main`-merged only; the canonical contract lives ONLY in
tokenmaxxxer-core — repos carry no copy; the board marker is
docs/specs/approvers.md (`spawn.py init` writes it);
`spawn.py approve` is gone — approval is a GitHub act the orchestrator
relays; core's four plugins (core/terse/freelunch/scout) attach to every
role session via --plugin-dir.

## 왜 필요한가

레포의 `.claude/settings.json` 을 고치면 그 레포에서 일하는 **모든** 에이전트에
적용된다 — 코딩 에이전트가 QA 룰북까지 읽는다. 플러그인 스코핑의 경계는 **세션**
이므로, 역할마다 세션을 따로 띄우는 수밖에 없다. 그게 on-the-record 다.

## Why this exists

Editing a repository's `.claude/settings.json` applies to **every** agent working in
that repository — the implementation agent ends up reading the execution-observation rulebook too. The boundary
of plugin scoping is the **session**, so the only way to give a role its own
environment is to start its own session. That is on-the-record.
