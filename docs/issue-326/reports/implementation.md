---
code_under_review:
  - spawn.py
  - test_spawn.py
loop_state: phase-2-complete-blocked-on-user-issue-edit
---

# Phase 2 — implementation record (issue #326)

## Why

Approved phase-1 proposal (`docs/issue-326/proposals/ensure-pushed-stranded-comment.md`,
approved via `APPROVE issue-326/implementation` on issue #326, single-account
mode, PR #348): `ensure_pushed()` had two silent dead-end returns (host
`git push` fails; `gh pr create` fails) that left stranded work invisible to
the operator — the exact shape of PR #290. This closes that gap by reusing
the existing `_post_crash_comment` idiom.

## What was done

1. Added `_post_stranded_push_comment(root, issue, role, branch, reason, detail)`
   in `spawn.py`, next to `_post_crash_comment`, reusing its idempotent
   marker/read-then-check/`gh api .../comments` pattern. Marker:
   `[on-the-record] stranded-relay: {branch}:{reason}`.
2. Wired both of `ensure_pushed()`'s previously-silent dead-end returns:
   - host `git push` failure -> `_post_stranded_push_comment(..., "push-failed", stderr)`
   - `gh pr create` failure -> `_post_stranded_push_comment(..., "pr-create-failed", stderr)`
3. Added three tests in `test_spawn.py` (class `EnsurePushedStrandedComment`):
   - `test_ensure_pushed_posts_comment_on_push_failure`
   - `test_ensure_pushed_posts_comment_on_pr_create_failure`
   - `test_ensure_pushed_stranded_comment_is_idempotent`

## What did not work

None.

## Verification

Per-file: `python3 -m pytest test_spawn.py -k stranded_push -v` — 3 passed.
Per-file full: `python3 -m pytest test_spawn.py -q` — reported in the reply
this record accompanies.

Full-suite (`python3 -m pytest -q`) is independently broken per #360
(test_approve_scope.py replaces `spawn.subprocess.run` process-wide with no
teardown) — pre-existing, unrelated to this change. Any full-suite failures
outside `stranded_push`/`EnsurePushedStrandedComment` pre-date this change.

## Doc placement

No env var, new dependency, migration, or public-signature/wire-format
change — nothing to place on the handbook/decisions/reports ladder beyond
this record itself.

## Reach beyond acceptance criteria (#330)

This closes only the narrower gap: `ensure_pushed()` runs and its own
push/PR-create attempt fails. It does not touch the deeper gap named in the
survey/proposal (a process dying before `ensure_pushed()` is ever invoked)
— that remains open, named explicitly in the proposal's Out of scope. No
already-on-disk state is invalidated: `_post_crash_comment`,
`RESPAWN_MAX_ATTEMPTS`, and the crash-comment marker are untouched; the new
marker constant and function are additive.

## Hunt

