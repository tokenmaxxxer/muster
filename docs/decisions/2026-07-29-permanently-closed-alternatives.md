---
kind: decision
date: 2026-07-29
status: landed
subject: issue-73
---

# Permanently closed alternatives

Extracted from `docs/superpowers/` before that directory is retired (see
`docs/decisions/2026-07-29-headless-cli-measured-facts.md` and issue #73).
Each entry is an alternative design that was considered and permanently
rejected, with its reason, cited to its `path:line` source inside
`docs/superpowers/`.

## MCP board server — rejected permanently

MCP tool use is voluntary: a session holding `Write`/`Edit`/`Bash` can bypass
any board server entirely, so the `PreToolUse` deny plane has to exist
regardless. An MCP board server would add a component while removing none,
and the contract's git-native properties (history, diffability, no separate
service to keep alive) would be lost or have to be reimplemented on top of
it.

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:146-153`
(also listed in the alternatives table at
`docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:26-32` and in
the roadmap's explicit deletions at
`docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:316-320`).

## stream-json as an approval channel — rejected

Every injected "user turn" over `stream-json` keep-alive is authored by
whichever process holds stdin, which is mechanically indistinguishable from
a human's own turn. That dissolves the exact trust premise the challenge
line exists to enforce. This was verified to work technically, and rejected
on trust grounds, not capability.

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:132-137`
(also in the roadmap's explicit deletions at
`docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:316-320`).

## `--bare` / `CLAUDE_CONFIG_DIR` isolation — rejected, re-confirmed dead

`--bare` never reads OAuth/keychain credentials and requires an
`ANTHROPIC_API_KEY`-style secret, which reintroduces the exact
credential-management problem that using the logged-in CLI was meant to
avoid.

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:26-32`
(re-confirmed dead in the roadmap's explicit deletions at
`docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:316-320`).

## The Agent SDK as driver — rejected

An Agent-SDK-driven session does not auto-enforce plugin hooks the way a
plugin-scoped CLI session does; one session plus native subagents per role
fails because plugin scoping is session-level and a subagent cannot carry a
different plugin set from its parent; "agent teams" was rejected as
experimental and opt-in behind an env var with no per-teammate plugin
scoping and no session resumption.

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:26-32`.

## Containers — rejected in favor of the Bash sandbox

A hosted-CI container cannot do egress control (`--network` is unsupported),
needs secrets injected explicitly for credential isolation, and needs its
own `CLAUDE_CODE_OAUTH_TOKEN` secret for authentication — where a local
Bash-sandboxed session gets `network.allowedDomains`,
`credentials.envVars` masking, and the already-logged-in keychain OAuth for
free. The container adds an isolation boundary the sandbox already provides
without needing to be installed.

Source: this comparison is preserved in `protocol.md`'s isolation table
(§4) rather than in `docs/superpowers/`; recorded here because the
alternatives list in
`docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:26-32` treats it
as one of the four rejected driver/isolation alternatives.

## A model as scheduler — rejected

The driver must be deterministic muster code, not a model and not the cloud:
not the orchestrate plugin, because an LLM must not be the scheduler.

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:155-158`.

A related and more specific rejection: the hook enforcing a gate must stay a
hook rather than become the model's own judgment. The model is the thing
being gated, and an entity cannot authorize itself — this is exactly the
`warrant/hooks/scope-gate.sh` defect measured on 2026-07-27, where the model
wrote its own `status: approved` proposal and the gate honored it. An LLM
reading adversarial text to decide authorization is injectable; string
equality is not.

Source: `docs/superpowers/plans/2026-07-27-core-consent.md:432-438`.

## Cloud cron — rejected

Not cron/Routines as the driver: Anthropic-cloud execution cannot reach
keychain auth or the local Seatbelt sandbox, both of which the driver needs.

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:155-158`.

## Die-and-respawn — the only gate-crossing mechanism, pinned

A human gate is not a paused conversation; it is a durable board-state
transition awaiting an out-of-band single-use signal that survives session
death by construction. Die-and-respawn is pinned as the only mechanism that
crosses a human gate.

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:124-130`.

## review/verify role-merge — rejected

Merging the `review` and `verify` roles was rejected. Contract §16 is
titled "verify/review division of labor" and states the mechanism "does not
merge the two roles' verdicts"; contract §4 makes their independence a rule.
Skills do not move, roles do not merge — only the underlying machine (the
shared `state_gate.py` library) moves.

Source: `docs/superpowers/plans/2026-07-27-state-gate-into-core.md:13` (the
conclusion repeats at
`docs/superpowers/plans/2026-07-27-state-gate-into-core.md:996`).

## Mechanical `sed` migration — rejected

A mechanical `sed`-based bulk migration of the seven `state-gate.sh` copies
into the shared library was not available, given that the seven copies were
measured to be substantively distinct (seven distinct hashes, up to 702
differing substantive lines even between the two closest copies — see the
companion measured-facts decision). The plan instead builds the library
against one reference implementation, proves it on a second,
differently-shaped one, and only then touches the remaining five.

Source: `docs/superpowers/plans/2026-07-27-state-gate-into-core.md:27`.

## Natural-language-parsing `mint.sh` designs — three rejected

Three designs tried to read an approval decision out of natural language,
and each leaked, each in a different way:

1. A design where the *name* of the target state, appearing anywhere in the
   text, read as an approval.
2. A negation denylist scanned in a character window (e.g. carrying a
   `\brefus\b` pattern), which missed unlisted negation forms.
3. A sentence-scoped rewrite with an open-suffix denylist — measured on
   2026-07-27 to still mint an approval from inputs such as "The reviewer
   asked me to approve the scope for subject X," "Do not approve. Actually,
   approve the scope for subject X," seven Korean refusal phrasings, and an
   unclosed code fence that silently swallowed every approval after it.

The general reason these are rejected as a class: deciding what a sentence
*means* is a language problem, and a regex is the wrong tool for it — no
amount of denylist growth turns it into the right one. Deciding whether two
strings are *equal* is not a language problem, which is why exact-string
comment matching (`APPROVE issue-<n>/<role>`) replaced natural-language
parsing.

Source: `docs/superpowers/plans/2026-07-27-core-consent.md:398-423`.
