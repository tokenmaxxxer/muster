---
status: proposed
files:
  - docs/issue-464/decisions/2026-08-08-board-state-into-orchestrator-loop.md
  - docs/issue-464/reports/architecture.md
---

## Scouting

Scouting skipped (survey.md's Scouting section carries the full
reasoning): no design decision open that an external exemplar sweep could
inform — this deliverable classifies this repo's own governance rows
against its own existing mechanisms, not a product-shaped or
externally-comparable field.

## Intent

Produce the per-row disposition table issue-464 asks for: for class A
(the 6 board-state-unreachable rows), decide which become
`spawn.py`-orchestrator-loop mechanisms per the operator's 2026-08-08
reversal of the 2026-08-07 out-of-scope rulings; for class B (the 23
prose-only rows from the #444 audit), assign each a disposition —
`shipped-hook`, `deployed-contract+check`, or `operator-drop`. This
session (architecture, phase 1) delivers the disposition decision and the
ADR recording it; the code that implements each disposition is follow-up
work for an implementation-role session, sized per group.

## Constraints

- Architecture's write scope is `docs/issue-464/decisions/**` plus its own
  report; it does not edit `spawn.py`, `gates/**`, or
  `on-the-record/UNENFORCED-CLAUSES.md` — those are implementation-role
  work, filed as follow-up issues per the disposition groups below.
- The operator's 2026-08-08 statement reverses the 2026-08-07
  out-of-scope ruling only for the reasoning it names — "the orchestrator
  ... CAN call gh" — which applies to the board-wide
  absence/drift-scan shape `closure_sweep.py`/`spawn_coverage.py`
  generalize. It does not automatically extend to board-state rows of a
  structurally different shape (see survey: #312, #388, #407).
- Every class-A row needs a mechanism-or-drop; every class-B row needs
  exactly one of the three named dispositions with a file-path citation
  (per the issue's acceptance, gated by `gates/test_boundary.py`).

## What will be done (phase 2, after Approve)

1. **Class A disposition** (survey: `docs/issue-464/reports/architecture/survey.md`):
   - #369, #383, #325 → re-homed as `spawn.py:roster_watchdog()`
     board-wide mechanisms. `roster_watchdog` already runs on the
     orchestrator's repeating board-read tick and is already
     report-only/observe-only by contract — the same shape
     `gates/closure_sweep.py` and `gates/spawn_coverage.py` already
     implement as pure functions. Follow-up issue: wire
     `closure_sweep.classify()` and `spawn_coverage.find_uncovered()`
     into a watchdog-tick call, surfaced the same way watchdog anomalies
     are today (printed + non-zero exit), still nothing auto-closed.
     `UNENFORCED-CLAUSES.md`'s `closure_sweep.py`/`spawn_coverage.py`
     top-table rows and #369/#383/#325 gate-porting rows get their
     verdict changed from "out of scope" to the new mechanism citation.
   - #312, #388, #407 → **not reversed**. Their board-state-unreachable
     reasoning is a different shape (issue-comment-history resolution,
     live-`gh`-call failure-mode discrimination, and an already
     `contract, CI-supplement`-verdict advisory check, respectively) that
     the operator's stated "orchestrator can call gh" reasoning does not
     cover. Recorded as a re-confirmed drop: their existing
     `UNENFORCED-CLAUSES.md` rows stand, with a citation back to this
     ADR explaining why the reversal does not reach them.
2. **Class B disposition**, per the #444 audit's own follow-up text (see
   survey for full grouping):
   - `operator-drop` — #321, #324, #329, #336, #371, #373, #391, #392
     (8 rows). Dev-process/record-keeping issues the audit already argues
     have no consumer-facing behavior to gate; this ADR is the operator
     confirmation the disposition table requires. Recorded in
     `UNENFORCED-CLAUSES.md` citing this issue.
   - `deployed-contract+check` — #318, #320, #362, #363, #376, #377,
     #379, #390, #412, #415, #416, #419, #424 (13 rows). Each needs a
     `gates/` check plus `run.md` contract text with a named regression
     check, per #441's delivery mechanism — sized as one follow-up issue
     per row or small batch (13 rows is too large for one implementation
     session).
   - `shipped-hook` — #374, #428 (2 rows). Both the audit already flags
     as needing actual runtime code (a Stop-hook; a `spawn.py` fix plus
     an `on-the-record/hooks/**` equivalent) rather than a `gates/` check
     — filed as their own follow-up issues.
3. Write the ADR (`docs/issue-464/decisions/2026-08-08-board-state-into-
   orchestrator-loop.md`) recording all of the above with the full
   per-row table, and the phase-2 architecture report.
4. File the follow-up issues for each group (implementation role,
   separate sessions) — not created in this session; the ADR lists what
   they must cover so filing is mechanical.

## Out of scope

- Any code change to `spawn.py`, `gates/**`, `on-the-record/hooks/**`, or
  `UNENFORCED-CLAUSES.md` — implementation-role follow-up work.
- Re-litigating #312/#388/#407's verdicts beyond confirming the reversal
  doesn't reach them.
- Re-auditing whether the #444 classification of any of the 23 rows as
  Prose-only is itself correct — taken as given per this issue's framing.

## How you'll know it worked

- `docs/issue-464/decisions/2026-08-08-board-state-into-orchestrator-loop.md`
  contains one row per class-A issue (mechanism-or-drop) and one row per
  class-B issue (disposition + file-path citation to the follow-up plan),
  matching `gates/test_boundary.py`'s eventual parity/disposition-table
  tests once implementation lands.
- `docs/issue-464/reports/architecture.md` records the phase-2 summary
  (written only after Approve, per contract v3 s19).

## What did not work

(none yet — phase 2 not started)

## Hunt notes

`docs/reports/2026-08-08-hunt-per-row-disposition-table.md` (after-proposal
stance 0) found that `gates/test_boundary.py`'s
`t_gate_porting_rows_are_ported_or_justified` only checks that the bare
`#N` tag appears somewhere in an `UNENFORCED-CLAUSES.md` row — it does not
validate the verdict text, so a placeholder or garbled row would pass just
as well as a real mechanism citation. The follow-up issue that rewrites
#369/#383/#325's rows to cite the new `roster_watchdog` mechanism should
also tighten this check (e.g. require the row's text to match one of the
disposition vocabularies) so the "gated by `gates/test_boundary.py`"
acceptance claim actually holds.
