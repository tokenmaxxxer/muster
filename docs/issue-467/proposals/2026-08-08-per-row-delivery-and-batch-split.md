---
status: landed
files:
  - docs/issue-467/decisions/2026-08-08-per-row-delivery-and-batch-split.md
  - docs/issue-467/reports/architecture.md
---

## Scouting

Scouting skipped — see survey.md's Scouting section. No externally-comparable
design decision; this maps existing internal proposals onto two named
delivery surfaces and splits by session sizing.

## Intent

issue-467 (step 1, architecture) asks for two things: (1) for each of the
13 `deployed-contract+check` rows from the issue-464 ADR (#318, #320,
#362, #363, #376, #377, #379, #390, #412, #415, #416, #419, #424), a
per-row delivery mapping — what `run.md` contract text and what named
`gates/`-style check each needs; (2) a batch split of the 13 rows into
follow-up implementation issues, since one session cannot hold all 13.
This session (architecture, phase 1) delivers the mapping and split as an
ADR; filing the follow-up issues and building the gates is implementation
follow-up work, per the same contract v3 s19 split issue-464 used.

## Constraints

- Every row's delivery must name concrete files under `gates/` (or
  `on-the-record/hooks/**` for the two rows already hook-shaped in their
  original proposal) plus the `run.md` section it lands in — a prose
  disposition without a file-path citation does not satisfy issue-467's
  acceptance (`gates/test_boundary.py` disposition-table check).
- Reuse each row's already-designed, never-implemented proposal (survey
  table) rather than re-designing from scratch — the design work is
  already sunk; only delivery + batching is this issue's job.
- 13 rows split into batches sized for one implementation session each
  (~3-4 rows), grouped by shared gate surface so a batch's PR touches a
  coherent slice of `gates/` rather than scattered unrelated files.
- Architecture's write scope stays `docs/issue-467/decisions/**` plus its
  own report — no edits to `gates/**`, `on-the-record/commands/run.md`,
  or `on-the-record/UNENFORCED-CLAUSES.md` in this issue.

## What will be done (phase 2, after Approve)

Write the ADR (`docs/issue-467/decisions/2026-08-08-per-row-delivery-and-
batch-split.md`) recording, per row: the `run.md` contract-text location
and gist, the named check file(s), and which batch it belongs to. Content
(full detail restated from survey.md; citations point at each row's
already-merged proposal):

### Per-row delivery

| issue | run.md contract text | named check | batch |
|---|---|---|---|
| #318 | new subsection under the approval-request section: approval requests must carry the decision-relevant fields (not just an issue link) | `gates/approval_request_shape.py` — pattern from `gates/flows.py`, checking a request body against the field list; new module (#318's proposal named no file, only a pattern) | B |
| #320 | new subsection: progress reports must state what changed, not enumerate issues/PRs | `on-the-record/hooks/report-framing-check.sh` + `gates/test_report_framing_check.py`, per PR#342's design | C |
| #362 | one paragraph in the gate-authoring section: a check must not retroactively invalidate an artifact that complied when authored | rule lands as a `gates/gates.py` module-docstring addition (per #362's own proposal) — the "check" here is `t_gates_docstring_states_retroactivity_rule`, a new assertion in `gates/test_boundary.py` that the docstring contains the rule text | A |
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

Each batch's follow-up issue also extends `gates/test_boundary.py` — an
**existing, live file** already carrying issue-441's boundary-coverage
checks (`t_all_gates_modules_recorded` and 8 siblings) and issue-457's
gate-porting check (`t_gate_porting_rows_are_ported_or_justified`,
test_boundary.py:146). The class-B disposition-table check is a **new
function added alongside those**, not a replacement or a new file — same
pattern #457 used to add its own table to this same file. First-landing
batch adds the function (e.g. `t_class_b_disposition_rows_cited`) plus a
13-row `ISSUE_467_DISPOSITION_ROWS` table (mirroring
`GATE_PORTING_ISSUES`'s shape at test_boundary.py:139); each subsequent
batch's row(s) were already present in that table from the first landing,
so later batches only need their own check file to start existing, not
further edits to `test_boundary.py`. The follow-up issue for whichever
batch lands first must state explicitly that it is adding to
`gates/test_boundary.py`, not overwriting it, and its PR diff must show
only additions to that file (no removed `t_*` functions).

## Out of scope

- Building any gate, hook, or `run.md` edit — implementation-role
  follow-up, one session per batch.
- Filing the 4 follow-up issues — not created in this session; the ADR
  lists what they must cover so filing is mechanical (operator action,
  matching issue-464's pattern).
- Re-designing any row's check shape beyond what its own already-merged
  proposal specifies, except #318 and #424 where the original proposal
  named no concrete file (flagged above; implementer resolves against the
  cited survey material).
- Building the `gates/test_boundary.py` disposition-table check itself —
  named as a deliverable item per batch above, not built here.

## How you'll know it worked

- `docs/issue-467/decisions/2026-08-08-per-row-delivery-and-batch-split.md`
  contains one row per issue (delivery mapping) and the 4-batch split,
  matching this proposal's tables.
- `docs/issue-467/reports/architecture.md` records the phase-2 summary
  (written only after Approve, per contract v3 s19).
- The 4 follow-up issues, once filed and closed, leave
  `gates/test_boundary.py`'s new disposition-table check passing with a
  file-path citation for all 13 rows — satisfying issue-467's acceptance.

## What did not work

- First `docs/issue-467/reports/architecture.md` write was refused by
  `record-fields-gate.sh` (missing what-was-done/why/loop_state/open-
  findings sections) — added those sections per contract §20.
- Second write refused by `adr-content-gate.sh` (loop_state left
  proposed/scope-proposed, so the record read as decision-bearing and
  needed Context/Decision/Consequences/Alternatives-Considered + a C4
  diagram) — added those sections and a `mermaid C4Context` block.
- Third write refused by `sequence-gate.sh`: this proposal's original
  scouting line ("Skipped — see survey.md's Scouting section") did not
  match the gate's exact skip-phrase list — changed the wording to
  "Scouting skipped" to match `SKIP_PHRASES` verbatim.