Per role-handoff/warrant cadence, a hunter should run at end of phase 1
(already recorded on approved PR #348) and before phase-2 completion. This
headless single-shot session cannot dispatch a background hunter without
consuming its result within the same turn (contract v3 s22 overrides
warrant's cadence here), so no additional hunt was dispatched this turn.
closed_checks: none beyond the tests listed above.

## Open findings

None outstanding.

## Open-finding resolution path

N/A — no open findings.

## Next steps

None for this issue's phase 2. The deeper gap (process dying before
`ensure_pushed()` runs) is explicitly out of scope; a future issue would
cover the rejected sweep alternative if the operator wants it closed.

## Rebase (2026-08-07)

PR #348 conflicted with `main` after ~40 unrelated PRs landed. Rebased
`issue-326/implementation` onto `origin/main` (`git rebase origin/main`).

Two real conflicts in `spawn.py`, both from independent same-region
additions, not overlapping logic:

1. `main` added `_post_stall_comment` (issue #325) directly above where
   this branch added `_post_stranded_push_comment`/`_STRANDED_PUSH_COMMENT_MARKER`
   (issue #326) — same insertion point, two unrelated functions. Resolved
   by keeping both functions, `_post_stall_comment` first (matches its
   position on `main`), `_post_stranded_push_comment` after.
2. `ensure_pushed()`'s two failure branches: `main` had independently
   changed the bare `return`s into structured `{"status": ..., "reason": ...}`
   dicts (issue #301 B2) on the same lines this branch changed to call
   `_post_stranded_push_comment(...)` before returning. Resolved by doing
   both — post the comment, then return the structured dict — since
   neither change supersedes the other; dropping either would silently
   regress #301 B2 (structured caller feedback) or #326 (this issue, the
   operator-visible comment).

`test_spawn.py` merged cleanly (no conflicts).

### Re-run acceptance evidence, on the rebased tree

- `python3 -m pytest test_spawn.py -k stranded -v` — 3 passed
  (`EnsurePushedStrandedComment::test_ensure_pushed_posts_comment_on_pr_create_failure`,
  `::test_ensure_pushed_posts_comment_on_push_failure`,
  `::test_ensure_pushed_stranded_comment_is_idempotent`).
- `python3 -m pytest test_spawn.py -q` — 266 passed.
- `python3 -m pytest -q --ignore=gates` — 392 passed (main's own
  verification note before this rebase reported 389; the +3 is this
  branch's own new tests, consistent).
- `python3 -m pytest -q gates` — 58 passed. This contradicts the
  verification note handed to this session (`gates/` reported as unable
  to collect due to a module-name collision, #398) — on this rebased
  tree, `gates/` collects and passes both alone and inside a full
  unfiltered `python3 -m pytest -q` run (450 passed, no `--ignore`
  needed). Reporting the discrepancy as observed rather than the
  expected failure; #398 may already be fixed on `main`, or the
  collision may be environment-dependent and not reproducing here.

No new tests were added and no additional scope was touched beyond the
conflict resolution above — the rebase changed no behavior other than
what the conflict markers show.

## Re-rebase and re-verification (2026-08-07, second pass)

`origin/main` had advanced 36 commits past this branch's base (3 local
commits ahead vs. 36 on `origin/main`) since the prior rebase note above —
per #390, a green run against a stale base attests to a state that no
longer exists. Re-ran `git rebase origin/main`: clean, no conflicts this
time.

Re-ran verification on the freshly rebased tree:

- `python3 -m pytest test_spawn.py -k stranded -q` — 3 passed (same three
  tests named above).
- `python3 -m pytest -q --ignore=gates` — 409 passed, 1 failed
  (`test_spec_index.py::t_baseline_repo_passes` — `docs/specs/reconciled-index.md`
  hash mismatch against current `protocol.md`/other spec files; unrelated
  to this issue's `spawn.py`/`test_spawn.py` write set, caused by other
  docs landing on `main` since the index was last regenerated).
- `python3 -m pytest -q gates` — 68 passed, 1 failed
  (`gates/test_closes_gate_ci.py::t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`
  — asserts issue #304 has an `## Acceptance` section; unrelated to this
  issue). `gates/` collects and runs on this tree — the module-name
  collision this session was told to expect (#398) is not reproducing
  here, consistent with the prior rebase note's same observation.

Both failures are outside this issue's write set (`spawn.py`,
`test_spawn.py`) and pre-date this branch's changes; the acceptance
tests named in the Acceptance-section proposal below (`EnsurePushedStrandedComment::*`)
pass cleanly.

## PART 1 — Acceptance-gate blocker: cannot edit issue #326

The PR's `closes-gate` check fails because issue #326's `## Acceptance`
section is prose-only (per #310). This session cannot fix that directly:
`gh issue edit 326` was refused by this session's `gh-guard` hook —
"issues are the user's requirement backlog, user-authored only (contract
v3 s9) — no role touches them." No role-side workaround exists; this is
a mechanical, not a judgment, block.

Proposed replacement `## Acceptance` text (for the operator to paste into
issue #326 directly — this session cannot apply it):

```
## Acceptance

Per #310, prose does not discharge this. Acceptance must name an executable artifact that fails when this regresses.

- `ensure_pushed()`'s two previously-silent dead-end returns (host `git push`
  failure; `gh pr create` failure) must post an operator-visible, idempotent
  comment on the subject issue instead of returning silently. Covered by:
  `test_spawn.py::EnsurePushedStrandedComment::test_ensure_pushed_posts_comment_on_push_failure`,
  `test_spawn.py::EnsurePushedStrandedComment::test_ensure_pushed_posts_comment_on_pr_create_failure`,
  `test_spawn.py::EnsurePushedStrandedComment::test_ensure_pushed_stranded_comment_is_idempotent`.
  gate: `python3 -m pytest test_spawn.py -k stranded`

- unverifiable: the deeper gap — a session process dying or being killed
  before `ensure_pushed()` is ever invoked (e.g. OOM, host kill, network
  partition mid-turn) — has no in-process hook to post a comment from,
  since the process that would post it is the one that died. Closing that
  gap needs an external watchdog (a separate process or scheduled job that
  notices a stalled/abandoned branch and posts on its behalf), which is
  out of scope for this issue per the approved phase-1 proposal
  (`docs/issue-326/proposals/ensure-pushed-stranded-comment.md`, Out of
  scope) and is not mechanically checkable from inside `spawn.py`'s own
  test suite.
```

This names a real, already-passing test path — not a path that merely
exists to satisfy the matcher (the irony this task flagged explicitly).
Until the operator applies this (or equivalent) text to issue #326, the
`closes-gate` check on PR #348 stays red; that is outside this session's
authority to fix.

## Third pass (2026-08-07): re-attempted issue edit, re-rebased, re-verified

This turn was asked to (1) apply the Acceptance rewrite to issue #326
directly, (2) verify the named artifact is real, (3) re-run acceptance
evidence against current `main`. Attempted `gh issue edit 326` with the
same replacement text drafted in PART 1 above; `gh-guard.sh` refused it
again, identical reason (contract v3 s9, issues are user-authored only,
no role touches them). This is the same mechanical block as before, not
a new finding — confirms it is not session-specific.

Re-rebased: `origin/main` had advanced 5 commits past this branch's base
(`23d90ea`, PR #429 merged). `git rebase origin/main` — clean, no
conflicts.

Re-ran verification on the freshly rebased tree:

- `python3 -m pytest test_spawn.py -k stranded -q` — 3 passed (same
  three `EnsurePushedStrandedComment` tests named throughout this record).
- `python3 -m pytest -q --ignore=gates` — 409 passed, 1 failed
  (`test_spec_index.py::t_baseline_repo_passes` — same pre-existing
  `docs/specs/reconciled-index.md` hash-mismatch failure noted in the
  prior rebase pass; unrelated to this issue's `spawn.py`/`test_spawn.py`
  write set).
- `gates/` was not run this pass per this turn's own instruction (its
  module-name collision, #398, is asserted un-collectable on `main`);
  only `--ignore=gates` was executed, as directed.

Both the acceptance-gate blocker (PART 1) and the `test_spec_index.py`
failure remain outside this session's authority/write set. The
Acceptance-section rewrite proposed in PART 1 is unchanged and still
awaits the operator pasting it into issue #326.

## Fourth pass (2026-08-07): re-attempted issue edit, re-rebased, re-verified

This turn was asked to unblock #326's `closes-gate` (PR #348) by
rewriting the issue's `## Acceptance` section so each criterion names an
executable artifact, then re-run acceptance evidence against current
`main`. Re-attempted `gh issue edit 326` with the exact replacement text
drafted in PART 1 (unchanged — it already names the real, passing
`EnsurePushedStrandedComment::*` tests as the gate, and marks the
watchdog gap `unverifiable:` with a reason, per this turn's own
instruction not to name a path that doesn't exist). `gh-guard.sh`
refused it again, identical reason (contract v3 s9, issues are
user-authored only, no role touches them) — third confirmation this is a
standing mechanical block, not session state. The proposed text in PART 1
is the deliverable for the operator to paste in; this session has no
path to apply it directly.

Rebased: `origin/main` had advanced 2 commits past this branch's base.
`git rebase origin/main` — clean, no conflicts.

Re-ran verification on the freshly rebased tree:

- `python3 -m pytest test_spawn.py -k stranded -q` — 3 passed (same
  three `EnsurePushedStrandedComment` tests named throughout this
  record) — this is the artifact PART 1's proposed Acceptance text
  names as the gate.
- `python3 -m pytest -q --ignore=gates` — 409 passed, 1 failed
  (`test_spec_index.py::t_baseline_repo_passes` — same pre-existing
  `docs/specs/reconciled-index.md` hash-mismatch against `protocol.md`,
  unrelated to this issue's write set).
- `python3 -m pytest -q gates` — 68 passed, 1 failed
  (`gates/test_closes_gate_ci.py::t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`
  — asserts issue #304 has an `## Acceptance` section; unrelated to
  issue #326).

Both failures are outside this issue's write set (`spawn.py`,
`test_spawn.py`) and pre-date this branch's changes. #326's own
acceptance artifact (`EnsurePushedStrandedComment::*`, 3/3) passes
cleanly on current `main`.
