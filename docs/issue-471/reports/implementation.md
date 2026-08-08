---
code_under_review:
  - gates/gates.py
  - gates/test_boundary.py
  - gates/test_merge_state_gate.py
  - on-the-record/hooks/self-update.sh
  - on-the-record/hooks/test_self_update_shallow.py
  - on-the-record/commands/run.md
loop_state: phase-2-complete
---

# implementation — issue-471 (Batch A: PR/merge-state integrity gates)

Phase-1 proposal approved via `APPROVE issue-471/implementation` (single-account
mode, exact-string issue comment by JiwonJung94, an approvers.md account) —
https://github.com/tokenmaxxxer/on-the-record/issues/471#issuecomment-5225523562.

## What was done

- `gates/gates.py`: added a docstring paragraph naming #362's retroactivity
  rule (a check must not fail an artifact for a reason its author could not
  have addressed at authoring time), next to the existing "how a gate dies"
  reasoning at the top of the file.
- `gates/test_boundary.py`:
  - `t_gates_docstring_states_retroactivity_rule` — asserts the docstring
    added above is present.
  - `ISSUE_467_DISPOSITION_ROWS` (13-row list) + `t_class_b_disposition_rows_cited`
    — mirrors `GATE_PORTING_ISSUES`/`t_gate_porting_rows_are_ported_or_justified`'s
    shape (test_boundary.py:138-166). Batch A's 3 rows (#362, #390, #412)
    are checked against real file-path citations; the other 10 rows are
    checked for table membership only, per the ADR's stated batch
    independence.
- `gates/test_merge_state_gate.py` (new) — self-contained synthetic-git-repo
  test: a `main`-side arity change to a function plus a `branch`-side stale
  caller (based on the pre-change commit) merge to a `TypeError`, while the
  branch runs clean alone. Docstring states coverage explicitly: stale-base
  caught, wrong-environment out of mechanism reach, mocked-boundary not
  mechanically reachable — not implied, stated. Standalone, not wired into
  `gates/ci.py`'s `closes-gate` job (CI via Actions is retired per the
  issue-467 ADR).
- `on-the-record/hooks/self-update.sh` — after the existing
  `pull -q --ff-only`, checks `git rev-parse --is-shallow-repository`; on
  `true`, attempts `git fetch -q --unshallow` (same offline-fail-open trap
  as the rest of the file), and writes `.shallow-check` in the checkout
  root recording the outcome regardless of success.
- `on-the-record/hooks/test_self_update_shallow.py` (new, plain Python —
  bats has no binary on this machine and every existing hook test in the
  repo is plain Python, per the survey) — builds a fixture repo, shallow-
  clones it via `file://`, runs `self-update.sh` against it via
  `TOKENMAXXXER_CHECKOUT`, and asserts the marker + successful unshallow;
  a second case asserts a non-shallow checkout records `shallow=false`.
- `on-the-record/commands/run.md` — added two new subsections before
  "## 하지 않는 것": one on the #362 retroactivity rule for gate authoring,
  one covering both #390 (PR green vs. landed state) and #412 (shallow
  checkout) as checkout/verification-state notes, per the survey's build-
  time placement resolution.

## Why (upstream basis)

Issue #471, itself Batch A of the issue-467 ADR
(`docs/issue-467/decisions/2026-08-08-per-row-delivery-and-batch-split.md`),
which reclassified #362/#390/#412 as `deployed-contract+check`
(design already done via each row's own earlier merged proposal, nothing
built) and named the exact check shape per row. Approved phase-1 proposal:
`docs/issue-471/proposals/2026-08-08-batch-a-merge-state-integrity-gates.md`.

## Closed checks (this session)

- `python3 gates/test_boundary.py` — 11/11 passed, including both new
  functions.
- `python3 gates/test_merge_state_gate.py` — 2/2 passed
  (`t_branch_alone_passes`, `t_merge_tree_fails_with_stale_base_arity_error`).
- `python3 on-the-record/hooks/test_self_update_shallow.py` — 2/2 passed
  (`t_shallow_clone_is_detected_and_marker_written`,
  `t_non_shallow_checkout_records_shallow_false`).
- `gates/gates.py`'s docstring visibly contains the #362 rule text (소급,
  작성 시점); `run.md` visibly carries both new subsections.

## What did not work

- First `test_merge_state_gate.py` construction had `branch` edit an
  unrelated file (`README.md`) while `main` edited both `lib.py` and
  `caller.py` together — expected: merge-tree run fails with `TypeError`.
  Actual: merge auto-combined main's consistent lib.py+caller.py pair with
  branch's unrelated README, producing no mismatch at all (both files came
  from the same, internally-consistent side). Fixed by moving the arity
  change to `main`'s `lib.py` only and the stale one-arg call to `branch`'s
  `caller.py` only, so the merge combines main's new signature with
  branch's stale call site.
- First `test_self_update_shallow.py` fixture used
  `git clone --depth 1 <local-path>` — expected a shallow clone. Actual: git
  auto-optimizes same-filesystem local clones (hardlinks) and can silently
  ignore `--depth`, so `--is-shallow-repository` reported `false`. Fixed by
  cloning via an explicit `file://` URL, which forces the real
  shallow-clone codepath.

## Rationale for deviations

None — delivery matched the approved proposal's "What will be done" as
written; no scope-exceeded stop, no alternative swap.

## Open findings

None.

## Next steps

None — Batch A (this issue) is complete. Batches B, C, D
(#318/320/363/376/377/379/415/416/419/424) are each their own follow-up
issue per the issue-467 ADR, not owed by this session.

## Open-finding resolution path

N/A — no open findings.

## Hunt record

Before-landing dispatch run and consumed in this turn (stance index 1:
"assume this change and another plugin's rule cancel each other — find the
pair"), tier size:large/180s. Full record appended to
`docs/reports/2026-08-08-hunt-issue-471-batch-a.md`.

Finding: `roles/implementation.json`'s `write_scope` (`src/**`, `test/**`)
does not cover any file this batch touches (`gates/*`, `on-the-record/*`),
and no `docs/specs/write_scope.md` override exists in this repo, so
`gates.role_scope()` would flag every file in this diff if invoked.
Verified pre-existing, not introduced by this diff: `gates/ci.py::check()`'s
only wired required check is `closes_only=True` mode, which explicitly
skips the `write_scope`/protected-path/deps/record bundle
(`gates/ci.py:389-397`, `t_ci_check_closes_only_skips_write_scope_and_protected_path_bundle`).
Confirmed by precedent — issue-460, issue-464, issue-467's implementation
PRs all landed while touching the same non-`src/`/`test/` paths
(`gates/*.py`, `docs/`, `on-the-record/hooks/*`) with no override file ever
added. Fixing the mismatch (updating `roles/implementation.json` or adding
`docs/specs/write_scope.md`) is outside this batch's frozen write set —
out of scope for issue-471, reported here rather than silently worked
around.
