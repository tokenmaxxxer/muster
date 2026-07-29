---
subject: issue-74
role: coding
kind: record
loop_state: executing
code_under_review: 36ae122a943d73060416d8d580b0e99fb62f9ec5
---

# issue-74 — record: revive the self-check suite

## What was done

(in progress — updated per item as landed; see items 1-7 below as they complete)

## Why

Upstream basis: issue #74 ("the self-check suite is dead: test_gates.py
crashes on its first test") + the approved proposal
`docs/issue-74/proposals/coding.md` (approver: jjongkwann, per
`docs/specs/approvers.md`). This is phase-2 execution of that frozen
proposal: rebuild the v2-shaped test fixtures to the v3 board/hypothesis
layout, retire two tests that call symbols v3 already removed, replace one
of them with `require_board()` coverage that did not exist, and make
`tests/run-orchestrate-tests.sh` safe to run in this sandbox before running
it.

## What did not work

(none yet)

## Scope decision recorded

(pending — will record the approver's choice of option (b) for wakes.py:335)

## Verification

(pending)

## closed_checks

(pending)

## Open findings

None yet — items 1-7 are still being worked through in order per the
proposal's sequencing.

## Next steps

Work through items 1-7 of `docs/issue-74/proposals/coding.md` in order,
isolating each test red before fixing it, committing per the prescribed
sequence, then set `loop_state: phase2-complete` once
`python3 test_gates.py`, `python3 test_spawn.py` (or its blocker), and
`bash tests/run-orchestrate-tests.sh` have all been observed with their
final verbatim output recorded here.

## Open-finding resolution path

No open findings block this record. The out-of-scope `wakes.py:335` defect
raised during phase-1 survey is being routed to a separate issue (#82) per
the approver's choice of option (b) in the proposal's "Scope decision
requested" section — it is not an open finding against this record, it is a
deliberately deferred, separately tracked item.
