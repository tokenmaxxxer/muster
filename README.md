# tokenmaxxxer / muster

*[한국어](README.ko.md)*

Musters a role — brings up one sandboxed session with only that role's
rulebook and the tokenmaxxxer-core plugins installed.

Not a dispatcher. A power outlet with a concierge: on contract v3 the
orchestration session (this marketplace's `orchestrate` plugin) talks to
the user, drafts issues the user dictates, spawns role sessions, explains
the PRs that come back, and relays the user's decisions — comments,
review Approve, merge — with the user's own account. Role sessions run on
the AGENT account (`MUSTER_AGENT_GH_TOKEN`), work on `issue-<n>/<role>`
branches, and return everything by PR. **Each role owns its state; muster
only reads it.**

```
protocol.md   the contract — muster's three jobs, the state-exposure deal, isolation
roles/        one role is one file: rulebook bundle plus sandbox boundary
spawn.py      reads state, brings up a session in a role's environment
              (--issue <n> creates the branch and anchors the prompt)
orchestrate/  the plugin that drives the loop from a conversation (/orchestrate:run)
wakes.py      evaluates contract s3's WAKES-ON table: whom does the board wake
gates/        deterministic checks, run by spawn.py after a session. Zero LLM calls
ledger/       the scorecard
```

## Getting started (what the user actually sets up)

Once, per machine:

1. `gh auth login` — your own account (this is what approves and merges).
2. In your conversational session:
   `claude plugin marketplace add tokenmaxxxer/muster` +
   `claude plugin install orchestrate@tokenmaxxxer-muster`.
   No clone needed — the marketplace add IS the clone, and the orchestrate
   plugin drives spawn.py from inside it. A manual checkout is only for
   developing muster itself.
(`spawn.py doctor` — the probe that verifies plugin hooks actually fire
headless on the current CLI version — runs automatically on the first
spawn after a CLI update; one small probe session. Manual run optional.)

Optional hardening: a separate agent identity (machine-account PAT via
`export MUSTER_AGENT_GH_TOKEN=<pat>`, or a GitHub App) moves the
agent/human split from the session layer (gh-guard) to the account layer.
The default needs neither — one account, everything in conversation.

Optional: `export MUSTER_ROLE_MODEL=<model>` pins the model used by
spawned role sessions (e.g. `sonnet`, `opus`). Unset by default — role
sessions then run on the CLI's default model. Does not affect the
`doctor()` haiku probe, which always hardcodes its own cheap model.

Rulebooks and tokenmaxxxer-core need NO manual clones: spawn fetches and
ff-updates them under `muster/runs/rulebooks/` automatically (a local
checkout, if present, wins — that is the development override).

Once, per target repo — and the orchestrator offers to do all of it in
conversation when it finds a piece missing:

1. A GitHub remote (`gh repo create --private --source . --push` if
   local-only).
2. `docs/specs/approvers.md` — the approver allowlist (and board opt-in).
   `python3 muster/spawn.py init -C <repo>` writes it from your gh login,
   or the orchestrate session creates it for you after confirming.
3. (Recommended) branch protection on main: PRs required. (Only with the
   optional agent account: invite it as a collaborator.)

Then everything is conversation: `/orchestrate:run`.

v3 notes: the board is `docs/issue-<n>/reports/<role>.md` in the target
repo, `main`-merged only; the canonical contract lives ONLY in
tokenmaxxxer-core — repos carry no copy; the board marker is
docs/specs/approvers.md (`spawn.py init` writes it);
`spawn.py approve` is gone — approval is a GitHub act the orchestrator
relays; core's four plugins (core/terse/freelunch/scout) attach to every
role session via --plugin-dir.

## Why this exists

Editing a repository's `.claude/settings.json` applies to **every** agent working in
that repository — the coding agent ends up reading the QA rulebook too. The boundary
of plugin scoping is the **session**, so the only way to give a role its own
environment is to start its own session. That is muster.

## Roles

A role file records the marketplace and the boundary, nothing else. `spawn.py` expands
the plugin list by reading that rulebook's `marketplace.json`, so a rulebook can add a
plugin without anyone editing a role file.

**Enabling only the `<role>-agent-env` bundle does not work.** A bundle's
`dependencies` are not resolved through `--settings`' `enabledPlugins` (measured A/B:
the bundle-only session never ran doctrine's SessionStart hook and grew no `docs/`
buckets; the session that enabled each plugin individually did). Taking "the bundle is
enabled" as proof is how **a session running zero rulebooks gets recorded as a
success** — which contaminates an ablation outright.

