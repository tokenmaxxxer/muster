---
issue: 114
role: coding
code_under_review: HEAD
loop_state: landed
---

# coding record — issue-114

## Scope

Implement the approved proposal (PR #116, APPROVE issue-114/coding):
event-exit spawn + `watch` subcommand, bounded by `--stall-timeout`
(default 5 minutes), stall non-terminal.

## why

Issue #114: a role's PR-opened event sat invisible mid-run because the
orchestrator is only re-invoked when a spawned process EXITS — a live
log line is unobservable no matter how early it lands. The approved
proposal (docs/issue-114/proposals/, PR #116) reworked the ask into
exit-shaped notification: bound every call (`role task` and `watch`) to
return at the first material event or a stall timeout, so visibility
becomes mechanical block-until-something-happens instead of a judgment
call about when to poll.

## upstream-basis

- docs/issue-114/proposals/*.md — the frozen contract: `events.jsonl`
  shape, `events.offset` semantics, `--stall-timeout` flag, bounded
  fork/detach requirement, stall non-terminal/re-arm behavior.
- PR #116 review feedback (folded into the proposal already): event-exit
  over log-line notification; bounded-return requirement for silent
  stalls/hangs.
- issue-115 (`approve-scope` in `spawn.py`, merged as PR #118 ahead of
  this branch) — rebased onto `origin/main` before starting so this
  work sits on top of it, per the invoking prompt's instruction.

## What was done

- `spawn.py`: `_spawn_one` gained `bounded`/`stall_timeout_min` params.
  When the direct `spawn.py <role> "<task>" --issue <n>` call is bounded,
  it forks right before launching the role's `claude` subprocess: the
  parent returns as soon as the first material event lands in
  `<workspace>.events.jsonl` or the stall timeout elapses
  (`_await_bounded`); the child calls `os.setsid()` and continues the
  existing drain-then-finalize body unchanged, appending `pr-opened`
  (regex on stream lines) and `gate-refusal` (reusing `_DENIAL_RE`)
  events live, and a `session-end` event (with the classified outcome)
  as its last act before `os._exit`. `Popen(..., start_new_session=True)`
  isolates the role session's process group so an early parent return
  can't signal it away.
- New `spawn.py watch --issue <n> [--role <role>] [--stall-timeout <min>]`
  resolves the workspace via a small `runs/workspaces.json` index
  (written alongside the roster entry, survives roster removal), then
  calls the same `_await_bounded`. A `stall` report never advances
  `events.offset`, so re-arming `watch` re-checks the same window.
  `drive()`'s code path is untouched (still calls `_spawn_one` with
  `bounded` defaulting to `False`), so its serial full-blocking loop
  semantics are unaffected.
- `on-the-record/hooks/directive.sh`: PROGRESS CHECKS bullet replaced —
  re-arm `watch` after every event that isn't `session-end` (stall
  included), states the wake-routing boundary is unrelated/unchanged.

## What did not work

- First draft let both the parent (early-return) and child (continuing)
  branches hit the same `finally: os.unlink(settings)`. The parent would
  delete the still-needed settings tempfile racing against the child's
  `claude` subprocess reading it at startup. Fixed with an
  `is_parent_return` flag that skips the unlink in the parent branch —
  only the child (which owns the subprocess through completion) deletes
  it.

## Verification run (this session, no-mock confirmation)

- `python3 -m py_compile spawn.py` — passes.
- `bash -n on-the-record/hooks/directive.sh` — passes.
- Stub trace of `_await_bounded`/`_append_event`: appended a `pr-opened`
  line, confirmed one report + `events.offset` advances by exactly one;
  confirmed a `stall` case (short timeout, no log growth) returns within
  bound and leaves `events.offset` unmoved on both an initial call and a
  re-armed call.
- `_watch`: confirmed workspace-index resolution (with and without
  `--role`, and a not-found issue reports a clean error).
- Fork-detach trace: forked, parent returned immediately via
  `_await_bounded`; a separately-scheduled child slept 1.5s, wrote to
  the session log, and appended `session-end` — the parent's bounded
  wait picked it up, proving the child kept running (and its writes
  landed) after the point where a real orchestrator turn would have
  already ended.

## closed_checks

- check: fork-detach survives early parent return — code_sha: HEAD —
  closed via the fork-trace run above.
- check: settings-tempfile double-unlink race — code_sha: HEAD — closed
  via the `is_parent_return` guard + the traces above (no exception
  raised in either branch).
- check: forked child's stdout/stderr fd inheritance — code_sha: HEAD —
  warrant-hunter (stance: fork-boundary composition regression) found
  that the role `claude` subprocess (`Popen` in `_spawn_one`) inherited
  the caller's stdout/stderr fds unredirected, so a caller piping/
  capturing spawn.py's output (the realistic case: the orchestrator's
  tool runner) would still block for the pipe's EOF until the whole
  session ends — silently defeating the bounded-return feature this
  issue exists to deliver. Fixed by `os.dup2`-ing the forked child's
  fd 0/1/2 to `/dev/null` right after `os.setsid()`, before `Popen()`.
  Reproduced the hang and the fix with a standalone fork+Popen(sleep 3)
  trace piped through `> out.log`: pre-fix the redirect blocked for the
  sleep's duration; post-fix it returned in ~0.04s.

## Open Findings

None outstanding. `watch`'s multi-role disambiguation is best-effort
(errors out asking for `--role` when more than one role is recorded for
the same issue in `runs/workspaces.json`); no known gap against the
proposal's acceptance criteria.

## Hunt

warrant-hunter dispatched pre-delivery (stance: composition regression /
silent failure at the fork boundary).
