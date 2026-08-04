---
kind: coding-record
code_under_review: spawn.py, test_spawn.py, docs/issue-266/decisions/watch-crash-trigger-wording-amendment.md
loop_state: landed
closed_checks:
  - check: "python3 -m unittest test_spawn.WatchFollow -v — 9/9 pass, no
      hangs (0.018s)."
    ref: test_spawn.py:3399
  - check: "red proof: new test run against unfixed spawn.py:1903 —
      AssertionError: 2 != 0 (WATCH_CRASH_RC returned instead of 0)."
    ref: test_spawn.py:3593
  - check: "green proof: same test re-run after the spawn.py:1903 fix —
      passes."
    ref: test_spawn.py:3593
  - check: "full test_spawn.py suite (197 discovered under the affected
      run) — 53 pre-existing ERRORs, all in ProgressEvents/EventReporting/
      IssueScopedPrompt/Ledger classes (rulebook_checkout git-clone
      failure, sandboxed network), reproduced identically with this
      diff stashed out. Zero errors/failures in WatchFollow."
    ref: spawn.py:209
  - check: "warrant-hunter dispatch (general-purpose, stance:
      composition-regression, rotated from issue-246's adversarial-self)
      — no blocking findings; one non-blocking observation matching the
      already-recorded deviation below."
    ref: spawn.py:1903
---

# Implementation record — issue #266

## Why

Phase 2, executing the approved proposal
(`docs/issue-266/proposals/roster-lifetime-vs-absence-signal.md`, upstream
basis), approved via issue-level comment `APPROVE issue-266/implementation`
(single-account mode, role-handoff contract v3, PR author and approver
both jjongkwann). `_watch()`'s post-processing tail misreports a
normally-completing session as crashed: `_spawn_one()` calls
`roster_remove(roster_key)` (spawn.py:2995) immediately after the claude
subprocess exits, but the `session-end` event isn't written until after
`ensure_pushed`/gate-and-ownership reports/`classify`/`ledger_write`
(spawn.py:3097) — during that whole window `_watch()`'s death check saw
`roster_entry is None` and returned `WATCH_CRASH_RC` for a session that
was still progressing normally.

## What was done

Delivered alternative (b) from the approved proposal: dropped
`roster_entry is None` as a death signal, entirely within `_watch()`'s
own death-determination.

1. **`spawn.py:1903`** (death-determination inside the `--follow` loop):
   narrowed `if roster_entry is None or not pid or not _alive(pid):` to
   `if pid is not None and not _alive(pid):`. An absent roster entry, or
   an entry present with no `wrapper_pid` field, no longer returns
   `WATCH_CRASH_RC` — it falls through to the existing stall loop and is
   covered by `stall_timeout_min`. Only "entry exists and its
   `wrapper_pid` is dead" still crashes.
2. **`test_spawn.py::WatchFollow`**: added
   `test_follow_tolerates_roster_entry_fully_absent_before_session_end`
   (entry fully absent via `roster_remove`, then a fake `_await_bounded`
   stalls twice before appending `session-end`) — proved red against the
   unfixed condition (`AssertionError: 2 != 0`, i.e. `WATCH_CRASH_RC`
   returned) and green after the fix (`rc == 0`), per the proposal's
   requirement 2.
3. Explicitly re-ran the full `WatchFollow` class (9 tests, all pass, no
   hang) confirming no regression — see "Rationale for deviations" for
   why the pre-existing `test_follow_detects_dead_session_and_returns_crash_rc`
   required rewriting, not just re-running unchanged.
4. Documented the corrected `WATCH_CRASH_RC` trigger wording — see
   "Rationale for deviations": the proposal's literal target file
   (`docs/issue-224/decisions/watch-crash-exit-code.md`) could not be
   edited from this branch, so the correction landed at
   `docs/issue-266/decisions/watch-crash-trigger-wording-amendment.md`
   instead.

## What did not work

