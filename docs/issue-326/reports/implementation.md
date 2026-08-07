---
code_under_review:
  - spawn.py
  - test_spawn.py
loop_state: phase-2-complete
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
