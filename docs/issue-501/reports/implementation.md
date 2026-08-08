---
code_under_review: HEAD
loop_state: landed
---

# issue-501 implementation record

## What was done
Step 2 (the cuts), built against the step-1 measurement's named terms —
model working time dominant (86.3%, not compressible without touching
model behavior, out of scope), inter-session idle tail (388.9m,
concentrated on issues 171/472/484/173) named as the compressible
candidate:

- `test/test_latency_report.py`: extracted the step-1 ad-hoc idle-gap
  script into tested, reusable functions — `compute_idle_gaps()` (keyed
  by `(repo, issue, role)`, the fixed grouping) and `median_idle_s()` —
  plus a regression test pinning the issue-#(number-collision) bug fixed
  in the step-1 warrant hunt, and a test asserting the delivered
  breakdown table cites a ledger/log source per row (the issue's own
  step-1 acceptance check, previously unimplemented).
- `docs/handbooks/operations.md`: added a "Respawn batching" section
  (KO + EN) codifying the practice named in the issue's fourth candidate
  direction — approve and respawn in the same orchestrator turn, never
  confirm-then-wait-for-a-separate-cycle — with the measured before
  numbers and the pre-registered after metric (re-run
  `compute_idle_gaps()`/`median_idle_s()` against a later ledger window).
- `python3 -m pytest test/test_latency_report.py -q` — 5 passed, 0
  failed.

## Why
Issue #501 step 2: the step-1 measurement killed fixed-startup-cost as
the primary lever (13.7% of in-session wall-clock) and named
inter-session idle as the compressible target (388.9m, long-tail on 4
issues). This delivers the cut that measurement supports — tightening
the approve→respawn turnaround — without touching model behavior or the
unmeasurable fixed-startup sub-terms (proposal's own Out of scope).
Refusal/rework rounds were checked against the data and found
*proportionate* to their session share (15/123 sessions, not a
disproportionate multiplier) — so "reduce rework rounds" was not built
as a separate cut; the numbers didn't support it as a distinct lever
beyond what #459's existing preflights already cover.

## Upstream basis
docs/issue-501/proposals/2026-08-08-session-latency-breakdown.md,
approved via `APPROVE issue-501/implementation` comment on issue #501
(single-account mode, contract v3 s19; PR #502 author and approver are
both JiwonJung94).

## What did not work
- Before-landing warrant hunt (stance 3) found the pre-registered
  before/after metric had no reproducible way to pick the "after" window:
  `compute_idle_gaps()`/`median_idle_s()` took no time boundary, and
  nothing recorded when the batching practice was adopted. Fixed by
  adding a `since_ts` parameter to both functions and a
  `PRACTICE_ADOPTED_TS` constant (commit 6009fc8, 2026-08-08T12:00:00Z)
  in `test/test_latency_report.py`, referenced from the handbook section
  — a future re-run passes `since_ts=PRACTICE_ADOPTED_TS` to select only
  post-adoption gaps. Re-cleared: `python3 -m pytest
  test/test_latency_report.py -q` → 6 passed, 0 failed.

## closed_checks
- `python3 -m pytest test/test_latency_report.py -q` → 6 passed, 0
  failed, code_sha HEAD.
- resolved_finding: before-landing hunt
  (`docs/reports/2026-08-08-hunt-session-latency-breakdown.md`, stance
  3, before-landing/step-2 section) — no-boundary before/after metric,
  fixed via `since_ts`/`PRACTICE_ADOPTED_TS`, re-cleared.

## Open findings
None outstanding. The proposal's own limits stand as recorded there: the
idle term still mixes orchestrator-respawn wait and human-approval wait
indistinguishably (not separable from what's logged today), so the
after-metric this record pre-registers measures the *combined* gap, same
as the before. A true attribution split would need new instrumentation
(operational-surface change to `spawn.py`), out of scope here as it was
in step 1.
