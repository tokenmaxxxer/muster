# Survey — issue-360

Scout skip: pure bugfix, no design decision open (test-isolation fix with a spec-given
mechanism — `unittest.mock.patch`/`addCleanup`). Scouting skipped per scout-directive
mandatory skip condition 1.

## Write set

- `test_approve_scope.py` — `_patch_gh` (lines 39-41) assigns `spawn._repo_slug`,
  `spawn._pr_for_branch`, `spawn._issue_comments`; two test methods (lines 57, 98)
  assign `spawn.subprocess.run = fake_run` directly, with no restoration in `tearDown`.
  `spawn.subprocess` is the imported `subprocess` module object (spawn.py:29), so this
  mutates the process-wide `subprocess.run`, not a spawn-local copy.
- New test file for the regression guard required by acceptance item 2 (a test that
  fails if any module leaves `subprocess.run`/`spawn.*` patches unrestored) —
  `test_isolation.py`.
- `docs/issue-360/reports/implementation.md` — phase-2 record (this issue).

## Reproduction (measured today, before fix)

```
$ python3 -m pytest -q
52 failed, 305 passed in 5.90s
$ python3 -m pytest test_spawn.py -q
235 passed in 14.76s
```
(Issue text recorded 51 failed/306 passed for the full run at file time; today's clean
checkout reproduces 52 failed/305 passed — one test's collection/order shifted by one
between then and now, not material to the fix. Both numbers were run, not assumed.)

## Cause confirmed

`spawn.subprocess.run = fake_run` at test_approve_scope.py:57 and :98 replaces the
`run` attribute on the shared `subprocess` module object. Any test file that imports
`subprocess` (directly or via `spawn`) and calls `subprocess.run` afterward in the same
process receives `fake_run`, which returns `returncode = 0, stdout = ""` unconditionally
— a stub that never raises, so downstream tests can pass for the wrong reason.
`_repo_slug`/`_pr_for_branch`/`_issue_comments` are reassigned on the `spawn` module
itself for the same reason, though they are lower-risk (no downstream test calls them
expecting real behavior).

## Fix mechanism

`unittest.mock.patch.object(spawn.subprocess, "run", fake_run)` (or
`patch.object(spawn, "_repo_slug", ...)`, etc.) via `self.addCleanup` in `setUp`/each
test — restoration becomes structural (guaranteed by `mock.patch`'s teardown), not
memorized in `tearDown`.

## Alternative considered

Manually save/restore the original attribute in `tearDown` (`self._orig_run =
spawn.subprocess.run` in `setUp`, restore in `tearDown`). Rejected: this is exactly the
"remembered, not structural" pattern the issue calls out as the root failure mode — a
future test added to this file (or copying this pattern into another file) can still
forget the manual restore. `mock.patch`/`addCleanup` ties restoration to the patch call
itself, so it can't be forgotten independently.
