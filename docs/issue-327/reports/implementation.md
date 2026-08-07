---
code_under_review:
  - spawn.py
  - test_spawn.py
  - docs/issue-327/decisions/watchdog-exit-code.md
loop_state: done
subject: issue-327
---

# Implementation record — issue #327

Phase 2 of the approved proposal
(`docs/issue-327/proposals/2026-08-07-idle-deadlock-watchdog-exit-code.md`).
Approval: `APPROVE issue-327/implementation` (issue #327 comment), with
binding conditional feedback attached to the same comment — see
"Feedback applied" below.

## What was done

- `spawn.py:1542` `roster_watchdog()`: replaced the unconditional `return 0`
  with `return anomaly_count`, where `anomaly_count` is the number of live
  roster entries for which `watchdog_check_one` returned at least one
  anomaly. `0` on a clean scan (unchanged from before), non-zero otherwise.
  `auto_respawn=True`'s crashed-only respawn/cap-comment side effects and
  all printed output are unchanged — only the return value changed.
- `spawn.py watchdog`'s CLI dispatch (`spawn.py:2445`,
  `return roster_watchdog(auto_respawn=a.auto_respawn)`) already passed the
  function's return value straight through as the process exit code, so no
  change was needed there — the exit-code behavior falls out of the
  `roster_watchdog()` change alone.
- `test_spawn.py`, class `Watchdog`: added
  `test_roster_watchdog_returns_zero_for_clean_non_empty_roster` (a
  non-empty, anomaly-free roster still returns `0`) and
  `test_roster_watchdog_returns_anomaly_count_for_stalled_entry` (a roster
  entry with a stale log — the existing `log-silence` signal — returns
  `1`). `Watchdog._entry()` gained a `pid` kwarg so these tests can build
  entries that pass `roster_watchdog()`'s `_alive()` liveness check using
  the test process's own pid.
- `docs/issue-327/decisions/watchdog-exit-code.md`: recorded the changed
  public signature (`roster_watchdog()`'s return value now carries
  meaning), per the doctrine ladder.

## Feedback applied

The conditional-approval comment corrected the proposal's cited roster
file name (`runs/roster.json`, which does not exist) to the actual
constant, `ROSTER = ROOT / "runs" / "active.json"` (`spawn.py:1378`).
Phase 2 code and tests reference `spawn.ROSTER`/`active.json` by the
constant/its real name throughout — no hardcoded `roster.json` path was
introduced anywhere in this change.

## What reaches beyond this issue's own acceptance criteria (per #330)

`roster_watchdog()`'s return value is a public signature whose meaning
changed for every caller, not only the `watchdog` CLI subcommand this
issue targets. A repo-wide grep
(`grep -rn "roster_watchdog(" --include="*.py" --include="*.sh" .`) at
write time found exactly one other call site (`spawn.py:2445`, the CLI
dispatch itself, already covered by this change) plus the test suite's
own calls; no other caller exists today, but any future caller relying
on the old always-`0` return would see different behavior. Recorded in
`docs/issue-327/decisions/watchdog-exit-code.md`.

## What did not work

None.

## Rationale for deviations

None — phase 2 implemented `## What will be done` from the approved
proposal without deviation, and applied the binding feedback (file-name
correction) as instructed rather than as a scope change.

## Verification run

`python3 test_spawn.py` — full suite, 235 tests, `OK` (ran in this
session; output confirmed, not narrated). `python3 test_spawn.py
Watchdog` — 13 tests, `OK`, including both new cases:
`test_roster_watchdog_returns_zero_for_clean_non_empty_roster` (clean
non-empty roster returns `0`) and
`test_roster_watchdog_returns_anomaly_count_for_stalled_entry` (stale-log
roster returns `1`). Reverting the `return 0` -> `return anomaly_count`
change makes the second of these fail, which is the executable
regression artifact the proposal's "How you'll know it worked" names.

A direct exit-code check of `spawn.py watchdog` against a live temp
roster (rather than the unittest harness) was attempted for extra
confirmation but was blocked by this session's shell sandbox (heredoc
containing a brace+quote pattern was rejected as "expansion
obfuscation"); the unittest-level check above exercises the same
`roster_watchdog()` return path that the CLI passes through unmodified
at `spawn.py:2445`, so it is not a gap in what was confirmed, only in
which harness ran it.

## Closed checks

- `roster_watchdog return value` — verified via
  `test_roster_watchdog_returns_zero_for_clean_non_empty_roster` and
  `test_roster_watchdog_returns_anomaly_count_for_stalled_entry`,
  code_under_review as listed above.
- `single call site for changed signature` — verified via
  `grep -rn "roster_watchdog(" --include="*.py" --include="*.sh" .`,
  one call site (`spawn.py:2445`) outside test files.

## Open findings

None.

## Hunt

No hunter dispatch this session — headless/single-shot (contract v3
s22): a background hunter dispatch whose result is not consumed within
the same turn is prohibited in this mode, and no earlier turn in this
session dispatched one that could be awaited here.
