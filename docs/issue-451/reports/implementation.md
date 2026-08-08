---
code_under_review:
  - spawn.py
  - test/test_silent_failure_repros.py
loop_state: phase-2-complete
---

# Phase-2 implementation record: bound `_watch(follow=True)` by the stall-timeout contract

Proposal: docs/issue-451/proposals/2026-08-08-follow-loop-stall-bound.md

## Why

#445 finding 2: `_watch(follow=True)`'s outer loop (spawn.py:2171-2235)
had no bound of its own — each `_await_bounded()` call inside it is
individually capped by `--stall-timeout`, but when the awaited roster
entry never appears, neither of the loop's two terminal conditions (a
`session-end` event, or a present roster entry's dead `wrapper_pid`)
ever fires, so the loop re-polled forever. `--follow` must honor the
same stall bound the non-follow path already promises, per the approved
proposal.

## What was done

- spawn.py:2194-2242 — added a cumulative-elapsed-since-last-progress
  tracker (`last_progress`, `stall_limit_s`) to the `follow=True` loop in
  `_watch()`. Reset on either offset advance (an event was consumed) or
  log-file size change, matching `_await_bounded()`'s own progress
  signal but tracked across iterations instead of within one call. A new
  terminal branch fires when total elapsed time with no such progress
  reaches `stall_timeout_min`, printing a stall report to stderr
  (mirroring `_await_bounded()`'s own message shape) and returning 0 —
  the loop no longer re-polls forever when the awaited roster entry
  never appears.
- `_await_bounded()` itself, the `follow=False` path, and the existing
  session-end / dead-`wrapper_pid` terminal branches are unchanged.
- test/test_silent_failure_repros.py:86 —
  `test_attempt_2_follow_loop_unbounded_on_absent_roster_entry` rewritten
  to drive the real `_watch(follow=True)` (workspace-index entry
  registered, no roster entry, no events) instead of manually stepping
  the loop body, and now asserts `rc == 0` (bounded return) instead of
  asserting the unbounded failure.

## Doc-placement ladder

- No new env var, config key, dependency, or migration — nothing to add
  to a handbook.
- No library/format choice over a named alternative and no public
  signature/wire-format change beyond internal control flow — no new
  `docs/issue-451/decisions/` entry.
- No benchmark/investigation numbers produced — no
  `docs/issue-451/reports/` entry beyond this record.
- [x] This record itself, phase-2 output per contract v3 s19.

## What did not work

None.

## Verification run (this session, generation-time confirmation only)

- `python3 -m pytest test/test_silent_failure_repros.py -k attempt_2 -q`
  → 1 passed.
- `python3 -m pytest test_spawn.py -k watch -q` → 24 passed (non-follow
  and all follow-mode regression tests, including crash detection and
  the #266/#255 ordering tests, stay green unmodified).
- `python3 -m pytest test/test_silent_failure_repros.py -q` → 4 passed
  (full repro file, all attempts).

## Hunt record

Before-landing dispatch (stance 3, `assume the rule as written cannot
hold — find the state nothing maintains`) ran and returned one finding,
recorded at
docs/issue-451/reports/implementation/hunt-2026-08-08-follow-loop-stall-bound.md
(the hunter could not write to the requested cross-role path due to
board-gate.sh and filed under its own role's allowed path instead,
noting that redirection in its own record).

Finding: if the session log keeps growing (any bytes appended) with no
roster entry ever appearing and no events ever produced, `_await_bounded()`
resets its own internal stall timer on every size change and never
returns, so the new outer cumulative-stall check (which only runs
between `_await_bounded()` calls) is never reached — the follow loop
stays unbounded in that specific sub-case.

Disposition: not a defect against the approved scope. The proposal's
Constraints section states explicitly: "the fix only adds a bound for
the no-progress case, not a new limit on legitimate long-running
sessions that keep producing log activity" — ongoing log growth is, by
the proposal's own design, treated as progress and must NOT be
stall-bounded, matching `_await_bounded()`'s pre-existing (unchanged)
per-call behavior. The issue's described failure mode (#445 finding 2)
is the no-progress case — no roster entry, no events, AND no log
growth — which this fix does bound (confirmed by the passing
`test_attempt_2_follow_loop_unbounded_on_absent_roster_entry`). A log
that grows forever with no events is a pre-existing property of
`_await_bounded()` shared identically by the `follow=False` path, which
this proposal was constrained not to touch. Resolved by reference to
the proposal's own stated scope, not by a code change.

closed_checks:
- name: before-landing warrant hunt (stance: state-nothing-maintains)
  code_sha: 5c0e435b12f0d7e9d401e7d1501c5b32307c719b

## Open findings

None outstanding — the one hunt finding above is resolved by scope
reference above, not left open.

## Next steps

None — implementation, test, and record are complete and ready for PR
review/merge. If the before-landing hunt (dispatched after this record
lands) returns a finding, it will be reported at the landing exchange
per the warrant directive.