- Ran `python3 -m unittest test_spawn.WatchFollow -v` (no `timeout`)
  immediately after applying the spawn.py fix and before rewriting the
  pre-existing dead-session test — expected all 9 tests to complete;
  actual: the run never returned within 210s+ and had to be killed
  (`TaskStop`). Isolated to
  `test_follow_detects_dead_session_and_returns_crash_rc` with
  `timeout 10`: it hung too. Root cause (see "Rationale for deviations"):
  that pre-existing test constructed "roster entry entirely absent," the
  exact scenario the fix now treats as non-crash, so its mocked
  `_await_bounded` (which never introduces a real stall timeout or
  `session-end`) spun the `--follow` loop forever. Fixed by rewriting the
  test to construct the scenario it was actually meant to protect (entry
  present, `wrapper_pid` dead) instead of re-running it unchanged.
- Attempted `Edit` on `docs/issue-224/decisions/watch-crash-exit-code.md`
  (per the approved proposal's item 4) — expected the edit to land;
  actual: `board-gate.sh` R4 refused it (writing `docs/issue-224/...`
  requires branch `issue-224/implementation`; this session is
  `issue-266/implementation`). Redirected per "Rationale for deviations"
  below.

## Rationale for deviations

Two deviations from the approved proposal's literal "What will be done,"
both discovered only at execution time (survey/proposal review did not
surface either):

1. **Proposal item 3** described the existing
   `test_follow_detects_dead_session_and_returns_crash_rc` as covering
   "entry exists and `wrapper_pid` is `_alive`-false," expecting it to
   "pass unchanged, no regression." Reading its actual body at execution
   time showed it instead called `spawn.roster_remove(...)` — constructing
   "roster entry entirely absent," which is precisely the scenario
   alternative (b) redefines as *not* a crash signal. Left unchanged, the
   fix makes this test's own mocked `_await_bounded` loop forever (no
   real stall timeout exists in the mock, and no `session-end` ever
   arrives) — confirmed by hanging it and killing the run (see "What did
   not work"). Swapped: rewrote the test to construct the scenario it was
   actually meant to represent — a live roster entry whose `wrapper_pid`
   points at a real, confirmed-dead process
   (`subprocess.Popen(["true"]); dead.wait()`, the same idiom already
   used at `test_stale_claim_from_dead_pid_is_cleaned_and_retried`,
   test_spawn.py:2723) — which is the one condition alternative (b)
   keeps as a live trigger. This stays inside the frozen write set
   (`test_spawn.py` was already in `files:`) and is required for the
   approved design to be internally consistent: two tests cannot both be
   correct if one asserts "entry absent ⇒ crash" and the other asserts
   "entry absent ⇒ not crash." Confirmed by the composition-regression
   hunt (closed_checks) that the rewritten test still exercises a
   genuinely distinct branch from the newly-added regression test, not a
   duplicate.
2. **Proposal item 4** called for editing
   `docs/issue-224/decisions/watch-crash-exit-code.md` directly. That
   write is mechanically blocked by this repository's `board-gate.sh` R4
   (contract v3 s10): a role session writes `docs/issue-<n>/` only from
   branch `issue-<n>/<role>`; this session is `issue-266/implementation`
   and has no access to `issue-224/implementation`. Swapped: the
   corrected trigger wording is fully specified at
   `docs/issue-266/decisions/watch-crash-trigger-wording-amendment.md`
   instead, with an explicit note that a small follow-up (a session on
   `issue-224/implementation`, or the human directly) still needs to
   paste the corrected paragraph into
   `docs/issue-224/decisions/watch-crash-exit-code.md:25-26`. This
   preserves the proposal's intent (an accurate, reachable record of the
   new trigger condition) without bypassing the branch-ownership gate.

## Doc-placement ladder

- No new env var / config key / dependency / migration / setup step ->
  N/A, none introduced.
- Changed public signature/wire format: none — `_watch()`'s signature and
  return-value contract (`0`/`1`/`WATCH_CRASH_RC = 2`) are unchanged, only
  the internal condition that decides which return value fires narrowed.
  A named-alternative choice *was* made (proposal's alternative (b) over
  (a), already recorded in
  `docs/issue-266/proposals/roster-lifetime-vs-absence-signal.md`'s
  Rationale) -> no *new* decision doc needed for that choice itself; the
  only new decision recorded in phase 2 is the trigger-wording amendment
  above (`docs/issue-266/decisions/watch-crash-trigger-wording-amendment.md`),
  written because the proposal's own target file was unreachable from
  this branch (see "Rationale for deviations" item 2).
