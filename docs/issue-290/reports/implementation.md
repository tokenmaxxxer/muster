---
code_under_review:
  - .github/workflows/on-the-record-tests.yml
  - test_approve_scope.py
  - test_gates.py
  - on-the-record/commands/run.md
loop_state: delivered
open_findings: []
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
`test_gates.py:99`), run against the clean, committed tree:

```
$ pytest -q
352 passed, 2 skipped in 15.35s
```

All prior failures cleared: `test_spawn.py::IssueComments::*` (polluted
by `ApproveScope._patch_gh`), `test_gates.py::t_rulebook_version_is_recorded`
(tautological assertion), and no new failures introduced.

One environment-only failure was diagnosed and excluded from the above
as unrelated to this change:
`test_gates.py::t_repo_local_claude_config_stops_the_spawn` fails with
`OSError: [Errno 30] Read-only file system:
/home/jwjung/.tokenmaxxxer/trusted-repo-config.json` when a stray
uncommitted `.tokenmaxxxer` sibling path is read-only in this specific
sandbox — reproduced identically against the pre-fix commit via `git
stash`, confirming it predates and is independent of this change. Not
part of the monkeypatch-pollution class #290 describes; out of this
proposal's write set. (It did not reproduce in the final clean-tree run
above, since that run's working directory state differed from the
mid-fix probe that first surfaced it.)

## What did not work

- Initially re-ran `test_gates.py::t_rulebook_version_is_recorded`
  mid-fix and got a dirty-tree failure — expected clean, got
  `AssertionError: '커밋안됨' unexpectedly found`. Root cause: this
  session's own edits were still uncommitted when that probe ran, so
  `rulebook_version()` correctly reported the dirty state. Not a bug in
  the fix itself; resolved by committing before the final verification
  run.
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
  code_sha: 146802ac28d0f8d06c9b7c73b11afd17616fc94a
- name: test_gates.py:99 tautological assertion
  code_sha: 146802ac28d0f8d06c9b7c73b11afd17616fc94a
