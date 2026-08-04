---
kind: coding-record
code_under_review: gates/ci.py, gates/test_closes_gate_ci.py, test_spawn.py,
  docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md
loop_state: in-progress
---

# Implementation record — issue #271

## Why

Phase 2, executing the approved proposal
(`docs/issue-271/proposals/2026-08-04-closing-trigger-surface-coverage-and-phase-predicate-separation.md`),
approved via issue-level comment `APPROVE issue-271/implementation`
(single-account mode, role-handoff contract v3, PR author and approver
both jjongkwann). Three independent 2026-08-04 observations (issues #245,
#262, #266) converged on the same gap: the plan-aware Closes gate only
inspects the PR body, missing the commit-message vector that twice
auto-closed an issue for real; a second, structural defect makes the
existing phase-1 "no closing keyword" check unreachable because phase
itself is derived from the same keyword predicate the check is supposed
to police.

## What was done

(in progress — filled in as work lands)

## What did not work

None yet.

## Open findings

None yet — hunt dispatched at end of phase 2 per role directive.

## Next steps

Implement `gates/ci.py`'s approval-derived phase signal and title/
commit-message surface widening, the `gates/test_closes_gate_ci.py`
red-green regression pair, the `test_spawn.py` drain-guard restoration,
the decision doc, and the operations handbook update, then land the
final record update (`loop_state: landed`).

## Open-finding resolution path

No findings open yet; none to resolve.
