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
              │   on-the-record    │   **reads** state, picks a role, brings up its environment
              └──────┬──────┘   never writes state
         ┌───────────┼───────────┐
         ▼           ▼           ▼
      coding        qa        review      ← each owns its own state machine
   (plugin set)  (plugin set) (plugin set)   "this is my turn, this is my step"
```

**State belongs to the agent.** on-the-record queries it and never writes it.

The first design put a label state machine inside on-the-record. That creates two
sources of truth, and worse, on-the-record's label transitions **bypass the agent's own
transition gate** — `qa-cycle` can intercept a write to `state.md` and refuse it,
but a label never passes that gatekeeper. That state machine was removed.

## 1. What on-the-record does — three things

**① Query state.** Read what each agent exposes. Never write it.

**② Pick a role.** Who runs next is not a table lookup — it is a judgment
call made by reading the board directly (each subject's record and its
`loop_state`).

**③ Spawn an environment.** Bring up a headless session carrying that role's
plugin set and boundary.

Anything on-the-record starts knowing beyond these three is the design leaking. "Which
step QA is on" is fine to know; "why it is on that step" must not be.

## 2. The state-exposure contract — on-the-record does not own it

**The role-handoff contract (v3) is the authority here, not this document.**
It lives only in `core/contract/role-handoff-contract.md` in
`tokenmaxxxer-core` — repos carry no copy — and defines the shared record
format for all nine roles. What follows is only what on-the-record needs
in order to read the board; where the two disagree, the contract wins.

The board is fully in-repo (contract §10): every role writes one status record
at `docs/issue-<n>/reports/<role>.md`, `main`-merged only. The board opt-in
marker is `docs/specs/approvers.md`. on-the-record reads the frontmatter and
nothing else.

```yaml
kind: feasibility-record
subject: 2026-07-26-car-wash
produced_by: feasibility
loop_state: verdict
verdict: go
```

`loop_state` (contract §7) is **the one field of a role's state machine other
roles may depend on.** A role's internal sub-states are its own business and
on-the-record must not try to infer them.

Two things on-the-record's reader has to get right, both named by the contract:

- **Trailing comments are legal** (§2): `kind: build-proposal  # re-scoped`. A
  parser that cannot read them is *a gate defect, not a violation by the
  record's author.*
- **A per-repo identifier is the repo's directory name** (§9). v1 derived
  `<owner>-<repo>` from the git remote; that existed only for the now-abolished
  `$QA_WORKSPACE` path, and the directory name is what keeps a remoteless repo
  working.

**Three rules**

1. A record is written by **exactly one role** (contract §11's ownership table).
2. Transition control belongs to that role's own gate. Not to on-the-record.
3. **on-the-record is read-only.** To move state, call that role's command.

### Transition state, stated plainly

The contract's own text says landing it in each rulebook is separate work, "one
proposal per repo" — and as of 2026-07-27 **all nine rulebooks have landed it:
every repository has a v3 board.** on-the-record reads the v3 board first and, if a
given repo somehow still lacks one, falls back to the v1 locations
(`review-record.md`, `feasibility-record.md`, `state.md`, `product-record.md`)
— not to use them, but to say *"this repo has not moved to v3 yet"* instead of
the flat "nothing in progress" that a v1 repo would otherwise get. **A false
quiet is the failure mode being avoided.**

`roles/qa.json` no longer carries `QA_WORKSPACE` or a sandbox `allowWrite`
scoped to it. Contract §10 abolished that external tree, and the qa rulebook
has since landed v3: qa's evidence — intake profile, bug reports, regression
records, run stats — now lives entirely inside the target repo, under
`docs/issue-<n>/reports/qa.md` and `docs/issue-<n>/reports/qa/**`,
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

`on-the-record`'s own marketplace (`.claude-plugin/marketplace.json`) also lists every
rulebook plugin from all nine role rulebooks, each with a GitHub `source`
(`{"source": "github", "repo": "tokenmaxxxer/<repo>"}`), alongside the local
`on-the-record` entry. This is a second install path for consumers who want
`claude plugin install <plugin>@tokenmaxxxer` to resolve a rulebook
plugin directly — it does not change how `spawn.py` locates a role's rulebook
above, and it does not make `claude plugin update` refresh a GitHub-sourced
plugin from remote HEAD (that still goes through `spawn.py update <role>`, or
a reinstall). No local clone of any rulebook, and no `TOKENMAXXXER_RULEBOOKS`,
is required for either path.

### The boundary is bidirectional, and it is a gate — not just prose

A role's phase-2 deliverable must be of the kind its `produces` declares.
This runs both ways: a judgment role (feasibility/review/qa/verify/
product/ux-design/reflect/ops) never ships `src/`/`test/` implementation,
and coding never ships another role's verdict, spec, or record artifact.
When a role's work surfaces a genuine need for a different kind of
output, that need routes to the role that produces it — it is never
self-expanded inside the current session. A boundary-crossing need gets
recorded in the current role's own record and the session ends there;
the transition to the other role is an orchestrator-and-human call, not
something a role does to itself.

This is enforced structurally, not only by convention: each
`roles/<name>.json` declares a `write_scope` — the glob patterns its
phase-2 output may touch — and `gates/ci.py` checks every PR's diff
against the acting role's declared scope (role resolved from the PR's
`issue-<n>/<role>` branch name), blocking on mismatch. A board repo may
narrow or relocate a role's scope for its own layout via
`docs/specs/write_scope.md`, but every role's own record and proposal
paths (`docs/issue-*/reports/<role>.md`, `docs/issue-*/reports/<role>/**`,
`docs/issue-*/proposals/<role>.md`) stay writable regardless of any
override — the record-writing obligation is unconditional and survives
any scope tightening.

