# Coding record — issue #123

code_under_review: protocol.md, protocol.ko.md
loop_state: landed

## Why

core #46 removed wake/WAKES-ON language from the contract canon
(role-handoff-contract.md): routing is orchestrator judgment reading the
board, not a machine-evaluated table. protocol.md/protocol.ko.md are mirrors
of that canon and still described the old wake-based routing — out of sync.

## Upstream basis

- core #46 (contract canon change removing WAKES-ON/wake language).
- issue-120 / README.md "Open" section — the phrasing this repo already
  settled on for describing orchestrator-judgment routing, reused in spirit
  here.
- Approved via PR #124, issue comment "APPROVE issue-123/coding"
  (2026-07-30T07:39:26Z).

## What was done

Reworded protocol.md/protocol.ko.md to drop wake/WAKES-ON routing language,
matching contract canon and the README.md phrasing from issue-120:

1. §1 "② Pick a role" (both files): "decide which role an event should wake"
   → "who runs next is a judgment call made by reading the board directly
   (record + `loop_state`)".
2. §8 "Unsettled" (both files): removed the "A WAKES-ON watcher" /
   "WAKES-ON 감시자" bullet — canon no longer names this as a future
   direction.

Record semantics (report format, `loop_state` wording) untouched, per
constraint. No files touched outside the frozen write set (protocol.md,
protocol.ko.md).

## Verification

`grep -in wake protocol.md protocol.ko.md` → no matches.

closed_checks:
- wake-mention-removal @ code_under_review above: grep -in wake protocol.md
  protocol.ko.md returns empty.

## What did not work

(nothing — edits applied cleanly on first pass)

## Hunt

Skipped: this is a two-file prose sync with no runtime behavior, no code
path, and no execution surface — a warrant-hunter probe has nothing to
exercise. Stance rotation resumes on the next code-bearing subject.

## Open findings

None outstanding. No blocking findings received against this record.
