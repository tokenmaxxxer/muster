---
kind: coding-record
code_under_review: gates/spawn_coverage.py, spawn.py, test_gates.py, test_spawn.py
loop_state: landed
---

# Implementation record — issue #325

## Why

Phase 2, executing the approved proposal
(`docs/issue-325/proposals/2026-08-07-spawn-and-stall-coverage-gate.md`),
approved via issue-level comment `APPROVE issue-325/implementation`
(single-account mode). Delivering exactly what the proposal says: a
deterministic, network-at-the-edge/pure-core gate script
(`gates/spawn_coverage.py`) that names any open GitHub issue with no
board entry past a grace window, and a durable comment posted the first
time a session is classified `stalled` (mirroring the existing
`_CRASH_COMMENT_MARKER` idempotent-comment pattern), so both silent
failure modes named in #325 become externally visible instead of
print-only / nonexistent.

## What was done

1. **`gates/spawn_coverage.py`** (new): `find_uncovered(open_issues, board,
   now, grace_hours=3.0)` — pure, network-free — flags an open issue number
   whose `issue-<n>` key is absent from `spawn.board(root)` and older than
   `grace_hours` (parses `createdAt`, ISO-8601 `Z`-suffixed). `main()` CLI
   calls `gh issue list --state open --json number,createdAt` plus
   `spawn.board(root)`, prints uncovered numbers, exits 1/0 — same
   network-at-the-edge/pure-core split as `closure_sweep.find_violations`
   vs `closure_sweep.main`. Not wired into `gates/ci.py`'s `check()`:
   confirmed `closure_sweep` itself still isn't wired there either (no
   reference in `ci.py` today), so this matches that existing precedent
   per the proposal rather than diverging from it.
2. **`spawn.py`**: added `_STALL_COMMENT_MARKER` (mirrors
   `_CRASH_COMMENT_MARKER`'s shape) and `_post_stall_comment(root, issue,
   key, work, log)` (line ~1778, next to `_post_crash_comment`) — same
   read-then-check idempotent-comment pattern via `_issue_comments`.
   `_auto_respawn_check` (line ~1841) now calls it on a `stalled` verdict
   before returning; `crashed` handling and the observation-only policy
   for `stalled`/`normal`/`in-progress` (no auto-respawn) are unchanged —
   only visibility changed, not the respawn policy.
3. Tests: `test_gates.py` gained `t_spawn_coverage_flags_open_issue_with_no_board_entry`,
   `t_spawn_coverage_covered_issue_not_flagged`,
   `t_spawn_coverage_grace_window_suppresses_freshly_filed_issue` (network-free,
   drive `find_uncovered` directly). `test_spawn.py` gained class
   `PostStallComment` with `test_skips_when_marker_already_present`,
   `test_posts_when_marker_absent` (mirrors `PostCrashComment`'s style
   exactly, `gh` mocked via `subprocess.run` monkeypatch), and
   `test_auto_respawn_check_posts_stall_comment_once_across_two_ticks`,
   which drives `_auto_respawn_check` with a fixture roster entry
   classified `stalled` across two consecutive ticks and asserts the
   comment call happens exactly once (dedup) — the exact acceptance case
   named in the proposal's "How you'll know it worked".

## Executed checks (this session, real runs)

- `python3 -m unittest test_spawn -v` — 236 tests, all pass, including
  the 3 new `PostStallComment` tests and no regressions in the existing
  236-test suite.
- New `test_gates.py` functions (`t_spawn_coverage_*`) run directly via a
  one-off Python invocation — all 3 pass. (Full `python3 test_gates.py`
  aborts partway through on an unrelated, pre-existing sandbox limitation:
  `t_repo_local_claude_config_stops_the_spawn` writes to
  `~/.tokenmaxxxer/trusted-repo-config.json`, which this sandbox mounts
  read-only — reproduced identically on unmodified `main`/pre-change HEAD
  via `git stash`, so it is not a regression this change introduced. This
  is an executed-and-observed environment constraint, not a claim of
  success for that one pre-existing test.)
- `python3 gates/spawn_coverage.py --repo .` run live against this repo's
  real GitHub state (real `gh` call, no mocking): exited 1 and printed 10
  real open-issue numbers (#284, #286-#292, #294, #298) with no board
  entry — confirming the script's network-at-the-edge path actually works
  end-to-end, not just its pure core.

## What did not work

None — no attempted approach was undone or replaced during this build.

## Open findings

None.

## Next steps

None for this issue — delivered as approved. Follow-ups noted below are
explicitly out of scope for this proposal, not deferred work owed by it.

## Open finding resolution path

N/A — no open findings.

## What this reaches beyond its own acceptance criteria (issue #330)

- `gates/spawn_coverage.py` is a new, standalone script with no caller —
  it discovers a fact (issue filed, no board entry) but nothing currently
  runs it automatically. Per the proposal's explicit "Out of scope," this
  is intentional: wiring it into a scheduler is the still-open "who calls
  on-the-record" question (`protocol.md:278`), which this issue does not
  decide. On-disk state this invalidates: none — it reads `gh` and the
  board, writes nothing.
- The `stalled` → comment change makes every currently-stalled roster
  entry, the next time `spawn.py watchdog` ticks over it, post a one-time
  GitHub comment where previously nothing was posted. This is new
  outward-visible behavior on issues that had no prior automated comment
  from this path — noted here since it is a side effect of running
  `watchdog` against already-on-disk roster/board state, not something
  the "how you'll know it worked" tests alone would surface to a reader.
  No respawn policy changed; `stalled` still never triggers a respawn.

## Rationale for deviations

None — implementation matches the approved proposal's "What will be
done" exactly; no scope-exceeded stop, no alternative swap.

## Warrant hunt (before-landing)

Dispatched `warrant-hunter`, stance 0 (assume the gate just touched is
bypassable — find the bypass), against the uncommitted diff. Finding:
`gates/spawn_coverage.py`'s `main()` returned exit code 0 (same as "no
uncovered issues") when `gh issue list` failed — a broken/unauthenticated
`gh` would look identical to a clean pass to any CI consumer checking
only the exit code, reproducing this issue's own "silent failure looks
like progress" defect inside the gate meant to catch it. Fixed in this
session: `main()` now returns 1 on `gh` failure with a distinct stderr
message ("판정 불가"), so a broken read is never mistaken for a clean
pass. Hunt record: `docs/reports/2026-08-07-hunt-spawn-and-stall-coverage-gate.md`.

closed_checks:
- check: gh-failure-exit-code-distinguishable-from-clean-pass
  code_sha: (working tree at commit time, see git log for this branch)
