---
status: proposed
files:
  - test/test_silent_failure_repros.py
---

## Request
Full suite is 1-red on main: `test_attempt_4_bundling_gate_is_documented_comment_only`
reads `.github/workflows/issue-bundling-gate.yml`, which #460/#463 deleted.
Decide whether the guarantee it pinned has a replacement surface to
assert, or retire the test with citation, and deliver a green suite.

Scout skip (stated per scout-directive): pure bugfix, no design decision
open — #460's migration table already decided this workflow's
disposition.

## Constraints
- `python3 -m pytest -q` must end 0 failed.
- Any retirement must cite the #460 migration-table entry it relies on.
- No coverage may be silently dropped: if the general "every deleted
  workflow has a named replacement" guarantee isn't otherwise asserted,
  this proposal cannot just delete the test.

## Rationale
Alternative considered and rejected: rewrite the test to assert against
`gates/issue_bundling.py` (the migration table's named local
replacement) instead of the deleted workflow file. Rejected because the
attempt-4 test's actual assertion is about *comment-only, non-blocking
behavior on an `issues: opened` webhook trigger* — a property intrinsic
to GitHub Actions' inability to block issue creation. `gates/issue_bundling.py`
is a differently-shaped surface (a local CLI blocking via exit code
against issue text); it has no comment-only behavior to inherit, so
there is nothing for a rewritten assertion to check. Retiring with
citation is therefore the correct outcome, not a rewrite.

Retirement is safe here specifically because the *general* Acceptance
guarantee from #460 ("every deleted workflow has a named replacement or
recorded drop") is independently and already asserted by
`gates/test_boundary.py` (which loads `test_boundary_workflow_migration.py`
and checks the migration table's completeness) — confirmed present in
the survey. So no coverage is dropped by removing attempt-4 specifically.

## What will be done
Remove `test_attempt_4_bundling_gate_is_documented_comment_only` from
`test/test_silent_failure_repros.py`, replacing it with a short comment
citing `docs/specs/enforcement-boundary.md:87` (the #460 migration-table
entry: "repo-local, deleted — no replacement possible ... runnable
locally as `python3 gates/issue_bundling.py <issue#>`") as the reason
the finding it pinned is moot.

## Out of scope
- Changing `gates/issue_bundling.py` or its coverage.
- Touching `gates/test_boundary.py` / `test_boundary_workflow_migration.py`.
- Any other attempt-N repro in the same test file.

## How you'll know it worked
`python3 -m pytest -q` reports 0 failed (currently 1 failed / 572
passed), and the commit message/diff cites the #460 migration-table
entry backing the retirement.
