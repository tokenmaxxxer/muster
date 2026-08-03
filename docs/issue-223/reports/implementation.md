---
code_under_review:
  - spawn.py
  - test_spawn.py
loop_state: landed
---

# Implementation record — issue #223

Phase 2, executing the approved proposal
(`docs/issue-223/proposals/spawn-one-issue-role-claim.md`, approved via
issue-level comment `APPROVE issue-223/implementation`, single-account
mode, role-handoff contract v3, PR author and approver both
jjongkwann).

## What was done

`spawn.py` (`_spawn_one()`, ~line 2510-2856, and 3 new helpers just
above it):

1. New helpers `_spawn_claim_path(work)`, `_acquire_spawn_claim(work,
   issue, role) -> str | None`, `_rewrite_spawn_claim_pid(work) ->
   None`, `_release_spawn_claim(work, pid) -> None`. Claim file:
   `Path(str(work) + ".spawn-claim")` — same sibling-file family as
   `.respawn-claim-{ts}` (issue #132), caught automatically by the
   `clean` command's existing glob (`w.parent.glob(w.name + ".*")`,
   spawn.py ~2246-2252) with no changes to `clean` itself.
2. `_acquire_spawn_claim`: writes `{"pid": os.getpid(), "ts":
   int(time.time())}` to a `tempfile.mkstemp` sibling, then
   `os.link()`s it onto the claim path — `os.link` is itself an atomic
   exists-check+create, so a concurrent reader can never observe a
   partially-written or truncated claim file. On `FileExistsError`,
   reads the existing claim's pid and checks `_alive(pid)`: alive ->
   returns a rejection string naming the pid/start-ts (issue #223
   requirement 3); dead -> unlinks the stale claim and retries once
   (requirement 2, capped at 2 attempts total).
3. `_spawn_one()` calls `_acquire_spawn_claim(cwd, issue, role)` right
   after `cwd = issue_workspace(cwd, issue, role)` and before
   `checkout_issue_branch()` — fast-fails before any workspace
   clone/checkout work. On rejection, prints the reason to stderr and
   `return`s `1` (not `sys.exit()`) so `_auto_respawn_check()`'s caller,
   `roster_watchdog()`'s per-entry loop (spawn.py ~1456-1459), keeps
   scanning the rest of the tick's crashed entries instead of the whole
   watchdog process dying on one claim conflict.
4. `_rewrite_spawn_claim_pid(cwd)` is called in the bounded fork's
   child branch (`child_pid == 0`), immediately before `os.setsid()`
   (spawn.py ~2697-2699) — fixes the fork-before-pid-rewrite pitfall
   this issue's kickoff prompt flagged: the claim is written with the
   parent's pid before `os.fork()`, but in the bounded path the parent
   returns/exits right after forking, so an un-rewritten claim would
   point at a soon-dead pid and the next liveness check would
   misjudge a live child session as stale.
5. `_release_spawn_claim(cwd, os.getpid())` runs right after
   `roster_remove(roster_key)` (spawn.py ~2839-2842), guarded by `if
   issue is not None`. Only unlinks the claim if its recorded pid still
   matches the caller's own pid, so it never deletes a claim that a
   different process legitimately stale-cleaned-and-reacquired in the
   meantime.

`test_spawn.py`: new `SpawnOneIssueRoleClaim` class (proposal item 6),
4 tests, all real (no `_spawn_one` replacement):
- `test_concurrent_spawn_one_calls_let_exactly_one_through` — two real
  `threading.Thread`s call `_spawn_one(..., issue=223)` concurrently on
  the same workspace; asserts `checkout_issue_branch` is reached
  exactly once and the two return codes are `[0, 1]`. Confirmed
  failing pre-fix (`checkout_issue_branch` reached twice) before
  writing the fix, per the issue's own ask for an actual concurrent-
  repro regression, not a mocked one.
- `test_stale_claim_from_dead_pid_is_cleaned_and_retried` — a claim
  file naming a real, already-`wait()`-ed (guaranteed dead) pid is
  cleaned and re-acquired.
- `test_rejection_names_the_live_claimant_pid_and_ts` — a claim naming
  the test process's own (alive) pid produces a rejection string
  containing that pid and its ts.
- `test_fork_child_rewrites_claim_pid_before_setsid` — mocks
  `os.fork`/`os.setsid`/`os._exit` to force the bounded child branch
  without a real fork (saving/restoring fds 0/1/2 around the call,
  since the real code `os.dup2`s onto them), and asserts the rewrite
  helper runs before `os.setsid`.

