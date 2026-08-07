# Survey — issue #383

Write set actually touched: `gates/closure_sweep.py`, `test_gates.py`,
`.github/workflows/closure-sweep.yml`, plus this report tree.

## What's there

- `gates/closure_sweep.py::classify()` was keyword-anchored: it only
  flagged `MERGED_DELIVERY_ISSUE_OPEN` when the PR body contained a
  `Closes/Fixes/Resolves #n` match. Confirmed live: `python3
  gates/closure_sweep.py` on this repo printed `종결 일관성 스윕: 위반 없음`
  while issue #367 (delivered via merged PR #368, no closing keyword)
  sat open.
- `gates/ci.py::_phase2_record_evidence()` (landed by #284,
  `a02d118`) already defines the exact alternate evidence needed: a
  branch's phase-2 record file (`docs/issue-<n>/reports/<role>.md`)
  existing with a non-empty `loop_state`. This is the same evidence
  #284 accepted for the closes-gate; classify() had no access to it.
- `grep -rn closure_sweep .github/` was empty — no workflow calls the
  sweep at all, scheduled or per-push.
- Existing tests in `test_gates.py` (`t_closure_sweep_*`) pin
  `classify()`'s current keyword-only behavior and
  `find_violations()`'s prefetch/board-walk plumbing; no test covers the
  no-keyword case.

## Cross-repo check (scope item 4)

`tokenmaxxxer-core` has no `gates/closure_sweep.py` of its own — the
sweep is an on-the-record-only mechanism. Its issues #132/#133/#151 are
open despite merged delivery (confirmed via
`closedByPullRequestsReferences` being empty and `docs/issue-<n>/reports/
implementation.md` present on `main` with the delivery commits folded
into the same PR as the phase-1 proposal — same shape as #367/#368).

Org-wide sweep via `gh search prs --owner tokenmaxxxer --merged`,
filtered to PRs merged **today** (2026-08-07, the day #284 merged) whose
body has a plain `#n` reference but no closing keyword: five hits.
Two are phase-1-only proposals by design (`risk-management-rulebook#17`,
`defect-verification-rulebook#31` — issue staying open is correct
there). `tokenmaxxxer-core#139` references issue #138, already CLOSED
(fine). The remaining two are the already-known leaks
(`on-the-record#368`->#367, `tokenmaxxxer-core#152`->#151). No
additional leaked issue was found in today's merge window.

## Decision

Two ways to make closure keyword-independent, per the issue's own
framing:
(a) derive closure from the same phase-2-record evidence #284
    established, reusing `ci._phase2_record_evidence`, or
(b) make the system emit the `Closes` keyword itself (e.g. a phase-2 PR
    body constructor step) so the author never has to remember it.

(a) wins: it needs no change to how PRs are authored, reuses code and a
precedent already approved on this exact question by #284, and closes
the detection gap immediately for both the four known leaks and any
future ones — without touching the PR-authoring path at all, which
stays exactly as free-form as #284 intended.
