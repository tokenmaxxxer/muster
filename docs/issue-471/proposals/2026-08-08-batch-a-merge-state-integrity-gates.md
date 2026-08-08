---
status: proposed
files:
  - gates/gates.py
  - gates/test_merge_state_gate.py
  - gates/test_boundary.py
  - on-the-record/hooks/self-update.sh
  - on-the-record/hooks/test_self_update_shallow.py
  - on-the-record/commands/run.md
  - docs/issue-471/reports/implementation.md
---

## Request

Batch A of the issue-467 ADR: deliver deployed-surface enforcement for
#362 (a check must not retroactively invalidate an artifact that complied
when authored), #390 (a PR's green attests to the state it was verified
against, not the state it lands in), and #412 (self-update's self-clone
fallback can silently leave a shallow checkout). Each needs `run.md`
contract text plus a named check that fails on regression. Because Batch A
lands first, it also adds the shared 13-row disposition-table check
(`t_class_b_disposition_rows_cited` + `ISSUE_467_DISPOSITION_ROWS`) to
`gates/test_boundary.py`, extending it per the issue-457 precedent, not
replacing it.

## Constraints

- Per issue #471 and the issue-467 ADR: `t_class_b_disposition_rows_cited`
  must be added alongside the existing `gates/test_boundary.py` functions —
  the PR diff must show only additions to that file, no removed `t_*`
  functions.
- Per the issue-467 ADR's per-row table: #390's check is
  `gates/test_merge_state_gate.py`, standalone and **not** wired into the
  `closes-gate` job — CI via GitHub Actions is retired and not a valid
  delivery surface for this batch, so no `.github/workflows/*.yml` is added
  (confirmed none exists today for this row).
- Per the ADR: #362's check is a `gates/test_boundary.py` assertion
  (`t_gates_docstring_states_retroactivity_rule`) that `gates/gates.py`'s
  docstring contains the rule text — not the older `record_enums` xfail
  design from #362's own merged phase-1 proposal.
- Per the ADR: #412's check reuses #412's own merged proposal design
  (shallow-detection in `self-update.sh` + a test file) essentially as-is;
  only the test-harness choice (bats vs. python) is open, and the survey
  resolves it to python — no bats binary exists on this machine and every
  existing `on-the-record/hooks/test_*.py` file is plain Python.
- Do not touch `gates/ci.py`'s existing `closes-gate` job or its required-
  check registration (per #390's own proposal's constraint, still valid).
- No new dependency, no new secret.

## Rationale

Considered reusing PR #393's design for #390 verbatim, including its
`.github/workflows/merge-state-gate.yml` GitHub Actions job. Rejected: the
issue-467 ADR — written after #393 merged, during the audit that reclassified
these rows as undelivered — states CI via Actions is retired and explicitly
names the #390 check as "standalone, not wired into the closes-gate job."
Landing an Actions workflow now would reproduce exactly the "green attests,
nothing enforces" shape #390 itself is about, since a retired CI surface
would not actually run it. Only `gates/test_merge_state_gate.py` (the
self-contained synthetic-merge-tree test, runnable locally with no GitHub
Actions dependency) is carried forward from #393's design.

Considered reusing #362's original `record_enums` xfail(strict=True) test
design from its own merged proposal. Rejected: the issue-467 ADR
(the current authority for this batch's acceptance) names a smaller check —
a docstring-content assertion in `gates/test_boundary.py` — as what #362
delivers here. The xfail/`record_enums` design is heavier (touches
`test_gates.py`, requires reconstructing a fixed board-repo record) and
addresses a real but separately-scoped gap (`record_enums`'s live-state
read) that the ADR did not fold into this batch's acceptance; re-litigating
that design choice is out of scope for a batch that exists to deliver
already-decided mappings, not redesign them.

## What will be done

- `gates/gates.py`: add one docstring paragraph naming the retroactivity
  rule from #362 (a check must not fail an artifact for a reason its author
  could not have addressed at authoring time), next to the existing "how a
  gate dies" reasoning it is already adjacent to.
- `gates/test_boundary.py`:
  - Add `t_gates_docstring_states_retroactivity_rule`: asserts
    `gates/gates.py`'s docstring contains the #362 rule text added above.
  - Add `ISSUE_467_DISPOSITION_ROWS = [318, 320, 362, 363, 376, 377, 379,
    390, 412, 415, 416, 419, 424]` and `t_class_b_disposition_rows_cited`,
    mirroring `GATE_PORTING_ISSUES` / `t_gate_porting_rows_are_ported_or_justified`'s
    shape (`test_boundary.py:138-166`): for each of the 3 rows this batch
    delivers (362, 390, 412), assert a file-path citation to this batch's
    named check exists somewhere findable (e.g. a small per-row citation
    map checked against the actual file paths on disk); for the other 10
    rows (not yet delivered by any batch), assert they are present in the
    table without yet requiring a citation — later batches add their
    citation when they land, per the ADR's stated batch-independence.
- `gates/test_merge_state_gate.py` (new): construct the #383-shape stale-
  base instance in a throwaway git repo — a "main" commit changing a
  function's arity and a "branch" commit (based on the pre-change commit)
  whose only caller still uses the old arity — merge them the way
  `refs/pull/<n>/merge` would, and assert the merge-tree run fails with the
  arity `TypeError` while the branch-alone run passes. Ported from PR
  #393's `gates/test_merge_state_gate.py` design, run locally (no Actions
  workflow). States coverage explicitly in its own docstring: 2 of 3 named
  #390 shapes (stale-base, wrong-environment) caught; mocked-boundary
  stated as not mechanically reachable by this mechanism, not implied.
