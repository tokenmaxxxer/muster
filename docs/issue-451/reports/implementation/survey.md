---
subject: issue-451
---

# Survey: bound `_watch(follow=True)` by the stall-timeout contract

Skip condition: this is a pure bugfix (contract v3 s19 / scout-directive skip
condition 1). The non-follow path's `--stall-timeout` contract already
exists and is fully specified (`_await_bounded`, spawn.py:2111); the
requirement is to make `--follow` honor that same, already-designed
contract instead of looping past it. No new design surface — no new
flags, no new UX, nothing to scout against external exemplars.

## Current state

`_watch()` (spawn.py:2171-2235) has two paths:

- `follow=False`: returns whatever `_await_bounded()` (spawn.py:2111)
  returns — one event, or a stall report after `stall_timeout_min` of no
  log-size change. This already satisfies the stall contract.
- `follow=True`: calls `_await_bounded()` in a `while True:` loop
  (spawn.py:2199-2235). Each call is itself bounded by
  `stall_timeout_min`, but the outer loop has no bound of its own — it
  treats every `_await_bounded()` return as "keep polling" unless one of
  two terminal conditions fires:
  1. the consumed event (or any pending unconsumed event) is
     `session-end` (spawn.py:2203-2218), or
  2. a *present* roster entry's `wrapper_pid` is dead (spawn.py:2225-2235).

  When the roster entry is absent (`roster_entry` is `None`, e.g. crash
  before registration, or the entry key never existed), `pid` stays
  `None`, condition 2 never fires by design (spawn.py:2227-2231, deliberate:
  "명부 엔트리 부재는 사망 신호로 안 쓴다(이슈 #266)" — absence must not
  be mistaken for death). Condition 1 also never fires because no event
  is ever produced. Result: the `while True:` loop just keeps calling
  `_await_bounded()` forever, each call individually bounded but the sum
  unbounded — this is `test_attempt_2_follow_loop_unbounded_on_absent_roster_entry`
  in test/test_silent_failure_repros.py:86 (currently asserts the failure
  mode directly, `terminal_hits == 0`; the issue requires flipping this to
  assert a bounded, reported return).

## Write set implications

- `spawn.py`: `_watch()`'s follow branch (spawn.py:2199-2235) needs a
  third terminal condition — an overall stall bound independent of
  roster-entry presence — that returns a stall report instead of
  looping past `stall_timeout_min`. `_await_bounded()` itself (spawn.py:2111)
  is not the right place: it already has a correct one-call stall bound
  and is also called from the non-follow path (spawn.py:2193), which
  must stay unchanged (issue's second Acceptance line).
- `test/test_silent_failure_repros.py`: attempt-2 (line 86) is the test
  the issue names — it must flip from asserting the unbounded failure to
  asserting the bounded, reported return within the stall bound, driving
  the real `_watch(follow=True)` (not just the loop body in isolation, as
  today) so it exercises the actual fix.
- `test/test_spawn.py`: no edit expected — its existing watch tests are
  the regression fence (issue's second Acceptance line: "existing
  test/test_spawn.py watch tests stay green"). Confirmed present:
  `grep -n "def test.*watch" test/test_spawn.py` finds coverage for
  session-end and crash termination of the follow loop.
- No new dependency, no new env var, no schema/migration.

## What "bounded by stall_timeout" means for the no-progress-at-all case

`_await_bounded()`'s own stall clock resets on log **byte-size** change,
not on roster-entry appearance — so a log that's merely quiet (before the
roster entry lands) already accumulates toward one call's stall bound.
The follow loop's fix is: track wall-clock time since the last iteration
that made *loop-visible* progress (event consumed, or a fresh
`_await_bounded` call's own last_change reset — i.e., simplest: track total
elapsed since follow started, or since the last non-stall
`_await_bounded` return) and stop once that exceeds `stall_timeout_min`,
regardless of roster-entry state. Exact mechanism (cumulative-elapsed
counter vs. re-using `_await_bounded`'s per-call clock) is an
implementation-time decision within this bugfix, not a design choice
requiring proposal-level alternatives — there is exactly one existing
contract (`stall_timeout_min`) to honor and one place to check it.

## Warrant-hunter dispatch

docs-only, no after-proposal dispatch — every path touched by this
transition (survey.md, the proposal file) is under `docs/`.