**Non-substitution.** A role's own self-test or confirmation pass (e.g.
coding's build-and-run-once) is a merge-decision input, never a
verification role's verdict. It tells the human "this is what I ran and
what happened"; it does not stand in for qa's execution, review's
requirements audit, or verify's independent reproduction.

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

No containers. Claude Code's Bash sandbox **gives us more of what we need**.

Per platform, stated rather than implied: on **macOS** it is Seatbelt and there
is nothing to install — that is where every measurement below was taken. On
**Linux** the driver runs (`bash`, `fork` and `flock` are all present) but the
sandbox and the credential store are **unmeasured**; treat the table below as
unverified there. **Native Windows is out of scope** — the enforcement plane is
`.sh` hooks and the driver forks, so `spawn.py` fails at import rather than
starting with no gates. Use WSL.

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

**Diagnose, don't delete**: a sandbox-denied write to `.git/config` can
surface as git's own `cannot lock config file .git/config: File exists` —
indistinguishable from real lock contention by wording alone (measured:
issue #289, three live sessions). A session that sees this should check for
the lock file from *outside* the sandbox (or ask `on-the-record`) before
removing anything, and should never `rm` a `*.lock` file as a first
response — against a genuine concurrent lock that reflex corrupts
`.git/config`. Same invariant as `allowUnsandboxedCommands = False` below:
a boundary denial is a signal to diagnose, not to route around.

## 5. Approval — a GitHub act

Approval is a GitHub act: an `APPROVED` PR review, or a comment that is
exactly `APPROVE issue-<n>/<role>`, from a login in
`docs/specs/approvers.md`. `gh-guard` keeps that honest in the default
single-account setup.

What that guarantees is not "a human did this" but **"an actor cannot approve
its own change."**

**Whether an agent may ever hold that seat is settled elsewhere, and currently
settled as no.** Contract §8 ("The human's seat") names four judgment points
reserved for a human — minting or retiring a `subject`, the approvals the
contract reserves (qa's is-this-a-defect call), resolving cross-role disputes,
and **approving scope changes**. warrant halting a headless coding run at
`proposed → approved` is that clause being honoured, not a defect.

> ⚠️ Moving any of those four to an agent is an amendment to the handoff
> contract, decided there. on-the-record must not route around it, and neither must a
> single rulebook's hook. A proposal that tried exactly that was withdrawn on
> 2026-07-26.

The canonical location for the `APPROVE issue-<n>/<role>` signal (contract v3
s19) is the **issue comment**, not a PR comment or PR review — role sessions
are told this at session start, and this repo's own relay instructions
(`on-the-record/commands/run.md`) and README follow the same canon. A PR
review Approve is only the two-account hardened alternative, when the
approving account differs from the PR's author. Location drift here already
caused one missed approval (issue-126); do not reintroduce a second signal
location without updating all three together.

## 6. Invariants

1. **on-the-record never writes state.** It reads, picks a role, and brings it up.
2. **A state file is written by exactly one plugin.** Transition control belongs
   to that plugin's gate.
3. **Every role gets its own session,** because the session is the boundary of
   plugin scoping.
4. **An actor cannot approve its own change.** Approval is a GitHub act — an
   `APPROVED` review or an `APPROVE issue-<n>/<role>` comment from a login in
   `approvers.md` — relayed by a separate session in a separate context.
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
| 2 | query state → pick a role | that on-the-record can dispatch without knowing an agent's internals |
| 3 | qa bench on/off | that the rulebook earns its keep — the organisation's first measurement |
| 4 | more trigger sources (issues, alerts) | that events arrive without passing through a person |
| 5 | an approving agent | a GitHub approval (review/comment) relayed by a separate context |

## 8. Unsettled

- **What calls on-the-record** — a person directly, cron, or an issue webhook. For
  stages 1–2 a person is enough. No long-running process is being built.
