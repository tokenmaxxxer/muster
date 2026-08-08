# issue-492 phase-1 survey — architecture

Scope: what already exists toward "every terminal state detected, orchestrator
continues from reconciled observable state" — so the proposal names only the
actual gap, not a rebuild.

## What already exists (do not duplicate)

**Per-session terminal-state derivation (#132/#484).** `session_end_verdict()`
(spawn.py:1409) reads `<work>.events.jsonl`, finds the last `session-start`,
and returns one of `normal` / `crashed` / `stalled` / `in-progress`. Crash
detection is process-liveness based: if no `session-end` event followed and
`_alive(pid)` is false, verdict is `crashed` — this already covers `kill -9`
mid-run, including SIGKILL, as long as the roster entry's `pid` is the
process that dies. `stalled` covers hang-past-timeout via log mtime vs
`WATCHDOG_SILENCE_MIN`. This is the "every terminal state produces a durable
observable event" half already answered for the *single-session* case.

**Outcome derivation layered on top (#484).** `fail_closed_downgrade()`
(spawn.py:1457) takes `classify()`'s report-trusting verdict
(`progressed`/`refused`/`silent-failure`/...) and downgrades/upgrades it
against git ground truth (new commit? push succeeded? uncommitted tree?
already delivered via existing PR?) — e.g. `progressed` with an uncommitted
tree becomes `progressed-dirty-tree`; a claimed `progressed` with no new
commit becomes `failed-no-commit`. This is "derived-from-state outcome" per
#484, already shipped, already the per-session half named in #492's own
constraint list.

**Board-wide anomaly sweep (#464's roster_watchdog).** `roster_watchdog()`
(spawn.py:1705) scans every live roster entry once, calls
`watchdog_check_one()` per entry, and — separately — `_board_wide_sweep()`
(spawn.py:1674) does a `gh`-backed closure/coverage sweep across the whole
board (observe-only, no fix/kill). `_auto_respawn_check()` (spawn.py:2079)
already turns a `crashed` verdict into a bounded auto-respawn
(`_respawn_or_cap`, spawn.py:2016, capped at 2, #488). `stalled` stays
observe-only by explicit prior decision (#132) — a stalled session may still
be making progress a hang-heuristic can't see.

**Bounded follow (#451).** `_watch()`/`_await_bounded()` (spawn.py:2263,
2189) give a caller a bounded wait for the next roster-visible event or
stall, already distinguishing "no event yet" from "the observation channel
itself vanished" (spawn.py:2231).

## The actual gap

None of the above compares **what a role/subject was dispatched to
deliver** against the observed state. `roster_watchdog` and
`session_end_verdict` answer "is this session alive, and how did it end" —
a purely internal question about the session process. They never read the
*expected* side: which subject+role was spawned for, what the issue's 실행
계획 step asked for, whether the branch it should have advanced actually
moved, whether the PR it should have opened exists, whether
`docs/issue-<n>/reports/<role>.md`'s `loop_state` is the state that
role-completion implies. `board()` (spawn.py:1194) and `status()`
(spawn.py:1218) read board frontmatter but only for display — nothing folds
that against roster/ledger state to name divergences with next actions. The
CLI has no `reconcile` verb; `drive()` (spawn.py:2502) drives from board
`loop_state` directly, not from a divergence list.

This is exactly the gap the scout brief's exemplar names: the "observed
state, freshly re-derived" must-be is met (session_end_verdict,
fail_closed_downgrade); the "diffed against desired state" must-be is not.
`#492`'s acceptance criteria confirm the shape: a session that dies without
pushing must produce reconciliation output naming the divergence and a
`respawn/resume` action — that comparison function does not exist yet.

## Write-surface inventory for the proposal

- `spawn.py` — new pure comparison function + a `reconcile` CLI verb; wire
  into `roster_watchdog`'s existing tick (spawn.py:1705) so reconciliation
  rides the same board-read cadence rather than adding a second poller.
- `test/test_spawn.py` — fixtures per the issue's two named checks (SIGKILL
  mid-run, dies-without-pushing).
- `gates/test_boundary.py` — manifest row(s) for the delivered piece(s), per
  the issue's third acceptance check.
- Cross-repo: whether core's role-handoff contract or a rulebook needs a
  canon entry for "reconciliation is authoritative over session self-report"
  is a phase-1 open question, resolved in the proposal's alternatives
  section per the #66 canon boundary (core owns contract text; rulebooks own
  role directives; this plugin owns the mechanism).
