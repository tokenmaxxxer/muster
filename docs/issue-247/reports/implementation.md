---
kind: coding-record
code_under_review: spawn.py, test_spawn.py, docs/handbooks/operations.md
loop_state: executing
---

# Implementation record — issue #247

## Why

Phase 2, executing the approved proposal
(`docs/issue-247/proposals/self-triggered-abandoned-work-respawn.md`,
upstream basis for this record), approved via issue-level comment
`APPROVE issue-247/implementation` (single-account mode, role-handoff
contract v3, PR author and approver both jjongkwann). Delivering the
proposal exactly as approved: a second, in-process trigger for the
existing capped auto-respawn machinery (issue #132), firing at the point
`_spawn_one()` already knows its own `uncommitted-work`/`failed-no-commit`
outcome, instead of only at the next `spawn.py watchdog` tick (which the
reported incident's normal exit never reaches — survey.md).

## Rebase note (line-number drift vs the proposal)

The proposal was written against a `main` that has since moved 46
commits (issues #224 wrapper_pid, #246 classifier fixes, #266 death
judgment, #245 Closes-gate, #262/#227/#258 and others landed in between).
This branch was rebased onto current `origin/main`
(`247051e2a40f6e877db5bc2704445165d06f7f50`) before phase-2 work started;
the rebase was clean (no conflicts). Line numbers the proposal cites
(e.g. `spawn.py:2884-2911`, `spawn.py:1611-1678`) have drifted — `spawn.py`
is now 3108 lines with `_spawn_one()` starting at line 2705 and
`_auto_respawn_check()` at line 1679; this record uses the current,
re-surveyed line numbers rather than the proposal's.

## What was done (in progress)

Not yet started — this record is written first, per contract v3 s19/
implementation-role directive, before any code write. Planned sequence:

1. Factor `_auto_respawn_check()`'s claim/attempt-cap/task-replay/
   cap-comment sequence into a shared helper `_respawn_or_cap()`, callable
   from both the existing watchdog `crashed` path and a new self-trigger
   call site.
2. Capture the session-start timestamp as a local variable in
   `_spawn_one()` (currently computed inline at the `_append_event(...,
   "session-start", ...)` call, spawn.py:2851-2852) so the self-trigger
   call can reuse the exact same claim key the watchdog path would
   independently reconstruct by reading it back from `events.jsonl`.
3. Add a small outcome-gate function `_self_trigger_respawn()` called at
   the end of `_spawn_one()`'s bounded/issue-scoped tail, before the
   terminal `session-end` event append (spawn.py:3102 area) — fires
   `_respawn_or_cap()` only when `outcome` is `uncommitted-work` or
   `failed-no-commit`.
4. `test_spawn.py`: new test class covering the outcome gate, the cap/
   comment behavior, and the self-trigger-vs-watchdog concurrent-claim
   race, reusing `AutoRespawnClaim`'s existing fixture style.
5. `docs/handbooks/operations.md`: new KO+EN subsection (matching the
   file's existing mirrored-section convention) documenting the abandoned-
   work outcomes, the new self-trigger behavior, and the manual resume
   command.

## What did not work

None yet.

## Open findings

None yet — hunt not yet dispatched.

## Next steps

Implement per the sequence above, run `python3 -m pytest test_spawn.py -k
"SelfTriggeredRespawn or AutoRespawnClaim or FailClosedDowngrade" -v` and
the full suite, dispatch the hunt (rotation: `assume-broken` is due next —
last used issue-236, everything else used more recently), update this
record's `loop_state` to `landed`, commit, push, open the PR.

## Open-finding resolution path

N/A — no open findings yet.
