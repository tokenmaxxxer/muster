# Survey — issue-471 (Batch A: PR/merge-state integrity gates)

## Source of truth

issue-471 is the first of 4 batch follow-ups defined by the issue-467 ADR
(`docs/issue-467/decisions/2026-08-08-per-row-delivery-and-batch-split.md`).
Batch A covers #362, #390, #412 and, because it lands first, also adds the
shared `gates/test_boundary.py` disposition-table check.

## Per-row prior design (already-merged phase-1 proposals)

All three rows already have a merged phase-1 proposal from when they were
worked as standalone issues, before the issue-464/467 audit reclassified
them as `deployed-contract+check` (design done, nothing built):

- **#362** — `docs/issue-362/proposals/2026-08-07-check-must-not-retroactively-invalidate.md`
  (PR merged). Original design: `docs/decisions/...md` + a `gates/gates.py`
  docstring paragraph + an `xfail(strict=True)` verdict-stability test in
  `test_gates.py` for `record_enums`.
  **The issue-467 ADR table overrides the check shape**: it names the check
  as `t_gates_docstring_states_retroactivity_rule` in `gates/test_boundary.py`
  asserting the docstring contains the rule text — simpler than the
  `record_enums` xfail test. The ADR table is the authority for issue-471's
  acceptance (`Refs #467`); the old proposal's decision-doc content (the
  three-property test, the audit) is still valid material to carry into the
  docstring paragraph, but the *check* is the smaller ADR-named one.
- **#390** — `docs/issue-390/proposals/2026-08-07-merge-state-gate.md` (PR
  #393, merged). Design: a `.github/workflows/merge-state-gate.yml` GitHub
  Actions job that checks out the PR's merge ref and re-runs the local test
  scripts, PLUS `gates/test_merge_state_gate.py` — a self-contained test that
  builds two synthetic git commits (a `main`-side arity change and a
  branch-side stale caller), merges them, and asserts the merge-tree run
  fails while the branch-alone run passes. Stated coverage: 2 of 3 named
  shapes (stale-base: caught; wrong-environment: caught; mocked-boundary:
  not mechanically reachable by this mechanism).
  **Conflict with current project state**: the issue-467 ADR context notes
  "CI via Actions is retired and not a valid delivery surface," and its
  per-row table names the check as `gates/test_merge_state_gate.py`
  "(standalone, not wired into the closes-gate job)" — i.e. the Actions
  workflow half of PR #393's design is not part of what issue-471 delivers.
  Confirmed no `.github/workflows/merge-state-gate.yml` exists on `main`
  today (`find .github -iname '*merge-state*'` → empty) — nothing to
  reconcile, just do not add it.
- **#412** — `docs/issue-412/proposals/2026-08-07-shallow-checkout-detection.md`
  (PR #420, merged). Design: after `_checkout_resolve`'s self-clone branch
  and the existing `pull -q --ff-only`, add
  `git rev-parse --is-shallow-repository`; on `true`, attempt
  `fetch -q --unshallow` and write a one-line marker file regardless of
  outcome. Test: a bats fixture that shallow-clones a local repo, points
  `self-update.sh` at it via `TOKENMAXXXER_CHECKOUT`, and asserts the
  marker/unshallow result. The proposal itself flagged bats as unconfirmed
  ("or an equivalent runnable shell test if bats isn't already the
  project's test harness — confirming that during phase 2"). Matches the
  issue-467 ADR table row exactly (hook change + test file), so no
  ADR-level conflict — only the bats-vs-python choice is open.

## Current repo state (checked directly, not from the old proposals)

- `gates/gates.py` docstring (`gates/gates.py:1-7`): states the "확실하면
  막는다" principle and references gate-death reasoning; carries no
  retroactivity rule paragraph and no #362 reference yet.
- No `gates/test_merge_state_gate.py` exists yet (`ls gates/ | grep -i
  merge` → empty).
- `on-the-record/hooks/self-update.sh` (34 lines): resolves the checkout via
  `_checkout_resolve`, then does a bare `pull -q --ff-only`. No shallow
  check anywhere in the file today.
- No `bats` binary on this machine (`which bats` → empty); the project's own
  `on-the-record/hooks/test_*.py` files are all plain Python
  (`test_pr_preflight.py`, `test_role_test_claim_guard.py`,
  `test_record_claim_guard.py`, `test_contract_guard.py`,
  `test_spec_index_preflight.py`) — no `.bats` file exists anywhere in the
  repo (`find . -iname '*.bats'` → empty). The project convention is
  therefore plain-Python hook tests, not bats; #412's proposal already
  flagged this as open, and the repo now settles it.
- `gates/test_boundary.py` already carries the precedent pattern issue-471
  must follow: `GATE_PORTING_ISSUES` (a flat list of issue numbers,
  `test_boundary.py:138-141`) plus `t_gate_porting_rows_are_ported_or_justified`
  (`test_boundary.py:146-166`), added by issue-457 as an *addition* to this
  file, not a rewrite. The issue-467 ADR explicitly names this as the
  pattern issue-471's disposition-table check must copy: a new
  `ISSUE_467_DISPOSITION_ROWS` table (13 rows, mirroring
  `GATE_PORTING_ISSUES`'s shape) plus a new `t_class_b_disposition_rows_cited`
  function, added alongside the existing functions with no `t_*` removed.
- `on-the-record/commands/run.md` (398 lines) has no existing
  "gate-authoring" or "merge-state" or "checkout-integrity" subsection — the
  three new run.md subsections the ADR calls for (one per row) are net-new,
  placed near the content each rule is about (gate authoring near the top
  where `gates/` conventions could be documented; merge-state and
  shallow-checkout are orchestrator-facing checkout/CI concerns, so they fit
  best as a small new subsection rather than forcing them into an unrelated
  existing heading — resolved as a build-time placement choice, not a
  proposal-blocking one, since run.md's structure imposes no single correct
  slot).

## Full 13-row disposition table (from the issue-467 ADR)

For `ISSUE_467_DISPOSITION_ROWS`, all 13 `deployed-contract+check` rows and
their per-row check-file citation (batch A's 3 rows point at files this
issue creates; the other 10 point at files future batches B/C/D will
create — per the ADR, later batches only need their own check file(s) to
start existing, no further edits to `test_boundary.py`):

318, 320, 362, 363, 376, 377, 379, 390, 412, 415, 416, 419, 424.

## Skip conditions checked

Not a pure bugfix and the spec (issue-467 ADR) already resolved the open
design questions (per-row check shape, batch grouping) — so scouting would
normally apply. Scout-directive skip condition used: **the spec leaves no
design decision open** for the row-to-check mapping and the disposition
pattern (both fixed by the merged issue-467 ADR, itself the product of a
prior scout-and-decide pass); the only genuinely open choices found by this
survey are internal implementation details (bats vs. python test harness,
run.md subsection placement) already resolved by direct repo inspection
above, not by an external competitive scout. No product-facing exemplar
search applies to an internal CI/gate-authoring mechanism.
