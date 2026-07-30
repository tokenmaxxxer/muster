# issue-114 build proposal

files:
- `spawn.py`
- `on-the-record/hooks/directive.sh`

## Request (paraphrased intent, secrets stripped)

A role opened its proposal PR minutes before its session exited, and it
sat undetected until the user asked how things were going. The original
plan was to write a `PR opened mid-run` line into the live session log
as it happened. Revision feedback on the first version of this proposal
(PR #116) rejected that: the orchestrator is only re-invoked when a
process EXITS, so a log line is invisible to it no matter how early it
lands — today, both this issue's own PR and a sibling PR sat open,
observed in the log, unreported, because the watching process never
exited (measured, not hypothetical). Notification has to be exit-shaped,
not log-shaped.

Reworked requirement: (1) `spawn.py`'s wrapper detaches the role
session and EXITS at the first material event (PR opened, gate refusal,
or session end), printing that event and returning it as the call's
output; (2) a new `spawn.py watch --issue <n>` subcommand blocks until
the NEXT material event for a still-running session (or reports the
session already ended); (3) the orchestration directive drops the
"poll logs on your own initiative" instruction and instead says: after
spawning, or after any `watch` call returns, re-arm by calling
`spawn.py watch --issue <n>` again before doing anything else — visibility
becomes mechanical (block-until-exit), not judgment-based (guess when
to check).

## Constraints

- Wake routing itself is out of scope — detection of COMPLETED,
  MERGED work stays on `wakes.py` reading merged main; this issue is
  in-flight visibility on running sessions only.
- No new dependency, env var, schema, or migration.
- The role's own harness process must keep running to completion
  (commit/push/PR) even after `spawn.py`'s CLI call has returned early
  — an early return must not kill or orphan the session. `_spawn_one`
  today calls `subprocess.Popen` without `start_new_session=True`, so
  the child inherits the parent's process group; if `spawn.py role ...`
  exits while its own parent (the orchestrator's shell/tool runner)
  reaps it, a signal to that group could still take the session down.
  Detaching correctly (`start_new_session=True` at minimum) is part of
  the write set, not an incidental detail.
- `ensure_pushed`, `gate_report`, `ledger_write`, and the outcome
  classification (`classify`/`fail_closed_downgrade`) in `_spawn_one`
  currently run synchronously after `proc.wait()`, in the same call
  that streams stdout. Whichever process ends up draining
  `proc.stdout` to completion must still run that finalization exactly
  once — splitting the read loop off must not duplicate or drop it.
- `spawn.py role task --issue n` and `spawn.py watch --issue n` are
  both entered fresh by a NEW orchestrator turn (headless, one-shot,
  contract v3 process model) — state that survives between them
  (which events already happened, whether the session PID is still
  alive) has to live on disk, not in Python process memory.

## What will be done

- Freeze one on-disk contract, referenced from both new pieces:
  - `<workspace>.events.jsonl` — one JSON object per material event,
    append-only, written by whichever process drains the session's
    stream. Shape: `{"ts": <epoch>, "type": "pr-opened"|"gate-refusal"|
    "session-end", "detail": <url or outcome string>}`.
  - `<workspace>.events.offset` — a single integer byte offset into
    `events.jsonl`, the last position `watch` has reported up through.
    Absent means nothing has been reported yet.
- In `spawn.py`, split `_spawn_one`'s current single blocking
  read-to-completion loop (`spawn.py:1872-1890` today) into two parts
  that run in the SAME detached child process (`start_new_session=True`
  on the `Popen` call so the child survives the parent CLI call
  exiting):
  1. The existing stream-json drain loop, extended to append to
     `events.jsonl` the moment it recognizes a PR URL (as the prior
     version of this proposal already specified) or a gate-refusal
     signal in the stream, in addition to the existing tee to
     `.session.log`.
  2. After `proc.wait()`, run the existing finalization block
     unchanged (board delta, `ensure_pushed`, `gate_report`,
     `classify`, `ledger_write`, roster_remove) and, as its last step,
     append a `session-end` event with the computed `outcome` to
     `events.jsonl`.
  This whole body becomes the detached child's job, launched via a
  double-fork (`os.fork` + `setsid`) or an equivalent re-exec of
  `spawn.py` itself with an internal `_run-detached` entry point, so it
  keeps running after the invoking CLI call exits.
- The invoking `spawn.py role task --issue n` call itself no longer
  blocks until session end. After launching the detached child and
  registering it in the roster (unchanged), it polls `events.jsonl` for
  the FIRST line to appear, prints that event to stderr, writes
  `events.offset` past it, and exits — returning control (and that one
  event) to the caller.
- Add `spawn.py watch --issue <n> [--role <role>]` (new argparse
  subcommand + `_watch()` function): resolve the workspace from the
  roster/issue exactly as `roster_kill` does today, read
  `events.offset`, and block (short poll loop, same style as the
  existing `roster_watchdog` poll) until a line past that offset
  appears in `events.jsonl`. Print that event, advance
  `events.offset`, and exit 0. If the roster entry for that issue/role
  is already gone (session ended before `watch` was called) but
  `events.jsonl` has an unreported `session-end` line, report that line
  immediately instead of blocking forever.
- In `on-the-record/hooks/directive.sh`'s PROGRESS CHECKS bullet
  (lines 71-74), replace the "when the user asks, tail the log"
  instruction with: after every spawn, and after every `watch` call
  returns an event that is not `session-end`, re-arm by calling
  `spawn.py watch --issue <n>` again before doing anything else; the
  block IS the notification mechanism, so no separate "check
  unprompted" judgment call is needed. State explicitly that wake
  routing (merged-main reads) is unchanged and unrelated.

## Out of scope

- Any change to `wakes.py` or wake routing/detection logic.
- A general-purpose IPC/pubsub mechanism — the two flat files
  (`events.jsonl`, `events.offset`) are the whole contract; no message
  queue, socket, or new dependency.
- Making `watch` interrupt a session or affect its outcome — it only
  observes and reports.
- Backfilling events for sessions already running when this ships
  (their `events.jsonl` won't exist) — `watch` against those falls
  back to blocking on roster liveness only and reports `session-end`
  once the PID disappears, with no earlier PR/refusal detail.

## How you'll know it worked

- `python3 -m py_compile spawn.py` passes and `bash -n
  on-the-record/hooks/directive.sh` passes.
- Manual trace of the detached child: feed the stream loop a stub line
  containing a `.../pull/<n>` URL and confirm one `pr-opened` line
  lands in `events.jsonl` with no duplicate on a repeated URL, and that
  the invoking `spawn.py role ...` call exits immediately after that
  line appears rather than waiting for the process to finish.
- Manual trace of `watch`: with a stub `events.jsonl` and `events.offset`
  pointing before its last line, confirm `spawn.py watch --issue n`
  prints exactly the unreported lines and exits 0; with the offset
  already at the end and the roster PID still alive, confirm it blocks
  until a new line is appended (simulate by appending from a second
  shell) rather than exiting early.
- Kill the detached child's parent CLI call mid-session (simulate the
  orchestrator's turn ending) and confirm the child keeps running,
  finishes, and still writes `session-end` — proving the
  `start_new_session=True` detachment actually holds.
- Read `directive.sh`'s rendered PROGRESS CHECKS text end to end and
  confirm it says "re-arm `watch` after each event", not "check logs
  when idle", and states the wake-routing boundary in plain language.
