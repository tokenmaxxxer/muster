---
code_under_review:
  - spawn.py
  - gates/flows.py
  - test_spawn.py
  - test_flows.py
loop_state: landed
---

# Implementation record — issue #224

Phase 2, executing the approved proposal
(`docs/issue-224/proposals/query-watch-reliability.md`, approved via
issue-level comment `APPROVE issue-224/implementation`, single-account
mode, role-handoff contract v3, PR author and approver both
jjongkwann).

PR #255 (the phase-1 PR carrying this proposal) also carries 3 phase-2
feedback items from the requester, separate from the approval itself —
addressed in "What was done" items 3-5 below.

## What was done

1. `spawn.py::_issue_comments()` (~line 830): `gh api
   repos/<slug>/issues/<n>/comments` now also passes `--paginate
   --slurp`. `data` (a list of per-page lists) is flattened
   (`[c for page in data for c in page]`) before the existing
   login/body dict conversion, so comments past #30 are no longer
   silently invisible to the approval gate (`approve_scope`), the
   phase-2 approval check (`gates/flows.py::_pr_approved`), and the
   respawn-cap idempotency check (`_post_crash_comment`) — all 3 share
   this function unchanged.
2. `gates/flows.py::_pr_list_all()` (~line 45): added `--limit`,
   `"1000"` after the `--json` argument, in the same position as the
   sibling `_issue_list_all()`'s existing idiom — open PRs past #30 no
   longer silently drop off the `flows` status board.
3. `spawn.py::_watch()` (~line 1789) — feedback 1 (session-end-drain
   ordering) and feedback 2 (exit code) both land here:
   - The role-unspecified multi-match branch now keeps its resolved
     workspace-index key (`matches[0][0]`) in a local `key` variable
     instead of discarding it, so the `--follow` loop can look the same
     subject/role back up in the roster.
   - New module constant `WATCH_CRASH_RC = 2` (decision recorded at
     `docs/issue-224/decisions/watch-crash-exit-code.md` — feedback 2).
   - In the `--follow` loop, on every iteration where `_await_bounded`
     did not just consume a `session-end` event, the loop now first
     scans `events.jsonl` past the current offset for an
     already-arrived-but-unconsumed `session-end` — if found, `continue`
     and let the next iteration's normal event-consumption path pick it
     up. Only when no such pending `session-end` exists does it look up
     the resolved key in the roster and check liveness. This mirrors
     `session_end_verdict()`'s (spawn.py:1191-1236) ordering, per PR
     #255 feedback 1: a normal exit that already wrote `session-end`
     must never be misjudged as a crash just because the offset hasn't
     caught up to it yet.
   - The liveness check reads `roster_entry.get("wrapper_pid")`, a new
     roster field (see item 4 and "Rationale for deviations" below), not
     `roster_entry.get("pid")`. Missing entry, missing `wrapper_pid`, or
     a dead `wrapper_pid` all return `WATCH_CRASH_RC` with a stderr
     explanation.
4. `spawn.py::_spawn_one()`'s `roster_register()` call (~line 2760)
   gains one new field, `"wrapper_pid": os.getpid()` — see "Rationale
   for deviations". `"pid"` (the `claude` subprocess's pid, used
   unchanged by `roster_kill()` as its SIGTERM target and by
   `flows_payload()`'s existing session-liveness display) is untouched.
5. Tests (feedback 3 — test file placement — resolved in items b and c
   below):
   a. `test_spawn.py::IssueComments` (new class, 2 tests): mocks
      `subprocess.run` to return a 2-page `--paginate --slurp` shape
      (`[[...], [...]]`) and asserts the flattened dict list plus
      `--paginate`/`--slurp` in the constructed command; a second test
      covers the real zero-comments shape (`[[]]` → `[]`).
   b. `test_flows.py::PrListAllLimit` (new class, 1 test) — **not**
      `test_spawn.py::FlowsPayload`. Neither existing file had a direct
      unit test of `_pr_list_all`'s own `subprocess.run` call (both
      `FlowsStageMapping` in `test_flows.py` and `FlowsPayload` in
      `test_spawn.py` only ever mock `_pr_list_all` away as a dependency
      stub for higher-level `flows_payload()` tests). `test_flows.py`
      already establishes the convention of testing `gates/flows.py`
      functions directly and in isolation (the bare `t_stage_for_*`
      functions test `flows._stage_for` directly); a direct test of
      `flows._pr_list_all`'s own command construction fits that existing
      convention, not the integration-style `FlowsPayload` class.
   c. `test_spawn.py::WatchFollow`: `setUp` now also registers a live
      roster entry (`wrapper_pid: os.getpid()`) for
      `issue-180/implementation`, so the pre-existing regression
      `test_follow_ignores_stall_and_keeps_going` and the other two
      pre-existing tests stay anchored to "alive," not to an
      accidentally-always-true drain-check shortcut. 4 new tests:
      `test_follow_detects_dead_session_and_returns_crash_rc` (no
      roster entry + perpetual stall + no `session-end` anywhere →
      finite-iteration `WATCH_CRASH_RC`, not an infinite loop),
      `test_follow_prioritizes_pending_session_end_over_pid_check` (dead
      pid but an unconsumed `session-end` already on disk → drains it,
      returns 0, never reaches the crash branch), and
      `test_follow_tolerates_post_processing_tail_before_session_end`
      (the hunt-discovered regression test — see below).