- `on-the-record/hooks/self-update.sh`: after `_checkout_resolve` and the
  existing `pull -q --ff-only`, add
  `git -C "$CHECKOUT" rev-parse --is-shallow-repository`; on `true`,
  attempt `git -C "$CHECKOUT" fetch -q --unshallow` (same offline-fail-open
  trap), and write a one-line marker file recording the shallow state and
  the unshallow outcome regardless of success.
- `on-the-record/hooks/test_self_update_shallow.py` (new, plain Python —
  not bats, per the constraints above): creates a local fixture git repo
  with multiple commits, shallow-clones it (`git clone --depth 1`), points
  `self-update.sh` at it via `TOKENMAXXXER_CHECKOUT`, runs the hook as a
  subprocess, and asserts the marker file is written and/or the checkout is
  no longer shallow afterward.
- `on-the-record/commands/run.md`: add three short subsections carrying
  each row's contract text — a gate-authoring note for #362's
  retroactivity rule, a note near checkout/verification guidance for #390's
  "green attests to verified state, not landed state," and a note for
  #412's shallow-checkout risk — placed at build time next to the existing
  content each is closest to (the survey found no single pre-existing
  "gate authoring" heading to slot into).
- `docs/issue-471/reports/implementation.md`: the phase-2 record, written
  per the record-shape directive, citing all three named checks and the
  disposition-table addition.

## Out of scope

- Any `.github/workflows/*.yml` addition for #390 — CI via Actions is
  retired per the issue-467 ADR.
- Redesigning #362's check beyond the ADR-named docstring assertion (the
  `record_enums` xfail gap from #362's original proposal stays unaddressed,
  as it was already out of scope in that proposal).
- Reproducing or fixing #412's unexplained upstream working-directory
  disappearance (item 2) — recorded as a searched-and-not-found entry per
  #358, carried forward from #412's own merged proposal, not re-investigated
  here.
- Batches B, C, D (#318/320/363/376/377/379/415/416/419/424) — their rows
  go into `ISSUE_467_DISPOSITION_ROWS` now (per the ADR, the table is
  written once) but their own check files and run.md sections are each
  batch's own follow-up issue, not this one.

## How you'll know it worked

- `python3 gates/test_boundary.py` (or the project's existing runner for
  that file) passes, including the new
  `t_gates_docstring_states_retroactivity_rule` and
  `t_class_b_disposition_rows_cited`.
- `python3 gates/test_merge_state_gate.py` run standalone: demonstrated red
  before the merge-tree re-run logic exists, green after — run, not
  reasoned about.
- `python3 on-the-record/hooks/test_self_update_shallow.py` run standalone
  against a fixture shallow clone: red before the hook change, green after.
- `gates/gates.py`'s docstring visibly contains the #362 rule text, and
  `on-the-record/commands/run.md` visibly carries the three new
  contract-text subsections.
