# issue-114 build proposal

files:
- `spawn.py`
- `on-the-record/hooks/directive.sh`

## Request (paraphrased intent, secrets stripped)

A role opened its proposal PR minutes before its session exited, and it
sat undetected until the user asked how things were going — an open PR
wakes no one (wake routing reads merged main only), and today's
directive only tells the orchestrator to tail live logs reactively.
Give the orchestrator in-flight visibility: (1) `spawn.py`'s wrapper
should surface a PR-opened event (the URL) to the live session log and
spawn output the moment the role creates it, not only at session exit;
(2) the orchestration directive should tell the orchestrator to check
running sessions' live logs on its own initiative — at minimum when a
session runs unusually long, and whenever the user's decision queue is
otherwise empty — and report material mid-run events (PR opened, gate
refusal, silent stall) unprompted.

## Constraints

- Wake routing itself is out of scope — detection of completed work
  stays on merged-main reads; this is in-flight visibility only, on
  top of the existing exit-time report.
- No new dependency, env var, schema, or migration.
- The stream-json wrapper already tees every line to the live log file
  and to a running `result` accumulator; the new behavior has to live
  inside that same loop rather than add a second read of `proc.stdout`
  (a pipe can only be consumed once).

## What will be done

- In `spawn.py:_spawn_one`'s stream-json loop, scan each parsed line
  for a GitHub pull-request URL (`https://github.com/.../pull/<n>`).
  The first time a given URL appears, write a
  `[<role>] PR opened mid-run: <url>` line to both the live log file
  and spawn's stderr immediately (not buffered to exit), then
  deduplicate against a per-session seen-set so the same PR doesn't
  spam repeated lines if it's echoed again later in the stream (e.g.
  `gh pr view` re-printing it). This is deliberately broad (any PR URL
  surfacing anywhere in the stream, not just `gh pr create`'s own
  stdout) because stream-json's tool-result shape varies and missing
  the event is more expensive than one duplicate-looking line.
- In `on-the-record/hooks/directive.sh`'s "PROGRESS CHECKS" bullet,
  add the unprompted-check instruction: check a running spawn's live
  log on the orchestrator's own initiative when the session has run
  unusually long or the user's decision queue is empty, and report
  material mid-run events (PR opened — now tagged with the new log
  line, gate refusal, silent stall) without being asked. State
  explicitly that wake routing (merged-main only) is unchanged.

## Out of scope

- Any change to `wakes.py` or wake routing/detection logic.
- Changing how `ensure_pushed`'s exit-time PR report works — it stays
  as the fallback for a role that never surfaced the event mid-stream
  (e.g. it opened the PR after the stream already closed, or the regex
  missed a malformed line).
- New automated triggers (timers, cron) for the orchestrator to poll
  sessions — the directive asks for judgment-based unprompted checks
  ("unusually long", "queue empty"), not a mechanical polling loop.

## How you'll know it worked

- `python3 -m py_compile spawn.py` passes and `bash -n
  on-the-record/hooks/directive.sh` passes.
- Manual trace: feed the stream-json loop a stub line containing a
  `.../pull/<n>` URL and confirm exactly one
  `[<role>] PR opened mid-run: <url>` line reaches both the log file
  and stderr, with no duplicate on a repeated URL.
- Read `directive.sh`'s rendered PROGRESS CHECKS text end to end and
  confirm it states the unprompted-check triggers and the
  wake-routing-unchanged boundary in plain language, matching what
  phase 2 will implement.
