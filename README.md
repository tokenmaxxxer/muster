# tokenmaxxxer / muster

*[한국어](README.ko.md)*

Musters a role — brings up one sandboxed session with only that role's rulebook installed.

Not a dispatcher. A power outlet. **Each role owns its state; muster only reads it.**

```
protocol.md   the contract — muster's three jobs, the state-exposure deal, isolation
              (protocol.ko.md is the same contract in Korean)
roles/        one role is one file: rulebook bundle plus sandbox boundary
spawn.py      reads state, brings up a session in a role's environment
orchestrate/  the plugin that calls it from a conversation (/orchestrate:run)
bench/        ablation runner — same target, rulebook on and off
gates/        deterministic checks, run by spawn.py after a session. Zero LLM calls
ledger/       the scorecard
```

*On the name: this was `harness`, but in this organisation "harness" already means
the rulebook stack and `qa-agent-rulebook/bench`. Names that collide make documents
unable to point at each other.*

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
| coding | tokenmaxxxer-coding | builds it (steering only, no state machine) |
| review | tokenmaxxxer-review | whether it matches the spec, requirement by requirement |
| qa | tokenmaxxxer-qa | whether it actually runs |
| ops | tokenmaxxxer-ops | ships it and keeps it up |

## Using it

Calling it from a conversation is the default. No separate trigger was built — the
place where work gets handed over is already the conversation.

```
/plugin marketplace add tokenmaxxxer/muster
/plugin install orchestrate@tokenmaxxxer-muster

/orchestrate:run                          just show the current state
/orchestrate:run qa /testrun:testrun smoke
```

From a shell:

```bash
python3 spawn.py                              # read state (read-only)
python3 spawn.py qa "/testrun:testrun smoke" -C ~/work/some-repo
python3 spawn.py review "x" --dry-run         # print the merged settings only
```

Authentication uses whatever is already logged in. No token, no secret.

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

- **`warrant`'s approval gate blocks headless runs (reproduced).** With the coding
  rulebook enabled, work stops at the pre-start approval, and a headless session has
  nobody to approve. `review-cycle` and `qa-cycle` already show the shape of the answer:
  a working session cannot mint its own approval and only accepts a single-use token
  issued from the user's turn. Applying that pattern to warrant resolves it, but that is
  the rulebook owner's call.
- **The coding rulebook has no state machine.** The other five roles were promoted to
  `<role>-cycle`.
- **Scoring is manual.** Whether a finding hit an answer-key entry is adjudicated by a
  person (the key's adjudication clause). The runner only builds the scoresheet —
  imitating automatic adjudication is how the ledger starts lying.
