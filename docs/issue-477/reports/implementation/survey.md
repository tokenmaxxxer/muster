# Survey — issue-477

Scout skip: pure bugfix (retiring a test whose target file was deleted by
an already-merged, already-decided migration). No design decision is
open — the migration table in #460 already made the call.

## Write set
- `test/test_silent_failure_repros.py` — remove
  `test_attempt_4_bundling_gate_is_documented_comment_only`, which reads
  `.github/workflows/issue-bundling-gate.yml` (deleted by #463 per #460).

## What I found
- `python3 -m pytest -q` on main: 1 failed, 572 passed. Sole failure is
  the attempt-4 case — `FileNotFoundError` on the deleted workflow path.
- `docs/specs/enforcement-boundary.md:87` (the #460 migration table) already
  records this workflow's disposition: "repo-local, deleted — no
  replacement possible — issue-creation is a GitHub webhook event,
  unreachable by any Claude Code session hook; runnable locally as
  `python3 gates/issue_bundling.py <issue#>`."
- The attempt-4 test's actual assertion was never about bundling
  detection — it asserted that the *workflow's comment-only, non-blocking*
  behavior (on `issues: opened`) was documented rather than a silent
  defect. That property is intrinsic to the deleted GitHub Actions
  workflow (a webhook trigger with no PR to block). `gates/issue_bundling.py`,
  the named local replacement, is a CLI with a different trigger and
  semantics (blocks via exit code against issue text) — it has no
  comment-only behavior to inherit, so there is nothing for a
  replacement assertion to check.
- Coverage for "every deleted workflow has a named replacement or
  recorded drop" already exists independent of this test:
  `gates/test_boundary.py` loads `test_boundary_workflow_migration.py`
  and asserts the migration table is complete. That is the actual
  replacement surface for #460's Acceptance criterion.

## Conclusion
The finding attempt-4 pinned (comment-only behavior undocumented) is
moot: the surface it pinned no longer exists, and the general "every
deleted workflow has a citation" guarantee is already asserted by
`gates/test_boundary.py` + `test_boundary_workflow_migration.py`. Retire
the test with citation, per issue-477's stated option.
