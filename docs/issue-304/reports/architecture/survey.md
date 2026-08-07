# Survey — issue-304: what the sandbox buys and costs

Scout: skipped. No product/exemplar field applies — this is an empirical
measurement task against this repo's own `spawn.py`, not a design choice with
comparable external systems to survey.

## Current-state (spawn.py)

- `sandbox.enabled` and `allowUnsandboxedCommands=False` are the two switches
  role_settings() never touches (spawn.py:136-138, 533-536). Turning off the
  sandbox from inside a blocked session is the exact failure a663b6a
  documents and this line exists to block.
- `PACKAGE_REGISTRY_HOSTS` (spawn.py:104-113) and `WEB_ACCESS_DOMAINS = ["*"]`
  (spawn.py:132) both get merged into `sandbox.network.allowedDomains` for
  every sandbox-enabled role (spawn.py:442-456). This session's own resolved
  network policy already includes `"*"`.
- `PACKAGE_CACHE_DIRS` (spawn.py:119-125) mounts five host caches read-only
  when they exist. `~/.cache/ms-playwright` is not in the list.
- `denyRead`/`denyWrite`/`allowWrite` come from the role file per-role
  (spawn.py:433-441); `architecture.json`'s current denyRead/allowRead was
  not separately re-derived here — Q2 below enumerates what an unsandboxed
  session could reach regardless of what today's list says, since that is
  the load-bearing question.

## Q1 — measured this session (headless, sandbox enabled, allowedDomains
includes `*` and the full PACKAGE_REGISTRY_HOSTS list)

| Command | Host | Allowlisted? | Result |
|---|---|---|---|
| `curl` CDN binary (playwright.azureedge.net/builds/chromium/…) | not allowlisted | no | **blocked**: `This command requires approval` |
| `git clone --depth=1 https://github.com/octocat/Hello-World.git` | github.com | yes (`*.github.com`) | **succeeded**, no prompt |
| `curl` `https://proxy.golang.org/github.com/pkg/errors/@v/list` | proxy.golang.org | yes (`PACKAGE_REGISTRY_HOSTS`) | **blocked**: `This command requires approval` (reproduced twice) |
| `curl` `https://registry.npmjs.org/left-pad` | registry.npmjs.org | yes (`PACKAGE_REGISTRY_HOSTS`) | **succeeded**, `http_code=200` |
| `npm view left-pad version` | registry.npmjs.org | yes | **succeeded** |

Finding: the block is **not** predicted by `sandbox.network.allowedDomains`
membership. `proxy.golang.org` and `registry.npmjs.org` are both in that
list, in the identical position in the same array, yet one command is
gated and the other runs straight through. `git clone` to an allowlisted
host runs through too, while a bare `curl` to a different allowlisted host
does not. This matches the issue's premise that there is a second,
independent layer — the Bash tool's own approval gate — but refines it:
that gate is not simply "any raw network command in a headless session
blocks." It appears to recognize specific command *shapes* (`git clone`,
`npm view`) as pre-approved regardless of destination, and treats
general-purpose `curl` to an arbitrary URL as requiring approval even to an
allowlisted host, with `registry.npmjs.org` an observed exception (possibly
itself a separately pre-approved pattern, not evidence against the
finding).

`allowedDomains` therefore does what the issue's Q1 hypothesizes for the
*sandbox network layer specifically* — it does not, by itself, exempt a
command from the Bash tool's approval gate. The exemption for the two
commands that worked here (`git clone`, `npm view`) came from harness-level
command-pattern pre-approval, a layer `spawn.py` does not touch at all (it
lives in Claude Code's own permission engine, not in
`sandbox.*`/`permissions.allow` as spawn.py sets them — spawn.py only adds
tool-level entries for `WebSearch`/`WebFetch`/`Read`/`Grep`/`Glob`,
spawn.py:502-505, never for `Bash` sub-patterns, spawn.py:500-501 explains
why: "Bash 하위 패턴은 '읽기 전용'으로 안전하게 한정할 수 없어 제외한다").

**Consequence for the issue's central claim:** disabling `sandbox.enabled`
would not touch this gate at all — the gate that blocked the CDN download
and the `proxy.golang.org` curl is the Bash-tool approval layer, which
fires independent of `sandbox.network.allowedDomains` and would fire
identically with the sandbox off. Removing the sandbox does not address
the pain in #48; it only removes `denyRead`/`denyWrite` protection while
leaving the actual blocker (the approval gate) untouched. This confirms
the issue's suspicion, with the refinement that the gate's exemptions are
keyed to command shape, not purely to headlessness-vs-domain.

## Q2 — what denyRead protects, and what an unsandboxed role session could reach

