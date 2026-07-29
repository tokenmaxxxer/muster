files:
- spawn.py
- test_spawn.py

## Request

Issue #89 (paraphrased): a headless role session (`claude -p`, single
turn) can hand work off to a `run_in_background` worker and end its turn.
The backgrounded process dies with the parent at turn end (reproduced
independently, 2026-07-29) — but the session still self-reports
"progressed", and `spawn.py` currently relays that through unmodified. In
the reported incident, a session said "worker running in background, will
own commit and push"; the run left one uncommitted 2-line diff, none of
the 7 promised deliverables, no report file, no commit — and still logged
as `progressed`.

Two fixes are requested:

1. **Preamble warning** in `_spawn_one`'s assembled task text: state that
   the turn is headless/single-turn, that anything delegated to
   background execution dies when the turn ends, and that all work must
   be completed directly within the turn.
2. **Fail-closed post-exit verification**: if a run is otherwise
   classified `progressed` but the workspace shows no new commits and/or
   a dirty tree, spawn must report the run as `FAILED`, not `progressed`.
   An honest `blocked` self-report from the session is a distinct,
   non-failure outcome and must not be caught by this downgrade.

## Constraints

- An honest `blocked` report is not a failure. The fail-closed check must
  only downgrade the `progressed` classification — it must never turn an
  honest `blocked` (or `waiting-on-human`, or `refused`) outcome into
  `FAILED`.
- Fail-closed applies narrowly: only when the run would otherwise be
  classified `progressed` (per `classify()`, spawn.py:951-974) **and**
  the workspace shows no new commits since before the session ran, and/or
  the tree is dirty. If real commits landed and the tree is clean, no
  downgrade happens even if the board delta alone looks small.
- No behavior change for any run that already produces a real commit —
  this fix must not add friction, false positives, or extra prompts to
  the honest-success path.
- Scope is limited to `issue is not None` (isolated issue-workspace)
  spawns, since that is the only path with a dedicated git workspace/
  branch to check commits against, and it is the path the incident and
  the existing dirty-tree check (spawn.py:1718-1729) already target.
  Ad-hoc (`issue is None`) spawns are out of scope for the git-based
  check (see Out of scope).
- The downgrade must happen before `wakes.consume(...)` (spawn.py:1735-
  1738) and before `ledger_write(...)` (spawn.py:1739-1748), so a
  downgraded run neither consumes the wake row nor is durably recorded as
  `progressed`.
- Preserve the existing `outcome` vocabulary (`errored`, `progressed`,
  `waiting-on-human`, `refused`, `silent-failure`, `uncommitted-work`)
  as-is; add the new fail-closed result as an additional distinct value
  (e.g. `"failed-no-commit"` or similar — final string decided at
  implementation time) rather than overloading `silent-failure` or
  `uncommitted-work`, since those already carry other meanings.

## What will be done

1. **Preamble warning** — extend the f-string built in `_spawn_one` at
   spawn.py:1623-1628 (the `issue is not None` branch) with an explicit
   statement that this is a headless single turn, background-delegated
   work does not survive turn end, and all work must complete within the
   turn. Keep it adjacent to the existing "commit before ending the
   session" language so the two constraints (commit discipline +
   no-background) read as one coherent completion-of-turn rule rather
   than two disconnected warnings.

