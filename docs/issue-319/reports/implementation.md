---
code_under_review:
  - gates/risk_report.py
  - test_risk_report.py
  - docs/handbooks/risk-classified-approvals.md
loop_state: phase-2-complete
---

# Implementation record — issue #319

Approved proposal: `docs/issue-319/proposals/2026-08-07-risk-classified-approval-report.md`
(approval: `APPROVE issue-319/implementation` comment on issue #319, 2026-08-07,
by `JiwonJung94`, an `approvers.md` login — single-account mode, exact
string match, no conditional-feedback comment followed it).

## Why

Approved proposal's Request/Rationale (see proposal file): approval volume
is unmanaged and degrades into reflex; this pass gives a human a
non-blocking, batched, risk-labeled view of open phase-1 proposals so
low-stake ones can be reviewed together, without changing what counts as a
valid GitHub approval act (contract v3 s19 untouched).

## What was done

- `gates/risk_report.py`: `classify(paths, added, removed) -> "high"/"low"`
  (protected path via `gates.is_protected`, or >30 changed lines, or empty
  write-set → `"high"`, fail-closed); `scan_open_proposals(root)` walking
  `docs/issue-*/proposals/*.md` and `docs/proposals/*.md` for
  `status: proposed`, parsing each `files:` block and pulling
  added/removed line counts via `git diff --numstat` against
  `origin/main`; `report(proposals)` rendering one Markdown table,
  `high` rows first, every input proposal exactly once.
- `test_risk_report.py`: 6 assertions, run via `python3 test_risk_report.py`
  — exit 0, all pass (executed this session). Covers: docs-only small
  change → low; protected paths → high regardless of size; oversized
  docs change → high; missing/unparseable `files:` → high; batch
  ordering/no-drop; and the blank-line write-set-truncation regression
  found by the before-landing hunt (below).
- `docs/handbooks/risk-classified-approvals.md`: usage + explicit
  advisory-only / non-blocking disclaimer, per proposal.

Ran `python3 test_risk_report.py` directly — real output, not narrated:
all 6 `t_*` cases print `ok`, process exits 0.

## What did not work

- Initial `_FILES_BLOCK` regex (`^files:\s*\n((?:^\s*-\s*\S+\s*\n?)+)`)
  stopped matching at the first blank line inside a `files:` list,
  silently truncating the parsed write-set and dropping later paths
  (including protected ones) from classification — found by the
  before-landing warrant-hunter dispatch, not by the original test suite.
  Fixed by widening the block regex to also consume blank lines
  (`^[ \t]*\n`) between `- path` entries, and added
  `t_blank_line_inside_files_block_does_not_truncate_write_set` as a
  permanent regression guard.

## Rationale for deviations

None — the fix above is a bug caught and closed before landing, not a
divergence from the approved proposal's `## What will be done` (which
already specified fail-closed-on-unparseable as the required behavior;
the bug was an implementation defect in meeting that spec, not a scope
or approach change).

## Doc placement (ladder)

- [x] `docs/handbooks/risk-classified-approvals.md` — new tool's
  usage/handbook home, same turn (no new env var/dep/migration to place
  elsewhere on the ladder).
- [x] Design rationale (advisory/non-blocking, standalone vs. wiring into
  `gates.py:check()`, standing-decision registry rejected) already lives
  in the approved proposal's `## Rationale` — no separate
  `docs/issue-319/decisions/` entry needed; nothing here changed a public
  signature or wire format beyond what the proposal already recorded.
- Reports bucket: this record + the hunt record below are the reports
  artifacts for this pass; no separate benchmark/investigation report.

## Hunt cadence

- End of phase 1: recorded in `docs/issue-319/reports/implementation/survey.md`
  / scout-brief cadence (phase-1 commit `5adb4e2`).
- Before phase-2 completion (this session): dispatched
  `warrant:warrant-hunter`, stance "assume the gate/classifier just added
  is bypassable — find the bypass", diff 229 lines / 3 files (tier:
  size:large, 180s cap), run in foreground per contract v3 s22 (headless
  single-shot — result consumed same turn, not backgrounded).
  Result: **FINDING**, reproduced, fixed (see "What did not work" above
  and `docs/reports/2026-08-07-hunt-issue-319-risk-classified-approval-report.md`).

## Closed checks

- closed_check: "blank-line write-set truncation" — code_sha: (see
  `code_under_review` above) — closed via
  `t_blank_line_inside_files_block_does_not_truncate_write_set` in
  `test_risk_report.py`. Offered to verify as a citable, already-run
  check (contract s16) — verify may re-derive independently; this entry
  does not itself discharge a blocking finding.

## Open findings

None outstanding. The one finding raised by the before-landing hunt was
fixed and covered by a new regression test in this same session, before
this record was written.

## What this reaches beyond its own acceptance criteria (per #330)

Unchanged from the approved proposal's own `## What this reaches...`
section — reproduced here for the record's completeness, not re-derived:
invalidates no on-disk state (`gates/gates.py` is imported, not modified);
reaches but does not resolve the operator's underlying approval-fatigue
complaint (visibility improves, decision *count* is unchanged — the
standing-decision reduction needs a contract v3 amendment, out of scope
here); establishes a `"low"/"high"` vocabulary other tooling may come to
depend on.

## Next steps

None required to close this issue's phase-2 delivery. Follow-up (not
built here, per proposal's Out of scope): a contract-level
standing-decision amendment, owned by whoever owns contract v3, to
actually reduce approval *count* rather than only its visibility.
