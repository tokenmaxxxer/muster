---
code_under_review:
  - gates/test_closes_gate_ci.py
  - gates/pr_reference.py
  - gates/acceptance_gate.py
loop_state: phase-2-complete
---

# issue-427 implementation record

## Why

#312's `t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`
reads real issue #304's body via a stubbed `pr_reference._issue_view_body`
whose text has never carried an `## Acceptance` section. #310's
`acceptance_gate.check_issue_body` landed after #312 and now runs inside
`pr_reference.check` on any phase2 PR whose body closes an issue — so this
test fails for a reason unrelated to the shape it pins. #427 asks that the
test's coupling to `acceptance_gate` be removed at the boundary it
actually uses, that a companion test still catch the inverse failure (the
gate silently stops firing), and that the suite be scanned for other
live-GitHub-state tests.

## What was done

Implemented the approved phase-1 proposal
`docs/issue-427/proposals/2026-08-07-isolate-fixture-from-acceptance-gate.md`
verbatim (already merged to main) — no re-survey, no re-proposal.

- `gates/test_closes_gate_ci.py`:
  `t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`
  now stubs `acceptance_gate.check_issue_body` directly (the pure,
  network-free boundary at `gates/acceptance_gate.py:34`), isolating it
  from `#310`'s content rule and any future body-shaped gate.
- Added companion test
  `t_autodetect_304_307_shape_still_surfaces_real_acceptance_gate_finding`:
  same #304/#307 shape, `acceptance_gate.check_issue_body` left
  un-stubbed, issue body genuinely missing `## Acceptance` — asserts the
  real gate's finding text is present in `ci.check(...)`'s result. This
  is the inverse pin: if the stub above is ever silently deleted, or
  `pr_reference.check` stops calling `acceptance_gate` at all, this test
  independently catches the gate going unreachable.
- Item-2 scan (suite-wide grep for tests reading live GitHub state):
  every `pr_reference._pr_view` / `pr_reference._issue_view_body` /
  `spawn._issue_comments` reference in `gates/test_closes_gate_ci.py` and
  `gates/test_closure_sweep.py` is a monkeypatched stub assigned inside
  the test, not a live call — `import subprocess` is present only in
  `pr_reference.py`/`spawn.py` themselves (the boundary functions), never
  invoked un-stubbed from a test. No other live-GitHub-state test found.
  Verified by running the two target tests with `subprocess.run` guarded
  to raise on any `["gh", ...]` invocation — both still pass, confirming
  no `gh` CLI call reaches the real boundary.
- Posted the #367 boundary-note comment (item in "What will be done"):
  https://github.com/tokenmaxxxer/on-the-record/issues/367#issuecomment-5215183396

### Pre-existing, unrelated to #427 (found and left alone)

While making the target test runnable, hit a signature-drift bug
unrelated to #427's cause: `spawn._issue_comments` now returns
`(list[dict], bool)` (`spawn.py:963`), but the `304_307` test's own
`spawn._issue_comments` stub returned a bare list, raising
`ValueError: not enough values to unpack` before the acceptance-gate
code path was ever reached. This is exactly the kind of test-stub drift
#419 warns "call-site searches miss" (a stub, not a call site, goes
stale silently). Fixed only inside the two tests this proposal's write
set covers (`t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`
and the new companion test) by returning `(comments, True)` instead of a
bare list — updating this stub was necessary to reach and demonstrate
the #427 fix at all, so it stays inside the proposal's file-level write
set even though the proposal text didn't anticipate this specific line.
The same drift affects 10 other pre-existing tests in this file
(`t_phase_from_approval_*`, most other `t_autodetect_*`) — those are
out of scope here (proposal names only the 304/307 pair) and are the
12 pre-existing `gates/` failures reported below.

## What did not work

- Tried blocking `socket.socket` at the Python level to prove "runs with
  network access removed" — broke pytest's own import machinery
  (`anyio`/`ssl` import `socket.socket` internally), unrelated to the
  code under test. Switched to guarding `subprocess.run` against any
  `["gh", ...]` argv instead — that's the actual boundary
  `pr_reference.py`/`spawn.py` use to reach GitHub, and it correctly
  proves the two target tests never call out.

## Open findings

- The current issue #427 body (orchestrator-rewritten to name executable
  artifacts per #310's closes-gate) lists as a bullet: "A test that fails
  if the fixture reverts to a live fetch, so the dependency cannot
  silently return." No such test exists on this branch. What exists is a
  one-time manual check (this turn and the prior one): guarding
  `subprocess.run` to raise on any `["gh", ...]` argv and re-running the
  two target tests by hand — that proves the *current* code doesn't call
  out, but nothing in the committed suite would fail if
  `pr_reference._issue_view_body`/`_pr_view` stubs were later deleted
  from the two 304/307 tests and the fixture reverted to hitting live
  GitHub. Reporting this as a gap rather than reinterpreting the
  artifact to match what was built.

## Next steps

Phase-2 work as scoped by the approved proposal is otherwise complete.
The open finding above (missing regression guard for "fixture reverts to
live fetch") is outside this proposal's frozen write set — not
implemented here, flagged for a follow-up decision rather than silently
added mid-build.

## Open finding resolution path

Not applicable — loop_state is terminal (`phase-2-complete`) with no open
findings.

## Test run (rebased tree, this turn)

Branch rebased onto `origin/main` at `68900a3` (two more PRs — #421/#289
and #343/#331 — landed since the prior rebase; this is the **third**
time this branch has been rebased onto a moving main, which is itself an
instance of the repeated-rebase cost #390 describes). Conflict in
`gates/test_closes_gate_ci.py` (main's pre-#427 version of the 304/307
test vs. this branch's stub+companion-test rewrite) resolved by taking
this branch's version wholesale — main had not touched that hunk
independently, so no logic merge was needed, only conflict-marker
removal.

- `python3 -m pytest -q` (repo root, no `--ignore`, single collection,
  full suite, run against the rebased tree) — **525 passed**, 0 failed.
  Main's own baseline (per the invoking instruction) is 524 passed with
  no ignore flag; this branch adds exactly one net test
  (`t_autodetect_304_307_shape_still_surfaces_real_acceptance_gate_finding`)
  over that baseline, consistent with 524 + 1 = 525.
- The 12 pre-existing `spawn._issue_comments` unpack-arity failures
  recorded in the prior version of this record (attributed to #435) are
  **gone** on the rebased tree — #435 (or an equivalent fix) landed on
  main in the interim, superseding that entire "Pre-existing, unrelated
  to #427" section above as stale history, not current state.
- `python3 -m pytest -q gates/test_closes_gate_ci.py -k 304_307` — 2
  passed (both target tests, isolated).

## Doc placement (completed)

- [x] Survey (phase 1, already merged):
      `docs/issue-427/reports/implementation/survey.md`
- [x] Proposal (phase 1, already merged):
      `docs/issue-427/proposals/2026-08-07-isolate-fixture-from-acceptance-gate.md`
- [x] This record: `docs/issue-427/reports/implementation.md`
