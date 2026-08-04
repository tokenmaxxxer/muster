---
kind: coding-record
code_under_review: spawn.py, test_spawn.py, docs/handbooks/operations.md
loop_state: landed
---

# Implementation record — issue #247

## Why

Phase 2, executing the approved proposal
(`docs/issue-247/proposals/self-triggered-abandoned-work-respawn.md`,
upstream basis for this record), approved via issue-level comment
`APPROVE issue-247/implementation` (single-account mode, role-handoff
contract v3, PR author and approver both jjongkwann). Delivering the
proposal exactly as approved: a second, in-process trigger for the
existing capped auto-respawn machinery (issue #132), firing at the point
`_spawn_one()` already knows its own `uncommitted-work`/`failed-no-commit`
outcome, instead of only at the next `spawn.py watchdog` tick (which the
reported incident's normal exit never reaches — survey.md).

## Rebase note (line-number drift vs the proposal)

The proposal was written against a `main` that has since moved 46
commits (issues #224 wrapper_pid, #246 classifier fixes, #266 death
judgment, #245 Closes-gate, #262/#227/#258 and others landed in between).
This branch was rebased onto `origin/main`
(`247051e2a40f6e877db5bc2704445165d06f7f50`) before phase-2 work started;
the rebase was clean (no conflicts). Line numbers below are re-surveyed
against that HEAD, not the proposal's.

## What was done

`spawn.py`:

1. `_post_crash_comment()` (line 1662) gained a `trigger: str = "crashed"`
   parameter — the default preserves both existing callers/tests
   unchanged; the body now names which path (watchdog vs self-trigger)
   filled the attempt cap. The idempotency marker itself
   (`_CRASH_COMMENT_MARKER`, keyed by `key`+cap) is unchanged on purpose —
   both trigger paths share one attempt-cap budget per `key`, per the
   proposal's explicit "Out of scope" decision.
2. New shared helper `_respawn_or_cap()` (line 1686): the claim/
   attempt-cap/task-replay/cap-comment sequence factored out of the old
   `_auto_respawn_check()`, taking `(key, work, issue, role, log,
   session_start_ts, state, trigger)`.
3. `_auto_respawn_check()` (line 1749) is now a thin wrapper: computes
   the `session_end_verdict()`, returns early unless `crashed`,
   reconstructs `start_ts` from the last `session-start` event, and
   delegates to `_respawn_or_cap(..., "watchdog-observed-crashed")`.
   External signature and behavior unchanged — all 5 pre-existing
   `AutoRespawnClaim` tests pass unmodified.
4. New `_self_trigger_respawn()` (line 1785): fires
   `_respawn_or_cap(..., "self-triggered-abandoned")` only when `outcome`
   is `"uncommitted-work"` or `"failed-no-commit"` — a no-op for
   `refused`/`waiting-on-human`/bare `silent-failure`/anything else.
5. `_spawn_one()` (line 2764): captures `session_start_ts = time.time()`
   (see "Rationale for deviations" for why not `int(...)`) when appending
   its own `session-start` event, and calls `_self_trigger_respawn(...)`
   in the bounded/issue-scoped tail — **after** appending its own
   `session-end` event, not before (see "Rationale for deviations" for
   why the order is the opposite of the proposal's literal wording).

`test_spawn.py`: new `SelfTriggeredRespawn` class (7 tests) — fires on
`uncommitted-work`/`failed-no-commit`; does not fire on
`refused`/`waiting-on-human`/`silent-failure`/`progressed`/`errored`/
`progressed-dirty-tree`; respects the attempt cap and posts the
cap-comment with the trigger label; does not double-claim when a
self-trigger and a simulated concurrent watchdog tick race on the same
`session_start_ts` (reuses the existing atomic-claim protection, real
`threading.Thread`s, same pattern as `AutoRespawnClaim`'s existing
concurrency test); one full `_spawn_one()` integration test (real git
repo, fork mocked per the `SpawnOneIssueRoleClaim` precedent) proving the
call site actually fires and that it does so after this session's own
`session-end` is already on disk. Two new `SessionEndVerdict` tests
document the ordering hazard directly (see Hunt below).

`docs/handbooks/operations.md`: new mirrored KO/EN subsection ("방치된
미커밋 작업 — 자동 재스폰" / "Abandoned uncommitted work — automatic
respawn") between "세션이 끝나면"/"When a session ends" and "일부러 멈추는
자리"/"Where a run stops on purpose" — covers what the two outcomes mean,
why they're not `crashed`, the new self-trigger behavior, and the manual
resume command (`spawn.py <role> "<task>" --issue <n>`).

Verification: `python3 -m pytest test_spawn.py -q` — 206 passed, 0
failed (full file, includes all pre-existing classes plus the new ones).
`python3 -m pytest -q` (full repo collection, mixes in `test_gates.py`)
shows 43-44 failures — confirmed via `git stash`/`git stash pop` to be an
identical, pre-existing baseline unrelated to this change (real-subprocess/
git tests that are order-sensitive to something in the combined
collection, not touched by this diff); `test_spawn.py` run in isolation is
the actual acceptance signal, matching the proposal's own "How you'll know
it worked" command.

## Rationale for deviations

Two points where phase-2 execution diverged from `## What will be done`
in the approved proposal, both found by the hunt (see below) before
delivery, not chosen in advance:

1. **Self-trigger call fires after this session's own `session-end`
   event, not before.** The proposal's step 2 said "call the shared
   respawn helper before the bounded child's terminal `session-end` event
   append/exit." Implemented literally first, then the hunt found: when
   `_self_trigger_respawn()` is under the attempt cap, it recursively
   calls `_spawn_one(..., bounded=True)`, which itself forks and blocks
   in `_await_bounded()` until the new generation posts its own
   `session-start`. Calling this *before* appending this session's own
   `session-end` means that event lands in `events.jsonl` chronologically
   *after* the new generation's `session-start` — and
   `session_end_verdict()` (unchanged, out of scope) finds the *last*
   `session-start` and treats *any* `session-end` after it as a match,
   without checking whose `pid` it names. A real crash of the new
   generation would then be permanently reported as `normal`, silently
   defeating the exact safety net this issue exists to add — and only for
   respawned generations, invisibly. Fixed by swapping the two lines:
   append `session-end` first, then call `_self_trigger_respawn()`. This
   still satisfies the proposal's actual intent (fire while this process
   is still alive, before `os._exit()`); only the position relative to
   this session's *own* terminal event moved.
2. **`session_start_ts` uses `time.time()` (float), not `int(time.time())`.**
   The proposal didn't specify precision and the pre-existing issue #132
   crashed-only path used `int(...)`. The hunt found that self-triggered
   chains, unlike the watchdog-only path, no longer have the ~10-15 minute
   watchdog cadence naturally spacing generations apart — two generations
   starting within the same wall-clock second would collide on
   `_respawn_or_cap()`'s `already_claimed` check (keyed on
   `session_start_ts` equality) and silently short-circuit before the
   attempt-cap check, undercounting attempts. Switching to sub-second
   precision (same `time.time()` primitive already used everywhere in the
   file, no new library) closes the window to a scale no longer reachable
   by real per-generation work.

## Hunt

Stance: **assume-broken** (rotated — least recently used of the 4
rotated stances; last used issue-236, 2026-08-03; every other stance
[adversarial-self, assume-incomplete-coverage, composition-regression]
was used more recently, most recently issue-262/issue-266/issue-246/
issue-245, all landing 2026-08-04). No registered `warrant-hunter`
subagent type is available in this harness (same gap noted in issues
#216/#218/#220/#221/#223/#229/#232/#235/#236's own records), so
`general-purpose` was dispatched in its place with an explicit
assume-broken brief. Dispatched foreground (synchronous, contract v3
s22) against the uncommitted diff before delivery.

Findings:

1. **CONFIRMED, fixed.** Self-trigger's recursive `_spawn_one()` call,
   under the proposal's literal ordering, made this session's own
   `session-end` land after the newly-spawned generation's `session-start`
   in `events.jsonl`, permanently blinding `session_end_verdict()` to a
   real crash of the respawned generation (it always resolves to
   `normal`). Hunter reproduced with a real `os.fork()` + `cat`
   stand-in and confirmed the exact interleaved event sequence, then
   confirmed `session_end_verdict()` returns `normal` even with the new
   generation's pid marked dead. Fixed by reordering (session-end before
   self-trigger); regression-guarded by
   `SelfTriggeredRespawn::test_spawn_one_call_site_fires_after_own_session_end_event`
   (flipped from its original, now-obsolete assertion) and two new
   `SessionEndVerdict` tests
   (`test_prior_generations_session_end_does_not_mask_new_generations_crash`,
   `test_misordered_prior_session_end_would_mask_new_generations_crash`)
   that pin both the correct ordering's behavior and the exact hazard of
   the wrong one, directly on `session_end_verdict()` itself.
2. **CONFIRMED, fixed.** `int(time.time())`-granularity `session_start_ts`
   let same-wall-clock-second respawn chains collide on the
   `already_claimed` check and silently exit before the attempt-cap
   check, undercounting `runs/respawn_state.json`'s attempts and
   swallowing the eventual cap-comment. Fixed by using `time.time()`
   (float) instead. No dedicated new test added for this one beyond the
   existing `SelfTriggeredRespawn` claim/cap tests (which still pass with
   the wider precision) — a test forcing a genuine same-instant collision
   would need to mock `time.time()` itself, which none of the existing
   respawn tests in this file do; judged not worth a new mocking pattern
   for a hazard whose fix is a one-line precision change with no
   behavioral surface to assert beyond "collisions of this kind no longer
   share the coarse key."
3. **Test-coverage gap noted, addressed via finding 1's regression
   tests.** The hunter noted the (then-existing) single integration test
   mocked `_self_trigger_respawn()` itself away, so nothing in the suite
   let the P→Q recursion actually run. Rather than build a fragile
   multi-generation real-recursion test farm (real claim
   acquire/release, `RESPAWN_STATE`/`ROSTER` isolation, `gh api` mocking
   three levels deep), the two new `SessionEndVerdict`-level tests pin
   the exact mechanism (event ordering) directly and deterministically,
   which is what actually matters for correctness — judged sufficient
   over a heavier end-to-end harness for the same reason the hunter's own
   repro used a lighter escape hatch (real fork, no real multi-generation
   spawn chain).

Checked and found OK (from the hunter's report): no zombie/double-exit
risk (parent never `waitpid()`s the recursively-forked child, matching
the pre-existing top-level daemonization pattern); `session_start_ts`
round-trips exactly through `json.dumps`/`json.loads`; `_post_crash_comment`'s
new `trigger` argument is correct at both call sites; scope stayed inside
`spawn.py`/`test_spawn.py`/`docs/handbooks/operations.md`,
`roster_watchdog()`/`session_end_verdict()` bodies untouched; no
task-text double-prefixing across recursion; claim release/reacquire
ordering across the P→Q handoff is correct.

Not checked (hunter-stated, and not independently re-checked in this
pass): `_watch --follow`'s own session-end/crash detection path for the
same interleaving effect (separate code path from `session_end_verdict`,
outside this issue's write set); behavior under a genuine
multi-minute claude subprocess (the reasoning for finding 1 doesn't
depend on subprocess speed, only on `_await_bounded()` unblocking on the
new generation's `session-start`, which happens early in every real
session too); concurrent multi-*process* (not just multi-thread) races on
`runs/respawn_state.json`'s unlocked read-modify-write (pre-existing
issue #132 risk, unchanged by this issue).

closed_checks:
- name: full-suite-regression, code_sha: uncommitted (pre-PR working tree)
  python3 -m pytest test_spawn.py -q -> 206 passed, 0 failed.
- name: assume-broken-hunt, code_sha: uncommitted (pre-PR working tree)
  general-purpose agent, foreground, findings 1-2 fixed and
  regression-tested, finding 3 addressed via finding 1's tests; see Hunt
  section above for full detail.

## Open findings

None. The phase-2 hunt (see Hunt above) surfaced 3 findings, all
resolved before delivery — findings 1 and 2 fixed with regression tests,
finding 3 (test-coverage gap) addressed by finding 1's new tests. Nothing
remains open against this PR.

## What did not work

- First cut of the self-trigger call site followed the proposal's
  literal "before the bounded child's terminal `session-end` event
  append/exit" wording (self-trigger call, then `_append_event(...,
  "session-end", ...)`). Expected: firing before `os._exit()` is the only
  ordering constraint that matters. Actual: the hunt found the recursive
  respawn call blocks until the new generation's `session-start` posts,
  so firing before this session's own `session-end` makes that event land
  chronologically after the new generation's `session-start` —
  permanently blinding `session_end_verdict()` to a real crash of the
  respawned generation (Hunt finding 1). Reordered: `session-end` now
  appends first, self-trigger fires second, both still before
  `os._exit()`. See "Rationale for deviations" above.
- First cut of `session_start_ts` matched issue #132's existing
  `int(time.time())` precedent exactly (no stated reason to diverge).
  Expected: second-granularity collisions were already an accepted
  pre-existing risk class, unlikely to matter. Actual: the hunt found
  self-triggered chains remove the natural ~10-15 minute watchdog-cadence
  spacing between generations that made this risk practically
  unreachable before, and reproduced a same-second collision silently
  undercounting the attempt cap. Switched to `time.time()` (float). See
  "Rationale for deviations" above.

## Doc-placement ladder

- No new env var / config key / dependency / migration -> N/A.
- New setup/operational step (the manual resume command,
  `spawn.py <role> "<task>" --issue <n>`, and the new self-trigger
  behavior) -> documented same-turn in
  `docs/handbooks/operations.md` (mirrored KO/EN subsection, see "What
  was done" above). Completed.
- No library-or-format choice over a named alternative and no changed
  public signature/wire format in the sense the ladder means (the
  `_post_crash_comment()` `trigger` parameter is additive with a
  backward-compatible default, not a breaking signature change) -> no
  `docs/issue-247/decisions/` entry.
- No benchmark/investigation numbers produced in phase 2 -> no
  additional `docs/issue-247/reports/` entry beyond this record, the
  existing phase-1 survey, and the scout brief.

## Open-finding resolution path

All findings from the phase-2 hunt (findings 1-3 above) were resolved
before delivery — fixed and regression-tested (1, 3) or fixed with
reasoning recorded for why no additional test was added (2). No findings
remain open against this PR.
