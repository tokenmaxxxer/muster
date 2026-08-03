---
kind: decision
date: 2026-08-03
status: landed
subject: issue-224
---

# `spawn.py watch --follow` pid-death exit code — `2`

## Decision

`_watch()`'s `--follow` loop returns a new module-level constant,
`WATCH_CRASH_RC = 2`, when it detects the session process is gone
without a `session-end` event ever arriving. This value becomes the CLI
process's exit code (`main()`'s return value is what `sys.exit(main())`
uses).

`_watch()`'s existing return values are unchanged and keep their
meaning:
- `0` — normal: either non-`--follow` bounded return (event-or-stall,
  pre-existing issue #114/#180 contract, unchanged), or `--follow`
  reaching `session-end`.
- `1` — usage/lookup failure: no workspace-index record for the
  `issue-<n>[/<role>]` key (pre-existing).
- `2` (new) — `--follow` detected the session's pid is dead (or its
  roster entry is gone) with no `session-end` in the events log —
  requester (PR #255 feedback 2) asked this value be pinned down and
  documented since it feeds the orchestrator's interpretation of the
  CLI's exit code.

## Why (adopted — a third value, not reusing `1`)

`1` already means "no record to watch" (a caller-input problem: nothing
was ever spawned for this issue/role). Reusing it for "something was
spawned, ran, and then died" would collapse two different orchestrator
responses (re-check the issue/role argument vs. re-check the crashed
session's log and consider respawning) into one code. `2` is free in
this function's existing range (`0`/`1` only) and matches the general
shell convention of reserving low small integers for distinct failure
classes rather than overloading a single non-zero code for every
failure.

**Rejected alternative — reuse `1` for both "no record" and "crashed
session."** Considered because it needed no new constant. Rejected:
collapses two orchestrator-actionable-differently conditions into one
signal, and this repo's own `_watch()` no-record message already prints
a distinct human-readable reason to stderr — an orchestrator or script
consuming only the exit code (not stderr) would otherwise be unable to
tell them apart programmatically.

**Rejected alternative — a larger/namespaced code (e.g. `86` or a
per-defect range).** Rejected: no existing exit-code registry or range
convention exists anywhere else in this codebase (`spawn.py` uses only
plain `0`/`1` throughout every other subcommand); introducing a new
numbering scheme for this one call site would be inventing structure the
rest of the codebase doesn't have and no consumer currently needs.
