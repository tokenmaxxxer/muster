---
code_under_review:
  - on-the-record/commands/run.md
  - on-the-record/hooks/report-framing-check.sh
  - on-the-record/hooks/hooks.json
  - gates/test_report_framing_check.py
  - gates/gates.py
  - gates/ci.py
  - gates/test_capability_gates.py
  - docs/specs/platform-capabilities.md
  - gates/claims.py
  - gates/test_claims.py
  - gates/test_boundary.py
  - docs/specs/enforcement-boundary.md
loop_state: phase-2-complete
---

# implementation — issue-473 (Batch C: reporting/discoverability gates)

Phase-1 proposal approved via `APPROVE issue-473/implementation` (single-account
mode, exact-string issue comment by JiwonJung94, an approvers.md account),
per `docs/issue-473/proposals/2026-08-08-batch-c-reporting-discoverability-gates.md`.

## Summary of work

Delivered the three `deployed-contract+check` rows named by issue #473
(Batch C of the issue-467 split), reusing each row's already-reviewed
2026-08-07 design per the ADR:

1. **#320 — semantic-effect reporting.** Added a framing-elements bullet
   and a Mission Board `Done`-item note to `on-the-record/commands/run.md`
   step 5. Added `on-the-record/hooks/report-framing-check.sh` (a `Stop`
   hook checking `last_assistant_message` for the four framing elements —
   resolved problem, prior cost, newly possible, still broken — on a
   PR/board report turn, `decision: "block"` naming the missing
   element(s) otherwise). Appended it to `hooks.json`'s existing `Stop`
   array (declared first by `stop-gate.sh`, unrelated to #318/#320, per
   the survey). Added `gates/test_report_framing_check.py` (6 tests: the
   run.md-text grep guard folded together with the hook's synthetic-reply
   cases) — `python3 gates/test_report_framing_check.py` passes 6/6.
2. **#376 — capability reachability.** Added `gates/gates.py::ci_reachable_gates`
   (parses `gates/ci.py`'s source for `gates.<name>(` calls and reports any
   `gates.ALL` entry never called, or called only after the `closes_only`
   guard) and `::schema_field_orphans` (parses `docs/specs/*.md` schema-table
   field names and reports any with no reader outside its own
   producer/test/spec file). Added `gates/test_capability_gates.py` (9
   tests, including two run against the real tree) and
   `docs/specs/platform-capabilities.md` (the #2 `Stop`-hook platform-fact
   pointer). `python3 -m pytest -q gates/test_capability_gates.py` passes
   9/9.
