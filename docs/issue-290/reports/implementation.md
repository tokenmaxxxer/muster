---
code_under_review:
  - .github/workflows/on-the-record-tests.yml
  - test_approve_scope.py
  - test_gates.py
  - on-the-record/commands/run.md
  - docs/handbooks/operations.md
loop_state: delivered
open_findings: []
resolved_findings:
  - PR #295 review (2026-08-07): on-the-record-tests.yml ran `pytest -q`
    with no install step, so CI failed at "pytest: command not found"
    (exit 127) without ever exercising the suite. Fixed by adding a
    `pip install pytest` step, then (discovered on the resulting CI
    run) a `git config --global` identity step, needed because the
    runner has no default git identity and one test performs a real
    `git commit`. Confirmed green on GitHub Actions run 31147608397
    (commit c03c7ae): 355 passed, 0 failed. Record's effect-verification
    numbers corrected from a sandbox-local "2 failed, 352 passed" (an
    artifact of this session's sandbox, not the branch) to the actual
    CI-measured 355 passed / 0 failed.
  - #390 unblock (2026-08-07): branch was ~179 commits behind main.
    Rebased onto origin/main (commit 0f3151a); one textual conflict in
    `test_approve_scope.py` (this branch's scoped-mock.patch fix and
    main's own equivalent fix landed on the same lines) resolved by
    keeping main's already-integrated version, which is behaviorally
    identical to this branch's. `gates/spec_index.py --update` reported
    drift on `docs/specs/reconciled-index.md` (protocol.md/protocol.ko.md
    hashes changed by a concurrent merge, issue-289); checked the
    concurrent diff — it does not touch the "Ledger storage location"
    resolved ambiguity, so only hashes were regenerated, no ambiguity
    text changed. Re-ran acceptance evidence against the rebased,
    committed tree: `python3 -m pytest -q --ignore=gates` — 407 passed,
    0 failed (commit 3946aa1). `python3 -m pytest -q gates` (informational,
    not part of this issue's acceptance) collects and runs but has 1
    pre-existing failure unrelated to this branch
    (`t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`,
    real issue #304 lacking an `## Acceptance` section) — #398's claim
    that the `gates/` subtree cannot collect does not reproduce here; it
    collects and runs, just with one pre-existing unrelated failure.
  - Second rebase, ~80-PR conflict (2026-08-07): branch was 38 commits
    behind main. `git rebase origin/main` hit one conflict, in
    `docs/specs/reconciled-index.md`, on the commit that had itself
    regenerated that index during the prior (#390) rebase — its recorded
    hashes were now stale against the new main tip, so the commit was
    skipped (`git rebase --skip`) rather than merged, since a fresh
    `spec_index.py --update` after rebase supersedes it entirely. Ran
    `python3 -m pytest -q` (no `--ignore`, per current instruction) on
    the rebased tree: 1 failure —
    `test_spec_index.py::t_baseline_repo_passes`, index hash drift from
    files main changed since the skipped commit. Ran
    `python3 gates/spec_index.py --update`, committed the regenerated
    `docs/specs/reconciled-index.md` (commit `3431c2d`), re-ran the full
    suite: `t_gates.py::t_rulebook_version_is_recorded` failed once
    against the *uncommitted* diff (dirty-tree self-detection working as
    designed), then passed clean once that diff was committed. Final
    measured result, full directory, no ignore flags, rebased +
    committed tree: **508 passed, 0 failed** — matches main's own stated
    508-passed baseline. Artifacts named in this record's
    `code_under_review` (the CI workflow, both test files, run.md,
    operations.md) all still exist unchanged on the rebased branch; no
    mismatch found between what this delivery claims and what it
    produces.
---

# issue-290 / issue-294 — phase 2: CI + test-hygiene fix

Implements `docs/issue-290/proposals/2026-08-07-ci-and-test-hygiene.md`
(approved via PR #295) exactly as scoped.

## What was done

- Added `.github/workflows/on-the-record-tests.yml`: runs on
  `pull_request` against `main`, checks out the PR head (default
  `actions/checkout@v4` ref, no `main` pin), sets up Python 3.11, runs
  `pytest -q`.
- `test_approve_scope.py`: replaced both process-global
  `spawn.subprocess.run = fake_run` assignments with
  `mock.patch("spawn.subprocess.run", fake_run)` scoped to the
  assertions that need it, matching `test_spawn.py`'s existing pattern
  (`mock.patch("spawn.subprocess.run", ...)`, lines 267/293 there).
  Also converted `_patch_gh`'s three unscoped monkeypatches
  (`_repo_slug`, `_pr_for_branch`, `_issue_comments`) to
  `mock.patch.object(...)` + `self.addCleanup(patcher.stop)` — same
  defect class (process-global patch, no teardown) in the same file,
  discovered while making the acceptance criterion ("`pytest -q` over
  the whole directory passes") actually true; leaving it would have
  left `test_spawn.py::IssueComments` polluted by whichever
  `ApproveScope` test ran first.
- `test_gates.py:99`: removed the `or True` so
  `t_rulebook_version_is_recorded` can actually fail on a dirty
  (`커밋안됨`) rulebook version string.
- `on-the-record/commands/run.md`: amended the acceptance bullet to
  require reading `gh pr checks <n>` before merge, refuse merge on any
  failing check, and state an explicit branch for "no checks exist"
  (escalate to the user rather than merge on the PR body's self-report),
  per #294.

## Effect verification (full-directory run, before/after)

Reported baseline in the invoking prompt (`pytest -q` scoped inside
`on-the-record/` plus `repo-status-board/`, combined): `50 failed / 305
passed`. This workspace's checkout root is itself the on-the-record
repo (no `on-the-record/` subdirectory nesting, no
`repo-status-board/`), so the directly reproducible measurement in this
tree is the whole-directory `pytest -q` run at repo root.

Before (this session's pre-edit `HEAD`, `146802a`, reproduced via `git
stash` against the unmodified tree):

```
4 failed, 350 passed in 15.67s
```

(lower than the prompt's reported 50-failed baseline because this
workspace does not contain the `repo-status-board/` JS-bridge suite
that contributed most of the prompt's failures — those tests are not
part of this repo's tree here — and only 2 of `test_approve_scope.py`'s
3 unscoped monkeypatches were exercised by the specific tests the
proposal named.)

After both fixes (`subprocess.run` scoping + `_patch_gh` scoping +
`test_gates.py:99`), run against the clean, committed tree (commit
`b408df8`) inside this session's sandbox:

```
$ pytest -q
2 failed, 352 passed in 19.09s
```

All monkeypatch-pollution failures cleared:
`test_spawn.py::IssueComments::*` (previously polluted by
`ApproveScope._patch_gh`) and the `subprocess.run`-dependent
`ApproveScope` tests now pass with the patch correctly scoped and torn
down; no new failures introduced by the fixes themselves.

The 2 remaining failures reproduced *in this sandbox* are environment
artifacts specific to this workspace, not to the branch's code — a
review of PR #295 (2026-08-07) caught that this needed correcting
after CI was wired up and actually run, since a "2 failed" number
recorded without distinguishing sandbox-local artifacts from real
branch state reads as a code defect that isn't one:
- `test_gates.py::t_repo_local_claude_config_stops_the_spawn`:
  `OSError: [Errno 30] Read-only file system:
  /home/jwjung/.tokenmaxxxer/trusted-repo-config.json` — a path outside
  the repo that this specific sandbox denies writes to.
- `test_gates.py::t_rulebook_version_is_recorded`: fails here because
  this sandbox's checkout root has untracked environment dotfiles
  (`.bash_profile`, `.claude/`, `.mcp.json`, etc. — pre-existing
  sandbox artifacts, not created by this session's work) that make
  `git status --porcelain` non-empty, so `spawn.rulebook_version()`
  correctly reports the tree as dirty (`커밋안됨`).

Neither condition exists on a fresh CI checkout (`actions/checkout@v4`
into a clean runner, no stray dotfiles, no read-only paths outside the
workspace), which is what the CI run below actually shows: both pass
there. What CI *did* catch that the sandbox run above could not is a
third, CI-only failure — `pip install pytest` alone was not enough for
green, because the runner also has no global `git user.name`/
`user.email`, so `test_spawn.py::RulebookCheckoutMemo::test_ttl_marker_does_not_dirty_clone`
(which does a real `git commit`) failed with exit 128. Fixed by adding
a "configure git identity for tests" step
(`.github/workflows/on-the-record-tests.yml`) before the run step.

**Actual measured result, this branch, GitHub Actions run
[31147608397](https://github.com/tokenmaxxxer/on-the-record/actions/runs/31147608397/job/92770241545)
(commit `c03c7ae`, PR #295), full directory, real CI environment —
this supersedes both prior counts above, which were sandbox-local, not
branch state:**

```
..................                                                       [100%]
355 passed, 23 subtests passed in 13.77s
```

0 failed. Job conclusion: success.

## What did not work

- Assumed `pip install pytest` alone would make the CI job green
  (PR #295 review); the first CI run after adding it still failed —
  `test_spawn.py::RulebookCheckoutMemo::test_ttl_marker_does_not_dirty_clone`
  needs to perform a real `git commit`, and the runner has no global
  git identity configured, so it failed with exit 128. Fixed by adding
  a "configure git identity for tests" step before the run step;
  confirmed green on the next run (355 passed, 0 failed).
- Expected `test_gates.py::t_rulebook_version_is_recorded` to pass
  clean after committing; it still fails post-commit because this
  sandbox's checkout root carries pre-existing untracked environment
  dotfiles (not created by this session), which keep
  `git status --porcelain` non-empty regardless of commit state. Left
  as a documented environment condition (see Effect verification)
  rather than papered over — deleting stray files outside this
  proposal's write set to force a clean measurement was judged riskier
  than reporting the honest, explained result.
- Fixing only the two `subprocess.run` process-global assignments named
  in the proposal left `test_spawn.py::IssueComments::*` polluted by
  `ApproveScope`'s `_patch_gh` helper (`_repo_slug`/`_pr_for_branch`/
  `_issue_comments` monkeypatched with no teardown) — same file, same
  defect class, not itself named in the proposal's bullet list. Fixed
  alongside the named lines since the proposal's own acceptance
  criterion (full-directory `pytest -q` green) could not otherwise
  hold.

## Doc placement (ladder)

- [x] No new env var, config key, dependency, or migration introduced —
      nothing owed to a component handbook.
- [x] No library/format choice over a named alternative and no changed
      public signature/wire format beyond what the proposal's Rationale
      already recorded in
      `docs/issue-290/proposals/2026-08-07-ci-and-test-hygiene.md` — no
      new `docs/issue-290/decisions/` entry needed.
- [x] Effect-verification numbers (before/after full-suite counts, #298)
      are recorded above in this report — this report is that home.

## Hunt

Cadence already satisfied for this issue's after-proposal transition:
recorded in
`docs/reports/2026-08-07-hunt-2026-08-07-ci-and-test-hygiene.md`
(committed as "issue-290: warrant hunt record (after-proposal, no
finding)"). Before-landing hunt: this is a headless, single-shot turn
with no later turn for an async dispatch's result to land in (contract
v3 s22) — every touched path in this delivery is a test file, a
workflow YAML, or a docs command file (no runtime production code path
changed), so the size-derived tier would be the smallest bucket, and
dispatching a background hunter whose result could not be consumed
before this turn ends would violate s22. No before-landing hunt was
dispatched; noting the omission here per the hunt-cadence requirement's
own rule (record a section even when a hunt was not run) rather than
leaving it silent.

closed_checks:
- name: subprocess.run process-global leak in test_approve_scope.py
  code_sha: b408df8
- name: test_gates.py:99 tautological assertion
  code_sha: b408df8
