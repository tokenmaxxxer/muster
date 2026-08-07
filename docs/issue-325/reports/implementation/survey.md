# issue-325 current-state survey

## Scope of the complaint

Two symptoms, one mechanism (operator's words): an issue's forward motion depends
entirely on the orchestrator remembering to move it.
1. An issue is filed on GitHub and no session is ever spawned for it.
2. A session runs, but the watch/monitoring loop fails to detect completion/stall,
   and everything sits waiting with no signal that anything is wrong.

Both degrade as parallel issue count grows, because the thing supposed to notice is
the orchestrating LLM's own turn loop, and its context budget is the scarce resource
that fails first.

## What exists today

- `spawn.py` is a manual, per-invocation CLI (`def main()` at spawn.py:2399). There is
  no listener, webhook, or scheduler that turns a filed GitHub issue into a spawn call.
- `spawn.board(root)` (spawn.py:1084) derives all state from `docs/issue-<n>/reports/*.md`
  files already present on the local filesystem. It never queries GitHub for open
  issues. Consequence: an issue that was filed but never spawned has **no board entry**
  and is invisible to every board-driven tool in the repo (spawn.py itself,
  `gates/closure_sweep.py`). There is currently no code path anywhere in the repo that
  can even observe symptom 1, let alone fail on it.
- `spawn.py watchdog` / `roster_watchdog()` (spawn.py:1542) is observe-only for *live*
  roster entries: `watchdog_check_one()` (spawn.py:1472) detects log silence
  (`WATCHDOG_SILENCE_MIN` = 90 min), background-delegation phrasing, ≥3 denied tool
  calls, or no commits past `WATCHDOG_NO_COMMIT_MIN` (71 min) — and only **prints**
  them (spawn.py:1550 docstring: "stalled 는 여전히 보고만 한다").
- For *dead* roster entries, `--auto-respawn` runs `_auto_respawn_check()`
  (spawn.py:1841) against `session_end_verdict()`'s three-way split (spawn.py:1294):
  `normal` / `crashed` / `stalled` / `in-progress`. Only `crashed` triggers
  `_respawn_or_cap()` (spawn.py:1778), which respawns up to a cap then posts a
  giving-up GitHub comment (`_CRASH_COMMENT_MARKER`). `stalled` is explicitly never
  auto-respawned or posted anywhere — it is a `print()` line in whatever terminal
  happens to be running `watchdog` at that moment.
- Nothing re-invokes `watchdog` on its own. `roster_watchdog()`'s docstring says it is
  meant to be called "오케스트레이터가 10-15분 간격으로 반복 호출한다" (spawn.py:1545) —
  i.e. by convention, the orchestrating Claude session is expected to remember to
  re-run it inside its own turn loop. This is exactly symptom 2's mechanism.
- `gates/closure_sweep.py` only checks issue↔PR closure *consistency* for subjects
  already on the board (`find_violations()` walks `spawn.board(root)`,
  closure_sweep.py:83) — it cannot see an issue that never got a board entry, and it
  is a one-shot command not wired into any watchdog tick (spawn.py:2444: "watchdog
  틱에 자동으로 안 물린다").
- No gate anywhere in `gates/` (`ci.py`, `pr_reference.py`, `flows.py`,
  `closure_sweep.py`) currently detects either failure mode named in #325.

## Rejected alternatives already on record

`docs/decisions/2026-07-29-permanently-closed-alternatives.md`:
- **Cloud cron — rejected**: Anthropic-cloud execution cannot reach keychain auth or
  the local Seatbelt sandbox the driver needs (source cited:
  `docs/superpowers/specs/2026-07-27-orchestrator-v2-design.md:155-158`, not present
  in this repo — external spec).
- **A model as scheduler — rejected**: "the driver must be deterministic muster code,
  not a model and not the cloud... an LLM must not be the scheduler" (same source).

`protocol.md:278` lists "what calls on-the-record — a person, cron, or an issue
webhook" under §8 Unsettled and states "no long-running process is being built" for
the current stage. So an always-on daemon/poller is out of bounds for this issue —
consistent with the two rejections above — and re-opening that question is not this
issue's job.

## Boundary with named sibling issues

- **#298** ("the orchestrator is the only unenforced actor... 9 gates constrain role
  sessions, exactly 1 constrains the orchestrator") is about gating the
  orchestrator's *approve/merge* actions (reading proposals before relaying approval,
  checking PR status before merge). It does not touch spawn coverage or watch/stall
  detection. No overlap with #325's write set.
- **#288** ("spawn.py CLI tells the truth about failures but lies about what it did")
  is a set of 8 CLI-flag correctness bugs (`clean --issue` scoping, `--dry-run`
  validation, issue-number validation, etc.). None of its 8 items concern GitHub-issue
  coverage or stall escalation. #325's own text describes #288 as "watch reports a
  deleted log as a stall," which does not match the actual filed #288 body — treating
  that as a loose paraphrase from the operator's original 15-item list, not a
  contradiction to resolve here. No overlap with #325's write set.
- Neither #298 nor #288 has a `docs/issue-<n>/` tree yet (unspawned as of this
  survey) — itself a live instance of #325's own complaint.

## What #310 requires here

#310: acceptance must name an executable artifact that fails on regression; a
promise, memory note, or doc sentence does not discharge the requirement. Given cron
and LLM-as-scheduler are both already closed alternatives, the fix cannot be "run
something continuously" — it must be a deterministic, git-committed check that some
already-existing trigger (a human running it, or wiring it into the existing
`gates/ci.py` entry point the same way `closure-sweep` already sits beside it) can
execute and that fails loudly (non-zero exit, and/or a posted comment analogous to
`_CRASH_COMMENT_MARKER`) when either symptom is present.

## Write set this survey supports

- `gates/spawn_coverage.py` (new) — pure-function violation detection (mirrors
  `closure_sweep.find_violations`'s injectable, network-free design) plus a `main()`
  CLI entry, for symptom 1 (issue filed, no board entry).
- `spawn.py` — extend `_auto_respawn_check`/the stalled branch so a `stalled` verdict
  that has been reported before (i.e. persists past a tick) posts a GitHub comment
  once (new marker constant, same read-then-check pattern as `_CRASH_COMMENT_MARKER`
  and `closure_sweep._SWEEP_COMMENT_MARKER`), for symptom 2 (stall never surfaces
  anywhere but stdout).
- `test_gates.py` and/or `test_spawn.py` — network-free tests pinning both behaviors.
- `gates/ci.py` — wire `spawn_coverage` in alongside `closure_sweep`'s existing
  invocation pattern, if such wiring exists for closure_sweep (needs confirming at
  build time; if closure_sweep is not itself wired into `ci.py`'s `check()`, match
  that same standalone-script precedent instead of inventing new wiring).