Verification run: `python3 -m unittest test_spawn -q` — 179 tests, 41
errors, identical error count and identical failing tests to a `git
stash`-verified baseline run of the same suite against pre-change
`spawn.py`/`test_spawn.py` (175 tests, same 41 errors) — every one of
the 41 is this sandbox's pre-existing, unrelated `rulebook_checkout()`
git-template-copy failure (`fatal: cannot copy
.../commit-msg.sample...`), not something this change touches or
introduces. All 4 new tests pass; the concurrency reproduction test
was independently re-run 20+ times with no flakes.

## Why

Executing the phase-1 proposal at
`docs/issue-223/proposals/spawn-one-issue-role-claim.md`: the main
spawn path (`main()` -> `_spawn_one()`) has no mutual-exclusion claim
against concurrent spawns of the same (issue, role) — only the respawn
path (`_auto_respawn_check()`) has one (issue #132's
`.respawn-claim-{ts}`). Adds the same O_CREAT|O_EXCL claim family
inside `_spawn_one()` itself so both callers inherit it.

## Upstream basis

`docs/issue-223/proposals/spawn-one-issue-role-claim.md`, approved via
issue #223's `APPROVE issue-223/implementation` comment.

## What did not work

- First cut of `_acquire_spawn_claim` followed the proposal's literal
  `os.open(O_CREAT|O_EXCL|O_WRONLY)`-then-write-content shape. Running
  the new concurrency test against it showed intermittent double-pass
  (both threads reaching `checkout_issue_branch`, or neither): a second
  thread's `FileExistsError` handler could read the claim file in the
  gap between its creation and its content write, see 0 bytes, treat
  that as a corrupt/stale claim, delete it, and re-acquire out from
  under the first thread. Expected: O_CREAT|O_EXCL alone makes the
  claim atomic (true for `.respawn-claim-{ts}`, which never reads its
  own content back). Actual: content survival across the create step
  is not atomic by itself once a reader inspects that content on
  conflict — replaced with write-to-tempfile-then-`os.link()`.
- The adversarial-self hunt (below) found the same TOCTOU class left
  unfixed in `_rewrite_spawn_claim_pid`, which used
  `Path.write_text()` (truncate-then-write). Expected: rewriting an
  already-atomically-created claim's pid field was a simple read-
  modify-write with no new concurrency exposure. Actual:
  `write_text`'s truncate opens the same empty-file-observation window
  the acquire path had already closed — replaced with write-to-
  tempfile-then-`os.replace()`.

## Open findings

From the adversarial-self hunt (see Hunt below), 2 findings are real
but out of this issue's frozen write set (`_spawn_one()`/its 3 new
helpers/`test_spawn.py` only — not `_auto_respawn_check()` or
`roster_watchdog()`):

1. A claim rejection inside `_auto_respawn_check()` still consumes one
   of `RESPAWN_MAX_ATTEMPTS` (2) attempts and posts the
   `respawn-attempt` event, even though no session actually started —
   `_spawn_one()`'s return code is discarded there today (pre-existing
   call-site behavior, unchanged by this issue). Two claim collisions
   in a row would trigger the "give up, needs a human" cap comment
   with zero real spawn attempts having run.
2. pid reuse: if a crashed claim-holder's pid gets recycled by an
   unrelated live process before the next acquire, `_alive()` reads
   the claim as legitimately held forever. This is the same accepted
   risk class ROSTER's own `_alive()` already carries (no incident
   since issue #139), just re-surfaced by the new claim as another
   `_alive()` consumer.

Resolution path: both are candidates for a follow-up issue against
`_auto_respawn_check()`/`roster_watchdog()` (e.g. have
`_auto_respawn_check()` distinguish a claim-conflict return from
`_spawn_one()` and not burn an attempt on it) — not fixed here per the
scope-exceeded rule, since fixing them requires touching a function
outside this issue's write set.

## Doc-placement ladder

- No new env var / config key / dependency / migration / setup step
  introduced -> N/A.
- Library-or-format choice already recorded in the phase-1 proposal's
  Rationale (O_CREAT|O_EXCL over `fcntl.flock()`; return-value rejection
  over `sys.exit()`) -> no new `docs/issue-223/decisions/` entry needed;
  phase 2 follows that choice as approved. The tempfile+`os.link`/
  `os.replace` atomic-write refinement (see "Rationale for deviations")
  is an implementation detail of writing content atomically within the
  same O_CREAT|O_EXCL claim family, not a different library/format
  choice over a named alternative.