| role | rulebook | decides |
|---|---|---|
| product | tokenmaxxxer-product | what to build |
| feasibility | tokenmaxxxer-feasibility | whether it can be built, from the spec alone, with no market reasoning |
| coding | tokenmaxxxer-coding | builds it — `build-proposal`, `loop_state: proposed,approved,landed` |
| review | tokenmaxxxer-review | whether it matches the spec, requirement by requirement |
| qa | tokenmaxxxer-qa | whether it actually runs |
| ux-design | tokenmaxxxer-ux-design | what it should look like to use |
| verify | tokenmaxxxer-verify | whether coding's and qa's artifacts agree |
| reflect | tokenmaxxxer-reflect | what the round taught, once it landed |
| ops | tokenmaxxxer-ops | ships it and keeps it up |

## Using it

### Installing

```
/plugin marketplace add tokenmaxxxer/muster
/plugin install orchestrate@tokenmaxxxer-muster
```

That is the whole install for `orchestrate`. `muster`'s own marketplace also lists
every rulebook plugin from all nine role rulebooks, each sourced straight from its
own GitHub repo (`{"source": "github", "repo": "tokenmaxxxer/<repo>"}`) — so
`claude plugin install <plugin>@tokenmaxxxer-muster` resolves any of them (say
`coding-cycle`, `freelunch`, `qa-cycle`) directly, without adding all nine
rulebook repos as separate marketplaces one at a time. No local clone of any
rulebook is required for this: the rulebooks are **not** cloned by hand — each
role file names its repo, and the first spawn of a role fetches that rulebook's
marketplace if it is not already on the machine. Private repos work — the fetch
uses the git credentials already in place.

This install-from-`muster`'s-marketplace path is a separate, optional route from
`spawn.py`'s own per-role fetch above — `spawn.py` warms its own marketplace
registration on first spawn and needs no marketplace add at all. Use `claude
plugin install <plugin>@tokenmaxxxer-muster` only when you want a rulebook
plugin installed and browsable outside of `spawn.py`.

**This listing resolves the install, not ongoing updates.** Per the measured
behavior below (`claude plugin update` compares only the pinned `version`
string and every rulebook sits at 0.1.0 forever), installing through
`tokenmaxxxer-muster` does not make `claude plugin update` refresh a
GitHub-sourced rulebook from remote HEAD either. Refreshing an installed
rulebook still goes through `spawn.py update <role>` (or a reinstall).

A local checkout still wins when one exists. `roles/<role>.json` keeps an optional
`path`, and if that directory holds a `.claude-plugin/marketplace.json` it is used
instead of the remote — so editing a rulebook and running it through muster does
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
<plugin>@tokenmaxxxer-muster` above. Set it only to work on a rulebook's own
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
  at all while muster reports it as present. Delete the named entry.
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
$ python3 spawn.py product "…" -C ~/work/new-app
대상 레포에 docs/specs/approvers.md 가 없다: …
```

Seed it once per project (`init` uses your gh login, or pass `--login`):

```bash
python3 spawn.py init -C ~/work/new-app
```

This is **the only thing muster writes into someone else's repository** —
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
the coding role for a one-off change, say). It is a flag rather than a warning
because the failure it prevents is silent, and a warning on stderr in a headless
run is not read.

### The loop

One call runs one role. After it, ask the board who is up next; `wake` evaluates
contract §3's WAKES-ON table and names them.

```bash
python3 spawn.py product "build me a car-wash timing app" -C ~/work/new-app
python3 spawn.py wake -C ~/work/new-app
#   [feasibility] hypothesis docs/proposals/…md — feasibility has not read it yet
python3 spawn.py feasibility "the board woke you. …" -C ~/work/new-app
python3 spawn.py wake -C ~/work/new-app
#   nothing standing — feasibility acknowledged it and is mid-work
```

**A board that has not changed wakes nobody** (contract §6). That is what ends the
qa↔coding cycle rather than letting it ping-pong.