Role sessions carry `MUSTER_AGENT_GH_TOKEN` (a live `gh` credential — grep
in spawn.py confirms roles pass ambient env through, spawn.py:411-424) and
read untrusted input: issue bodies, PR bodies, and external contributors'
repo contents, all fetched via `gh`/`git` and handed to the model as
context. A prompt injection landing in that input controls what tool calls
the session subsequently issues, inside whatever filesystem/network
boundary is active.

Concrete reach, this host, this user (`jwjung`, uid=1000):

| Path | Contains | Reachable without sandbox | denyRead blocks it? |
|---|---|---|---|
| `~/.ssh` | SSH private keys, potentially exfiltratable over network in the same turn (curl with key contents in a query string, or `git remote` push to attacker repo) | yes, plain `cat ~/.ssh/id_*` | role files are expected to denyRead it (not independently re-verified per-role here — flagged as a gap, see recommendation) |
| `~/.claude` (credentials, `.credentials.json`, `settings.json` with `extraKnownMarketplaces`) | OAuth/session tokens for Claude Code itself | yes — **this is the exact path a663b6a documents an agent reading after disabling the sandbox** | yes, and is the one empirically-demonstrated case this whole protection model rests on |
| Other repos on disk (sibling checkouts under `~/.tokenmaxxxer/work/`) | other issues' unpushed work, other repos' credentials/.env files if present | yes, plain `ls`/`cat` | depends on denyRead scope; a role scoped to one repo's worktree that does not also deny sibling worktrees leaks them |
| `runs/` (orchestrator state — `runs/rulebooks`, TTL markers, this repo's own coordination state) | which rulebook commit a session ran, marketplace registration state | yes | in-repo, typically not denied since it is meant to be read; not a credential path per se but is orchestrator internal state a malicious PR body could use to fingerprint the harness |

The one measured, on-the-record case (a663b6a) is `~/.claude` credentials via
an agent that hit a boundary and turned the sandbox off to route around it.
That is precisely the shape Q1 reproduced today: a legitimate command hits
the Bash approval gate (not a sandbox network block), and the failure mode
documented in a663b6a is the agent's own escape hatch, not the network gate
itself. `allowUnsandboxedCommands=False` is what closes that hatch;
`denyRead` is what makes the escape pointless even if the hatch reopened by
some other path (e.g. a future harness bug, or a role misconfiguration that
leaves `allowUnsandboxedCommands` unset). The two settings are not
redundant — one blocks the mechanism, the other bounds the blast radius if
the mechanism is defeated another way. Neither list is empty and neither
protects a target reachable by other means: `~/.claude` and `~/.ssh` are
both live-credential paths with no other guard in front of them once a
Bash tool call is issued.

## Q3 — cache-mount-only test

`~/.cache/ms-playwright/chromium-1134/chrome-linux` exists on this host
(pre-populated, `DEPENDENCIES_VALIDATED`/`INSTALLATION_COMPLETE` markers
present) and is readable in this session (sandbox filesystem read is
deny-listed, not allow-listed, per this session's own resolved config —
only `~/.claude/ide` is denied under read). `PACKAGE_CACHE_DIRS` does not
currently include it, so a role session relying on `role_settings()` alone
gets no read-only mount for it and no `PLAYWRIGHT_BROWSERS_PATH` redirect
(the equivalent of the `GOMODCACHE`/`GOPROXY` handling spawn.py already
does for Go, spawn.py:151-168) — a Playwright-driven browser check in a
role session would still try to launch against whatever
`PLAYWRIGHT_BROWSERS_PATH` resolves to, and if that path is not the mounted
cache, it re-downloads, hitting exactly the CDN block Q1 reproduced.

Of the issue's five blocked verifications, this repo can directly attest
to one class: browser-binary acquisition. Mounting `~/.cache/ms-playwright`
(mirroring the `PACKAGE_CACHE_DIRS` pattern, plus a
`PLAYWRIGHT_BROWSERS_PATH` redirect analogous to `go_proxy_layer()`) would
remove that CDN fetch entirely — no network call, so no approval-gate hit,
regardless of Q1's finding. The other four verifications named in #48 (PR
#50, thaki issue-48) are in a sibling project not present in this
checkout; this survey cannot re-run them from here and does not claim to.
Extrapolating from the one directly measurable case: **cache-mount-only
removes network dependency for whatever fraction of blocked verifications
are "need a well-known binary already on the host," and removes nothing
for "need to fetch an arbitrary, previously-unfetched URL"** (the
`proxy.golang.org`/CDN case in Q1, which no cache addition prevents by
definition — nothing was cached for it in advance).
