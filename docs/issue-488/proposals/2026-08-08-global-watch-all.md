---
status: proposed
files:
  - spawn.py
  - test_spawn.py
---

## Request
`spawn.py watch` today only follows a session the caller already knows the
`{issue, role}` key for, and only if the caller remembers to re-arm it
after every spawn/respawn. Several respawned sessions ended unnoticed
because the orchestrator skipped re-arming watch. Add a way to make an
unmonitored session ending structurally impossible: either spawn itself
auto-arms a watcher, or a single `watch --all` call streams every
session's material events across the whole board, armed once and left
running.

## Constraints
- Must not change the meaning of existing `spawn.py watch --issue n
  [--role r] [--follow]` — it stays as is; this adds a surface, not a
  rewrite.
- Must reuse the existing event/offset/workspace-index machinery
  (`_events_path`, `_offset_path`, `_workspace_index_load`,
  `_read_offset`, `_write_offset` — spawn.py:2137-2150, 2105-2136) rather
  than inventing a parallel notification channel.
- Must keep `WATCH_CRASH_RC = 2` / session-end semantics consistent with
  the single-session `--follow` loop (spawn.py:2205-2295), per the
  issue-224 decision already fixing those exit codes.
- Acceptance requires demonstrating a session spawned **after** the
  watcher started is still observed — the watcher cannot snapshot the
  workspace index once at startup.
- No new dependency, no new env var, no schema/migration — pure
  spawn.py/test_spawn.py change.

## Rationale
Two options were on the table per the issue text: (1) auto-arm — have
`_spawn_one()` itself detach a background watcher process per spawn, or
(2) a single long-lived `watch --all --follow` the orchestrator arms once
per conversation.

Chosen: **(2) `watch --all --follow`**.

Rejected: **auto-arm-per-spawn**. `_spawn_one()` (spawn.py:3285) already
forks once per spawn to run the session to completion detached from the
CLI caller (spawn.py:3373-3376) — auto-arm would mean forking *again*,
per spawn, to run a *second* detached process whose only job is to poll
the first. That doubles the number of detached processes per spawn
(current roster/claim/workspace-index bookkeeping is keyed by
`{issue}/{role}`, spawn.py:1508 and 2137, not by watcher-instance, so a
second live process per session needs its own lifecycle tracking to avoid
leaking one watcher per respawn). It also cuts against this repo's
existing stance on auto-triggered background processes:
`roster_watchdog`'s `--auto-respawn` was deliberately left **off by
default, "관찰-전용 유지"** (spawn.py:2669-2671, decided in
docs/issue-90/proposals/coding-watchdog.md) specifically to avoid a sweep
silently taking action without an explicit flag. Auto-arm-per-spawn is a
stronger version of the same risk (a background process starts on every
spawn, unconditionally, with no way to opt out per-call) for a problem
that a single explicit `--all` call already solves without adding a new
process-per-session failure mode. `watch --all --follow` costs the
orchestrator exactly one call per conversation (matching how `drive` and
`watchdog` are already single standing invocations) and needs no new
process bookkeeping — one existing CLI process just widens its own poll
loop from one workspace-index entry to all of them, re-reading the index
every iteration so new spawns are picked up live.

## What will be done
- Add `--all` flag to `main()`'s argparse block (spawn.py:2645-2676,
  alongside the existing `--follow`/`--stall-timeout`), valid only with
  `a.role == "watch"`; `--issue` becomes optional when `--all` is given
  (mutually exclusive: `--all` with `--issue` is a usage error).
- Add `_watch_all(stall_timeout_min: float) -> int` in spawn.py, next to
  `_watch()` (spawn.py:2211): a loop that, each iteration, re-reads
  `_workspace_index_load()` (so keys registered by spawns that started
  *after* the watcher did are picked up), and for every `{issue}/{role}`
  key not yet at `session-end`, checks `_events_path`/`_offset_path` for
  new lines the same way `_await_bounded`/the `--follow` loop already do,
  printing `[watch-all] issue-<n>/<role> <type>: <detail>` per event and
  advancing that key's own offset file (so a later single-key `spawn.py
  watch --issue n` still sees the correct remaining events, not a false
  "nothing left" from `--all` having consumed them). Runs until
  interrupted (SIGINT/SIGTERM) — it is meant to be armed once and left
  running for the conversation, per the issue's own framing ("streams
  every session's material events ... in one long-lived call"). Reuses
  `WATCH_CRASH_RC` crash detection per key via the same `wrapper_pid`
  liveness check the existing `--follow` loop uses (spawn.py:2275+), so a
  crashed, un-ended session is still reported instead of silently
  dropped from the multiplexed stream.
- Wire `if a.role == "watch"` (spawn.py:2718) to call `_watch_all` when
  `a.all` is set, else the existing per-issue path unchanged.
- Tests in `test_spawn.py` (new class, alongside `WatchFollow` at line
  4904): 
  - red-green for the issue's own acceptance line: register a session in
    the workspace index, start `_watch_all` consumption of a fixed number
    of iterations (test harness caps iteration count / injects a stop
    condition — no real infinite loop under test), append a
    `session-end` event to a key that was **not** in the index when
    watching began (added mid-loop, simulating a spawn that happened
    after the watcher armed), assert it is reported.
  - respawn continuity: same `{issue}/{role}` key re-registered (new
    work dir/log, same key) mid-loop after a prior `session-end`, assert
    the new session's events are still observed without re-arming
    `_watch_all` itself.
  - multiplexing: two concurrent keys, assert events from both are
    reported and each key's own offset file only advances past what
    `_watch_all` actually consumed for that key (regression guard against
    cross-key offset corruption).

## Out of scope
- Auto-arm-per-spawn (rejected above) — not built in this pass.
- Any change to `roster_watchdog`/`--auto-respawn` behavior.
- A durable "notification stream" beyond stdout printing (e.g. piping
  `--all` output to Slack/webhook) — the issue's acceptance is satisfied
  by observability from the ledger/stream via this CLI call, not by a new
  delivery channel.
- Changing single-session `spawn.py watch --issue n` behavior.

## How you'll know it worked
- `test_spawn.py` red-green case: a session registered in the workspace
  index *after* `_watch_all` begins polling still has its `session-end`
  event reported by that same running call — this is exactly the
  issue's acceptance check ("a single --all watcher demonstrably reports
  a session that was spawned AFTER the watcher started").
- Respawn-continuity test passes without any re-arm call between the two
  sessions on the same `{issue}/{role}` key.
- Existing `WatchFollow` and `Watchdog` test classes remain green
  unmodified (no regression to the single-session path).
