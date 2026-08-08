# issue-464 architecture report

Phase 2, per role-handoff contract v3 s19. Approved 2026-08-08
(`APPROVE issue-464/architecture`, single-account mode).

loop_state: done

## What was done

Wrote the ADR recording a per-row disposition for all 29 rows
(`docs/issue-464/decisions/2026-08-08-board-state-into-orchestrator-loop.md`).
This report restates that ADR's decision content at report level (per
this role's phase-2 record norm) and adds the phase-2 summary and
follow-up issue list. No code, `UNENFORCED-CLAUSES.md`, or
`docs/specs/enforcement-boundary.md` edits — those are
implementation-role follow-up, out of architecture's write scope per the
phase-1 proposal.

## Why / upstream basis

issue-464 asked for a per-row disposition table given the operator's
2026-08-08 reversal of the 2026-08-07 "board-wide GitHub state
unreachable from a local session" out-of-scope ruling. Upstream: the
phase-1 survey (`docs/issue-464/reports/architecture/survey.md`) and
proposal (`docs/issue-464/proposals/2026-08-08-per-row-disposition-table.md`),
the #444 conformance audit's class-B grouping.

## Context

`on-the-record/UNENFORCED-CLAUSES.md` records 6 board-state-unreachable
rows (#312, #325, #369, #383, #388, #407) and 23 `Prose-only` rows from
the #444 audit with no disposition. `spawn.py:roster_watchdog()` already
runs a report-only, repeating board-read tick (spawn.py:1635-1654) with
`gh`-backed judgment calls; `gates/closure_sweep.py:classify()` and
`gates/spawn_coverage.py:find_uncovered()` are pure functions built to
that exact injectable shape. The operator's 2026-08-08 statement reverses
the 2026-08-07 ruling only for the reasoning it names ("the orchestrator
... CAN call gh").

## Decision

Class A (6 rows): #369, #383, #325 re-homed as `roster_watchdog()`
orchestrator-loop mechanisms via the two existing gates; #312, #388,
#407 re-confirmed as drops (their judgment shape — comment-history
resolution, live-call failure-mode discrimination, already-recorded
CI-supplement verdict — is not the shape the reversal's reasoning
covers).

Class B (23 rows): 8 `operator-drop` (#321, #324, #329, #336, #371,
#373, #391, #392); 13 `deployed-contract+check` (#318, #320, #362, #363,
#376, #377, #379, #390, #412, #415, #416, #419, #424); 2 `shipped-hook`
(#374, #428).

Full per-row rationale and citations: the ADR.

## Consequences

`UNENFORCED-CLAUSES.md` and `docs/specs/enforcement-boundary.md` need
verdict updates for #369/#383/#325 and the class-B rows
(implementation-role follow-up, listed below). `gates/test_boundary.py`'s
`t_gate_porting_rows_are_ported_or_justified` needs tightening to
validate verdict text, not just `#N` tag presence (hunt finding, folded
into follow-up issue 1). Follow-up work is sized into separate issues,
not built in this session.

## Alternatives considered

Reversing all 6 class-A rows was rejected — the operator's stated
reasoning is scoped to the board-wide absence/drift-scan shape
`closure_sweep.py`/`spawn_coverage.py` generalize, and #312/#388/#407
have no board-wide-scan analog. A new standalone watchdog mechanism per
class-A row was rejected — `roster_watchdog()`'s existing tick plus the
two existing pure-function gates already provide the injection point.
One follow-up issue for all 13 `deployed-contract+check` rows was
rejected as oversized for one implementation session. Full detail: the
ADR.

## C4 container diagram (boundary unchanged by this decision)

```
+----------------------------------------------------------------+
|                     on-the-record plugin (repo)                 |
|                                                                  |
|  +----------------+   tick (10-15min)   +---------------------+ |
|  | spawn.py        |-------------------->| roster_watchdog()    | |
|  | (orchestrator)   |                     | report-only, gh-backed| |
|  +----------------+                     +----------+----------+ |
|                                                     |            |
|                          calls (new, follow-up)     v            |
|                                          +-----------------------+ |
|                                          | gates/closure_sweep.py | |
|                                          | gates/spawn_coverage.py| |
|                                          | (pure functions)       | |
|                                          +-----------------------+ |
|                                                                  |
|  +----------------+   session-scoped    +---------------------+ |
|  | PreToolUse/Stop  |-------------------->| local hooks (no      | |
|  | hooks             |                    | board-wide gh access)| |
|  +----------------+                     +---------------------+ |
+----------------------------------------------------------------+
```

This decision adds a call edge from `roster_watchdog()`'s existing tick
into the two existing gate modules; it does not change the plugin's
container boundary or add a new container. #312/#388/#407 stay on the
local-hook side (no board-wide access), unchanged.

## Follow-up implementation issues to file (operator action)

1. Class-A orchestrator-loop wiring — #369, #383, #325.
2. Class-A re-confirmed-drop citation — #312, #388, #407.
3. Class-B `operator-drop` recording — #321, #324, #329, #336, #371,
   #373, #391, #392.
4. Class-B `deployed-contract+check` delivery — #318, #320, #362, #363,
   #376, #377, #379, #390, #412, #415, #416, #419, #424 (13 rows; size as
   multiple issues, one per row or small batch — not one session).
5. Class-B `shipped-hook` delivery — #374 (Stop-hook implementation).
6. Class-B `shipped-hook` delivery — #428 (`spawn.py` fix +
   `on-the-record/hooks/**` equivalent).

## Open findings

None new. Carried from the phase-1 proposal's hunt notes: the
after-proposal hunt (`docs/reports/2026-08-08-hunt-per-row-disposition-table.md`,
stance 0) found `gates/test_boundary.py`'s
`t_gate_porting_rows_are_ported_or_justified` only checks tag presence,
not verdict-text validity — folded into follow-up issue 1 above.

## Hand-off

Implementation-role sessions, one branch per follow-up issue, per
contract v3. Architecture's role in this issue ends here.
