# Coding record — issue #51

loop_state: landed

code_under_review: spawn.py (`clean` branch), test_spawn.py (`Clean` class)

## why

PR #52 phase-1 (survey + proposal, docs/issue-51/proposals/coding.md)
received a human Approve review on issue-51/coding, authorizing execution.

## what was done

Implemented the approved proposal exactly:

- `clean` loads the roster once via `_roster_load()` before the loop, builds
  a `{resolved work path: entry}` map keeping only entries whose `pid` is
  alive per `_alive()`.
- For each candidate workspace, if its resolved path matches a live roster
  entry, prints `남김 (실행 중인 세션 있음): <name> [issue-<n>/<role>, pid <pid>]`,
  counts it under `kept`, and `continue`s before any git status/rmtree work —
  ahead of the existing preserved-work check.
- Dead roster entries do not block deletion (mirrors `roster_ps()`'s
  liveness semantics).
- Added `Clean` test class in test_spawn.py: seeds `runs/active.json` (via
  patched `spawn.ROSTER`) with a live-pid entry pointing at one clean
  workspace, runs `clean`, asserts that workspace survives with the
  "실행 중인 세션 있음" message while a sibling clean workspace with no
  roster entry is deleted.

## what did not work

(nothing — implementation matched the proposal on first pass)

## upstream basis

docs/issue-51/proposals/coding.md, approved via PR #52 review.

## verification run

`python3 -m pytest test_spawn.py -v` — 43 passed.

## closed_checks

- roster-skip-before-git-status: manually traced — the live-check `continue`
  sits before the `git status --porcelain`/`git log ahead` subprocess calls,
  so a live workspace incurs no git call and no rmtree.
- dead-roster-entry-does-not-block: `_alive()` filters the live map before
  comparison; a dead entry's workspace falls through to the normal
  preserved-work check.

## open findings

None.
