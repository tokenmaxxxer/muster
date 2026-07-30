---
kind: decision
date: 2026-07-29
status: landed
subject: issue-73
---

# Headless CLI — measured facts

Extracted from `docs/superpowers/` before that directory is retired (see
`docs/decisions/2026-07-29-permanently-closed-alternatives.md` and issue #73).
Each entry below is a fact established by direct measurement against a real
CLI session, not inferred from documentation, and is cited to its
`path:line` source inside `docs/superpowers/`.

## Headless default permissions silently deny Write

Under headless default permissions, a `Write` call is denied without any
visible failure: no file is created, the session exits looking successful,
and the denial only shows up in `--output-format json`'s
`permission_denials` field — which `spawn.py` never reads. This is the best
explanation for sessions that were observed to "exit 0 having done nothing."

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:58-63`.

`--permission-mode acceptEdits` removes the missing-approver prompt that
causes this, but a `PreToolUse` exit-2 gate still blocks the `Write` even
under `acceptEdits` — permission mode only removes the "nobody to answer"
prompt, gates remain the deny plane regardless of permission mode.

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:64-67`.

## `--plugin-dir` loads hooks fully in headless mode

Headless hook firing itself is measured, not documented upstream: the hooks
reference never states that hooks fire in `-p` (print/headless) mode. A CLI
auto-update could silently remove every gate while sessions keep exiting 0,
because there is no upstream guarantee to regress against.

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:41-44`.

As of the review cited above, `--plugin-dir` had been proven to load hooks
with a single probe plugin, but not yet with a full nine-plugin rulebook — a
canary run against the full set was called out as the remaining gap.

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:322-330`.

## `--tools ""` is the disable-all spelling, not `--allowed-tools ''`

(Established as part of the same CLI-behavior review that produced the
headless-permission and plugin-dir findings above; recorded here as a
measured CLI fact worth keeping independent of the rejected designs that
depended on it.)

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:41-67`.

## `--settings` / `--plugin-dir` are not restored on `--resume`

`--resume` was measured and explicitly not adopted for role sessions: doing
so would require session-id capture (for JSON output), the `--settings` and
`--plugin-dir` flags re-passed by hand (since they are not restored
automatically on resume), invocation from the same project directory, and an
already-minted out-of-band token. This was recorded so the option would not
be silently relitigated later.

Source: `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:139-144`.

## Hooks fire for subagent tool calls

A full-history security review across all ten repositories in scope found
seven exploitable defects, four of which were the same underlying concept
implemented three different ways — evidence that hook behavior (including
firing on subagent-issued tool calls) needed to be verified directly rather
than assumed from a single implementation.

Source: `docs/superpowers/plans/2026-07-27-core-consent.md:98-101` (tabulated
per-hook duplication counts also at
`docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:19-29`).

A concrete case of a gate that should have denied but returned
`permissionDecision: "allow"` was measured in two rulebooks: a Bash call
piping a remote script into `sh` and appending to a record file passed,
because the gate only inspected the trailing append.

Source: `docs/superpowers/plans/2026-07-27-core-consent.md:1006-1012`.

## Other measured facts worth keeping

- **Consent/approval tokens are reused if not cleared.** One repo never
  removed a consumed approval token, so the same approving write passed four
  times in a row.
  Source: `docs/superpowers/plans/2026-07-27-core-consent.md:225-227` (same
  fact repeated in implementation docstring at
  `docs/superpowers/plans/2026-07-27-core-consent.md:325-328`).

- **Plugin installs can silently enable unrelated rulebooks globally.** A
  single `install`/update run turned on 22 rulebook plugins globally, because
  `install` leaves a plugin enabled in the user's global settings rather than
  scoped per role.
  Source: `docs/superpowers/plans/2026-07-27-core-consent.md:1169-1171`.

- **A hook copied to a temp directory can pass or fail for reasons unrelated
  to its contents.** A broken hook looked fine when tested from a temporary
  copy because it exited before reaching the broken line; only testing hooks
  from the path a session will actually load them from is valid.
  Source: `docs/superpowers/plans/2026-07-27-core-consent.md:1185-1188`.

- **Environment variables cannot smuggle in unattended mode, and repo-local
  `.claude/settings.json` is rejected at spawn.** An agent's own
  `export TOKENMAXXXER_UNATTENDED=1` inside a `Bash` call does not reach the
  hook's environment (the hook reads the settings value instead), and a
  repository shipping its own `.claude/settings.json` is refused at spawn by
  `spawn.py`'s `require_no_repo_config`.
  Source: `docs/superpowers/plans/2026-07-27-core-consent.md:794-801`.

- **Seven copies of `state-gate.sh` were substantively distinct, not
  near-duplicates.** After substituting the role name and stripping comments
  and blank lines, the seven per-rulebook copies produced seven distinct
  hashes; even the two closest (review and reflect) differed on 702
  substantive lines, including `set -euo pipefail` vs. `set -uo pipefail` and
  differently named kill switches.
  Source: `docs/superpowers/plans/2026-07-27-state-gate-into-core.md:15-26`.