- No benchmark/investigation numbers produced in phase 2 beyond the test
  run counts already cited in `closed_checks` -> no additional
  `docs/issue-266/reports/` entry beyond this record and the existing
  phase-1 `docs/issue-266/reports/implementation/{survey,scout-brief}.md`.

## Hunt

Stance: **composition-regression** (rotated — the immediately prior
`implementation`-role hunt, issue-246, used adversarial-self; no
registered `warrant-hunter` subagent type is available in this session,
so `general-purpose` was dispatched in its place with an explicit
adversarial framing, matching the issue-216/218/220/222/232/236
precedent). Dispatched in the foreground against the uncommitted diff
before delivery (headless single-shot session — contract v3 s22 requires
consuming the result within the same turn, never backgrounding it past
turn end).

Findings: none blocking. The hunter independently verified:

1. The three other roster-mutating/reading call sites
   (`roster_kill` spawn.py:1914, `roster_ps` spawn.py:1338,
   `flows_payload` gates/flows.py:357) iterate only entries that
   physically exist — none of them special-case key-absence as a death
   signal, so the new "absence = unknown, not death" semantics introduce
   no inconsistency with them (matches the proposal's Rationale, which
   is exactly why alternative (b) was adopted over (a)).
2. The `subprocess.Popen(["true"]); dead.wait()` dead-pid idiom in the
   rewritten test is byte-for-byte the same as the pre-existing
   `test_stale_claim_from_dead_pid_is_cleaned_and_retried` precedent
   (test_spawn.py:2723) — same theoretical PID-reuse exposure, not a new
   risk this diff introduces.
3. The new and the rewritten-pre-existing test exercise genuinely
   distinct branches of the narrowed condition (`pid is None` vs.
   `pid is not None and not _alive(pid)`) — confirmed not redundant.
4. Re-read the fixed condition directly (not just diffed) and confirmed
   both non-crash cases hold: entry+alive `wrapper_pid` → no crash;
   entry present but no `wrapper_pid` field → no crash, waits.
5. Independently re-ran `test_spawn.WatchFollow` with a hard `timeout`
   — 9/9 pass, no hang — and `test_flows.py` — 3/3 pass, unaffected.
6. One non-blocking observation: `docs/issue-224/decisions/watch-crash-exit-code.md:25-26`
   is now stale — already the known, explicitly-recorded deviation above,
   not a silent gap.

## Verification run

- `python3 -m unittest test_spawn.WatchFollow.test_follow_tolerates_roster_entry_fully_absent_before_session_end -v` against unfixed `spawn.py:1903` — **red**: `AssertionError: 2 != 0`.
- Applied the `spawn.py:1903` fix.
- `timeout 30 python3 -m unittest test_spawn.WatchFollow -v` — **green**: 9/9 pass in 0.018s (includes the rewritten `test_follow_detects_dead_session_and_returns_crash_rc`, no regression).
- `timeout 120 python3 -m unittest test_spawn -v` (full suite) — 53 pre-existing ERRORs, all outside `WatchFollow`, all reproduced identically with this diff stashed out (`git stash` / `git stash pop`) — confirmed pre-existing and environmental (sandboxed network blocks `rulebook_checkout`'s git clone), not a regression from this change.

## Open findings

None. The one hunt observation (stale `docs/issue-224/` wording) is
already a recorded, tracked deviation, not an unresolved finding.

## Next steps

A small follow-up (out of this session's reach, not out of scope for the
work itself): a session running on branch `issue-224/implementation` (or
the human directly) should paste the corrected paragraph from
`docs/issue-266/decisions/watch-crash-trigger-wording-amendment.md` into
`docs/issue-224/decisions/watch-crash-exit-code.md:25-26`, replacing the
now-stale "or its roster entry is gone" wording.

## Open-finding resolution path

N/A — no open findings.
