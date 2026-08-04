---
kind: decision
date: 2026-08-04
status: landed
subject: issue-266
---

# Amendment to `docs/issue-224/decisions/watch-crash-exit-code.md`'s trigger wording

## Decision

`docs/issue-224/decisions/watch-crash-exit-code.md` (lines 25-26) documents
`WATCH_CRASH_RC = 2`'s trigger as: "`--follow` detected the session's pid
is dead (**or its roster entry is gone**) with no `session-end` in the
events log." As of this issue (#266), the parenthetical is no longer
accurate: `_watch()` (spawn.py:1903) now returns `2` **only** when the
roster entry exists and its `wrapper_pid` is dead. A merely absent roster
entry is treated as unknown and waits out the existing
`stall_timeout_min` safety net instead — see
`docs/issue-266/proposals/roster-lifetime-vs-absence-signal.md` for the
full rationale (`_spawn_one()`'s post-processing tail removes the roster
entry, spawn.py:2995, before the `session-end` event is written,
spawn.py:3097, which made the old "entry gone = dead" equivalence
misreport a normally-completing session as crashed).

The corrected trigger text is:

> `2` (new) — `--follow` detected the session's pid is dead **with the
> roster entry still present** (a merely absent roster entry is no
> longer treated as death — issue #266) with no `session-end` in the
> events log.

## Why this decision lives here instead of amending the source file directly

The approved phase-1 proposal's item 4 called for editing
`docs/issue-224/decisions/watch-crash-exit-code.md` directly. That edit
is blocked by this repository's `board-gate.sh` R4: a role session may
write under `docs/issue-<n>/` only from branch `issue-<n>/<role>`
(contract v3 s10) — this session runs on `issue-266/implementation` and
cannot write under `docs/issue-224/`, regardless of what the approved
write set names. This is a deviation from the proposal's literal
mechanics (recorded in
`docs/issue-266/reports/implementation.md`'s "Rationale for deviations"),
not a scope change: the corrected wording is fully specified above so a
session running on `issue-224/implementation` (or the human directly) can
apply it as a small follow-up — insert this decision's corrected
paragraph in place of the current lines 25-26 of
`docs/issue-224/decisions/watch-crash-exit-code.md`, and add a one-line
pointer to this file.

**Rejected alternative: leave the stale wording undisputed with no
written correction anywhere.** Rejected — an accurate record of what the
trigger now is must exist somewhere reachable from this issue's own
tree, or a future reader hitting the stale `docs/issue-224/` text has no
path to the truth. This file is that reachable, accurate record; the
literal edit to the issue-224 file remains a small pending follow-up.
