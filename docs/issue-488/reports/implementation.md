---
code_under_review: HEAD
loop_state: landed
---

## What was done

Built per `docs/issue-488/proposals/2026-08-08-global-watch-all.md`,
approved on issue #488 with feedback (`APPROVE issue-488/implementation`)
that overrides the proposal's chosen approach: deliver **auto-arm** as
primary (the rejected alternative in the proposal's own Rationale), with
`watch --all` as an aggregate view on top, because the after-proposal
hunt's own open finding said `--all` alone does not make an unmonitored
session structurally impossible.

**Auto-arm (primary, per feedback)**
- `spawn.py:_workspace_index_put()` — new optional `watcher_pid` param;
  stored in the workspace-index entry when given, omitted otherwise.
- `spawn.py:_spawn_one()`, the bounded/`--issue` fork-and-return-to-caller
  branch (`if child_pid > 0:`): before returning to the caller, launches
  `spawn.py watch --issue n --role r --follow` as a detached
  (`start_new_session=True`) subprocess, stdout/stderr redirected to
  `<work>.watcher.log`, and records its pid into the workspace index via
  `_workspace_index_put(..., watcher_pid=wproc.pid)`. If the `Popen`
  itself raises `OSError`, the spawn returns `1` instead of completing —
  a spawn cannot report success without its watcher registered.
- `spawn.py:watchdog_check_one()` — new signal 5: reads the workspace
  index entry for the roster key under scan; if no `watcher_pid` is
  recorded, reports `watcher-missing`; if recorded but the pid is not
  alive (`_alive()`), reports `watcher-dead`. `roster_watchdog()`'s
  existing per-key loop surfaces these the same way as the other four
  signals — a dead watcher is not silent, it shows up on the next
  watchdog tick.

**`watch --all` (aggregate view, per approved proposal)**
- `spawn.py:_watch_all()` — new function: each iteration re-reads
  `_workspace_index_load()` (so keys registered after the call started
  are picked up), and for every key not yet at `session-end`, drains new
  `events.jsonl` lines via the same `_events_path`/`_offset_path`
  machinery `_watch`/`_await_bounded` already use, printing
  `[watch-all] <key> <type>: <detail>` and advancing that key's own
  offset file. Runs until `KeyboardInterrupt`.
- `main()`: new `--all` flag on `watch`, mutually exclusive with
  `--issue`; wired to call `_watch_all(a.stall_timeout)`.

**Tests** (`test_spawn.py`, all pass, run this session):
- `WatcherAutoArm` (5 cases): `_workspace_index_put` records/omits
  `watcher_pid`; `watchdog_check_one` flags `watcher-dead` (dead pid),
  `watcher-missing` (no `watcher_pid` field), stays silent when the
  watcher pid is alive, and stays silent when there is no workspace-index
  entry for the key at all (adhoc/no-`--issue` spawns).
- `WatchAll` (4 cases): multiplexes two keys' events independently; a key
  registered *after* polling started is picked up on the next iteration
  (the issue's own acceptance line); each key's offset file advances only
  by what was consumed for that key (no cross-key offset corruption); CLI
  usage error when `--all` and `--issue` are combined.
- `python3 -m pytest test_spawn.py -q`: 293 passed (full suite including
  the pid-reuse regression test added after the before-landing hunt, no
  regressions).

Completed-items list (doc-placement ladder):
- No new dependency, no new env var, no migration, no operational-surface
  file touched — nothing routes to a handbook.
- Deviation from the approved phase-1 proposal recorded below, not as a
  separate `docs/decisions/` ADR — the deviation is scoped to this one
  issue's build and the "why" (feedback overriding the proposal's own
  rejected-alternative reasoning) is fully captured in the issue's PR
  review comment plus this record.

## Why

Per the approver's feedback on issue #488: `watch --all` reduces the
opt-in call from per-spawn to per-conversation but is a mitigation, not
the structural fix the operator asked for ("구조적으로 해결") — nothing
gated a spawn on a watcher being armed. Auto-arm closes that: a spawn
cannot report success without its own watcher process registered, and a
dead watcher is watchdog-checked rather than silently unsupervised.

## Upstream

Basis: `docs/issue-488/proposals/2026-08-08-global-watch-all.md`,
approved with feedback on the issue (comment overriding the proposal's
chosen alternative — see `## Rationale for deviations`).

## What did not work

- First cut of `_watch_all()` followed the proposal's fuller spec
  (reusing `WATCH_CRASH_RC`/`wrapper_pid` liveness checking per key,
  matching the single-session `--follow` loop's crash detection).
  Descoped to plain event-draining without crash detection: given the
  feedback's emphasis that `--all` is now the secondary "aggregate view"
  layered on top of auto-arm (not the primary structural fix), and the
  proposal itself is superseded on the primary-mechanism question,
  building the full crash-detection parity for the now-secondary surface
  was not worth the additional write-set risk in this pass. Noted here
  rather than silently built past — see `## Next steps`.

## Rationale for deviations

`## What will be done` in the phase-1 proposal specified `watch --all`
as the sole mechanism and explicitly rejected auto-arm-per-spawn (citing
double-forking cost and this repo's stance against unconditional
background processes, per `roster_watchdog --auto-respawn` precedent).
The approver's PR-review feedback overrides that choice directly: it
names the after-proposal hunt's own open finding as decisive and directs
that auto-arm be delivered as primary, with `--all` retained as the
aggregate view on top — not a request to relitigate, a instruction on
which of the two named options actually ships as the answer to the
issue's acceptance criterion ("a spawn with no active watcher cannot
occur"). Built accordingly: `_spawn_one()`'s bounded/`--issue` path now
gates its own successful return on having launched and registered a
watcher process, and `watchdog_check_one()` surfaces a dead/missing
watcher as a first-class anomaly signal — this is the "dead watcher must
surface loudly (watchdog-checked)" half of the feedback. The proposal's
own risk concern (a second detached process per spawn, needing its own
liveness supervision) is answered, not ignored: that supervision is
exactly what the new watchdog signal provides, so the risk the proposal
flagged is the thing this build's second half closes.

## Open findings

None. The after-proposal hunt's finding (`--all` alone is a mitigation,
not the structural fix) is what this whole build addresses. The
before-landing hunt (`docs/reports/2026-08-08-hunt-global-watch-all.md`,
"before-landing" section, stance 0) found: `watchdog_check_one` signal
5's `_alive()`-only liveness check cannot distinguish a real watcher
process from an unrelated pid the OS reused after the real watcher
died/crashed, so PID reuse could silently pass the auto-arm liveness
check.

resolved_findings:
- before-landing hunt finding (watcher-pid-reuse, `docs/reports/2026-08-08-hunt-global-watch-all.md`):
  fixed by `spawn.py:_watcher_looks_real()` — when the roster entry
  carries an `issue` number, cross-checks `/proc/<pid>/cmdline` for the
  expected `watch`/`<issue>` tokens before trusting `_alive()`, falling
  back to plain `_alive()` only when `issue` is unknown or `/proc` is
  unavailable (non-Linux). Covered by
  `test_watchdog_flags_pid_reused_by_unrelated_process` (skipped where
  `/proc` does not exist).

## Next steps

## Next steps

- `_watch_all()` does not yet reuse `WATCH_CRASH_RC`/`wrapper_pid`
  liveness detection per multiplexed key (see `## What did not work`) —
  a crashed session with no `session-end` event is silently absent from
  the `--all` stream today, same as it would be absent from a
  non-crash-aware poll. A follow-up proposal scoped to `_watch_all()`
  alone should add per-key crash detection mirroring `_watch`'s
  `--follow` loop.
- The watcher subprocess launched by auto-arm is itself a `spawn.py
  watch --follow` invocation with no supervision beyond the new
  watchdog signal (which only fires on the next `watchdog` tick, not
  immediately). If watchdog is not run regularly, a dead watcher can sit
  unreported between ticks — acceptable per the issue's own framing
  (watchdog is the existing periodic sweep this repo already relies on),
  but worth naming for whoever schedules `watchdog` cadence.

## Resolution path

Both next-steps items are follow-up-proposal-scoped, not blocking findings
against this build — file against issue #488 or a new issue once
triaged by the user/orchestrator.