2. **Fail-closed post-exit verification**:
   - Capture the pre-run HEAD (`git -C {cwd} rev-parse HEAD`, tolerating
     a repo with no commits yet) alongside the existing `before =
     board_snapshot(cwd)` at spawn.py:1659, for `issue is not None` runs.
   - After `proc.wait()`, alongside the existing `after =
     board_snapshot(cwd)` / `uncommitted` computation (spawn.py:1710,
     1718-1729), capture the post-run HEAD the same way and compare
     against the pre-run HEAD to determine whether any new commit landed.
   - After `outcome = classify(rc, result, delta, blocked)`
     (spawn.py:1731), add: if `outcome == "progressed"` and
     `issue is not None` and (no new commit landed since pre-run HEAD, or
     `uncommitted` is non-empty), downgrade `outcome` to the new
     fail-closed value and print a clear stderr reason string (mirroring
     the existing style of the `refused`/`silent-failure` messages at
     spawn.py:1762-1769) explaining what was expected (a commit) versus
     what was observed (none / dirty tree), so a human or the next
     re-spawn has an actionable signal.
   - Ensure the downgrade happens before the `wakes.consume(...)` call
     (spawn.py:1735-1738) so the wake row is not silently marked
     answered, and before `ledger_write(...)` (spawn.py:1739-1748) so the
     ledger records the true outcome.
   - Leave `classify()` itself (spawn.py:951-974) and its existing tests
     untouched — the downgrade is a distinct post-classification step
     applied in `_spawn_one`, since `classify()` has no access to git
     state and its existing contract (rc/result/delta/blocked only) is
     already covered by tests and should not be widened.

3. **Tests** (in `test_spawn.py`, alongside the existing `classify()`
   test class, e.g. near `test_progress_outranks_refusal` /
   `test_silent_failure_is_loud`):
   - A test that a `progressed`-classified run with no new commits (HEAD
     unchanged) and a clean tree is downgraded to the fail-closed
     outcome.
   - A test that a `progressed`-classified run with no new commits but a
     dirty tree is downgraded to the fail-closed outcome.
   - A test that a `progressed`-classified run **with** a new commit and
     a clean tree is left as `progressed` (no false positive on the
     honest-success path).
   - A test that a `waiting-on-human` / `refused` / `blocked`-style
     outcome is never touched by the downgrade, even with no new commits
     (proves the "honest blocked is not failure" constraint).
   - A test (string-containment or similar) confirming the assembled
     task text for `issue is not None` calls includes the new
     headless/single-turn/no-background warning.
   - Depending on how the downgrade is factored (inline in `_spawn_one`
     vs. extracted into a small testable helper alongside `classify()`),
     these may be unit tests against the helper or lighter-weight
     integration tests against `_spawn_one` with a temp git repo fixture;
     final shape decided during implementation, but coverage of the four
     bullets above is the bar.

## Out of scope

- Ad-hoc (`issue is None`) spawns: no dedicated git workspace exists to
  check commits against, so the fail-closed git check is not applied
  there in this phase. The preamble warning could arguably still apply,
  but since ad-hoc `task` is passed through unmodified today (no
  f-string insertion point exists), adding one is a separate, larger
  change and is left out of phase 2 unless explicitly requested.
- The companion "mid-run watchdog" (in-flight monitoring) mentioned in
  the issue as filed separately — not part of this proposal.
- Determining which of the issue's two candidate root-cause paths
  (worker spawned then killed vs. spawn attempt denied and never
  started) applies to the original incident — the issue states the
  remedy is identical either way, and phase 1/2 do not need to
  distinguish them.
- Any change to `classify()`'s existing signature or the meaning of its
  existing outcome strings.
- Any change to `wakes.py`, `ledger_write`'s schema beyond the new
  outcome string being a valid value, or CLI-level (`main()`/`drive()`)
  behavior.

## How success will be known

- New unit/integration tests in `test_spawn.py` (per `## What will be
  done`, item 3) pass, specifically demonstrating:
  - a no-commit `progressed` run is downgraded to the fail-closed outcome
    (both clean-but-no-commit and dirty-tree variants),
  - a real-commit `progressed` run is unaffected,
  - `blocked`/`waiting-on-human`/`refused` outcomes are unaffected by the
    downgrade,
  - the assembled preamble text contains the new headless/no-background
    warning for `issue is not None` spawns.
- Full existing `test_spawn.py` suite continues to pass unmodified
  (`classify()`'s existing tests, spawn_cmd/env tests, gate-report tests,
  doctor-halt tests, etc.), confirming no regression to the
  already-covered paths.
- Manual/optional: re-running the issue's own reproduction (background a
  short-lived command, end the turn, spawn with `issue` set) should now
  surface the run as the new fail-closed outcome in stderr and the
  ledger, instead of `progressed`.
