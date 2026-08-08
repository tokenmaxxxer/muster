---
status: proposed
files:
  - on-the-record/commands/run.md
  - on-the-record/hooks/report-framing-check.sh
  - on-the-record/hooks/hooks.json
  - gates/test_report_framing_check.py
  - gates/gates.py
  - gates/ci.py
  - gates/test_gates.py
  - docs/specs/platform-capabilities.md
  - gates/claims.py
  - gates/test_claims.py
  - gates/test_boundary.py
  - .github/workflows/plan-aware-closes-gate.yml
---

## Request

Issue #473 (Batch C of the issue-467 split): deliver deployed-surface
enforcement + a named regression check for three `deployed-contract+check`
rows — #320 (progress reports must state the resolved problem/effect,
not just enumerate issues/PRs), #376 (a landed capability must be
reachable from CI wiring and from schema, not silently dead), #377 (the
system's self-descriptions must not go stale unchecked). Land after
Batch A (already merged, `9554c53`), which added the shared
`gates/test_boundary.py::ISSUE_467_DISPOSITION_ROWS` table this batch
extends with citations only.

## Constraints

- Reuse each row's already-reviewed 2026-08-07 proposal design
  (`docs/issue-320`, `docs/issue-376`, `docs/issue-377`) rather than
  re-designing — per the issue-467 ADR's explicit instruction.
- `gates/test_boundary.py`: only additions (a citation-dict update for
  320/376/377), never a rewrite of `ISSUE_467_DISPOSITION_ROWS` or
  removal of any existing `t_*` function — the same requirement Batch A
  already satisfied and this batch must not regress.
- `on-the-record/hooks/hooks.json`'s `Stop` key already exists (declared
  by `stop-gate.sh`/`role-test-claim-guard.sh`, unrelated to #318/#320)
  — append `report-framing-check.sh` as one more entry in the existing
  array; never redeclare the key.
- `gates/ci.py::check()`'s `closes_only` early-return (line 453) is the
  real CI entry point's only mode; #376's `ci_reachable_gates` must be
  wired before that line or it fails to catch the exact defect class it
  targets.
- Test file locations for #320 and #376 follow the ADR's `gates/`-rooted
  naming (`gates/test_report_framing_check.py`, `gates/test_gates.py`),
  not the repo-root paths named in those two rows' own 2026-08-07
  proposals — see survey.md's naming-reconciliation section. #377's
  proposal already used `gates/test_claims.py`; unchanged.
- Do not build #330 (general reach-check) or #333 (derived-numbers) —
  both remain open, unimplemented, out of this batch's scope per #376's
  own proposal.

## Rationale

**Chosen approach**: implement each row's proposal as already designed,
adjusting only the two test-file locations flagged in the survey to
match the ADR's `gates/`-rooted convention, and add the three
file-path citations to `gates/test_boundary.py`'s existing
`_ISSUE_467_BATCH_A_CITATIONS`-equivalent dict.

