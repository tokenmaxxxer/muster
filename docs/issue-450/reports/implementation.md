---
code_under_review: spawn.py
loop_state: phase-2-complete
---

## What was done

Narrowed `issue_workspace()`'s bare `except OSError: pass` around the
`.git/info/exclude` credential-guard write (`spawn.py`, formerly
lines 2964-2983) to catch-and-report: on `OSError`, print a warning to
stderr naming the workspace path and the exclude entries that were not
written, then continue (the function still returns the workspace,
unchanged happy-path behavior). Updated
`test_attempt_1_exclude_write_swallowed_no_warning` in
`test/test_silent_failure_repros.py` to assert the warning is present in
captured stderr (workspace path + `.mcp.json`) instead of asserting its
absence.

## Why

Issue #450 (approved via `APPROVE issue-450/implementation` from
approvers.md account JiwonJung94, single-account mode): the guard write
failure was silently swallowed, leaving a live workspace with none of the
credential-leak-guard exclude entries and no signal to the caller. The
approved phase-1 proposal
(`docs/issue-450/proposals/2026-08-08-surface-exclude-guard-write-failure.md`)
specifies a non-fatal stderr warning over `sys.exit` — rejected
alternative recorded there — matching the existing non-halting-diagnostic
convention elsewhere in `spawn.py`.

## Upstream basis

- Issue #450 (Acceptance criteria).
- Phase-1 proposal `docs/issue-450/proposals/2026-08-08-surface-exclude-guard-write-failure.md`
  (## What will be done section, executed as written, matching the plan).
- After-proposal warrant hunt `docs/reports/2026-08-08-hunt-surface-exclude-guard-write-failure.md`
  (reuse-path gap flagged out of scope in the proposal; not built here).

## What did not work

None — the fix landed as scoped in the proposal on first pass.

## Doc placement

- No env var, config key, new dependency, or migration introduced —
  nothing required for handbooks.
- No library/format choice or public-signature/wire-format change beyond
  what the proposal's Rationale already recorded — no new
  `docs/issue-450/decisions/` entry needed.
- No benchmark/investigation numbers produced — nothing for
  `docs/issue-450/reports/` beyond this record.

## How it was confirmed

Ran (this session, this turn):
`python3 -m pytest test/test_silent_failure_repros.py::test_attempt_1_exclude_write_swallowed_no_warning test_spawn.py -q`
→ `276 passed in 19.07s`. Confirms: the target repro test now asserts and
observes the surfaced warning, and the full `test_spawn.py` happy-path
suite stays green (unchanged behavior when the write succeeds).

## Open findings

- After-proposal hunt's reuse-path finding (guard never re-checked on
  reuse branches) stays flagged as a follow-up candidate per the
  proposal's Out of scope section, not addressed here.
- Before-landing hunt (`docs/reports/2026-08-08-hunt-surface-exclude-guard-write-failure.md`,
  stance 0): `ex.read_text()` (spawn.py, unchanged line) raises
  `UnicodeDecodeError` on a pre-existing non-UTF-8 `.git/info/exclude`,
  which is not an `OSError` subclass and so isn't caught by the
  except block — pre-existing gap, not introduced by this change (the
  original bare `except OSError: pass` had the same blind spot). Outside
  issue #450's stated Acceptance (write-failure surfacing, not read
  robustness). Follow-up candidate, not built here.

## Next steps

None — phase-2 delivery for issue #450 is complete pending PR review/merge.
