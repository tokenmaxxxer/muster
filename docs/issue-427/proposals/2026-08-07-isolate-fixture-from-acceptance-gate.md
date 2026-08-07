---
status: proposed
files:
  - gates/test_closes_gate_ci.py
  - docs/issue-427/reports/implementation/survey.md
  - docs/issue-427/proposals/2026-08-07-isolate-fixture-from-acceptance-gate.md
---

## Request

`t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`
(#312) fails on any PR because it happens to route through
`acceptance_gate`'s content rule (#310), which its stubbed issue-#304
body never satisfied. Fix the test so it pins only the shape #312
actually wrote it for, scan the suite for other tests touching live
GitHub state, and record what #367's scan didn't search.

## Constraints

- Per #310: acceptance for this fix must be an artifact that actually
  runs, not prose.
- Per #335: a recorded/stubbed fixture must not trade "depends on live
  state" for "silently drifts from the real interface and keeps passing
  meaninglessly."
- Per #427 acceptance: the target test must pass with network access
  removed or the call stubbed at the boundary it actually uses; a
  companion test must fail if the dependency on live/unstubbed state
  silently returns.
- Test/write set stays inside `gates/test_closes_gate_ci.py` and
  `docs/issue-427/**` — no change to `gates/pr_reference.py` or
  `gates/acceptance_gate.py` themselves; the survey found no defect in
  either, only in the test's fixture scope.

## Rationale

Two approaches were available for item 1:

1. **Chosen: stub `acceptance_gate.check_issue_body` inside the #312
   test.** `acceptance_gate.check_issue_body` is already a pure,
   network-free function (`gates/acceptance_gate.py:34`) — replacing it
   with a fixed `lambda issue, body: []` for the duration of this one
   test removes the coupling to any body-content-shaped gate,
   permanently and by construction, not just for today's Acceptance
   rule. The test keeps asserting exactly what #312 wrote it to assert
   (autodetected phase == phase2, no closing-keyword mismatch).

2. **Rejected: keep the stub-body approach and just add a valid
   `## Acceptance` section to the fixture text.** This satisfies today's
   gate, but is exactly the treadmill #427 describes — the next
   body-shaped gate (a required `## Rollback` section, a required
   `unverifiable:` escape for a different rule, etc.) breaks this test
   again for a reason unrelated to what it pins. #335's fixture-drift
   caution applies directly: a fixture kept "realistic" against an
   open-ended and independently-evolving set of external rules is a
   private specification nobody maintains going forward. Rejected
   because it re-creates the same defect class one gate later, which is
   the outcome #427 explicitly asks not to trade into.

## What will be done

- In `gates/test_closes_gate_ci.py`, inside
  `t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`,
  monkeypatch `acceptance_gate.check_issue_body` to `lambda issue, body:
  []` alongside the existing stubs (same save/restore-in-finally
  pattern already used for every other patched function in this file),
  so the test's `bad == []` assertion is reachable regardless of any
  content-shaped gate wired downstream of `pr_reference.check`.
- Add one new test,
  `t_autodetect_304_307_shape_still_surfaces_real_acceptance_gate_finding`,
  same phase2/`Closes #304`/role-blind-approval fixture shape, but with
  `acceptance_gate.check_issue_body` left un-stubbed and
  `pr_reference._issue_view_body` returning a body that genuinely lacks
  `## Acceptance` — asserts the acceptance-gate finding text IS present
  in `ci.check(...)`'s result. This is the regression pin: if the #312
  test's isolation from `acceptance_gate` is ever silently removed (the
  stub deleted, or `pr_reference.check` changed to bypass the stub), this
  companion test still exercises the real wiring and would independently
  catch a case where `acceptance_gate` stopped firing at all — covering
  the inverse failure mode.
- `docs/issue-427/reports/implementation/survey.md`: the item-2 scan
  results (already run, see survey) and the item-1 mechanism trace.
- Post the item-2 scan-dimension note as a GitHub comment on #367 (not a
  file write — #367 is closed and out of this issue's write set; a
  comment records the boundary note #427 asks for without reopening or
  amending #367's own scope).

## Out of scope

- Changing `gates/acceptance_gate.py` or `gates/pr_reference.py` — no
  defect found in either; the defect is entirely in the test's fixture
  scope.
- Item 3 of #427 ("decide whether any test may depend on live remote
  state at all, and how it's marked") — the survey's scan found that
  *no* test in this suite currently reaches the network at runtime, so
  there is presently nothing to mark. Deferred as a policy question with
  no live instance to attach a marker to right now, not silently
  dropped: recorded here so a future PR that adds a genuinely
  live-network test has this open question to answer, rather than
  inventing a marking convention against zero real cases.
- Filing new issues or reopening #367 — the #367 note is a comment
  only, per #427's own Boundary section language ("worth recording
  there").

## How you'll know it worked

- `python3 -m pytest -q gates/test_closes_gate_ci.py -k 304_307` — both
  the repaired original test and the new companion test pass.
- `python3 -m pytest -q --ignore=gates` and `python3 -m pytest -q gates`
  run and reported (main's `gates/` subtree collection limitation per
  #398 is why these are run separately, not because either is skipped).
- The new companion test, run against the pre-fix state of
  `t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`
  (i.e. without the `acceptance_gate` stub), still passes on its own —
  demonstrating it exercises the real gate wiring independently of the
  fix, satisfying #427's "fails if the fixture reverts to a live fetch"
  criterion for the inverse direction (fails if the gate itself stops
  being reachable, not only if the pinned test's isolation breaks).