**Alternative considered and rejected — re-design #320/#376/#377's
checks from scratch for this batch.** Rejected: the issue-467 ADR
explicitly evaluated and rejected re-designing sunk work
("re-designing #318 and #424's checks now instead of flagging them...
out of scope"); the three rows here already have full designs reviewed
against real objections (#320's proposal was revised once already, after
a #342 review caught a factual error about hook capability). Redoing
that work would duplicate review effort already spent and risks
reintroducing the same error the revision fixed.

**Alternative considered and rejected — keep the two rows' own
repo-root test-file names (`test_run_md_semantic_reporting.py`,
`test_report_framing_check.py`, `test_gates.py`) instead of moving them
under `gates/`.** Rejected: those names predate the issue-467 ADR's
batch split and were never revised against it; the ADR's own per-row
delivery table names `gates/test_report_framing_check.py` explicitly,
every other gate test in this repo already lives under `gates/`
(`gates/test_boundary.py`, `gates/test_acceptance_gate.py`, etc.) and
imports `gates` as a sibling module, and #377's sibling proposal in the
same batch already used the `gates/`-rooted name — keeping repo-root
paths for only two of the batch's three rows would leave an
inconsistent, harder-to-find test layout inside one PR for no benefit.

## What will be done

1. **#320 — semantic-effect reporting.** In `on-the-record/commands/run.md`
   step 5, add the framing-elements bullet and the Mission Board
   `<flow 요약>` note exactly as `docs/issue-320/proposals/2026-08-07-semantic-effect-reporting.md`
   §"What will be done" items 1-2 specify. Add
   `on-the-record/hooks/report-framing-check.sh` per that proposal's item
   3. Append it to `hooks.json`'s existing `Stop` array (not a new key)
   per the Constraints above. Add `gates/test_report_framing_check.py`
   (the proposal's `test_report_framing_check.py`, relocated) covering
   the address-only/four-element/non-report cases from item 6, plus a
   grep-based `run.md`-text assertion (the proposal's
   `test_run_md_semantic_reporting.py`, folded into the same file since
   both check the same row and the ADR names only one test file for
   this row).
2. **#376 — capability reachability.** Add `gates/gates.py::ci_reachable_gates`
   and `::schema_field_orphans` per
   `docs/issue-376/proposals/2026-08-07-capability-reachability-gates.md`
   §"What will be done" items 1-2. Wire `ci_reachable_gates` into
   `gates/ci.py::check()` before the `closes_only` return per item 3;
   `schema_field_orphans` unconditional (repo-wide, not diff-scoped).
   Add `gates/test_gates.py` (relocated from the proposal's repo-root
   name) with the `writeset`/`record_enums`/`decision_queue` regression
   fixtures from item 4. Add `docs/specs/platform-capabilities.md` per
   item 5. Run both gates against the tree and record the count (3 of 4
   named instances, per the proposal's own stated expectation) in the
   phase-2 record.
3. **#377 — stale self-descriptions.** Add `gates/claims.py` and
   `gates/test_claims.py` per
   `docs/issue-377/proposals/2026-08-07-stale-description-claim-checker.md`
   §"What will be done" items 1-2, registered in `gates.ALL` but not
   wired into `gates/ci.py`'s required path (per that proposal's own
   Rationale — promotion to required-check is a separate follow-up
   decision). Add the two `# CLAIM-CHECK:` markers to `gates/gates.py`
   per item 3. Rewrite the mixed-claim comment in
   `.github/workflows/plan-aware-closes-gate.yml` per item 4.
4. **Shared disposition table.** Extend
   `gates/test_boundary.py`'s Batch-A citation dict with 320 → the new
   `gates/test_report_framing_check.py` path, 376 → `gates/test_gates.py`,
   377 → `gates/test_claims.py`, so `t_class_b_disposition_rows_cited`
   verifies all six landed rows (Batch A's three plus this batch's
   three) once this PR merges. No change to `ISSUE_467_DISPOSITION_ROWS`
   itself (already 13 rows, already includes 320/376/377 from Batch A's
   landing).

## Out of scope

- #318, #362, #363, #379, #390, #412, #415, #416, #419, #424 — other
  rows, other batches (B/A/D), not this issue.
- #330's general reach-check, #333's derived-numbers mechanism, #147's
  `loop_state` enum drift fix itself, `roster_watchdog`'s docstring
  (#325) — all named out of scope by the source proposals and repeated
  here for traceability, not re-litigated.
- Promoting `gates/claims.py` to a required CI status check — a
  follow-up decision per #377's own Rationale.
- A UI/CLI/query interface for capability discovery — #376's gates are
  CI-time regression checks, not a search tool.

## How you'll know it worked

- `python3 gates/test_report_framing_check.py` (or via the repo's
  existing test-run convention) fails on `main` today (script/tests
  don't exist) and passes once `report-framing-check.sh` and the run.md
  edits land, including the address-only-reply-blocked and
  four-element-reply-passes cases.
- `python3 -m pytest -q gates/test_gates.py -k "ci_reachable or schema_field_orphans"`
  passes, including the `writeset`/`record_enums`/`decision_queue`
  regression fixtures.
- `python3 -m pytest gates/test_claims.py` passes; running
  `gates.claims.check_claims()` against the tree after the two markers
  land reports exactly 2 failures before the underlying drift is fixed,
  0 after.
- `python3 gates/test_boundary.py` (or its existing invocation) stays
  green, including `t_class_b_disposition_rows_cited` with the three new
  citations resolving to real files.
