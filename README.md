# tokenmaxxxer / on-the-record

*[한국어](README.ko.md)*

## Five walls every solo AI-coding user hits

1. **Vibe coding drifts.** One long chat session runs for hours; context
   rots, early requirements get forgotten, and the codebase ends up in a
   state nobody — including the user who asked for it — still understands.
2. **Quality is a coin flip.** Some sessions land great work, some land
   sloppy work, and nothing gates an agent from committing unverified
   changes either way.
3. **You repeat yourself every session.** Working rules — "tests first,"
   "write the design doc before the code" — have to be re-taught from
   scratch each time, because nothing carries them forward.
4. **Nothing is handover-able.** Requirements, decisions, and history live
   only in a chat log. Nobody — not a teammate, not future-you — can onboard
   onto the work or audit how it got there.
5. **Parallel agents collide.** Run more than one agent at a time and there
   is no isolation and no merge discipline, so their work steps on itself.

## Other AI works off the record. Yours works on the record.

Every piece of work on-the-record produces becomes an official git record:
**requirements are issues, work arrives as PRs, decisions are recorded
approvals, rules are versioned rulebooks.** Nothing here lives only in a
chat transcript.

That is what turns AI output into something trustworthy, handover-able, and
sellable-grade — not just demo-grade:

- **Role experts, clean context per task.** Each role gets its own
  sandboxed session with only that role's rulebook loaded — no context
  bleed from an execution-observation rulebook into an implementation session, or vice versa.
- **The process asset lives in git.** Rulebooks are versioned files a
  better model can pick up and run immediately, with nothing re-taught.
- **The user stays the sole approver.** Nothing merges without the user's
  own GitHub account approving it — the CEO position, not a bystander.
- **Self-contained.** One plugin installs the whole system; nothing else to
  wire up.

Everything below this point is how that promise is actually implemented —
supporting detail, not the pitch.

Musters a role — brings up one sandboxed session with only that role's
rulebook and the tokenmaxxxer-core plugins installed.

Not a dispatcher. A power outlet with a concierge: on contract v3 the
orchestration session (this marketplace's `on-the-record` plugin) talks to
the user, drafts issues the user dictates, spawns role sessions, explains
the PRs that come back, and relays the user's decisions — comments,
review Approve, merge — with the user's own account. Role sessions run on
the AGENT account (`MUSTER_AGENT_GH_TOKEN`), work on `issue-<n>/<role>`
branches, and return everything by PR. **Each role owns its state; on-the-record
only reads it.**

```
protocol.md   the contract — on-the-record's three jobs, the state-exposure deal, isolation
roles/        one role is one file: rulebook bundle plus sandbox boundary
spawn.py      reads state, brings up a session in a role's environment
              (--issue <n> creates the branch and anchors the prompt)
on-the-record/  the plugin that drives the loop from a conversation (/on-the-record:run)
gates/        deterministic checks, run by spawn.py after a session. Zero LLM calls
ledger/       the scorecard
```

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

## Why this exists

Editing a repository's `.claude/settings.json` applies to **every** agent working in
that repository — the implementation agent ends up reading the execution-observation rulebook too. The boundary
of plugin scoping is the **session**, so the only way to give a role its own
environment is to start its own session. That is on-the-record.

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
| product-discovery | tokenmaxxxer-product-discovery | what to build |
| technical-feasibility | tokenmaxxxer-technical-feasibility | whether it can be built, from the spec alone, with no market reasoning |
| implementation | tokenmaxxxer-implementation | builds it — `build-proposal`, `loop_state: proposed,approved,landed` |
| conformance-review | tokenmaxxxer-conformance-review | whether it matches the spec, requirement by requirement |
| execution-observation | tokenmaxxxer-execution-observation | whether it actually runs |
| interaction-design | tokenmaxxxer-interaction-design | what it should look like to use |
| defect-verification | tokenmaxxxer-defect-verification | whether implementation's and execution-observation's artifacts agree |
| issue-retrospective | tokenmaxxxer-issue-retrospective | what the round taught, once it landed |
| release-engineering | tokenmaxxxer-release-engineering | ships it and keeps it up |

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

### Where a run stops on purpose

Two halts are the contract working, not failures to route around:

- **implementation, at `proposed → approved`.** Contract §8 reserves approving scope
  changes for a human. A headless run stops there and waits.
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

## Self-check

```bash
python3 test_gates.py
```

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
