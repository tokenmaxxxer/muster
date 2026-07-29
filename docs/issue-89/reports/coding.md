# Issue #89 — Coding Record

loop_state: phase2-started

code_under_review: (pending — will be updated to the final code commit sha)

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

(updated as work proceeds)

## What did not work

(none yet)

## Open findings

None raised against this work yet.

## Next steps

(updated as work proceeds)

## Open-finding resolution path

No open findings currently block progress. Should a reviewer raise a
blocking finding, it will be addressed and logged here as
resolved_findings before further commits, per the coding-progress gate.

## resolved_findings

(none)

## closed_checks

(pending — filled in once code_under_review is set to the final sha)
