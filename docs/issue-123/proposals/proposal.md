# Build proposal — issue #123

files: `protocol.md`, `protocol.ko.md`

## Request (paraphrased)

core #46 removed wake/WAKES-ON from the contract canon (role-handoff-contract.md):
routing is the orchestrator's own judgment from reading the board, not a
machine-evaluated table. protocol.md/protocol.ko.md are mirrors of that contract
and still describe the old wake-based routing. Sync them to canon. Keep record
semantics (report format, `loop_state`) unchanged.

## Constraints

- Only reword the wake/WAKES-ON *routing description*; leave the report-format
  and `loop_state` sections untouched.
- Match the replacement phrasing this repo already settled on in issue-120
  (`5b9e76c`, README.md "Open" section): routing is orchestrator judgment
  exercised by reading the board, not an automated watcher/table.
- protocol.ko.md must stay a faithful Korean mirror of protocol.md, not a
  independent rewrite.

## What will be done

1. `protocol.md` §1 "② Pick a role": reword from "Decide which role an event
   should wake" to describe reading the board and picking the next role by
   judgment (no "wake").
2. `protocol.md` §8 "Unsettled": remove the "A WAKES-ON watcher" bullet (the
   canon no longer names this as a future direction — core #46 settled it).
3. Mirror both edits into protocol.ko.md at the corresponding lines.

## Out of scope

- Any change to `docs/specs/role-handoff-contract.md` (already canon, lives
  upstream).
- Any code change (issue-120 already handled code/README).
- Record-format / `loop_state` wording.

## How you'll know it worked

`grep -in wake protocol.md protocol.ko.md` returns nothing, and the surrounding
sections still read coherently (reviewed by eye — this is prose, not code with
a test suite).
