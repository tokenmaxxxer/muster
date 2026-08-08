---
status: proposed
files:
  - spawn.py
  - test_spawn.py
---

## Request
`watch` run right after a spawn returns errors out ("기록 없음") instead
of waiting a bounded grace period for the roster entry to appear.
Separately, session-end outcome labels are derived from `classify()`'s
raw verdict (rc/board-delta/blocked/permission-denials) rather than from
observable git/PR state, so successful re-delivery-of-already-landed and
successful-push-with-no-docs-delta sessions get labeled
`silent-failure`.

## Constraints
- Bound the registration-race wait by the existing `stall_timeout_min`
  (same knob `_await_bounded` already uses) — no new CLI flag.
- Do not touch `classify()`'s existing signature/semantics (rc, result,
  delta, blocked) — it stays a pure, git-blind classifier per its own
  docstring contract; the fix lives in the derivation step that already
  wraps it (`fail_closed_downgrade` + the `already_delivered` computation
  in `_spawn_one`).
- Do not regress the refused-commit-no-push → `failed-no-commit` shape,
  already correct and covered by test_spawn.py:899-1007.
- No new dependency, env var, or schema/migration.

## Rationale
**Alternative considered and rejected — make `classify()` itself
git-aware (pass it `new_commit`/`already_delivered` directly):**
rejected because `classify()`'s docstring states it "판정하지 않는다 —
이름만 붙인다" and deliberately stays blind to git state so its four
inputs (rc/result/delta/blocked) stay unit-testable in isolation; folding
git checks in would conflate the "what did the session self-report"
layer with the "what actually landed" layer that `fail_closed_downgrade`
exists to own. Chosen instead: extend the existing post-classify
derivation step so `already_delivered`/`new_commit`-and-pushed checks run
unconditionally (not gated on `outcome == "progressed"`), keeping the two
layers separate.

**Alternative considered and rejected — poll roster registration with a
fixed short sleep (e.g. `time.sleep(2)`) instead of reusing
`_await_bounded`'s backoff:** rejected because a fixed sleep either wastes
time on the common case (registration usually lands in well under a
second) or is too short under load; the repo already has a proven
poll-with-backoff-and-bound pattern for exactly this "wait for a
condition, bounded by stall_timeout" shape, and reusing it keeps the
watch race fix consistent with `--follow`'s existing bounded-wait
behavior instead of introducing a second timing policy.

## What will be done
1. **Registration race**: in `_watch()` (spawn.py:2211-2227), when the
   roster lookup finds no entry, poll the roster (same backoff schedule
   as `_await_bounded`: start at 0.05s, double to a 2.0s cap) until an
   entry appears or `stall_timeout_min * 60` elapses. On appearance,
   proceed into the existing `_await_bounded`/`--follow` path unchanged.
   On timeout, keep today's `기록 없음` message and exit code 1 — a
   genuinely-never-spawned issue must still fail this way (distinct from
   issue #451's never-appearing case per the issue text).
2. **Outcome derivation**: in `_spawn_one` (around spawn.py:3611-3644),
   compute `already_delivered` and a push-succeeded check independent of
   `classify()`'s raw verdict — i.e. drop the `outcome == "progressed"`
   gate at spawn.py:3620 so these checks run whenever `issue is not None
   and not blocked`, before `fail_closed_downgrade` is applied.
   `already_delivered` must NOT reuse `_pr_for_branch` unmodified for
   this purpose: that helper queries `--state all`, so a branch whose
   only PR was closed *without* merging would count as "delivered" and
   silently mask a genuinely failed/no-op session under the new
   unconditional check (found by the after-proposal warrant hunt,
   docs/reports/2026-08-08-hunt-watch-registration-race-and-outcome-derivation.md).
   The outcome-derivation use of "a PR exists" must check the PR is
   **open or merged**, not closed-unmerged (e.g. filter `_pr_for_branch`'s
   underlying `gh pr list` output on state, or add a merged-or-open
   variant used only here; `_pr_for_branch`'s existing `--state all`
   callers for approval-lookup are unaffected). Extend
   `fail_closed_downgrade`'s logic (or an equivalent pre-step) so a raw
   `"silent-failure"` verdict is upgraded to `"progressed"` (or a new,
   more precise label — see tests) when `already_delivered` is true or
   when `new_commit` is true and the push succeeded, even though the
   docs-board delta was empty.
3. **Tests** (`test_spawn.py`): add the four Acceptance-listed cases —
   watch-before-registration grace-window attach; already-landed
   re-delivery not classified `silent-failure`; successful-push-with-
   empty-docs-delta not classified `silent-failure`; refused-commit-no-
   push still `failed-no-commit` (regression guard, not new behavior).

## Out of scope
- Any change to `classify()`'s own signature or the four-input contract
  it documents.
- The `--follow` recursion session-end ordering (already fixed, issue
  #247/#180 references in code).
- New CLI flags or configuration for the grace window.
- Non-git-workspace (`issue is None`) spawn paths.

## How you'll know it worked
`test/test_spawn.py` (repo root `test_spawn.py`) gains and passes:
- a case starting `watch` before the roster entry exists, entry appearing
  within the grace window → watch attaches and streams (red before the
  fix, green after).
- a case: no board delta, but branch already has an open or merged PR
  (`already_delivered`-equivalent) and no new local commit → outcome is
  not `silent-failure` (red before, green after).
- a case: no board delta, branch's only PR is closed *without* merging,
  no new local commit → outcome stays `silent-failure` (regression guard
  for the closed-unmerged-PR gap found by the after-proposal hunt).
- a case: no board delta, `new_commit` true, push succeeded → outcome is
  not `silent-failure` (red before, green after).
- existing refused-commit-no-push → `failed-no-commit` cases
  (test_spawn.py:899-1007) stay green (no regression).