3. **#377 — stale self-descriptions.** Added `gates/claims.py`
   (`# CLAIM-CHECK: enum-subset|producer-exists` marker checker,
   `record_fulfils_diff`'s opt-in-marker shape, registered in `gates.ALL`
   via a deferred import to avoid a `gates.py`↔`claims.py` circular
   import) and `gates/test_claims.py` (7 tests, including one against the
   real tree). Added the two markers: `# CLAIM-CHECK: enum-subset
   roles/implementation.json:record_fields.loop_state
   docs/issue-*/reports/*.md:loop_state` near `record_frontmatter`, and
   `# CLAIM-CHECK: producer-exists spec.md` on `writeset()`'s docstring.
   `python3 -m pytest gates/test_claims.py` passes 7/7; `python3
   gates/claims.py .` against the real tree: **2 failure classes** — the
   `spec.md` producer-exists claim (0 files named `spec.md` anywhere in
   the tree — matches the proposal's expected instance), and the
   `loop_state` enum-subset claim (many records use values outside
   `roles/implementation.json`'s declared `["scope-proposed",
   "scope-approved", "in-progress", "landed"]` set — a much larger drift
   surface than the proposal's "#147 alone" framing anticipated; stated
   honestly rather than narrowed to match the expected count).
4. **Shared disposition table.** Extended
   `gates/test_boundary.py`'s Batch-A citation dict with a sibling
   `_ISSUE_467_BATCH_C_CITATIONS` dict (320 → `gates/test_report_framing_check.py`,
   376 → `gates/test_capability_gates.py`, 377 → `gates/test_claims.py`) so
   `t_class_b_disposition_rows_cited` verifies all six landed rows.
   `docs/specs/enforcement-boundary.md` gained two rows (`claims.py`,
   `report-framing-check.sh`) so `t_all_gates_modules_recorded` stays
   green — every new `gates/*.py`/`on-the-record/hooks/*.sh` module needs
   one, per #441's own gate.

## Why

Per the issue-467 ADR: deliver each row's already-reviewed design rather
than re-designing sunk work, landing after Batch A (merged `9554c53`).

## Rationale for deviations

Three points where execution diverged from the approved proposal's "What
will be done":

1. **`gates/test_gates.py` → `gates/test_capability_gates.py`.** The
   proposal (and the issue-467 ADR before it) named
   `gates/test_gates.py` for #376's tests. A repo-root `test_gates.py`
   (110 test functions, the repo's primary `gates.py` unit-test suite)
   already exists — creating `gates/test_gates.py` reproduces the exact
   basename-collision defect `gates/test_duplicate_test_basenames.py`
   exists to catch (its own docstring cites this precise `gates/test_gates.py`
   vs `test_gates.py` shape as historical issue #330/#337). The survey's
   naming-reconciliation section checked convention but not this specific
   collision. Renamed to `gates/test_capability_gates.py` — same content,
   same location convention (`gates/`-rooted), different basename — and
   updated the `gates/test_boundary.py` citation to match.
   `gates/test_duplicate_test_basenames.py::t_duplicate_test_basenames_passes_on_current_tree`
   confirms no collision.
2. **`ci_reachable_gates`/`schema_field_orphans` not wired into
   `gates/ci.py::check()`.** The proposal's item 3 specified wiring both
   before the `closes_only` return. Implementing and wiring both exactly
   as designed broke 4-6 tests in `gates/test_closes_gate_ci.py` (a file
   outside this proposal's write set) that assert `bad == []` for a
   clean synthetic PR fixture: both new gates are repo-wide/unconditional
   (not diff-scoped, matching the proposal's own design for
   `schema_field_orphans`, and `ci_reachable_gates` inspects the real
   on-disk `gates/ci.py` regardless of what a test mocks), so once wired
   they surface *pre-existing* global debt — 8 already-registered gates
   unreachable or past-guard, 6 already-documented schema fields with no
   external reader — on every `check()` call, not just PRs that touch
   that debt. The proposal's premise that `closes_only` is "the only mode
   the real CI entry point ever uses" is itself now stale: `.github/workflows/`
   was retired by issue #460 (discovered mid-build, not visible to the
   survey since it only checked `gates/ci.py`'s own code, not the current
   `.github/` state), and `docs/specs/enforcement-boundary.md` now documents
   the full-bundle local invocation (`python3 gates/ci.py . --pr <n>
   --autodetect`) as an equally legitimate, separately-scoped path — so
   "unreachable under `--closes-only`" no longer means "unreachable by the
   real entry point," it means "scoped to the other documented path,"
   which is by design for several of the flagged gates. Fixing that
   would mean either resolving all pre-existing reachability/orphan debt
   (far outside this batch's scope) or editing `gates/test_closes_gate_ci.py`
   (outside the write set) to tolerate repo-wide findings. Left both
   gates registered in `gates.ALL`, runnable standalone
   (`python3 -c "import gates; print(gates.ci_reachable_gates(...))"`,
   same pattern `claims.py` already uses) and covered by regression tests
   including two run against the real tree — satisfying the proposal's
   "run both new gates against the tree and record the count" acceptance
   without landing the wiring. Not wiring the required-CI path is the
   same follow-up-decision treatment #377's own `claims.py` already uses
   for its promotion.
3. **`.github/workflows/plan-aware-closes-gate.yml` comment split
   (proposal item 3 of #377's "What will be done") skipped.** That file
   no longer exists — deleted by issue #460's `.github/workflows/`
   retirement (`gates/test_boundary_workflow_migration.py` confirms it's
   gone, replacement recorded in `docs/specs/enforcement-boundary.md`).
   The proposal's write set named it because the 2026-08-07 source
   proposal predates #460; the survey didn't catch the deletion since it
   only re-derived the two 320/376 test-file-naming items, not every
   listed path's continued existence. Nothing to edit — the stale-comment
   defect this item targeted no longer exists on disk.

## What did not work

- Wired `ci_reachable_gates`/`schema_field_orphans` into `gates/ci.py::check()`
  exactly per the proposal's item 3 — broke 4-6 pre-existing tests in
  `gates/test_closes_gate_ci.py` (outside the write set). Reverted the
  wiring; see "Rationale for deviations" above.
- `ci_reachable_gates`'s first draft matched `gates.<name>(` call sites
  literally against `gates.ALL`'s keys and produced false positives for
  `record_wellformed`/`record_no_tool_residue`/`record_derived_counts`
  (each registered under its bare name but called in `gates/ci.py` via a
  `_in`-suffixed wrapper, e.g. `gates.record_wellformed_in(`) — caught
  before landing by re-running the check against the real tree and
  reading each finding, not assumed correct from the algorithm alone;
  did not end up mattering for the final delivery since the wiring itself
  was reverted, but the false-positive shape is worth noting for whoever
  picks up the wiring follow-up.
- `schema_field_orphans`'s first draft only parsed field rows nested
  under `### N.N` sub-headings, missing `flows-schema.md`'s top-level
  `## 1.` fields table entirely — `decision_queue` (the proposal's named
  instance #1) went undetected until this was caught by checking the
  actual tree output against the expected instance instead of trusting
  the test suite alone (the synthetic unit tests used single-level docs
  that happened not to expose the gap). Fixed by scanning the whole
  document for the field-row shape instead of gating on heading depth.

## Open findings

None new. The after-proposal warrant-hunt finding recorded in this PR's
prior commit (`5c06fd1`) was addressed in "What will be done" item 4
above (the disposition-table citation extension) — no open finding
remains against this delivery.

## Next steps

None required for this batch to be considered delivered. Follow-ups
identified but explicitly out of this delivery's scope: promoting
`gates/claims.py` to a required CI status check; wiring
`ci_reachable_gates`/`schema_field_orphans` into `gates/ci.py::check()`
once the pre-existing reachability/orphan debt they surface is either
resolved or the wiring is scoped to diff-relevant findings only
(resolution path: a follow-up issue, since fixing that debt is a
separate, larger write set than this batch's).
