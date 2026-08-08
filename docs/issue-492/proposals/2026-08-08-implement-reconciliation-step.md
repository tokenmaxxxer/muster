---
status: proposed
files:
  - spawn.py
  - test/test_spawn.py
  - gates/test_boundary.py
  - docs/issue-492/reports/implementation/survey.md
  - docs/issue-492/reports/implementation.md
---

# Implement the reconciliation step (issue-492 step 2)

## Request

Build what the landed architecture ADR
(`docs/issue-492/decisions/2026-08-08-reconciliation-step-for-supervision.md`,
#493) specified: a pure `reconcile(expected, observed)` function in
`spawn.py`, a `spawn.py reconcile [--issue N]` CLI verb, an `expects_pr`
field written at dispatch time, `drive()` consuming reconciled state
instead of doing nothing, and tests covering the issue's SIGKILL and
vanish-without-push acceptance cases.

## Constraints

- No new schema beyond what the ADR named: `expects_pr: bool` added to
  the roster entry dict at `roster_register()` call time
  (`spawn.py:3583`), not a new file or store.
- `reconcile()` reads only already-available data
  (`session_end_verdict`, `_pr_open_or_merged_for_branch`, `board()`,
  `_is_new_commit`) — no new `gh` calls beyond what those existing
  functions already make.
- Next-action set is closed, per the ADR: `respawn`, `resume-watch`,
  `manual-review`, `none`.
- `roster_watchdog` rides the existing tick — no second poller.
- Skip condition invoked per survey-order/scout-directive: no open design
  decision remains (see survey.md) — this proposal implements a decision
  already made, it does not scout alternatives to that decision.

## Rationale

The ADR itself already evaluated and rejected the two live alternatives
for *where this logic goes* (folding into `session_end_verdict`, a
second daemon/poller) — see the ADR's Alternatives section. The one
implementation-level choice left open by the ADR is **where in
`drive()` the reconciled state gets consumed**, since the survey found
`drive()` is currently a no-op, not a `loop_state`-reading function as
the ADR's prose assumed.

Two options considered for that:
1. **Have `drive()` call `reconcile()` itself and act on divergences**
   (auto-respawn on `respawn`, resume-watch on `resume-watch`, etc.) —
   rejected for this step: `drive()`'s existing contract is explicitly
   "never auto-picks a role" (`spawn.py:2585-2589`, issue #120) because
   role selection is an orchestrator judgment call, not a routing table.
   Making `drive()` act on `reconcile()`'s output would silently reverse
   that #120 decision without a proposal of its own.
2. **Have `drive()` print `reconcile()`'s divergence list for the
   orchestrator to read, then still stop** (chosen) — preserves #120's
   contract (`drive()` never chooses a role to spawn) while satisfying
   the ADR's requirement that `drive()` be edited to consume
   `reconcile()`'s output "before falling back to `loop_state`": there is
   no `loop_state` fallback to preserve (survey finding), so `drive()`'s
   new behavior is print-reconciled-divergences-then-stop, replacing
   print-nothing-then-stop. This is the smallest change that satisfies
   the ADR's explicit `drive()` write-surface requirement without
   reopening #120.

## What will be done

- `reconcile(expected: dict, observed: dict) -> list[dict]` in `spawn.py`,
  near `session_end_verdict`/`fail_closed_downgrade`. Pure function:
  `expected = {"expects_pr": bool, "role": str, "branch": str}`,
  `observed = {"session_verdict": str, "pr_number": int|None,
  "loop_state": str|None, "new_commit": bool}`. Returns a list of
  `{"kind": str, "detail": str, "next_action": str}` dicts — empty when
  nothing diverges. Divergence rules directly from the issue's worked
  examples: `session_verdict in ("crashed", "stalled")` → `next_action`
  `respawn` (crashed) or `resume-watch` (stalled); `expects_pr` true and
  `pr_number` is None and `session_verdict != "in-progress"` → `respawn`
  (issue's own "dies without pushing → respawn/resume" example);
  otherwise `none`. Unrecognized/inconsistent input (e.g. `loop_state`
  present but `session_verdict` missing) → `manual-review`, never a
  silent pass.
- `_build_expected(entry: dict) -> dict` and
  `_build_observed(root, entry) -> dict` helpers wiring the roster entry
  and existing readers (`session_end_verdict`, `_pr_open_or_merged_for_branch`,
  `board`, `_is_new_commit`) into `reconcile()`'s input shape.
- `roster_register()` call site (`spawn.py:3583`): add `"expects_pr":
  issue is not None` to the entry dict. Not a per-role table:
  `ensure_pushed()` (`spawn.py:3259`, called unconditionally for every
  role at `spawn.py:3799`) opens a PR for *any* role's branch once it has
  commits ahead of origin, gated only on `issue is not None`, never on
  which role ran — a static per-role table would silently record
  `expects_pr=False` for a role outside the table that pushes and then
  dies before the PR opens, exactly the divergence #492 exists to catch
  (after-proposal warrant hunt finding, stance 0,
  `docs/reports/2026-08-08-hunt-implement-reconciliation-step.md`).
  Additive field, existing consumers unaffected.
- CLI verb: `if a.role == "reconcile":` branch in `main()` alongside the
  `watchdog` branch, honoring `--issue` to scope to one roster entry (all
  live+dead entries when omitted, matching `watchdog`'s auto_respawn
  scan). Prints one line per divergence; exit code = divergence count
  (0 = clean), same convention as `roster_watchdog`'s return value
  (`spawn.py:1752-1755`).
- `roster_watchdog()`: call `reconcile()` once per scanned entry inside
  the existing loop (`spawn.py:1773+`), print any divergences alongside
  existing anomaly output, fold the count into `anomaly_count` — rides
  the tick, no new poller.
- `drive()`: replace the unconditional no-op with: read the board/roster,
  call `reconcile()` per entry, print each divergence and its
  `next_action`, then still return 0 without spawning anything — `drive()`
  remains a reporter, never a role-picker (preserves #120).
- Tests in `test/test_spawn.py`: unit tests for `reconcile()` covering
  each divergence rule and the empty/clean case; one fixture test
  reproducing "`kill -9` a running session process → supervision reports
  a terminal state, not silence" (compose `session_end_verdict` with an
  `alive_fn` that returns False + no `session-end` event, feed through
  `reconcile()`, assert `respawn`); one fixture test reproducing "session
  asked to open a PR dies without pushing → reconciliation names the
  divergence and `respawn`" (`expects_pr=True`, `pr_number=None`,
  `session_verdict="crashed"`).
- `gates/test_boundary.py`: one manifest row per delivered piece
  (`reconcile()`, `reconcile` CLI verb, `drive()` edit), per the issue's
  third acceptance check.

## Out of scope

- Execution-observation instrumentation (issue's step 3) — separate role.
- Reopening #120's "drive never auto-picks a role" contract — `drive()`
  reports divergences, it does not act on them.
- `stalled`'s observe-only standing decision (#132) — unchanged;
  `resume-watch` is a reported next action, not an automatic re-arm.
- Any core contract-text or rulebook canon change — the ADR's
  Alternatives section already closed this (no companion delivery
  needed); this step does not reopen that call.

## How you'll know it worked

`python3 -m pytest test/test_spawn.py -k reconcile` green, including the
two fixture tests reproducing the issue's SIGKILL and vanish-without-push
acceptance checks; `spawn.py reconcile --issue <n>` runnable against a
live roster and printing named divergences; `gates/test_boundary.py`
passing with the new manifest rows present.

## What did not work

(none yet — appended during phase-2 build if anything is undone or an
expectation fails to hold.)
