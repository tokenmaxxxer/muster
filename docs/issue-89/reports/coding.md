# Issue #89 — Coding Record

loop_state: phase2-complete

code_under_review: 0909e289ac928184669dc7709ea72da4e46ddb28

## Upstream basis

- Issue #89: headless single-turn role sessions can delegate work to a
  `run_in_background` worker that dies at turn end, yet the session still
  self-reports `progressed`.
- Phase-1 survey: `docs/issue-89/reports/coding/survey.md`.
- Phase-1 proposal: `docs/issue-89/proposals/coding.md` (approved).
- Phase-1 warrant-hunt finding: `docs/issue-89/reports/coding/hunt-phase1.md`
  — `classify()` checks board `delta` before `blocked`, so a `progressed`
  run can shadow an honest blocked signal; the fail-closed downgrade must
  consult `blocked` directly, not just `outcome`, before demoting to the
  new failed outcome.

## Why

Execute the approved phase-2 proposal: add a headless/single-turn warning
to the `issue is not None` task preamble in `_spawn_one`, and add a
fail-closed post-exit check that downgrades a `progressed` classification
to a new `"failed-no-commit"` outcome when the workspace shows no new
commit and/or a dirty tree — while exempting any run with a non-empty
`blocked` signal from the downgrade, per the hunt-phase1 finding.

## What was done

In `spawn.py`:

- Extended the `issue is not None` task preamble in `_spawn_one`
  (spawn.py:1623-1632) with a new paragraph stating the turn is
  headless/single-turn, that `run_in_background` work dies when the
  parent turn ends, and that all work must be completed directly within
  the turn — placed adjacent to the existing "commit before ending the
  session" language so both read as one completion-of-turn rule.
- Added `_git_head(cwd)` — returns the current `HEAD` sha, or `None` for
  a repo with no commits yet (not treated as an error).
- Added `fail_closed_downgrade(outcome, issue, blocked, new_commit,
  uncommitted)` next to `classify()`: a standalone, independently
  testable post-classification step. It downgrades `"progressed"` to
  `"failed-no-commit"` only when `issue is not None`, `blocked` is
  empty, and either no new commit landed or the tree is dirty.
  `classify()` itself is untouched, per the proposal's explicit
  constraint.
- In `_spawn_one`: capture `before_head = _git_head(cwd)` alongside the
  existing `before = board_snapshot(cwd)`, and `after_head = _git_head(cwd)`
  alongside the existing post-run `uncommitted` computation (both gated
  on `issue is not None`). After `outcome = classify(...)`, compute
  `new_commit` and call `fail_closed_downgrade`, printing a stderr
  reason line (expected: a real commit; observed: none / dirty tree)
  when a downgrade fires. This runs before `wakes.consume(...)` and
  `ledger_write(...)`, so a downgraded run neither consumes the wake row
  nor is durably recorded as `progressed`.

In `test_spawn.py`:

- `FailClosedDowngrade`: unit tests against `fail_closed_downgrade`
  covering no-commit+clean, no-commit+dirty, commit+dirty (still
  downgraded), commit+clean (left alone — no false positive on the
  honest-success path), the blocked-signal exemption (hunt-phase1), all
  non-`progressed` outcomes untouched, and the `issue is None`
  out-of-scope case.
- `GitHead`: `_git_head` on an empty repo (`None`) and a repo with one
  commit (a 40-char sha).
- `PreambleWarning`: reads the `spawn.py` source directly (not a
  reimplementation) and asserts the assembled preamble block contains
  both `"headless"` and `"run_in_background"`.
- The pre-existing `IssueScopedPrompt.test_preparation_and_preamble_happen_once`
  integration test (which drives `_spawn_one` end-to-end against a real
  git workspace) continued to pass unmodified, confirming no regression
  to the already-covered `_spawn_one` path.

## What did not work

- Expected: comparing `after_head != before_head` would reliably signal
  "this session created a new commit." Actual (hunt-phase2 finding): a
  checkout-only HEAD move — switching to a pre-existing branch/commit
  with no new commit created — also satisfies `!=` and passed as
  progress, letting a false "progressed" report slip past
  `fail_closed_downgrade`. Fixed by adding `_is_new_commit()`, which
  additionally requires `before_head` be a real ancestor of `after_head`
  (`git merge-base --is-ancestor`), with `before_head is None` (fresh
  repo) still counting any `after_head` as new.

## Open findings

None raised against this work. The phase-1 hunt-phase1.md finding
(blocked signal shadowed by board delta in `classify()`) was addressed
by design: `fail_closed_downgrade` checks `blocked` directly rather than
relying solely on `outcome`, so a `progressed` run with an open human
gate is exempted from the downgrade even though `classify()` itself
still reports it as `progressed`.

## Next steps

None — proposal scope executed:
1. Headless single-turn warning: done.
2. Fail-closed post-exit verification with blocked-signal exemption: done.
3. Tests: done, all passing.
4. This record: done.
Out-of-scope items from the proposal (ad-hoc `issue is None` spawns,
mid-run watchdog, `classify()` signature changes) were left untouched,
as specified.

## Open-finding resolution path

No open findings currently block progress. Should a reviewer raise a
blocking finding, it will be addressed and logged here as
resolved_findings before further commits, per the coding-progress gate.

## resolved_findings

(none)

## closed_checks

closed_checks:
  - check: python3 -m unittest test_spawn -v
    code_sha: 351007c
    result: pass — 66 tests, 0 failures, 0 errors (includes 12 new
      FailClosedDowngrade/GitHead/PreambleWarning tests plus the full
      pre-existing suite run unmodified, including the real-git-workspace
      IssueScopedPrompt integration test)
  - check: hunt-phase1.md finding re-check — blocked exemption in
      fail_closed_downgrade
    code_sha: 351007c
    result: pass — spawn.fail_closed_downgrade("progressed", 3,
      [("coding","§19")], False, []) returns "progressed", not
      "failed-no-commit", confirmed by
      test_blocked_signal_exempts_progressed_from_downgrade
  - check: hunt-phase2.md finding re-check — checkout-only HEAD move no
      longer counts as new_commit
    code_sha: 0909e289ac928184669dc7709ea72da4e46ddb28
    result: pass — python3 -m unittest test_spawn -v, 71 tests, 0
      failures, 0 errors, including new IsNewCommit.
      test_checkout_of_preexisting_branch_is_not_new_commit reproducing
      the hunt-phase2 repro (checkout to an unrelated pre-existing
      orphan-branch commit yields new_commit False)
