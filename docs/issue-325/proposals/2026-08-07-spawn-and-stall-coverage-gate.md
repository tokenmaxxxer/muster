---
status: proposed
files:
  - gates/spawn_coverage.py
  - gates/ci.py
  - spawn.py
  - test_gates.py
  - test_spawn.py
---

## Request

#325 (paraphrased): when the operator files a GitHub issue they assume a session is
now working it, but two things silently happen instead: (1) an issue gets filed and
no session is ever spawned for it, and (2) a session runs, but the watch loop's
"stalled" signal is never surfaced anywhere beyond a `print()` line, so a stalled
session and a progressing one look identical from outside. Both worsen as parallel
issue count grows, because the only thing that currently re-arms detection is the
orchestrating LLM's own turn loop remembering to do so.

## Constraints

- Per #310: acceptance must name an executable artifact that fails on regression — a
  promise, memory note, or doc sentence does not discharge this.
- Cron-as-driver and LLM-as-scheduler are both already rejected in
  `docs/decisions/2026-07-29-permanently-closed-alternatives.md`; `protocol.md:278`
  keeps "what calls on-the-record" as an open, stage-appropriate unsettled question.
  This proposal does not reopen that — it does not add a daemon, poller, or
  always-on process of any kind.
- No overlap with #298 (orchestrator approve/merge gating) or #288 (spawn.py CLI flag
  correctness) — confirmed by reading both issues directly, since neither has a
  `docs/issue-<n>/` tree to check against.

## Rationale

Considered making the fix "teach the orchestrator's run-loop instructions to always
re-invoke `spawn.py watchdog` every N turns" — rejected. That is exactly the
non-discharge #310 and the issue text itself call out: a prose/convention promise
about orchestrator behavior ("I will remember to poll") is indistinguishable from the
status quo (`roster_watchdog`'s own docstring already says this, spawn.py:1545) and
already demonstrably fails under context pressure — that failure is the bug being
filed. A promise cannot be the fix for "promises aren't being kept."

Chose instead: a deterministic, git-committed check with a real exit code and a
real board-state read, following `gates/closure_sweep.py`'s existing precedent
(injectable pure function + thin CLI, no daemon) — because that pattern already
exists in this repo, is already how the project turns "the orchestrator forgot X"
into "a script can independently discover X happened or didn't," and needs no new
scheduling infrastructure to be useful: a human or CI can run it on demand, and it
gives a correct, falsifiable answer either way, which prose reassurance cannot.

## What will be done

1. **`gates/spawn_coverage.py`** (new, mirrors `closure_sweep.py`'s shape):
   - `find_uncovered(open_issues: list[int], board: dict, now, grace_hours: float) -> list[int]`
     — pure, network-free, unit-testable: an open issue number with no matching
     `issue-<n>` key in `spawn.board(root)` and older than `grace_hours` (default a
     few hours, to avoid flagging an issue filed minutes ago) counts as uncovered.
   - `main()` CLI: `python3 gates/spawn_coverage.py [--repo <path>] [--grace-hours N]`
     — calls `gh issue list --state open --json number,createdAt` for the live list,
     calls `spawn.board(root)` for local state, prints uncovered issue numbers, exits
     1 if any, 0 otherwise. Same network-at-the-edge / pure-core split as
     `closure_sweep.find_violations` vs `closure_sweep.main`.
2. **`spawn.py`**: extend the `stalled` branch of `_auto_respawn_check` (spawn.py:1841
   area) so a `stalled` verdict posts a GitHub issue comment once, using a new marker
   constant (`_STALL_COMMENT_MARKER`) and the same read-then-check dedup pattern
   `_CRASH_COMMENT_MARKER` and `closure_sweep._SWEEP_COMMENT_MARKER` already use — so
   repeated `watchdog` ticks don't spam, but the *first* detection of a stall becomes
   a durable, externally-visible fact instead of a line in a terminal nobody is
   watching. This does not change the "never auto-respawn a stall" policy — only
   whether the stall becomes visible outside the invoking terminal.
3. **`gates/ci.py`**: no forced new wiring, since `closure_sweep` itself is not wired
   into `ci.py`'s `check()` (confirmed — no reference exists there today). Match that
   precedent: `spawn_coverage.py` stays a standalone script runnable the same way
   `closure_sweep.py --post` is, not force-integrated into a `check()` signature it
   doesn't share a spec with. If build-time inspection finds `ci.py` gained a
   closure_sweep hook since this survey, mirror it identically for spawn_coverage
   instead of diverging.
4. Tests in `test_gates.py` (for `find_uncovered`, network-free, same fixture style
   as `t_board_reads_loop_state`) and `test_spawn.py` (for the new stall-comment
   posting, mocking `gh` the way existing crash-comment tests already do).

## Out of scope

- Any daemon, cron job, webhook listener, or other always-on trigger — closed
  alternatives per the constraints above.
- Auto-respawning a `stalled` session (only crash currently triggers respawn) —
  changing that policy is a separate decision this issue does not make.
- #298's orchestrator-approve/merge gating and #288's CLI flag-correctness bugs —
  confirmed no overlap.
- Wiring `spawn_coverage.py` or the stall comment into any scheduler — that is the
  same "who calls on-the-record" question `protocol.md:278` leaves open; this
  proposal only makes the underlying fact mechanically checkable and visible, it
  does not decide who checks it or how often.

## How you'll know it worked

- `python3 gates/spawn_coverage.py` exits 1 and names the issue number when an open
  GitHub issue has no board entry past the grace window; exits 0 when every open
  issue has one. A committed unit test constructs both cases against
  `find_uncovered` with no network access and pins both exit paths.
- A committed unit test drives `_auto_respawn_check` (or its stalled-handling helper)
  against a fixture roster entry classified `stalled`, and asserts a GitHub comment
  call is made exactly once across two consecutive ticks (dedup), where today no
  comment call happens at all (`stalled` is print-only).
- Both are executable artifacts (`pytest`/direct script invocation) that fail on
  regression, per #310 — not documentation, not a memory note, not a promise.
