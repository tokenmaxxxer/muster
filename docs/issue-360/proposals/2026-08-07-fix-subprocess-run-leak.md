---
status: landed
files:
  - test_approve_scope.py
  - conftest.py
  - docs/issue-360/reports/implementation.md
---

Scout skip: pure bugfix, no design decision open — see
`docs/issue-360/reports/implementation/survey.md`.

## Request

`test_approve_scope.py` patches `spawn._repo_slug`, `spawn._pr_for_branch`,
`spawn._issue_comments`, and (the damaging one) `spawn.subprocess.run`, all as raw
attribute assignment with no teardown. Since `spawn.subprocess` is the shared
`subprocess` module object, this replaces `subprocess.run` process-wide for the rest of
the test run, which is why the full suite shows 51-52 failures while every per-file
invocation looks clean. Fix the leak, determine how many of the failures are genuine
defects vs. pollution artifacts (report the number, don't assume), and add a regression
test that fails if any module leaves a patched attribute unrestored.

## Constraints

- Restoration must be structural (`mock.patch`/`addCleanup`), not remembered, per the
  issue's own diagnosis of why this happened in the first place.
- Acceptance requires running both `pytest -q` and `pytest test_spawn.py -q` and
  recording both numbers — not asserting they agree.
- Genuine defects among the 51-52 (if any) get filed as their own issues, not fixed in
  this branch.

## Rationale

Considered manually saving/restoring the original attributes in `tearDown` instead of
`mock.patch`. Rejected: that's the same "remembered, not structural" shape the issue
identifies as the root cause — a future edit to this file (or a copy of this pattern
elsewhere) can silently drop the manual restore. `mock.patch.object(...)` +
`self.addCleanup(...)` (or the `with mock.patch.object(...)` context form) ties
restoration to the patch call so it can't be forgotten independently, which is what the
issue is actually asking for ("restoration must be structural, not remembered").

## What will be done

1. In `test_approve_scope.py`, replace the three raw assignments in `_patch_gh` and the
   two `spawn.subprocess.run = fake_run` assignments with `mock.patch.object` calls
   registered via `self.addCleanup` (or `setUp`-scoped `patch.object(...).start()` +
   `addCleanup(patch.stop)`), so every patched attribute is restored after each test
   regardless of pass/fail.
2. Run `python3 -m pytest -q` and `python3 -m pytest test_spawn.py -q` after the fix,
   record both raw outputs in the implementation record.
3. Diff the post-fix failing set against the pre-fix 51/52 failing set to identify which
   pre-fix failures were pollution (disappear once the leak is fixed) vs. genuine
   (still fail on a clean, isolated run). Report the exact count and enumerate genuine
   ones by name. File genuine defects as new issues (not fixed here) if any are found.
4. Add a session-scoped autouse fixture to `conftest.py` that snapshots `subprocess.run`
   (and the `spawn._repo_slug`/`_pr_for_branch`/`_issue_comments` attributes) at session
   start and asserts they are unchanged at session teardown. A fixture (not an ordinary
   test) is required: an ordinary test only observes state at its own fixed collection
   position, so it cannot detect a leak from a file collected after it (confirmed by the
   after-proposal warrant hunt — see `docs/reports/2026-08-07-hunt-fix-subprocess-run-leak.md`).
   `conftest.py` fixtures wrap the whole session regardless of collection order.

## Out of scope

- Fixing any genuine defect uncovered by the diff in step 3 — those become their own
  issues per the issue's own scope note ("Genuine ones get filed as their own issues,
  not fixed here").
- Issue #360 scope item 3 ("establish why nothing caught this") beyond what the new
  regression test in step 4 already demonstrates structurally.

## How you'll know it worked

`python3 -m pytest -q` and `python3 -m pytest test_spawn.py -q` are both run and their
raw pass/fail counts are recorded in `docs/issue-360/reports/implementation.md`,
matching each other's genuine-failure set (module-order independent). The pollution
count from step 3 is stated as a number with genuine failures (if any) enumerated by
name. The new `conftest.py` session-teardown check fails on the pre-fix code (reproducing the
leak, run as a control) and passes post-fix.
