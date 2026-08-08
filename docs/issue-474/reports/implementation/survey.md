# Current-state survey — issue #474 (Batch D)

Base: `a8dc412` (main, clean tree — `git status` clean, `git log -1` confirms).

## Scope

Batch D per the #467 ADR (`docs/issue-467/decisions/2026-08-08-per-row-delivery-and-batch-split.md`,
lines 36-39): #415, #416, #419, #424. The shared `gates/test_boundary.py`
`ISSUE_467_DISPOSITION_ROWS` table already landed in Batch A (#471,
`gates/test_boundary.py:213-238`) — this batch adds only its own rows'
named checks, no table changes.

## What each row's own already-merged design says (already on `main`)

- **#415** — `docs/issue-415/proposals/implementation.md` (status: proposed,
  merged to `main`'s docs tree). Ships `gates/repo_scope.py::check_repo_scope`
  + `test_repo_scope_gate.py`, a standalone syntactic checker flagging a
  capability/contract-shaped absence claim with no adjacent repo-scope
  phrase. Explicit ceiling: does not verify cross-repo truth, and a
  warrant-hunt finding narrows it further (fixed phrase list misses
  paraphrases) — both must be restated in Batch D's own record, not just
  implied.
- **#416** — `docs/issue-416/proposals/2026-08-07-provenance-and-empty-state-gates.md`.
  Extends `gates/acceptance_gate.py::check_issue_body` with two additive
  checks (`empty state:`, `provenance:`) on the `## Acceptance` section,
  plus a standalone `gates/test_setup_failure_propagates.py` for the
  setup-step-failure finding. Presence-only ceiling stated explicitly.
- **#419** — `docs/issue-419/proposals/2026-08-07-pattern-recurrence-checks.md`.
  Adds `subprocess_call_shape_divergence` and `sibling_mention_check` to
  `gates/gates.py`'s `ALL` registry, wires both into `gates/ci.py`'s
  non-`--closes-only` chain, adds fixtures to `gates/test_gates.py`, and
  applies `# sibling:` markers to the real `core_root`/`core_version` pair
  in `spawn.py`. Ceiling: catches 1 of 4 named instances outright, 1
  prospectively once marked, 2 explicitly out of reach.
- **#424** — `docs/issue-424/proposals/accumulation-gate.md` answers a
  different, superseded question (root-vs-symptom wiring, not accumulation
  cost) and names no concrete `gates/` module for the #467 ADR's row
  wording ("a proposal must state what the codebase becomes after N more
  changes of the same shape"). Per the ADR (line 39): least-specified row,
  implementer designs against
  `docs/issue-424/reports/architecture/survey.md`'s named recurrence
  instances as test fixtures. That survey names 5 instances; instances 1
  (6 inline `gh` call sites in `gates/ci.py`, no shared helper) and 5 (43
  identical one-line edits to `roles/*.json`) are the two with concrete,
  git-log-derivable "same shape repeated N times" evidence usable as
  fixtures — instances 2-4 have only a single occurrence each, no
  repetition to fixture against.

## Current file state relevant to Batch D's write set

- `gates/repo_scope.py` — does not exist yet.
- `gates/acceptance_gate.py` — `check_issue_body` (line 37) has no
  `empty state:`/`provenance:` checks; only `_ARTIFACT_REF` and
  `_UNVERIFIABLE` patterns exist (lines 20-26).
- `gates/gates.py` (928 lines) — `ALL` registry at line 928; no
  `subprocess_call_shape_divergence` or `sibling_mention_check` entries;
  `PROTECTED_ROOT_DIRS` (line 36) includes `gates`, so any diff here
  routes to mandatory human review regardless of this batch's own content.
  `duplicate_test_basenames` (~line 738) is the one existing dedup check —
  same-family precedent for #424's accumulation gate.
- `gates/ci.py` — 6 inline `subprocess`/`gh` call sites
  (`ci.py:59,79,104,122,204,256`), matching #424 instance 1 exactly;
  no shared invocation helper.
- `gates/accumulation.py` — does not exist yet.
- `spawn.py` — `core_root`/`core_version` sibling pair (per #419's
  proposal) not yet marked with `# sibling:` comments.
- `on-the-record/commands/run.md` — has a "## 하지 않는 것" trailer
  section (line 396) and, per Batch A's precedent (#471), new subsections
  are added immediately before it (`git show 9554c53` confirms this
  placement for #362/#390/#412's contract text).
- `gates/test_boundary.py:213-238` — `ISSUE_467_DISPOSITION_ROWS` already
  lists #415/#416/#419/#424 (line 214) inside the 13-row table; nothing
  in this batch needs to touch that table.

## Test/CI baseline

`python3 -m pytest -q --ignore=gates` from repo root: not re-run in this
phase-1 session (no code changes yet); #419's and #471's own records
already establish the working invocation shape (`--ignore=gates` from
root, plus `python3 -m pytest gates/test_*.py -q` run directly inside
`gates/`, per #398's module-collision constraint) — reused as-is for
Batch D's phase-2 acceptance, not re-derived.

## Gap this batch's proposal targets

Four rows' checks are designed (three already, by their own merged
proposals) but none are built. #424 additionally needs its concrete
module design decided in this proposal, since its own proposal named
none.
