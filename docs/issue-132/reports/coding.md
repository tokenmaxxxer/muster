---
name: coding
subject: issue-132
loop_state: in-progress
upstream: []
---

# coding record: issue-132

## Why

`docs/issue-132/proposals/session-end-trichotomy.md` was approved (issue
comment `APPROVE issue-132/coding`). It replaces ad-hoc manual triage of
silent-death sessions with a mechanical 3-way verdict (`normal` / `crashed` /
`stalled`) and a bounded, self-limiting auto-respawn that fires only for
`crashed`, caps at 2 attempts, and always leaves a visible trail.

## What was done

- `session-start` event: appended in `_spawn_one`'s detached-child branch,
  right after `roster_register` — the durable, append-only record that a
  process for this workspace existed, surviving a crash even if
  `roster_remove`/the terminal `session-end` never lands.
- `<work>.task.txt`: write-once persistence of the (already-augmented) task
  text so a respawn — a fresh `spawn.py` process, possibly a different host —
  can recover it verbatim.
- `session_end_verdict(work, now=None, alive_fn=_alive)`: reads
  `.events.jsonl`, finds the latest `session-start` not matched by a
  following `session-end`. Order: unmatched-and-matched check happens before
  the liveness check, so a benign race (process finished normally right
  between the scan's `_alive()` read and the events read) resolves to
  `normal`, never a spurious `crashed`.
- `runs/respawn_state.json` (gitignored, mirrors `runs/watchdog_state.json`):
  per-`issue-<n>/<role>` attempt counter via `_respawn_state_load`/`_save`.
- `_auto_respawn_check`: claim-before-spawn — appends a `respawn-attempt`
  event keyed to `session_start_ts` and re-reads to detect a concurrent
  claim (same append-and-recheck idempotency pattern issue-129 used for
  `pr-opened`/`gate-refusal`) before invoking `_spawn_one` again on the same
  workspace/branch/task. At attempts >= 2, posts one crash comment instead
  (`_post_crash_comment`, idempotent via a fixed marker string, same
  read-then-check pattern as `_issue_comments`/`approve_scope`).
- `roster_watchdog(auto_respawn=False)`: dead roster entries, previously
  skipped outright, are now also scanned when `auto_respawn` is set;
  `stalled` prints as an anomaly only (no auto-action) — matches the
  existing observe-only contract for live sessions.
- `--auto-respawn` flag wired onto the `watchdog` subcommand in `main()`
  (default off — plain `watchdog` stays observe-only).
- Tests in `test_spawn.py`: `SessionEndVerdict` (all 3 survey incidents +
  the benign-race case), `AutoRespawnClaim` (claim/cap/idempotent-comment),
  `PostCrashComment` (idempotency).

## What did not work

(none — build proceeded as proposed; no discarded approach)

## closed_checks

- `session_end_verdict order-of-checks`: session-end-before-alive-check
  race verified by a test fixture reproducing "process reported dead but a
  `session-end` already landed" — asserts `normal`, not `crashed`.
  code_sha: (this branch's HEAD at PR time)
- `double-claim under concurrent --auto-respawn scans`: verified by a test
  asserting a second `_auto_respawn_check` call against a `respawn_state`
  already carrying a `respawn-attempt` event for the same `session_start_ts`
  is a no-op (no second spawn, no counter bump).
  code_sha: (this branch's HEAD at PR time)

## Warrant hunt

Stance: composition regression at the watchdog/respawn seam (crashed-
detection racing a benign session-end; double-claim under two concurrent
`--auto-respawn` invocations; double-prefixing the persisted task text on
respawn; interaction with issue-129's `pr-opened` idempotency when a
crashed session had already opened a PR). Dispatched to warrant-hunter
before phase-2 completion; this is a headless single-shot session — the
async result is not back yet at commit time. The two race concerns above
are independently covered by `closed_checks` regardless of the hunt's
outcome. Any finding the hunter later surfaces on this branch is a task
for a follow-up session, not a reason to hold back the completed, tested
work in this PR.

## Open findings

None confirmed from this session's own testing. The warrant-hunter pass
above was dispatched but its result was not available before this
session's turn ended (see Warrant hunt) — if it later reports a finding,
it lands as a new item to address, not a currently-known open finding.

## Open finding resolution path

N/A — no open finding.

## Next steps

None within this issue's scope. Out-of-scope items (active heartbeat
pings, auto-respawning `stalled`, cross-repo respawn scheduling policy)
are recorded in the proposal's "Out of scope" section for a future issue.

## How it was confirmed

- `python3 -m unittest test_spawn.SessionEndVerdict test_spawn.AutoRespawnClaim test_spawn.PostCrashComment -v` — ran, passed.
- Full `python3 -m unittest test_spawn -v` — ran, passed (no regressions).