`wake` reports; it does not spawn. Two of the six rows are content judgments —
product's ("does this question the acceptance criteria") and ops's ("is this ready
to roll out") — so they are printed as *not evaluated*, never as *did not fire*.

### From a conversation

Calling it from a conversation is the default. No separate trigger was built — the
place where work gets handed over is already the conversation.

```
/plugin marketplace add tokenmaxxxer/muster
/plugin install orchestrate@tokenmaxxxer-muster

/orchestrate:run                          just show the current state
/orchestrate:run qa /testrun:testrun smoke
```

### Every command

```bash
python3 spawn.py                              # read the board (read-only)
python3 spawn.py wake                         # who does the board wake? (contract §3)
python3 spawn.py <role> "<task>" -C <repo>    # bring up that role
python3 spawn.py <role> "x" --dry-run         # print the merged settings only
python3 spawn.py <role> "x" --no-contract     # skip the contract precondition
python3 spawn.py <role> "x" --unattended      # human absent: mint off, human gates stand
python3 spawn.py doctor                       # measure hook firing on this CLI (once per version)
python3 spawn.py drive -C <repo>              # run whoever the board names, one at a time, until it stops
python3 spawn.py approve <kind> --subject <s> # mint an approval token yourself (needs a TTY)
python3 spawn.py wake --all                   # include the rows already answered
```

Authentication uses whatever is already logged in. No token, no secret.

### When a session ends

Every spawn captures the session's result JSON, appends one line to muster's
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

### Where a run stops on purpose

Two halts are the contract working, not failures to route around:

- **coding, at `proposed → approved`.** Contract §8 reserves approving scope changes
  for a human. A headless run stops there and waits.
- **any role, on a first read of an upstream artifact.** Contract §12 makes the role
  ask once, by name, before acting on it — and forbids guessing the answer.

## Isolation — a sandbox, not a container

Claude Code's Bash sandbox gives us more of what we need than a container does, and on
macOS it is Seatbelt, so there is nothing to install.

| requirement | container (hosted CI) | Bash sandbox |
|---|---|---|
| egress control | **not possible** (`--network` unsupported) | `network.allowedDomains` |
| credential isolation | secrets injected explicitly | `credentials.envVars` masking plus `injectHosts` |
| filesystem boundary | the container edge | `filesystem.denyRead/allowWrite`, enforced by the OS |
| authentication | needs its own token secret | **whatever is already logged in** |

## Three traps, each one measured

**① `--settings` merges, it does not replace.** A role file naming only the qa rulebook
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

**Trade-off, explicit:** the cache mount is read-only and low-risk — a
compromised build step can read stale packages but cannot write back to the
host cache. The registry allowlist is higher but bounded risk: it reopens
outbound network to a fixed set of hosts, and package install is a
code-execution path, so anything reachable through the allowlist can pull and
run arbitrary published code from that registry. This is accepted
deliberately, scoped to official registries only — no wildcards, no mirrors,
no CDNs beyond the registry's own asset host.

## Gates

After a session ends, look deterministically at **what that session touched.** Zero LLM
calls.

```
[gate] needs a look:
  - protected path changed: .env
  - package does not exist: lodahs (package.json)
```

**It does not block** — the writes already happened and cannot be taken back, and muster
does not adjudicate. It also does not wave anything through. When the check itself is
impossible (not a git repository, no default branch) it reports **"cannot check"**, not
"nothing found" — those two deserve opposite treatment.

The comparison base is the default branch `origin/HEAD` points at. `GATE_BASE` overrides it.

## Self-check

```bash
python3 test_gates.py
```

## Open

- **Carrying one subject end to end with the driver.** `spawn.py drive` exists, but
  only single-role turns have been measured. Walk a full multi-role round by hand
  before letting it run long — every step so far has surfaced something a loop
  would have swallowed.
- **Six gate families still live once per rulebook.** `state-gate.sh` exists seven
  times and all seven differ. core holds consent and the board gate today; lifting
  the rest in, with their transition tables as data, has not started.
- **Contract §3's table disagrees with §5.** §5 says every role wakes on a finding
  addressed to it; the table names findings only in coding's row. `wakes.py`
  follows §5 — the table alone would leave findings addressed to anyone else unseen.
- **Scoring is manual.** Whether a finding hit an answer-key entry is adjudicated by
  a person (the key's adjudication clause). The runner only builds the scoresheet —
  imitating automatic adjudication is how the ledger starts lying.
