---
kind: coding-record
code_under_review: spawn.py, test_spawn.py, docs/issue-224/decisions/watch-crash-exit-code.md
loop_state: executing
---

# Implementation record — issue #266

## Why

Phase 2, executing the approved proposal
(`docs/issue-266/proposals/roster-lifetime-vs-absence-signal.md`, upstream
basis for this record), approved via issue-level comment
`APPROVE issue-266/implementation` (single-account mode, role-handoff
contract v3, PR author and approver both jjongkwann). Delivering
alternative (b) exactly as approved: `_watch()`'s post-processing tail
misreports a normally-completing session as crashed because its death
determination (spawn.py:1903) treats a temporarily-absent roster entry as
a death signal.

## What was done (in progress)

Not yet started — this record is written first, per contract v3 s19/
implementation-role directive, before any code write. Planned sequence:

1. Add the entry-absent regression test to `test_spawn.py::WatchFollow`
   against the current (unfixed) `spawn.py:1903` and run it to confirm
   `WATCH_CRASH_RC` (red).
2. Narrow `spawn.py:1903`'s condition to drop the `roster_entry is None`
   branch.
3. Re-run the new test to confirm `0` (green), plus the full `WatchFollow`
   class for regressions.
4. Update the trigger wording in
   `docs/issue-224/decisions/watch-crash-exit-code.md`.

## What did not work

None yet.

## Open findings

None yet — hunt not yet dispatched.

## Next steps

Execute the four-step sequence above; update this record's `loop_state`
to `landed` and fill in results once done.

## Open-finding resolution path

N/A — no open findings yet.
