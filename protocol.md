# protocol — the agent contract

*[한국어](protocol.ko.md)*

*Second design, 2026-07-25. A contract people and agents read together.
The reasoning behind it is in `orchestrator-design-2026-07.md`.*

## On one page

```
                    person
                     │  "take this on"
                     ▼
              ┌─────────────┐
              │   muster    │   **reads** state, picks a role, brings up its environment
              └──────┬──────┘   never writes state
         ┌───────────┼───────────┐
         ▼           ▼           ▼
      coding        qa        review      ← each owns its own state machine
   (plugin set)  (plugin set) (plugin set)   "this is my turn, this is my step"
```

**State belongs to the agent.** muster queries it and never writes it.

The first design put a label state machine inside muster. That creates two
sources of truth, and worse, muster's label transitions **bypass the agent's own
transition gate** — `qa-cycle` can intercept a write to `state.md` and refuse it,
but a label never passes that gatekeeper. That state machine was removed.

## 1. What muster does — three things

**① Query state.** Read what each agent exposes. Never write it.

**② Pick a role.** Decide which role an event should wake.

**③ Spawn an environment.** Bring up a headless session carrying that role's
plugin set and boundary.

Anything muster starts knowing beyond these three is the design leaking. "Which
step QA is on" is fine to know; "why it is on that step" must not be.

## 2. The state-exposure contract

Each agent exposes its state in **one readable place**. The format is markdown
with YAML frontmatter (the format `qa-cycle` already uses).

```yaml
---
phase: session-executed
updated_by: testrun
transition: session-chartered -> session-executed
evidence: runs/2026-07-25-smoke.md
---
```

There are two conventions. **Most cycles keep their record in the project
directory; only qa uses a central workspace** — qa tracks many projects from one
place.

| role | where state lives |
|---|---|
| qa | `$QA_WORKSPACE/projects/<owner>-<repo>/state.md` |
| review | `<project>/review-record.md` (overridden by `REVIEW_RECORD_NAME`) |
| feasibility | `<project>/feasibility-record.md` |
| ops | `<project>/state.md` |
| product | `<project>/product-record.md` |
| coding | **none** — never promoted to a state machine. It only steers |

**Three rules**

1. A state file is written by **exactly one plugin**. `qa-cycle` is the sole
   owner of `state.md`.
2. Transition control belongs to that plugin's `PreToolUse` gate. Not to muster.
3. **muster is read-only.** To move state, call that role's command.

## 3. A role is a plugin set plus a boundary

One role is one `roles/<name>.json`. It carries **only the rulebook and the
boundary**; `spawn.py` expands the plugin list by reading that rulebook's
`marketplace.json`.

```json
{ "marketplace": "tokenmaxxxer-qa",
  "path": "…/qa-agent-rulebook",
  "sandbox": { "network": {…}, "filesystem": {…}, "credentials": {…} } }
```

This is **why an orchestrator was needed in the first place.** Editing a
repository's `.claude/settings.json` applies to **every** agent working in that
repository, so the coding agent ends up reading the QA rulebook too. A
per-role environment can only be drawn at the session boundary — which is why
each role gets its own session.

### Three traps, each one measured

**① `--settings` merges, it does not replace.** A role file naming only the qa
rulebook still arrives with the user's global plugins attached. Isolation only
holds if you read the global list and override everything the role did not
enable to `false`.

**② Enabling only the `<role>-agent-env` bundle attaches no rulebook.** A
bundle's `dependencies` are not resolved through `--settings`' `enabledPlugins`.
A/B: the bundle-only session never ran doctrine's SessionStart hook, so no
`docs/` buckets appeared; the session that enabled each plugin individually grew
them. **Taking "the bundle is enabled" as proof is how a session running zero
rulebooks gets mistaken for a success** — which contaminates an ablation
wholesale.

**③ The first spawn only registers the marketplace.** Plugins attach from the
next run onward. `spawn.py` verifies installation and stops if anything is
missing.

## 4. Isolation — a sandbox, not a container

No containers. Claude Code's Bash sandbox **gives us more of what we need**, and
on macOS it is Seatbelt, so there is nothing to install.

| requirement | container (hosted CI) | Bash sandbox |
|---|---|---|
| egress control | **not possible** (`--network` unsupported) | `network.allowedDomains` |
| credential isolation | secrets injected explicitly | `credentials.envVars` masking plus `injectHosts` |
| filesystem boundary | the container edge | `filesystem.denyRead/allowWrite`, OS-enforced |
| covers child processes | ✓ | ✓ (at the OS level) |
| authentication | needs its own token secret | **the keychain OAuth already there** |

The last row decides it. A CI container needs `CLAUDE_CODE_OAUTH_TOKEN` as a
secret; a local spawn uses credentials that are already logged in. **The
authentication problem disappears.**

`sandbox.credentials.envVars` structurally closes one unsolved defect from the
first design — clearing worker env by denylist (one missed name and it leaks)
becomes masking plus host-scoped injection.

**Careful**: turning off the filesystem layer with `filesystem.disabled: true`
lets a command inside the sandbox edit `~/.claude/settings.json` or an
executable on `$PATH` and **widen its own permissions on the next run.** Leave
it on.

## 5. Approval — tokens

`qa-cycle`'s four human-only transitions (`Confirmed-Defect`, `Go`, `No-Go`,
`Shipped-Under-Exception`) require a verdict token minted by `signoff`, and the
token is consumed the moment it passes.

What a token actually guarantees is not "a human did this" but **"an actor
cannot mint its own approval."** That property survives replacing the approver
with a **review agent in a separate context** — the approving session is a
different process, a different plugin set, a different context from the working
one.

> ⚠️ This would change `qa-cycle`'s design intent (human-only). Changing it means
> changing `docs/specs/qa-cycle-state-machine.md` and `signoff` together, and
> that is the rulebook owner's decision. muster must not route around it.

## 6. Invariants

1. **muster never writes state.** It reads, picks a role, and brings it up.
2. **A state file is written by exactly one plugin.** Transition control belongs
   to that plugin's gate.
3. **Every role gets its own session,** because the session is the boundary of
   plugin scoping.
4. **An actor cannot mint its own approval.** Only a separate session in a
   separate context can.
5. **Untrusted values are never interpolated into a shell.** A `$(…)` in an
   issue title executes — and anyone can open an issue, so that is remote code
   execution. Pass through env and quote.
6. **Retries are idempotent.** Every attempt starts fresh from base plus the
   contract.
7. **`filesystem.disabled` stays off.** The sandbox could widen its own
   permissions.

## 7. Shipping order

| # | what | what it proves |
|---|---|---|
| 1 | `roles/*.json` plus one spawn | that per-role plugin environments really do differ |
| 2 | query state → pick a role | that muster can dispatch without knowing an agent's internals |
| 3 | qa bench on/off | that the rulebook earns its keep — the organisation's first measurement |
| 4 | more trigger sources (issues, alerts) | that events arrive without passing through a person |
| 5 | an approving agent | a token minted by a separate context |

## 8. Unsettled

- **State exposure for the coding rulebook** — there is no state machine today.
  Whether it needs a promotion like `qa-cycle`'s, or whether coding is right to
  run stateless, is undecided.
- **Moving the approver to an LLM** — see §5. The rulebook owner's decision.
- **What calls muster** — a person directly, cron, or an issue webhook. For
  stages 1–2 a person is enough. No long-running process is being built.