Verification: `python3 -m unittest test_spawn -q` — 184 tests, 41
errors, identical count and identical failing test names to this
sandbox's pre-existing `rulebook_checkout()` git-template-copy failure
(same baseline issue-223's record documented; unrelated to this
change). `python3 -m pytest test_flows.py -q` — 10 passed. All new
tests pass; `test_follow_ignores_stall_and_keeps_going` and the other 2
pre-existing `WatchFollow`/`FlowsPayload` tests still pass unchanged.

## Why

Executing the phase-1 proposal at
`docs/issue-224/proposals/query-watch-reliability.md`: three reliability
defects audited 2026-08-03 — unpaginated `_issue_comments()` silently
misses APPROVE comments past #30 (shared by the approval gate),
unlimited `gates/flows.py::_pr_list_all()` silently drops PRs past #30
from the status board, and `spawn.py::_watch()`'s `--follow` branch has
no session-death signal and can block forever on a crashed session.

## Upstream basis

`docs/issue-224/proposals/query-watch-reliability.md`, approved via
issue #224's `APPROVE issue-224/implementation` comment. PR #255's 3
feedback items (quoted in the phase-1 PR body) are folded in above; none
of them changed the proposal's frozen file-level write set
(`spawn.py`, `gates/flows.py`, `test_spawn.py`, `test_flows.py`).

## What did not work

