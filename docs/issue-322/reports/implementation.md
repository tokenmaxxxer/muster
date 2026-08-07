---
code_under_review:
  - ledger/decisions.py
  - ledger/test_decisions.py
loop_state: phase-2-complete
---

Subject: issue-322

# Implementation record

## What was done
Added `ledger/decisions.py`, matching `ledger/collect.py`'s shape (read the record, compute
something objective, no LLM). It walks `docs/issue-*/reports/*.md` across each file's full git
history (`git log --reverse` + `git show`, same mechanism as `ledger/collect.py.history()`),
extracts bullets under `## What did not work` / `## Rationale for deviations`, normalizes them
(lowercase, strip `#<n>`/`issue-<n>`/hex-sha tokens), and counts occurrences per normalized key
across *distinct* subjects (`issue-<n>` directories). A key recurring at or above threshold
(default 2) with no `docs/decisions/*.md` file whose body contains that normalized key as a
substring is emitted as a candidate on stdout; the process exits 1 iff any candidate exists,
0 otherwise. `--json` emits the same data machine-readably.

Added `ledger/test_decisions.py`, matching `gates/test_closes_gate_ci.py`'s harness shape
(`t_*` functions, no pytest dependency, `__main__` runner). Six tests, each spinning up a real
temporary git repo (so `history()` runs its actual git-shelling code path, not a mock):
normalize() strips issue/sha tokens so the same correction text matches across subjects;
extract_bullets() reads both target sections and ignores unrelated `##` sections; a single
occurrence does not flag; a second occurrence across two subjects flags with the correct
subject list and the exit-code-1 contract; a recurrence already cited in a `docs/decisions/*.md`
file passes; placeholder "None." bullets (the record-shape-gate's own mandated empty-section
filler) are not treated as findings.

## Why
Discharges #322's acceptance bar per #310: `python3 ledger/test_decisions.py` is the executable
artifact — it failed before this build (module did not exist) and passes now, exercising exactly
the regression #322 exists to prevent (a recurring correction with no confirmed
`docs/decisions/*.md` entry must fail non-zero, not silently pass). Confirmed against real
history, not just fixtures: `python3 ledger/decisions.py .` on this repo's actual
`docs/issue-*/reports/*.md` corpus exits 1 and names a real unconfirmed recurring correction
(shared between issue-218 and issue-220, about running the hunt in foreground) — proof the
detector generalizes past its own test fixtures to the actual corpus it was built to mine.

## Concrete upstream basis
Approved proposal: `docs/issue-322/proposals/2026-08-07-decision-mining.md` (APPROVE issue-322/implementation,
issue #322 comment, single-account mode). Survey: `docs/issue-322/reports/implementation/survey.md`.
Scout brief: `docs/issue-322/reports/implementation/scout-brief.md`.

## Beyond its own acceptance criteria (#330)
This reaches beyond `ledger/decisions.py` passing its own fixture-based test in one concrete,
observed way: run live against this repo's real `docs/issue-*/reports/*.md` corpus (see above),
it already found and named one genuine unconfirmed recurring correction that predates this
build — issue-218 and issue-220 both hit the same "run the hunt in foreground, not background"
correction with no `docs/decisions/*.md` entry citing it. Filing or confirming that specific
finding is out of scope for this build (the proposal's own Out of scope: retroactive backfill of
`docs/decisions/*.md` entries is a separate proposal) — recorded here only as evidence that the
mechanism reaches real, uninstrumented history, not only its own test fixtures.
It does not reach into `docs/decisions/*.md` authorship, PR review bodies, or the GitHub API —
those remain exactly as before, per the proposal's Out of scope.

## What did not work
None.

## Doc placement
- No new env var, config key, dependency, or migration was introduced — nothing to add to a
  handbook.
- No library-or-format choice over a named alternative beyond the one already recorded in the
  proposal's own `## Rationale` (LLM clustering vs. mechanical substring match) — the proposal
  itself is the durable artifact for that choice; no separate `docs/issue-322/decisions/*.md`
  entry was written since nothing hard-to-reverse was decided beyond what the proposal states.
- No benchmark/investigation numbers were produced — nothing for `docs/issue-322/reports/`
  beyond this record itself.

## Hunt record
After-proposal hunt: `docs/reports/2026-08-07-hunt-decision-mining.md` (no finding, already on
branch per prior commit). Before-landing hunt: every touched path in this transition is under
`ledger/` (not `docs/`), so the docs-only fast path does not apply; diff is ~230 added lines
across 2 new files (21-200 line tier boundary — treated as the >200/multi-file tier's lower
neighbor, one stance, 120s cap, tier `default`) — dispatched separately; see
`docs/reports/2026-08-07-hunt-decision-mining.md` for its appended before-landing section.

## Open findings
None open. (After-proposal hunt: no finding. Before-landing hunt: see appended section in the
hunt record file above for its result.)

## Next steps
None required to close #322 — the approved proposal's write set is fully delivered and its own
test passes. Follow-ups explicitly deferred by the proposal's Out of scope (not this issue's to
pick up): wiring the detector into a merge gate; mining PR review bodies/issue comments directly;
retroactively confirming or filing the issue-218/issue-220 finding this run surfaced.

## Rationale for deviations
None — build matches the approved proposal's `## What will be done` exactly.
