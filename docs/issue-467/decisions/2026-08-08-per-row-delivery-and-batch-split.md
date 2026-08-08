# ADR: Class-B per-row delivery mapping + 4-batch split (issue-467)

## Context

The issue-464 ADR classified 13 rows as `deployed-contract+check`
(#318, #320, #362, #363, #376, #377, #379, #390, #412, #415, #416, #419,
#424): each row's 2026-08-07 proposal merged design with nothing built
behind it. Per the ADR each needs (a) contract text landed in the
deployed surface (`on-the-record/commands/run.md`) and (b) a named
regression check (a `gates/`-style local check or a shipped hook — CI
via Actions is retired and not a valid delivery surface). 13 rows exceed
one implementation session, so issue-467 also required a batch split
into follow-up issues sized for one session each.

## Decision

Reuse each row's already-designed, never-implemented proposal rather
than re-designing from scratch. Deliver a fixed `run.md` contract-text
location and a named check file per row, then group the 13 rows into 4
batches by shared gate surface so each batch's PR touches a coherent
slice of `gates/`.

### Per-row delivery

| issue | run.md contract text | named check | batch |
|---|---|---|---|
| #318 | new subsection under the approval-request section: approval requests must carry the decision-relevant fields (not just an issue link) | `gates/approval_request_shape.py` — pattern from `gates/flows.py`, checking a request body against the field list; new module (#318's proposal named no file, only a pattern) | B |
| #320 | new subsection: progress reports must state what changed, not enumerate issues/PRs | `on-the-record/hooks/report-framing-check.sh` + `gates/test_report_framing_check.py`, per PR#342's design | C |
| #362 | one paragraph in the gate-authoring section: a check must not retroactively invalidate an artifact that complied when authored | rule lands as a `gates/gates.py` module-docstring addition (per #362's own proposal) — the "check" is `t_gates_docstring_states_retroactivity_rule`, a new assertion in `gates/test_boundary.py` that the docstring contains the rule text | A |
| #363 | new subsection: a proposal addressing a symptom must also name the generator | `gates/gates.py::proposal_generator_section`, wired into `gates/ci.py`, per PR#366's design | B |
| #376 | new subsection: a landed capability must be reachable (from CI wiring and from schema) | `gates/gates.py::ci_reachable_gates` + `::schema_field_orphans`, wired into `gates/ci.py`, per PR#380's design | C |
| #377 | new subsection: the system's self-descriptions (README/run.md claims) must not go stale unchecked | `gates/claims.py` (new) + `gates/test_claims.py`, per PR#378's design | C |
| #379 | new subsection: a constraint-framed choice put to the operator must be checked before being presented as constrained | `gates/open_work.py::open_work_for` + `gates/test_open_work.py`, per PR#382's design | B |
| #390 | new subsection: a PR's green attests to the state it was verified against, not necessarily the state it lands in | `gates/test_merge_state_gate.py` (standalone, not wired into the closes-gate job), per PR#393's design | A |
| #412 | new subsection: `self-update.sh`'s self-clone fallback must not silently leave a shallow checkout | `on-the-record/hooks/self-update.sh` shallow-detection change + `on-the-record/hooks/test/self-update-shallow.bats`, per PR#420's design | A |
| #415 | new subsection: a role session must not conclude a feature is absent from reading only its own repo | `gates/repo_scope.py::check_repo_scope`, per PR#418's design | D |
| #416 | new subsection: a behavioral claim must carry provenance, not be discharged by reading code alone | `gates/acceptance_gate.py` new cases + `gates/test_acceptance_gate.py`, `gates/test_setup_failure_propagates.py`, per PR#417's design | D |
| #419 | new subsection: structurally identical code that is not textually identical is still a recurrence | `gates/gates.py::subprocess_call_shape_divergence` + sibling-marker check, wired into `gates/ci.py`, per PR#423's design | D |
| #424 | new subsection: a proposal must state what the codebase becomes after N more changes of the same shape (accumulation) | `gates/accumulation.py` (new — #424's proposal named no concrete module, least-specified row; implementer designs the check against `docs/issue-424/reports/architecture/survey.md`'s two named recurrence instances as its test fixtures) | D |

### Batch split (4 follow-up issues, one implementation session each)

- **Batch A — PR/merge-state integrity** (#362, #390, #412): all three
  gate a PR's or checkout's state-at-verification-time claim. Touches
  `gates/gates.py`, `gates/test_merge_state_gate.py`,
  `on-the-record/hooks/self-update.sh`.
- **Batch B — proposal-content-shape gates** (#318, #363, #379): all
  three gate what a proposal/request document must contain before it's
  actionable. Touches `gates/gates.py`, `gates/ci.py`, new
  `gates/approval_request_shape.py` and `gates/open_work.py`.
- **Batch C — reporting/discoverability gates** (#320, #376, #377): all
  three gate whether the system's self-reports (progress reports, gate
  reachability, stale claims) stay honest. Touches
  `on-the-record/hooks/report-framing-check.sh`, `gates/gates.py`,
  `gates/ci.py`, new `gates/claims.py`.
- **Batch D — code/claim provenance and recurrence gates** (#415, #416,
  #419, #424): all four gate a claim-about-code or a code-recurrence
  pattern. Touches `gates/repo_scope.py`, `gates/acceptance_gate.py`,
  `gates/gates.py`, new `gates/accumulation.py`. 4 rows (one more than
  the other batches) because #424 is the least-specified row and needs
  the most net-new design work alongside #419's closely related
  pattern-recurrence check — pairing them keeps `gates/gates.py`'s edits
  in one PR instead of two sessions touching the same file.

### `gates/test_boundary.py` disposition-table check

Each batch's follow-up issue also extends `gates/test_boundary.py` — an
existing, live file already carrying issue-441's boundary-coverage
checks (`t_all_gates_modules_recorded` and 8 siblings) and issue-457's
gate-porting check (`t_gate_porting_rows_are_ported_or_justified`,
test_boundary.py:146, backed by `GATE_PORTING_ISSUES` at line 137). The
class-B disposition-table check is a **new function added alongside
those**, not a replacement or a new file — the same pattern #457 used to
add its own table to this same file.

The first-landing batch adds the function (e.g.
`t_class_b_disposition_rows_cited`) plus a 13-row
`ISSUE_467_DISPOSITION_ROWS` table (mirroring `GATE_PORTING_ISSUES`'s
shape). Each subsequent batch's row(s) are already present in that table
from the first landing, so later batches only need their own check
file(s) to start existing — no further edits to `test_boundary.py`
beyond that. Whichever batch's follow-up issue lands first must state
explicitly that it is adding to `gates/test_boundary.py`, not
overwriting it, and its PR diff must show only additions to that file
(no removed `t_*` functions).

## Consequences

- Each of the 4 follow-up issues (Batch A/B/C/D above) is self-contained:
  a fixed row list, a fixed `run.md` location per row, a fixed check
  file per row, and (for whichever lands first) the shared
  `test_boundary.py` disposition-table addition.
- No row's check design is redone; #318 and #424 are flagged as the two
  rows where the implementer must resolve concrete file naming against
  cited survey/proposal material, since the original proposals named no
  file.
- `gates/test_boundary.py` gains one more long-lived table pattern
  (`ISSUE_467_DISPOSITION_ROWS`) alongside `GATE_PORTING_ISSUES`; both
  coexist as issue-467's acceptance requires this to extend, not replace,
  the existing gate.

## Alternatives considered

- **One follow-up issue for all 13 rows.** Rejected: exceeds one
  implementation session (13 rows spanning `gates/gates.py`,
  `gates/ci.py`, 4 new modules, one hook, and `test_boundary.py`); the
  issue itself requires a batch split.
- **Batching by issue number / chronological order.** Rejected: would
  scatter edits to shared files (`gates/gates.py`, `gates/ci.py`) across
  multiple unrelated batches, forcing merge-order coordination between
  otherwise-independent follow-up PRs. Grouping by gate surface keeps
  each batch's diff self-contained.
- **Re-designing #318 and #424's checks now instead of flagging them.**
  Rejected: out of scope for this issue — the proposal's job is mapping
  and batching already-sunk design work, not producing new designs;
  flagging is enough for the implementer to resolve against cited
  material.

## Follow-up issues to file (operator action)

Filing these 4 issues is operator work, not part of this session's write
scope. Each should cite this ADR and cover:

1. **Batch A — PR/merge-state integrity**: #362, #390, #412. First
   batch to land also adds the `test_boundary.py` disposition-table
   check + `ISSUE_467_DISPOSITION_ROWS` table (13 rows) — state
   explicitly in the issue that this extends, not replaces,
   `gates/test_boundary.py`.
2. **Batch B — proposal-content-shape gates**: #318, #363, #379.
3. **Batch C — reporting/discoverability gates**: #320, #376, #377.
4. **Batch D — code/claim provenance and recurrence gates**: #415,
   #416, #419, #424.

Each issue's acceptance: the row's `run.md` contract-text section
exists, its named check file exists and passes, and its rows are cited
in `ISSUE_467_DISPOSITION_ROWS` with a file-path citation (once that
table exists from whichever batch lands first).
