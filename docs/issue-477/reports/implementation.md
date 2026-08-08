---
code_under_review:
  - test/test_silent_failure_repros.py
loop_state: landed
---

## What was done
Removed `test_attempt_4_bundling_gate_is_documented_comment_only` from
`test/test_silent_failure_repros.py` (it read the deleted
`.github/workflows/issue-bundling-gate.yml`) and replaced it with a
comment citing the #460 migration-table entry
(`docs/specs/enforcement-boundary.md:87`) as the reason the finding it
pinned is moot. `python3 -m pytest -q` now reports 0 failed, 572 passed
(previously 1 failed / 572 passed).

## Why
The attempt-4 test's assertion (comment-only, non-blocking behavior on
an `issues: opened` webhook trigger) is intrinsic to GitHub Actions'
inability to block issue creation. The workflow was deleted with no
replacement possible per #460's migration table, so there is no
surface left to assert that property against; `gates/issue_bundling.py`
(the named local replacement) is a differently-shaped CLI surface with
no comment-only behavior to inherit the assertion. The general "every
deleted workflow has a named replacement or recorded drop" guarantee
stays covered by `gates/test_boundary.py` +
`test_boundary_workflow_migration.py`, so no coverage was dropped.

## Upstream
docs/issue-477/proposals/2026-08-08-retire-attempt-4-repro.md

## Doctrine ladder
- No env var/config key/new dep/migration/setup step introduced — no
  handbook update required.
- No library-or-format choice or changed public signature/wire format —
  no `docs/issue-477/decisions/` entry required.
- No benchmark/investigation numbers produced — no
  `docs/issue-477/reports/` entry beyond this record required.

## What did not work
None.

## Hunt
Diff is a single test-file edit under 20 lines net; per warrant-directive
size tiering this falls under the 60s docs/test-only fast tier. No
blocking finding surfaced during delivery.

## Open findings
None.
