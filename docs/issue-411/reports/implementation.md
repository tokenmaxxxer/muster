---
code_under_review:
  - on-the-record/hooks/stop-gate.sh
  - on-the-record/hooks/hooks.json
  - tests/test_stop_gate.sh
  - docs/issue-411/decisions/2026-08-07-stop-hook-enforcement-scope.md
loop_state: phase-2-complete
---

References #411.

## What was done

Implemented the approved proposal
(`docs/issue-411/proposals/2026-08-07-stop-hook-structural-check.md`)
exactly:

1. `on-the-record/hooks/stop-gate.sh` — new `Stop` hook, orchestrator-only
   (pass-through when `CLAUDE_ROLE` set), fires only on approval-shaped
   `last_assistant_message`, checks for issue ref (`#\d+`) / change clause
   / risk clause, emits `hookSpecificOutput.additionalContext` naming the
   missing clause(s) rather than blocking, fail-closed via `trap`.
2. `on-the-record/hooks/hooks.json` — added a `Stop` entry pointing at
   `stop-gate.sh`.
3. `tests/test_stop_gate.sh` — behavioral test, 3 fixtures: (a)
   approval-shaped, missing risk clause → `additionalContext` names it;
   (b) approval-shaped, all three clauses → silent exit 0; (c)
   non-approval-shaped → pass-through, exit 0, no output.
4. `docs/issue-411/decisions/2026-08-07-stop-hook-enforcement-scope.md` —
   coverage record: 1 of 6 requirements (#318, structural subset only)
   gets real firing/tested coverage from this hook; 5 of 6 (#320, #341,
   #371, #373, #379) remain open, each with its own reason, per #310.

## Why

Issue #411: six prior requirements assumed some hook inspects the
orchestrator's conversational output; none did (`hooks.json` declared no
`Stop` entry). The proposal's chosen approach — one structurally-checkable
item (#318's issue-ref/change/risk clauses), non-blocking
`additionalContext` on violation — was picked over building all three
sketched checks (#318/#320/#379) because #320 and #379 are honesty/framing
judgment calls a regex heuristic cannot reliably make, and over
`decision: "block"` because a structural heuristic misfiring on an
unusually-phrased but legitimate reply shouldn't discard the whole turn.

## Concrete upstream basis

`docs/issue-411/proposals/2026-08-07-stop-hook-structural-check.md`
(approved, status: proposed → phase-2 opened per orchestrator's phase-2
instruction), itself built on `docs/issue-411/reports/implementation/survey.md`.

## What did not work

None.

## Open findings

None outstanding. Warrant-hunter dispatched before landing (see below);
no blocking finding returned to resolve.

## Doc placement (completed)

- [x] `docs/issue-411/decisions/2026-08-07-stop-hook-enforcement-scope.md`
      — coverage decision record, written per the proposal's write set.

## Closed checks

- `tests/test_stop_gate.sh` run directly: 3/3 fixtures pass (missing-clause
  caught, compliant silent, non-approval pass-through).
  code_sha: (see code_under_review above; test run at implementation time).

## Generator

Hand-written bash + embedded Python, following `deliverable-guard.sh`'s
existing house style (trap fail-closed, `CLAUDE_ROLE` pass-through, cheap
prefilter before Python). No code-generation tool used.

## Where else this pattern occurs

Searched for other `Stop` hook declarations or `last_assistant_message`
consumers in the repo before this change: none existed (`hooks.json` had
only `SessionStart`/`UserPromptSubmit`/`PreToolUse`; no
`check()`/`*-check.sh`/`*-guard.sh` referencing `last_assistant_message`).
This is the first and only site touching that surface. Test-stub check:
`tests/run-orchestrate-tests.sh`'s existing manifest test only asserts the
three prior hook *keys* are declared (never that they fire) — the same
"declared but not verified to fire" gap #411 names, for the pre-existing
three hooks. That test is untouched here (out of scope per the approved
proposal's "Out of scope" section) and remains structural-only for those
three; `test_stop_gate.sh` is the behavioral one for the new `Stop` hook.

## Next steps

None required for this proposal's scope. Follow-ups explicitly deferred
by the proposal (not this session's to build): #320/#373's judgment-call
checks, #341's stale-premise reopen, #379's re-check-observability
problem, #371's `spawn.py` status-computation fix — all recorded as open
in the decision doc with per-item reasons.

## Rationale for deviations

None — implementation follows the approved proposal as written, no
scope-exceeded stop and no alternative swap.