- No benchmark/investigation numbers produced in phase 2 -> no
  additional `docs/issue-223/reports/` entry beyond this record and the
  existing phase-1 survey/proposal.

## Hunt

Stance: **adversarial-self** (rotated — issue-229 used this stance
once and it hasn't been used since; issue-220/232 used
assume-incomplete-coverage, issue-216/218/235/236 used assume-broken
repeatedly, issue-221/222 used composition-regression — adversarial-self
is the least-recently-used of the 4 rotated stances). No registered
`warrant-hunter` subagent type is available in this harness (same gap
noted in this issue's own phase-1 PR body and in issue-216/218/220/
221/232/235/236's records), so `general-purpose` was dispatched in its
place with an explicit adversarial-self brief (assume the change's own
reasoning about correctness is wrong and try to break it, rather than
re-deriving the same conclusion). Dispatched foreground (synchronous)
against the uncommitted diff before delivery.

Findings:

1. **CONFIRMED, fixed.** `_rewrite_spawn_claim_pid` used
   `Path.write_text()`, which truncates before writing — reopening the
   exact TOCTOU class `_acquire_spawn_claim`'s tempfile+`os.link`
   pattern exists to close. A concurrent acquire hitting
   `FileExistsError` during that truncate-write window could read 0
   bytes, misjudge the claim as corrupt, delete it, and let a second
   session through while the first (rewritten) child was still alive.
   Fixed by writing to a tempfile then `os.replace()`-ing it onto the
   claim path (same fix shape as the acquire path). Full suite
   re-run after the fix: same 41 pre-existing environment errors, no
   new failures; all 4 new tests still pass.
2. **PLAUSIBLE, out-of-scope.** Claim rejection silently burns a
   `_auto_respawn_check()` retry attempt with no session started — see
   Open findings item 1.
3. **PLAUSIBLE, accepted risk, out-of-scope.** pid-reuse can make a
   claim look permanently held — see Open findings item 2, same risk
   class as ROSTER's existing `_alive()` usage.
4. **Checked, accepted.** The concurrency test has no explicit
   `threading.Barrier` forcing simultaneous arrival at the claim; the
   hunt flagged this could in principle let a serialized run pass for
   the wrong reason. Accepted as-is because it follows the exact same,
   already-proven pattern as the pre-existing
   `AutoRespawnClaim.test_concurrent_watchdogs_do_not_double_respawn`
   (two real `threading.Thread`s, no barrier, real atomic-file syscalls
   release the GIL) — not a new risk this issue introduces, and
   changing that established pattern here would be an unrelated
   test-design change outside this issue's scope.
5. **Checked, no bug.** Fork/rewrite ordering is race-free against
   `_await_bounded()`: the parent can't return before the child's
   `session-start` event posts, which can't happen until after
   `_rewrite_spawn_claim_pid`/`Popen`/`roster_register` in the child.
   No deadlock/double-block with the separate `.respawn-claim-{ts}`
   mechanism (different files, neither blocks the other) or with the
   `clean` command's sibling-file glob (pattern verified to match
   `.spawn-claim`).

Disposition: finding 1 fixed in this session (in-scope, same 2
helpers, no signature change). Findings 2-3 are real but out-of-scope
elevated risks, recorded above as follow-up candidates. Finding 4 is an
accepted, precedent-consistent test-design choice. Finding 5 found
nothing further.

## Rationale for deviations

One deviation from `## What will be done`, driven by the mandatory
phase-2 self-testing/hunt loop rather than a scope-exceeded stop: the
proposal's step 1 described claim acquisition as a plain
`os.open(O_CREAT|O_EXCL|O_WRONLY)` call followed by writing the
pid/ts content. Building and testing it that way (with the exact
real-thread concurrency test the proposal itself specified) showed
this two-step create-then-write is not actually atomic against a
concurrent reader — see "What did not work" for both instances (the
acquire path, found before the hunt; the rewrite path, found by the
hunt). Both were replaced with a write-to-tempfile-then-atomic-move
pattern (`os.link()` for create-if-absent, `os.replace()` for
in-place update), still inside the same two helpers, same file, same
O_CREAT|O_EXCL claim family and file format the proposal's Rationale
chose over `fcntl.flock()` — no new dependency, no signature change,
no change to the chosen lock family, only to how its content is
written atomically.
