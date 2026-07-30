# issue-132 phase-1 survey: session-end 3-way classification + capped auto-respawn

## Current session-end machinery (spawn.py)

- `_spawn_one` (spawn.py:2045) forks a detached (`setsid`) child that runs the
  `claude` subprocess synchronously (`proc.wait()` at spawn.py:2175), computes
  `outcome = classify(rc, result, delta, blocked)` (spawn.py:2208), then
  appends one `{"type": "session-end", "detail": outcome}` line to
  `<work>.events.jsonl` (spawn.py:2264) before `os._exit`.
- `classify()` (spawn.py:1139) only distinguishes `errored` / `progressed` /
  `waiting-on-human` / `refused` / `silent-failure` — all five require the
  detached child to survive long enough to reach the `_append_event(...,
  "session-end", ...)` line. **If the detached child itself dies first
  (OOM-kill, host reboot, `kill -9`, orchestrator machine crash), no
  session-end event is ever written and no outcome is ever computed** — the
  roster entry (`runs/active.json`, `roster_register` at spawn.py:2143) is
  simply left stale with a pid that `_alive()` (spawn.py:1214) will report
  dead.
- `roster_watchdog` / `watchdog_check_one` (spawn.py:1278-1373) already scans
  *live* roster entries for anomaly signals (log silence >90min, delegation
  phrasing, repeated denials, no-commit->71min) but is explicitly
  observe-only — it prints, never acts, and it is never invoked against a
  *dead* pid.
- `_watch`/`_await_bounded` (spawn.py:1441-1496) is a bounded wait for the
  next `.events.jsonl` line or a stall timeout; it also never classifies
  "no event ever came because the process died" vs "no event ever came
  because it's still working."
- There is currently no code path that (a) checks `_alive(pid)` against a
  dead-but-still-registered roster entry, (b) distinguishes that from an
  alive-but-log-frozen entry, or (c) automatically respawns anything. All
  four incidents in the issue were recovered by a human opening the log file
  by hand and deciding.

## The 4 cited incidents, verified against preserved logs/events

Preserved under `~/.tokenmaxxxer/work/`: `<repo>-issue-<n>-coding.session.log`
(live tee of stream-json, **overwritten** — opened `"w"` — by every
respawn, spawn.py:2156) and `<repo>-issue-<n>-coding.events.jsonl`
(append-only, spawn.py:1390-1393).

1. **ops-agent-rulebook issue-24 phase 2**: `events.jsonl` shows an actual
   `session-end: silent-failure` (ts 1785383363, 23s duration, 4 turns) —
   i.e. `classify()`'s existing `rc==0 & no delta & no denials` case fired
   correctly and the *process itself exited cleanly with nothing done*. This
   is a real occurrence of today's `silent-failure`, not a crash. A manual
   respawn ~2min later produced `session-end: progressed` and PR #26.
2. **on-the-record issue-123 / tokenmaxxxer-core issue-49 phase 2**: neither
   workspace's `events.jsonl` contains *any* `session-end` entry preceding
   the eventual `progressed` one — no `silent-failure`, no `errored`,
   nothing. The overwritten live log's last line is a valid final `result`
   event only for the *recovered* run. This is consistent with the
   detached child dying before it ever reached the `_append_event(...,
   "session-end", ...)` line — exactly the (b) "no result record + process
   dead" case the issue describes, not a `classify()`-produced outcome.
   Because the pre-crash log was overwritten by the recovery run, the
   original stdout is not recoverable from disk; the *absence* of a
   pre-recovery `session-end` event is the strongest surviving evidence.
3. **on-the-record issue-129 phase 2**: `events.jsonl` shows a
   `session-end: failed-no-commit` (ts 1785401177) sandwiched between two
   `progressed` entries — a real `classify()`/`fail_closed_downgrade`
   outcome, correctly reported and then followed by a respawn that
   completed the work. Not a crash or a stall; the existing pipeline
   handled this one as designed (case (a), refused/failed content).

Net: of the 4 cited incidents, 1 (issue-24) and 1 (issue-129) are cases the
*existing* `classify()` already names correctly (`silent-failure`,
`failed-no-commit`) — they just weren't auto-recovered. The other 2
(issue-123/core-49, same wall-clock incident) are true (b)-type crashes with
**zero** result record, confirming the issue's premise that a process-death
path exists which today's `classify()` cannot see at all because it only
runs *inside* the process that may be the one dying.

## Write surface for phase 2 (preview, not yet built)

- `spawn.py`: a new judgment function (dead-roster scan) distinct from
  `classify()`, since `classify()` is intentionally scoped to "the process
  that finished, and how" (spawn.py:1139-1153 docstring) — the new function
  answers "did a process finish at all," which needs `_roster_load()` +
  `_alive()` + presence/absence of a `session-end` event, not rc/result.
  Likely lives near `roster_watchdog`/`watchdog_check_one`.
- Respawn-attempt counter: needs persistent state keyed by
  `issue-<n>/<role>` (same shape as `WATCHDOG_STATE`/`ROSTER`, both under
  gitignored `runs/`), since `spawn.py` processes are short-lived and the
  count must survive across separate `spawn.py` invocations.
- Issue-comment-on-cap: `gh api repos/<slug>/issues/<n>/comments` (already
  used read-side by `_issue_comments`, spawn.py:804) — will need a write
  call, new.
- No new dependency, no new env var expected; this is pure orchestration
  logic inside the existing `spawn.py`.

Scouting ran on this gap (dead-process vs hung-process classification and
capped auto-restart are well-trodden supervisor territory) — see
`scout-brief.md` in this same directory.
