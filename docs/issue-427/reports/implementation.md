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

None.

## Next steps

None — phase 2 complete for this proposal's scope. Push, verify remote,
open PR with `Closes #427`.

## Open finding resolution path

Not applicable — loop_state is terminal (`phase-2-complete`) with no open
findings.

## Test run (this turn, both suites, no ignore flag overall)

- `python3 -m pytest -q gates/test_closes_gate_ci.py -k 304_307` — 2
  passed (both the repaired original test and the new companion test).
- Re-ran the same 2 tests with `subprocess.run` guarded to raise on any
  `gh` CLI invocation — still 2 passed, demonstrating no live-network
  call is reached.
- `python3 -m pytest -q --ignore=gates` (repo root) — 418 passed.
- `python3 -m pytest -q gates` — 65 passed, 12 failed. All 12 failures
  pre-exist on `main` (verified via `git stash`/re-run before this
  change): `t_phase_from_approval_*` (7), and
  `t_autodetect_success_derives_issue_role_and_phase_from_approval`,
  `t_autodetect_reachability_fix_blocks_closes_keyword_without_approval`,
  `t_autodetect_closes_only_blocks_commit_message_keyword_with_clean_body`,
  `t_autodetect_resolves_fork_pr_with_role_none`,
  `t_autodetect_missing_approval_refusal_names_role_searched_and_approvals_present`
  — same `spawn._issue_comments` unpack-arity drift described above,
  attributed by the operator to #435 (in flight). Baseline (pre-change,
  same command) was 13 failed, 63 passed — the one now-fixed failure is
  the #427 target test.
- Combined: 495 passed, 12 failed (all pre-existing/#435), across the
  full suite with no ignore flag applied overall (root run + gates run,
  per #398's known separate-collection limitation, noted in the
  proposal's own "How you'll know it worked").

## Doc placement (completed)

- [x] Survey (phase 1, already merged):
      `docs/issue-427/reports/implementation/survey.md`
- [x] Proposal (phase 1, already merged):
      `docs/issue-427/proposals/2026-08-07-isolate-fixture-from-acceptance-gate.md`
- [x] This record: `docs/issue-427/reports/implementation.md`
