# issue-473 current-state survey (phase 1)

## Scouting

Skipped. The three rows' checks were already fully designed in
2026-08-07 proposals (issue-320, issue-376, issue-377), reviewed and
cited by the issue-467 ADR (`docs/issue-467/decisions/2026-08-08-per-row-delivery-and-batch-split.md`)
as "reuse each row's already-designed, never-implemented proposal rather
than re-designing from scratch." No external exemplar sweep applies —
this is mapping sunk design onto delivery, not a product-shaped or
externally-comparable decision.

## What issue-473 is

Batch C of the issue-467 split: deliver run.md contract text + a named
regression check for rows #320 (semantic-effect reporting), #376
(capability discoverability), #377 (stale self-descriptions). Batch A
(#362/#390/#412) already landed on main (PR merged: `9554c53 feat(issue-471):
deliver Batch A merge-state integrity gates`) and added
`gates/test_boundary.py::ISSUE_467_DISPOSITION_ROWS` (13-row table,
already includes 320/376/377) and `t_class_b_disposition_rows_cited`.
Per the ADR, Batch C only needs to add file-path citations for its own
three rows to `_ISSUE_467_BATCH_A_CITATIONS`-equivalent — i.e. extend
that citation dict with 320/376/377 once their files exist — no new
table, no new boundary-check function.

## Per-row proposals already on main (design source of truth)

- `docs/issue-320/proposals/2026-08-07-semantic-effect-reporting.md` —
  `on-the-record/commands/run.md` step-5 addition + Mission Board note;
  new `on-the-record/hooks/report-framing-check.sh` (Stop-hook handler);
  tests named `test_run_md_semantic_reporting.py` and
  `test_report_framing_check.py` (repo-root paths in that proposal's own
  write set).
- `docs/issue-376/proposals/2026-08-07-capability-reachability-gates.md`
  — `gates/gates.py::ci_reachable_gates` + `::schema_field_orphans`,
  wired into `gates/ci.py::check()`; new
  `docs/specs/platform-capabilities.md`; tests named `test_gates.py`
  (repo-root path in that proposal's own write set).
- `docs/issue-377/proposals/2026-08-07-stale-description-claim-checker.md`
  — new `gates/claims.py` (+ registered in `gates.ALL`), `# CLAIM-CHECK:`
  markers added to `gates/gates.py` and
  `.github/workflows/plan-aware-closes-gate.yml`; test named
  `gates/test_claims.py` in that proposal's own write set (inconsistent
  with the frontmatter `files:` list, which says `gates/test_claims.py`
  too — both agree, see below).

## Naming reconciliation needed (issue-467 ADR vs 2026-08-07 proposals)

The ADR's per-row delivery table names test files under `gates/`
(`gates/test_report_framing_check.py`, implied `gates/` location for
#376's `test_gates.py`-shaped tests via `ci_reachable_gates`/
`schema_field_orphans` living in `gates/gates.py`, `gates/test_claims.py`
for #377). The 2026-08-07 proposals for #320 and #376 instead name
repo-root paths (`test_run_md_semantic_reporting.py`,
`test_report_framing_check.py`, `test_gates.py`) in their own `files:`
frontmatter — those proposals predate the ADR's batch split and weren't
revised for it. #377's proposal already uses `gates/test_claims.py`,
matching the ADR.

Existing convention check: every other gate test in this repo lives
under `gates/` (`gates/test_boundary.py`, `gates/test_acceptance_gate.py`,
`gates/test_merge_state_gate.py`, etc.) and imports `gates` as a sibling
module (`sys.path.insert(0, str(Path(__file__).parent))` pattern seen in
`gates/ci.py`). `report-framing-check.sh` is a shell hook, not a gates.py
function, but its Python-side test still belongs with its siblings under
`gates/` per that established pattern, and `docs/issue-467/decisions/...`
explicitly lists `gates/test_report_framing_check.py` (not the repo-root
name). This survey resolves the naming toward the ADR's `gates/`-rooted
paths, overriding the two proposals' repo-root paths for #320 and #376's
test files only — the check logic and behavior stay as those proposals
designed, only the file location changes to match the batch's own ADR
and the repo's one existing convention.

## Current state of touched surfaces

- `on-the-record/hooks/hooks.json`: `Stop` key already exists (declared
  by an unrelated, already-landed pair of hooks — `stop-gate.sh` and
  `role-test-claim-guard.sh`, neither from #318 nor #320). #320's
  proposal's landing-order clause (whichever of #318/#320 lands first
  declares the `Stop` key) is moot: the key is already declared by
  something else entirely. Batch C's work is simply to append
  `report-framing-check.sh` as one more entry in the existing `hooks`
  array under the existing `Stop` key — never redeclare the key.
- `on-the-record/commands/run.md` (398 lines): step 5 and the Mission
  Board section carry no framing-elements text yet (grepped for
  "310"/"318"/"프레이밍"/"report-framing"/"semantic" — only the existing
  #310 non-discharge rule at line 37, unrelated).
- `gates/gates.py::ALL` registry (line 928): no `ci_reachable_gates`,
  `schema_field_orphans`, or claims-check entry yet.
- `gates/ci.py::check()` (line 385): has the `closes_only` early-return
  at line 453; anything meant to run under `--closes-only` (the only
  mode the real `.github/workflows` entry point uses, per #376's own
  Constraints) must be wired before that line, matching what #376's
  proposal already specifies.
- `docs/specs/`: no `platform-capabilities.md` yet; existing spec files
  (`requirements.md` etc.) already use the `| \`name\` | type | notes |`
  table shape #376's `schema_field_orphans` design parses.
- `gates/claims.py`, `gates/test_claims.py`: do not exist yet.
- `gates/test_boundary.py::_ISSUE_467_BATCH_A_CITATIONS` (line ~218):
  currently only cites 362/390/412 (Batch A's rows). Batch C's landing
  needs to add 320/376/377 with real file-path citations once those
  files exist, per the ADR's stated pattern ("later batches only need
  their own check file(s) to start existing").

## Sizing note

Three rows, three independent gate surfaces (a Stop-hook shell script +
run.md text; two `gates.py` functions wired into `gates/ci.py`; a new
`gates/claims.py` module + two annotation sites) — matches one
implementation session per the ADR's own batch sizing. No further split
needed within Batch C.
