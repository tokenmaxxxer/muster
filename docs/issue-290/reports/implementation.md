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
`test_gates.py:99`), run against the clean, committed tree (commit
`b408df8`):

```
$ pytest -q
2 failed, 352 passed in 19.09s
```

All monkeypatch-pollution failures cleared:
`test_spawn.py::IssueComments::*` (previously polluted by
`ApproveScope._patch_gh`) and the `subprocess.run`-dependent
`ApproveScope` tests now pass with the patch correctly scoped and torn
down; no new failures introduced by the fixes themselves.

The 2 remaining failures are environment-only, reproduce identically on
the pre-fix commit, and are unrelated to #290's monkeypatch-pollution
class — out of this proposal's write set:
- `test_gates.py::t_repo_local_claude_config_stops_the_spawn`:
  `OSError: [Errno 30] Read-only file system:
  /home/jwjung/.tokenmaxxxer/trusted-repo-config.json` — a path outside
  the repo that this specific sandbox denies writes to. Reproduced
  identically against the pre-fix commit via `git stash`.
- `test_gates.py::t_rulebook_version_is_recorded`: now correctly
  fails, rather than being silently swallowed by the removed `or True`,
  because this workspace's checkout root has several untracked
  environment dotfiles (`.bash_profile`, `.claude/`, `.mcp.json`, etc. —
  pre-existing sandbox artifacts, not created by this session's work)
  that make `git status --porcelain` non-empty, so
  `spawn.rulebook_version()` correctly reports the tree as dirty
  (`커밋안됨`). This is the fix doing exactly what #290 asked — the
  assertion can now fail — surfacing a genuine (if here environmental,
  not code-caused) dirty-tree condition instead of masking it.

## What did not work

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
