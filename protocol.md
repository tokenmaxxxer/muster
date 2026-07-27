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

## 2. The state-exposure contract — muster does not own it

**`docs/specs/role-handoff-contract.md` (v2, `status: final`) is the authority
here, not this document.** It lives in `review-agent-rulebook` and defines the
shared record format for all six roles. What follows is only what muster needs
in order to read the board; where the two disagree, the contract wins.

The board is fully in-repo (contract §10): every role writes one status record
at `docs/reports/records/<subject>/<role>.md`, inside doctrine's `reports`
bucket. muster reads the frontmatter and nothing else.

```yaml
kind: feasibility-record
subject: 2026-07-26-car-wash
produced_by: feasibility
loop_state: verdict
verdict: go
```

`loop_state` (contract §7) is **the one field of a role's state machine other
roles may depend on.** A role's internal sub-states are its own business and
muster must not try to infer them.

Two things muster's reader has to get right, both named by the contract:

- **Trailing comments are legal** (§2): `kind: build-proposal  # re-scoped`. A
  parser that cannot read them is *a gate defect, not a violation by the
  record's author.*
- **A per-repo identifier is the repo's directory name** (§9). v1 derived
  `<owner>-<repo>` from the git remote; that existed only for the now-abolished
  `$QA_WORKSPACE` path, and the directory name is what keeps a remoteless repo
  working.

**Three rules**

1. A record is written by **exactly one role** (contract §11's ownership table).
2. Transition control belongs to that role's own gate. Not to muster.
3. **muster is read-only.** To move state, call that role's command.

### Transition state, stated plainly

The contract's own text says landing it in each rulebook is separate work, "one
proposal per repo" — and as of 2026-07-27 **all eight rulebooks have landed it:
every repository has a v2 board.** muster reads the v2 board first and, if a
given repo somehow still lacks one, falls back to the v1 locations
(`review-record.md`, `feasibility-record.md`, `state.md`, `product-record.md`)
— not to use them, but to say *"this repo has not moved to v2 yet"* instead of
the flat "nothing in progress" that a v1 repo would otherwise get. **A false
quiet is the failure mode being avoided.**

`roles/qa.json` no longer carries `QA_WORKSPACE` or a sandbox `allowWrite`
scoped to it. Contract §10 abolished that external tree, and the qa rulebook
has since landed v2: qa's evidence — intake profile, bug reports, regression
records, run stats — now lives entirely inside the target repo, under
`docs/reports/records/<subject>/qa.md` and `docs/reports/records/<subject>/qa/**`,
the same place every other role's record lives. qa's scratch space for a run
is whatever session-scoped temp directory the run already has; no dedicated
external workspace and no role-file default are needed for it.

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

`muster`'s own marketplace (`.claude-plugin/marketplace.json`) also lists every
rulebook plugin from all nine role rulebooks, each with a GitHub `source`
(`{"source": "github", "repo": "tokenmaxxxer/<repo>"}`), alongside the local
`orchestrate` entry. This is a second install path for consumers who want
`claude plugin install <plugin>@tokenmaxxxer-muster` to resolve a rulebook
plugin directly — it does not change how `spawn.py` locates a role's rulebook
above, and it does not make `claude plugin update` refresh a GitHub-sourced
plugin from remote HEAD (that still goes through `spawn.py update <role>`, or
a reinstall). No local clone of any rulebook, and no `TOKENMAXXXER_RULEBOOKS`,
is required for either path.

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
cannot mint its own approval."**

**Whether an agent may ever hold that seat is settled elsewhere, and currently
settled as no.** Contract §8 ("The human's seat") names four judgment points
reserved for a human — minting or retiring a `subject`, the verdict tokens the
contract reserves (qa's is-this-a-defect call), resolving cross-role disputes,
and **approving scope changes**. warrant halting a headless coding run at
`proposed → approved` is that clause being honoured, not a defect.

> ⚠️ Moving any of those four to an agent is an amendment to the handoff
> contract, decided there. muster must not route around it, and neither must a
> single rulebook's hook. A proposal that tried exactly that was withdrawn on
> 2026-07-26.

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

- **A WAKES-ON watcher** — contract §3 names "a future automated watcher, if one
  is built" as the thing that could carry the table instead of a human. That is
  muster's job, and it implements §3's table rather than inventing a schedule.
  Now that all eight rulebooks have a board, this is buildable but not yet
  built.
- **What calls muster** — a person directly, cron, or an issue webhook. For
  stages 1–2 a person is enough. No long-running process is being built.
