# issue-467 architecture survey (phase 1)

## Scouting

Skipped. No design decision open that an external exemplar sweep could
inform — this deliverable maps 13 already-fully-designed but
never-delivered proposals onto two named delivery surfaces
(`on-the-record/commands/run.md` contract text, a `gates/`-style named
regression check) per the issue-464 ADR, and splits them into
implementation-sized batches. Not a product-shaped or
externally-comparable decision.

## Current state

The 13 rows are the `deployed-contract+check` class from the issue-464
ADR (`docs/issue-464/decisions/2026-08-08-board-state-into-orchestrator-loop.md`),
sourced from the #444 conformance audit
(`docs/issue-444/reports/conformance-review.md`). Each row's 2026-08-07
proposal was **merged as a proposal/survey document only** — no gate, no
contract text landed. Concretely, each already has a fully-specified,
unbuilt design in its own `docs/issue-<n>/proposals/*.md`:

| issue | closing PR (proposal only) | named files in that proposal |
|---|---|---|
| #318 | PR#338 | `gates/flows.py`-pattern check (approval-request content shape) — no file list frozen, pattern only |
| #320 | PR#342 | `on-the-record/commands/run.md`, `on-the-record/hooks/report-framing-check.sh`, `test_run_md_semantic_reporting.py`, `test_report_framing_check.py` |
| #362 | PR#365 | `gates/gates.py` (docstring rule addition + doc link) |
| #363 | PR#366 | `gates/gates.py::proposal_generator_section`, `gates/ci.py` wiring, `on-the-record/hooks/generator-guard.sh` |
| #376 | PR#380 | `gates/gates.py::ci_reachable_gates`, `::schema_field_orphans`, `gates/ci.py` wiring |
| #377 | PR#378 | `gates/claims.py` (new), `gates/test_claims.py`, `gates/gates.py::writeset()` docstring hook |
| #379 | PR#382 | `gates/open_work.py::open_work_for`, `gates/test_open_work.py` |
| #390 | PR#393 | `gates/test_merge_state_gate.py` (standalone gate, explicitly not wired into `gates/ci.py`'s closes-gate job) |
| #412 | PR#420 | `on-the-record/hooks/self-update.sh` (shallow-checkout detection), `on-the-record/hooks/test/self-update-shallow.bats` |
| #415 | PR#418 | `gates/repo_scope.py::check_repo_scope` |
| #416 | PR#417 | `gates/acceptance_gate.py` + `gates/test_acceptance_gate.py` cases, `gates/test_setup_failure_propagates.py` |
| #419 | PR#423 | `gates/gates.py::subprocess_call_shape_divergence`, sibling-marker convention + check, `gates/ci.py` wiring |
| #424 | PR#425 | proposal/architecture-survey only — no concrete gate module named yet (least-specified row) |

`gates/test_boundary.py` today has no class-B disposition table or check
— `t_gate_porting_rows_are_ported_or_justified` (test_boundary.py:146)
is the nearest existing pattern (scans `on-the-record/hooks/*.sh` for a
ported `#N` tag, or a justification row in `UNENFORCED-CLAUSES.md`), but
it is scoped to the #457 category-2 `GATE_PORTING_ISSUES` list, which
does not include any of these 13 issue numbers. issue-467's acceptance
("`gates/test_boundary.py` class-B disposition table rows updated with
file-path citations per row") requires a **new** table + check, not an
edit to the existing one — this is itself a delivery item, not something
already in place to point at.

`on-the-record/commands/run.md` (398 lines) is the deployed contract
surface; it already documents `UNENFORCED-CLAUSES.md` and gate-invocation
patterns (`run.md:259`, `:271`) but carries no text for any of these 13
issues today.

## Sizing note

13 rows, each needing its own gate/hook module plus contract text plus a
disposition-table row, exceeds one implementation session (per the ADR's
own sizing instruction and issue-467's phase-1 ask to split into
follow-up issues). Grouped by thematic proximity of the underlying gate
surface into 4 batches of 3-4 rows — see proposal.