- First cut of the `--follow` pid-death check (matching the proposal's
  literal wording) read `roster_entry.get("pid")` — the same field
  `roster_kill()` and `flows_payload()` already use for liveness.
  Expected: reusing this existing, already-registered signal would be
  accurate, as the proposal's Rationale (rejecting the outer-timeout
  alternative) asserted. Actual: an adversarial hunt (see below) found
  and reproduced a real false-positive — `_spawn_one()`'s `roster_key`
  entry's `pid` is the `claude` subprocess's pid, which `proc.wait()`
  legitimately reaps *before* the wrapping function's post-processing
  tail (`ensure_pushed()`'s real `git push`/`gh` calls, `gate_report`,
  `ownership_report`, `classify`, `ledger_write`) finishes and appends
  `session-end`. A `--follow` caller using a short `--stall-timeout`
  (exactly what this issue's fast-crash-detection goal invites) could
  have its check land inside that legitimate tail window, see a dead
  `pid` and no pending `session-end`, and report a crash for a session
  that was completing normally. Reproduced live (unmocked `_watch`/
  `_append_event`/`roster_remove`, a background thread simulating the
  real tail ordering with a short stall timeout) before writing the
  fix. Replaced with a second, dedicated `wrapper_pid` roster field (see
  "Rationale for deviations") that stays alive for the whole
  `_spawn_one()` invocation, not just the inner subprocess.

## Open findings

From the adversarial hunt, 2 findings are real but out of this issue's
frozen write set or an accepted, precedent-consistent risk class:

1. The new drain-check's `json.loads(line)` over `lines[after:]` is
   unguarded (no `try/except ValueError`), same as the pre-existing,
   immediately adjacent `json.loads(lines[after - 1])` in `_watch()`'s
   existing session-end match. The phase-1 proposal's Rationale
   (alternative 5) already scoped unguarded `events.jsonl` parsing as a
   separate, out-of-scope failure family requiring its own
   corrupted-line policy decision — this is the same family, not a new
   one this change introduces.
2. `_roster_load()` has no read-lock (only `_roster_locked()`-guarded
   writes do); a concurrent `roster_register`/`roster_remove` could in
   principle produce a torn read that its `except (OSError, ValueError):
   return {}` silently turns into "roster empty." This is the same
   accepted risk class as this repo's existing `_alive()`/pid-reuse
   tolerance (see issue-223's own Open findings item 2) — pre-existing,
   just polled more frequently now by `--follow`. Fixing it is a
   `workspaces.json`-style locking design decision the phase-1 proposal
   explicitly scoped out (Rationale alternative 5, `_workspace_index_put`
   locking).

Resolution path: both are candidates for a follow-up issue if the
`--roster` read path or `events.jsonl` parsing ever need a shared
hardening pass — not fixed here, since fixing either requires a design
decision (corrupted-line policy; a new locking scheme) outside this
issue's write set.

## Doc-placement ladder

- No new env var / config key / dependency / migration / setup step
  introduced -> N/A.
- Exit-code value (`WATCH_CRASH_RC = 2`) is a changed public contract
  (the CLI's process exit code on `--follow`) -> recorded at
  `docs/issue-224/decisions/watch-crash-exit-code.md` (PR #255 feedback
  2).
- Test file placement for the new `_pr_list_all --limit` test
  (`test_flows.py::PrListAllLimit`, not `test_spawn.py::FlowsPayload`)
  -> recorded in "What was done" item 5b above (PR #255 feedback 3) —
  an internal test-organization choice, not a library/format decision,
  so no separate `docs/issue-224/decisions/` entry.
- No benchmark/investigation numbers produced in phase 2 -> no
  additional `docs/issue-224/reports/` entry beyond this record and the
  existing phase-1 survey/scout-brief.

## Hunt

Stance: **assume-incomplete-coverage** (rotated — the immediately prior
implementation session, issue-223, used adversarial-self; rotating away
from repeating the same stance twice in a row). No registered
`warrant-hunter` subagent type is available in this harness (same gap
noted in issue-216/218/220/221/223/232/235/236's records), so
`general-purpose` was dispatched in its place with an explicit
assume-incomplete-coverage brief (assume the new tests pass for the
wrong reason or miss the real failure mode, rather than trusting that
green tests mean the fix works). Dispatched foreground (synchronous)
against the uncommitted diff before delivery, with instructions to
actually run the tests and, where useful, reproduce against the real
(unmocked) functions rather than trusting the diff's own reasoning.

Findings:

1. **CONFIRMED, fixed.** The post-processing-tail false-positive
   described in "What did not work" above — `roster["pid"]` (claude
   subprocess) legitimately dies before `session-end` is appended.
   Fixed by adding a dedicated `wrapper_pid` roster field tracking the
   `_spawn_one()` invocation itself (fork-child in the bounded+issue
   path), and switching `_watch()`'s liveness check to read it instead
   of `pid`. New regression test
   `test_follow_tolerates_post_processing_tail_before_session_end`
   added; full suite re-run after the fix shows the same 41
   pre-existing environment errors, no new failures, all new tests
   pass.
2. **PLAUSIBLE, out-of-scope, accepted.** Unguarded `json.loads` in the
   new drain-check — see Open findings item 1.
3. **PLAUSIBLE, out-of-scope, accepted risk.** `_roster_load()` has no
   read-lock — see Open findings item 2.
4. **Checked, no bug.** `_issue_comments`'s flatten assumption
   (`--paginate --slurp` → list-of-lists) verified against real,
   multi-page `gh api` output on an external repo.
5. **Checked, no bug.** `_pr_list_all`'s `--limit 1000` +
   `isinstance(data, list)` verified against a real repo with 55+ open
   PRs — flat list, no interaction issue.
6. **Checked, no bug.** The no-`--role` multi-match `key` resolution is
   correctly ordered before any use; `key` is never `None` by the time
   the follow loop's roster check runs (the `entry is None` early-return
   already covers that case).
7. **Checked, no bug.** A burst of multiple events arriving between
   polls is handled correctly — the drain-check scans the *entire*
   unconsumed tail (`any(... for line in lines[after:])`), not just the
   very next line.
8. **Checked, accepted, pre-existing.** A transient `gh api` rate-limit
   mid-pagination still silently reports "no comments" (existing
   `returncode != 0` fallback, unchanged) — now potentially hit across N
   sequential paginated requests instead of 1. Same accepted fallback
   behavior the proposal's Rationale already chose over failing loudly;
   modestly wider surface, not a new failure mode.

Disposition: finding 1 fixed in this session (in-scope, same file,
additive roster field, no consumer's existing contract changed).
Findings 2-3 are real but out-of-scope/accepted risks, recorded above as
follow-up candidates. Findings 4-8 found nothing further to fix.

## Rationale for deviations

One deviation from `## What will be done`, driven by the mandatory
phase-2 hunt rather than a scope-exceeded stop: the proposal's item 3
described the `--follow` pid check as reusing the existing roster `pid`
field verbatim ("로스터에서 같은 키의 현재 pid 를 다시 조회해
`_alive(pid)`를 확인"). Building it exactly that way and then hunting it
(per the mandatory pre-completion hunt cadence) surfaced a real false-
positive: that `pid` is the `claude` subprocess's pid, which dies before
`_spawn_one()`'s post-processing tail finishes and appends
`session-end` — the crash check would fire during a legitimate
in-progress window. Fixed by adding one new, purely additive roster
field (`wrapper_pid`, set to `os.getpid()` at the same
`roster_register()` call site) that stays alive for the whole
`_spawn_one()` invocation, and pointing the liveness check at it instead
of `pid`. This stays inside the same frozen file (`spawn.py`) and
touches no other consumer's existing contract: `roster_kill()` and
`flows_payload()`'s session-liveness display keep reading `pid`
unchanged — only `_watch()`'s new check reads the new field. No
change to `_watch()`'s or `_await_bounded()`'s signature, return type,
or the issue-#180-protected "one event or stall" contract.
