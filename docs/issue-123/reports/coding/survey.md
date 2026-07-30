# Current-state survey — issue #123

## Scope

protocol.md / protocol.ko.md still describe a WAKES-ON / "pick a role to wake"
mechanism that core #46 removed from the contract canon (role-handoff-contract.md):
routing is now the orchestrator's own judgment from reading the board, not a
machine-evaluated table. issue-120 already did the equivalent removal at the
code/README level in this repo (`5b9e76c`); protocol.md/.ko.md were not touched
then and are the last mirrors carrying the old wording.

## Write set (frozen)

- `protocol.md`
- `protocol.ko.md`

Both are paraphrase-mirror pairs of the same content — one translation unit, not
independently producible pieces. Width = 1 (freelunch: lean solo, no fan-out).

## Wake-mentions found

`protocol.md`:
- L34: "**② Pick a role.** Decide which role an event should wake." — describes
  wake-based role selection.
- L225-229 ("## 8. Unsettled"): "A WAKES-ON watcher" bullet — describes an
  unbuilt future automated watcher carrying contract §3's routing table.

`protocol.ko.md`: mirrors of the same two spots (L204 area, and the analogous
"② 역할을 고른다" line).

## What must NOT change

Record semantics (report format, `loop_state` field, the board-reading model in
§2) are canon and unaffected by core #46 — issue #123 explicitly says to keep
them. Only the wake/WAKES-ON *description* of how routing happens is in scope.

## Reference wording already established in this repo

README.md (issue-120, `5b9e76c`) already rewrote the equivalent passage:
"Who runs next is orchestrator judgment, not a routing table. `spawn.py drive`
no longer picks a role automatically — it stops immediately, every time.
Carrying a subject end to end means the orchestrating conversation reads the
board … and spawns the next role itself." This is the canon phrasing to mirror
into protocol.md/.ko.md's own voice.

## Scout

Skipped — pure doc-sync mirroring an already-decided, already-implemented canon
change (core #46, and this repo's own issue-120 precedent for the exact
replacement wording). No open design decision.
