# Current-state survey — issue-492 step 2 (implementation role)

Scout skip condition applies: the architecture ADR
(`docs/issue-492/decisions/2026-08-08-reconciliation-step-for-supervision.md`,
landed via #493) already made every design decision this step needs —
function shape, CLI verb, data sources, the closed next-action set, and
the `drive()` write-surface requirement. This step has no open design
choice left to scout; it implements the ADR. Per scout-directive this is
recorded as the mandatory skip line, not silently omitted.

## Write surfaces read

- `spawn.py:994-1020` — `_pr_for_branch` (any state), `_pr_open_or_merged_for_branch`
  (OPEN/MERGED only). The latter is what "PR exists" should mean for
  reconciliation — `_pr_for_branch` counts a closed-without-merge PR as
  "exists", which would wrongly satisfy an `expects_pr` divergence.
- `spawn.py:1194-1215` — `board(root)`: `{subject: {role: frontmatter}}`,
  reads `docs/issue-<n>/reports/<role>.md` frontmatter (`loop_state`,
  `verdict`, etc). This is the `loop_state` observed-state input.
- `spawn.py:1409-1454` — `session_end_verdict(work, log_path, now, alive_fn)`:
  returns `normal`/`crashed`/`stalled`/`in-progress` from
  `<work>.events.jsonl` + pid liveness + log mtime. Pure given its inputs;
  already covers SIGKILL (`crashed`, pid dead + no session-end event) and
  hang (`stalled`, pid alive + log silent > 90min).
- `spawn.py:1331-1352` — `_is_new_commit(cwd, before_head, after_head)`:
  git-grounded "did this session's own workspace advance".
- `spawn.py:1568-1572` — `roster_register(key, entry)`: entry today carries
  `pid, role, issue, ts, work, log, before_head, wrapper_pid` (call site
  `spawn.py:3583`). No `expects_pr` or any "what was this session asked to
  deliver" field exists yet — the ADR's step-1 addition.
- `spawn.py:1741-1839` (`roster_watchdog`) — the existing repeating tick
  (10-15min cadence, called by the orchestrator) that already sweeps every
  live and (with `auto_respawn`) dead roster entry. The ADR's chosen ride
  point for the reconcile call.
- `spawn.py:2582-2594` — `drive(cwd, unattended, limit)`: **currently a
  pure no-op** — prints "no auto-routing table" and returns 0
  unconditionally. It does not read `loop_state` or board state today at
  all, contrary to what the ADR's Context section describes as its
  current behavior ("driven by trusting `loop_state` directly"). This
  survey corrects that: `drive()` has no board-read logic to replace: the
  ADR's `drive()` write-surface requirement means *adding* a reconciled-
  state consumption path to a function that currently does nothing, not
  swapping out an existing `loop_state`-read path.
- `spawn.py:2952-2957` — CLI dispatch for `role == "drive"`: calls
  `require_board`, `require_no_repo_config`, `require_doctor`, then
  `drive(...)`. `role == "watchdog"` (`spawn.py:2823-2824`) is the sibling
  dispatch pattern a new `reconcile` verb would follow.
- `spawn.py:2679-2699` (argparse) — verbs are dispatched by a flat chain of
  `if a.role == "<verb>":` checks in `main()`; no subparsers. A `reconcile`
  verb needs one more `if a.role == "reconcile":` branch plus an
  `--issue` filter (the `--issue` argument already exists,
  `spawn.py:2792-2793`, reused by `closure-sweep`/`kill`/`watch`).
- `test/test_spawn.py` — existing coverage includes
  `session_end_verdict` unit tests (crashed/stalled/normal/in-progress
  fixtures via `alive_fn` injection and synthetic `.events.jsonl` files)
  and `fail_closed_downgrade` unit tests. The reconcile tests fit this
  same pattern: pure-function unit tests with fixture dicts for
  `expected`/`observed`, plus one fixture reproducing the issue's own
  SIGKILL and vanish-without-push acceptance cases by composing
  `session_end_verdict` + `_pr_open_or_merged_for_branch` (mocked) inputs.
- `gates/test_boundary.py` — manifest-row pattern already used by prior
  phase-2 deliveries (per the issue's third acceptance check); confirmed
  present as the file the ADR names for the required rows.

## What is missing (confirms the ADR's Decision section)

Nothing today compares `expected` (what a roster/ledger entry says the
dispatched session was asked to deliver) against `observed`
(`session_end_verdict` + PR existence + `board()` loop_state + git delta),
and nothing in `drive()` consumes such a comparison — `drive()` currently
consumes nothing at all. The ADR's `reconcile()` + CLI verb + `expects_pr`
roster field + `drive()` edit closes exactly this gap; no additional gap
was found during this survey.
