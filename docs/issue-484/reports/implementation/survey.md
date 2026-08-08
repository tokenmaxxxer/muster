# Survey — issue-484

## Scope: watch registration race + session-end outcome misclassification

### Scout skip
Pure bugfix on existing internal orchestration control flow (spawn.py); no
external product surface, no design decision needing category exemplars.
Skip condition: "the change is a pure bugfix."

## 1. Registration race (`_watch`, spawn.py:2211-2227)

`_watch()` looks up `idx.get(key)` once. If the roster entry for
`issue-<n>[/role]` hasn't been written yet (spawn just returned, roster
write hasn't landed), `entry is None` and the function prints `기록 없음`
and returns 1 immediately — no retry, no wait. `_await_bounded` (line
2151) already implements the pattern needed: poll with backoff
(`poll_s` starting at 0.05s, doubling to a 2.0s cap) until either a
condition is met or `stall_timeout_min * 60` elapses. The fix is to wrap
the roster lookup itself in the same bounded-wait shape before falling
through to the current stall/absence handling.

Existing precedent for "distinguish absent-forever from not-yet-appeared"
is `--follow`'s stall-accumulation logic (spawn.py:2239-2243), which
already speaks to exactly this class of race for a *different* signal
(session-end during recursion) — same repo, same shape, not yet applied
to the roster-lookup entry point itself.

## 2. Outcome misclassification (`classify` / `fail_closed_downgrade`, spawn.py:1362-1469, 3611-3644)

Pipeline as it stands:
```
outcome = classify(rc, result, delta, blocked)          # line 3611
if outcome == "silent-failure" and uncommitted: ...      # uncommitted-work
elif outcome == "silent-failure" and push-rejected: ...  # push-rejected
new_commit = ...
already_delivered = False
if issue is not None and outcome == "progressed" and not blocked and not new_commit:
    already_delivered = _pr_for_branch(...) is not None   # <-- gated on outcome == "progressed"
downgraded = fail_closed_downgrade(outcome, issue, blocked, new_commit, uncommitted, already_delivered)
```

`classify()` returns `"progressed"` only when `delta` (the docs-board
snapshot diff, `board_snapshot()` at line ~1340, which hashes files
under `docs/issue-*/**`) is non-empty. Two of the issue's three cited
misclassifications never reach `"progressed"` at all, so the
`already_delivered` check — the only place that consults git/PR state —
never runs for them:

- **issue-441 re-delivery over already-merged work**: session correctly
  does nothing (work already landed), so `delta` is empty → `classify()`
  returns `"silent-failure"` directly. `already_delivered` is never
  computed because the `outcome == "progressed"` guard at line 3620
  short-circuits.
- **issue-58 after a successful push**: the session's real change was a
  code commit outside `docs/issue-*/**` (or a commit whose net docs diff
  happened to be empty), so `board_snapshot()` sees no delta even though
  `new_commit` is true and the push succeeded → same `silent-failure`
  short-circuit, `already_delivered`/push-success is never checked.
- **first issue-58 fix session, refused commit (no delivery) →
  `progressed`**: this shape (uncommitted docs present, no new commit)
  is already handled correctly by the current `fail_closed_downgrade`
  (`uncommitted` and not `new_commit` → `"failed-no-commit"`,
  spawn.py:1465-1466) and by existing tests (test_spawn.py:899-1007).
  No further code change identified for this specific shape; the
  proposal's fix for the other two shapes must not regress it.

Root cause for the two live misclassifications: **success signals are
derived from the docs board diff, gated behind `classify()` already
having said `"progressed"`**, instead of being checked independently of
`classify()`'s verdict. A `silent-failure`-shaped classify() result
should still be re-checked against `already_delivered` (PR exists on
this branch, no new commit needed) and `new_commit`+push-succeeded before
being finalized.

## Write set (frozen)
- `spawn.py` — `_watch()` (registration grace wait), the outcome-derivation
  block around spawn.py:3611-3644 (move/extend the `already_delivered`
  and new-commit-pushed checks so they run independent of `classify()`'s
  raw verdict).
- `test_spawn.py` — new cases per Acceptance: watch-before-registration
  grace-window case; three red→green outcome-misclassification cases
  (already-landed re-delivery, successful-push-with-empty-docs-delta,
  refused-commit-no-push already covered/kept green).

No new dependency, no new env var, no schema change.
