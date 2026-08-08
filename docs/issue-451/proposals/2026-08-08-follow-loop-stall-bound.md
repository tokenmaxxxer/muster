---
status: proposed
files:
  - spawn.py
  - test/test_silent_failure_repros.py
---

# Bound `_watch(follow=True)` by the stall-timeout contract

## Request

Follow-up from #445 finding 2. `_watch(follow=True)`'s outer loop
(spawn.py:2171-2235) has no bound of its own: each `_await_bounded()`
call inside it is individually capped by `--stall-timeout`, but when the
awaited roster entry never appears, neither of the loop's two terminal
conditions (a `session-end` event, or a *present* roster entry's dead
`wrapper_pid`) ever fires, so the loop re-polls forever. `--follow` must
honor the same stall bound the non-follow path already promises.

## Constraints

- Non-follow behavior (`_await_bounded()` and the `follow=False` branch,
  spawn.py:2192-2193) must not change — it already satisfies the
  contract and is covered by existing test/test_spawn.py tests.
- Normal follow behavior — events stream until `session-end` — must stay
  unchanged (issue's second Acceptance line); the fix only adds a bound
  for the no-progress case, not a new limit on legitimate long-running
  sessions that keep producing log activity.
- Do not treat roster-entry absence as a death/crash signal (issue #266,
  spawn.py:2227-2231 comment) — the fix must not reintroduce that
  false-positive.
- Skip condition: pure bugfix (contract v3 s19 scout skip condition 1) —
  the stall-timeout contract itself is pre-existing and fully specified
  by `_await_bounded()`; nothing here is a new design surface. See
  `docs/issue-451/reports/implementation/survey.md`.

## Rationale

Two places could hold the fix:

- **Inside `_await_bounded()` itself** — rejected. It already has a
  correct, single-call stall bound (`limit_s`, spawn.py:2119) and is
  shared with the `follow=False` path (spawn.py:2193). Changing its
  semantics to also track cross-call elapsed time would conflate "one
  call's stall" with "the follow loop's cumulative stall," and would
  risk changing non-follow behavior, which the issue's second Acceptance
  line explicitly forbids.
- **In `_watch()`'s follow loop, as a third terminal condition** —
  chosen. The loop already owns the concept of "no progress across
  iterations" (it inspects `before`/`after` offsets each cycle,
  spawn.py:2200-2202); adding a wall-clock check there — total elapsed
  time since the last iteration that made loop-visible progress — keeps
  `_await_bounded()`'s contract untouched and scopes the new bound to
  exactly the case the issue names (follow-mode looping with no roster
  entry and no events).

## What will be done

- Add a cumulative-elapsed-since-last-progress tracker to the
  `follow=True` loop in `_watch()` (spawn.py:2199-2235): reset it
  whenever an iteration consumes an event or observes log-size movement
  (i.e., whenever `_await_bounded()` did not itself time out with zero
  observed change); when total elapsed time with no such progress
  reaches `stall_timeout_min`, stop the loop and print a stall report
  (mirroring `_await_bounded()`'s own stall message shape) instead of
  looping again, returning the same way `_await_bounded()`'s stall
  branch does today (rc 0, stderr report).
- Update `test_attempt_2_follow_loop_unbounded_on_absent_roster_entry`
  (test/test_silent_failure_repros.py:86) to drive the real
  `_watch(follow=True)` (not just the loop body in isolation) with no
  roster entry ever appearing, and assert it returns within the stall
  bound with a stall report on stderr — flipping it from a reproduction
  of the bug to a regression test of the fix.

## Out of scope

- Any change to `_await_bounded()`'s own per-call contract or the
  `follow=False` path.
- Any change to crash detection (`WATCH_CRASH_RC`, dead-`wrapper_pid`
  handling) — untouched, still checked before the new stall bound would
  trigger.
- test/test_spawn.py — no edit; it's the regression fence per the
  issue's second Acceptance line and is expected to stay green
  unmodified.

## How you'll know it worked

- `test_attempt_2_follow_loop_unbounded_on_absent_roster_entry` goes
  from red (asserting the unbounded failure) to green (asserting the
  bounded, reported return) — run via `python -m pytest
  test/test_silent_failure_repros.py -k attempt_2`.
- `python -m pytest test/test_spawn.py -k watch` stays green unmodified,
  confirming normal follow behavior (event streaming to `session-end`,
  crash detection) is unchanged.
