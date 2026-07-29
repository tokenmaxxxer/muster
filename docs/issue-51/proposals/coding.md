# Proposal — issue #51: clean must not delete workspaces of live sessions

files:
- spawn.py (the `clean` branch, spawn.py:1299-1326)
- test_spawn.py (new `Clean` test class)

## Request (paraphrased intent, secrets stripped)

`spawn.py clean` has twice deleted the workspace of a role session that was
still running, because it only checks git preserved-work state and never
consults the live-session roster spawn.py already maintains. Fix `clean` so
it is structurally impossible for it to delete a workspace with a live
registered session, and add a regression test for that case.

## Constraints

- Reuse the existing roster (`runs/active.json` via `_roster_load`/`_alive`),
  do not invent a second liveness mechanism.
- `clean`'s current safety criteria (no uncommitted changes, no unpushed
  commits) stay as-is; the roster check is an additional, independent skip
  condition, checked first since it's the cheapest and needs no git calls.
- Keep the Korean bilingual print-message style already used in `clean`'s
  "남김 (미보존 작업 있음): ..." line.

## What will be done

In the `clean` branch:
1. Load the roster once via `_roster_load()` before the loop.
2. Build a `{resolved work path: entry}` map, keeping only entries whose
   `pid` is alive per `_alive()` (mirrors `roster_ps()`'s liveness check —
   a dead entry must not block deletion, matching "정리됨" semantics
   elsewhere).
3. For each candidate workspace `w`, if its resolved path matches a live
   roster entry, print a "남김 (실행 중인 세션 있음): <name> [issue-<n>/<role>, pid <pid>]"
   line, count it under `kept`, and `continue` before any git status/rmtree
   work — this check runs before the existing preserved-work check.
4. No change to the preserved-work check or the summary line format.

## Out of scope

- Pruning dead roster entries from disk during `clean` (that's `roster_ps`'s
  job already; `clean` only reads the roster).
- Changing `_spawn_one`'s registration/removal timing.
- Any change to `roster_ps`/`roster_kill`.

## How you'll know it worked

New test in `test_spawn.py`: seed `runs/active.json` with an entry whose
`pid` is the test process's own live pid (or another guaranteed-alive pid)
and whose `work` matches a clean, no-git-diff workspace directory created
under a temp `MUSTER_WORK_DIR`; run `clean`; assert the workspace directory
still exists and the "실행 중인 세션 있음" line appears in stdout — while a
sibling clean workspace with no roster entry is still deleted.
