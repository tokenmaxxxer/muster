---
code_under_review:
  - spawn.py
  - test_spawn.py
loop_state: landed
---

# Implementation record — issue-484

## Upstream
Based on: docs/issue-484/proposals/2026-08-08-watch-registration-race-and-outcome-derivation.md
(approved via `APPROVE issue-484/implementation` comment, single-account mode).

## What was done
1. **Registration race** (spawn.py `_watch`): factored the roster lookup
   into `_lookup_roster_entry`; when the entry is absent, `_watch` now
   polls it with the same backoff as `_await_bounded` (0.05s start,
   double to 2.0s cap) until it appears or `stall_timeout_min * 60`
   elapses, before falling through to today's `기록 없음` / exit-1 path.
2. **Outcome derivation** (`_spawn_one` / `fail_closed_downgrade`):
   - added `_pr_open_or_merged_for_branch` (filters `gh pr list --state
     all` on `state in (OPEN, MERGED)`, unlike `_pr_for_branch`, which
     `_spawn_one` still uses unmodified for its other, approval-lookup
     callers).
   - dropped the `outcome == "progressed"` gate on the
     already_delivered/branch check in `_spawn_one` — it now runs
     whenever `issue is not None and not blocked and not new_commit`,
     using the new open-or-merged helper.
   - added `push_succeeded` (derived from `ensure_pushed`'s status,
     excluding `push-rejected`/`pr-create-failed`) as a new
     `fail_closed_downgrade` parameter.
   - `fail_closed_downgrade` gained a `silent-failure` upgrade branch,
     symmetric to the existing `progressed` downgrade branch: a
     `silent-failure` verdict with no uncommitted changes is upgraded to
     `progressed` when `already_delivered` or (`new_commit` and
     `push_succeeded`).
   - added a stderr message for the new upgrade path, mirroring the
     existing downgrade messages.
3. **Tests** (`test_spawn.py`):
   - `WatchRegistrationRace` (2 cases): entry appearing on the 3rd poll
     attaches and streams; entry never appearing times out at
     `stall_timeout_min` and returns 1.
   - `FailClosedDowngrade` (+5 cases): already-delivered upgrade,
     new-commit+push-succeeded upgrade, no-upgrade-without-push-success,
     no-upgrade-on-not-already-delivered (closed-unmerged-PR regression
     guard), no-upgrade-with-uncommitted-changes.
   - `PrOpenOrMergedForBranch` (3 cases): closed-unmerged -> None,
     open -> number, merged -> number.
   - existing `test_non_progressed_outcomes_are_never_touched` (includes
     `"silent-failure"`) and the refused-commit-no-push suite
     (test_spawn.py:899-1007 originally, now shifted) verified still
     green — no regression.
   - full suite: `python3 -m pytest test_spawn.py -q` -> 290 passed.

## Why
Watch attaches before the roster write lands (registration race), and
session-end outcome labels are derived from `classify()`'s raw
docs-board-delta verdict rather than observable git/PR state, causing
`silent-failure` on already-landed/pushed work. Per approved proposal.

## What did not work
None.

## Open findings
None.

## loop_state
landed
