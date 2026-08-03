---
code_under_review: e545fcc
loop_state: landed
closed_checks:
  - name: fetch-fail-closed-4-sites
    code_sha: e545fcc
  - name: origin-only-branch-tracking
    code_sha: e545fcc
  - name: origin-head-fix-composition
    code_sha: e545fcc
---

# Implementation record — issue #221

Phase 2, executing the approved proposal
(`docs/issue-221/proposals/workspace-sync-fail-closed.md`, approved via
issue-level comment `APPROVE issue-221/implementation`, single-account
mode, role-handoff contract v3, PR author and approver both jjongkwann).

## What was done

`spawn.py` (`issue_workspace()`/`checkout_issue_branch()`, lines
~2327-2450):

1. New helper `_fetch_or_halt(work_dir, label, after=None)` — fail-closed
   fetch per the proposal: `sys.exit` if `returncode != 0` or `"failed
   to store"` is in stderr, matching the file's existing hard-failure
   `sys.exit` house style (`ensure_pushed`'s 2380/2420-line pattern).
2. All 4 previously fire-and-forget `git fetch` calls replaced with
   this helper: `issue_workspace()`'s 2 reuse-path fetches, its
   fresh-clone fetch, and `checkout_issue_branch()`'s fetch.
3. `issue_workspace()`'s fresh-clone path adds `git remote set-head
   origin -a` right after the clone's origin is redirected to the real
   remote — fixes `origin/HEAD` inheriting the user's WIP checkout
   branch from clone time, which `_base()` reads first.
4. `checkout_issue_branch()`'s branch-fork `else` clause now checks
   `git rev-parse --verify -q origin/<br>` before falling back to
   `_base()`: if the branch exists on origin but not locally, it
   creates a tracking branch (`git checkout -b br origin/<br>`)
   instead of forking a fresh branch from base — the exact issue-235
   failure mode. The pre-existing "local branch already exists" path
   (the `if` branch, one line above) is untouched, per the proposal's
   explicit no-force-sync constraint.

`test_spawn.py`: new `WorkspaceSyncFailClosed` class, 5 real-git
regression tests (proposal specified 4; a 5th was added mid-build after
a hunt finding — see "Rationale for deviations"):
- `test_fetch_halts_on_nonzero_returncode`
- `test_fetch_halts_on_exit_zero_with_failed_to_store_stderr`
- `test_checkout_tracks_origin_only_branch`
- `test_checkout_preserves_existing_local_branch_with_unpushed_commit`
- `test_set_head_attempted_even_when_fresh_clone_fetch_fails` (new,
  added in response to the hunt finding below)

No mocks in any of the 5 — two-repo real-git fixtures (an "origin"/
"github" repo and a clone of it), plus a PATH-injected executable `git`
wrapper for the one scenario (exit-0-with-"failed to store"-stderr)
that cannot be reproduced deterministically with real git alone.

## Why

Executing the phase-1 proposal at
`docs/issue-221/proposals/workspace-sync-fail-closed.md`, approved by
the issue-level `APPROVE issue-221/implementation` comment: fail-closed
fetch across the 4 call sites in `issue_workspace()`/
`checkout_issue_branch()`, origin-only branch tracking on reuse, and an
`origin/HEAD` fix at clone time, backed by real-git regression tests —
closing the workspace-sync triple defect the issue documents, including
its two real-world incidents (core issue-90's exit-0 fetch failure,
issue-235 phase 2's branch-fork-instead-of-track incident).

## Upstream basis

`docs/issue-221/proposals/workspace-sync-fail-closed.md` (commit
`e545fcc`), approved via issue #221's `APPROVE issue-221/implementation`
comment.

## What did not work

- First draft of `_fetch_or_halt` called `remote set-head origin -a`
  *after* the fail-closed halt check in the fresh-clone path. The hunt
  (below) found this drops `set-head` entirely whenever the first fetch
  after a fresh clone fails — replaced with an `after=` callback run
  before the halt decision. Expected: fetch-then-halt-then-fix. Actual:
  needed fetch-then-fix-then-halt, since the fix must run even on the
  path that's about to `sys.exit`.

## Doc-placement ladder

- No new env var / config key / dependency / migration / setup step ->
  N/A, none introduced (`_fetch_or_halt`'s `after` parameter is an
  internal function argument, not user-facing config).
- No library-or-format choice beyond what
  `docs/issue-221/proposals/workspace-sync-fail-closed.md` already
  decided -> no new `docs/issue-221/decisions/` entry needed. The
  `after=` callback pattern is an in-build refinement of the proposal's
  own `_fetch_or_halt` design (same function, same file, same frozen
  signature contract for `issue_workspace`/`checkout_issue_branch`),
  not a new library-or-format choice over a named alternative.
- No benchmark/investigation numbers produced in phase 2 -> no
  additional `docs/issue-221/reports/` entry beyond this record and the
  existing phase-1 `docs/issue-221/reports/implementation/survey.md` +
  `scout-brief.md`.

## Hunt

Stance: **composition-regression** (rotated — issue-229 used
adversarial-self, issue-222 composition-regression, issue-220/232
assume-incomplete-coverage, issue-216/218/235/236 assume-broken; picking
composition-regression here since both of the two most-recently-landed
records on `main`, issue-235 and issue-236, independently landed on
assume-broken — rotating to the least-recently-used stance instead of
repeating it a third time in a row). No registered `warrant-hunter`
subagent type is available in this harness (same gap as
issue-216/218/220/232/235/236's records), so `general-purpose` was
dispatched in its place with an explicit adversarial composition-
regression brief. Dispatched foreground (synchronous) against the
committed diff before delivery, with instructions to probe specifically
for interaction bugs between the shared helper, the 4 call sites, the
new branch-tracking `elif`, and the new `set-head` call — not to praise
or summarize.

Findings:

1. **CONFIRMED, fixed.** `_fetch_or_halt`'s fail-closed `sys.exit` on
   the fresh-clone path ran *before* the new `remote set-head origin
   -a` call. If that first post-clone fetch failed, the process halted
   before `set-head` ever ran — and because `git clone` had already
   succeeded, every later call for that same workspace takes the reuse
   branch (`if (work / ".git").exists(): ...`), which never calls
   `set-head` either. Net effect: a single transient fetch hiccup on
   first clone would permanently trap the workspace in exactly the
   `origin/HEAD` pollution this issue exists to fix — a composition
   regression between the fetch fix and the `origin/HEAD` fix that
   neither one shows in isolation. Fixed by adding an `after=` callback
   to `_fetch_or_halt`, run before the halt decision, and passing the
   `set-head` call through it on the fresh-clone site. New regression
   test `test_set_head_attempted_even_when_fresh_clone_fetch_fails`
   confirmed the bug against the pre-fix ordering (reverted just that
   one code block, temporarily, in-process, and re-ran the single new
   test — `origin/HEAD` came back `origin/feature-wip` instead of
   `origin/main`) and confirmed the fix (test passes with the ordering
   restored). Full suite re-run after the fix: no new failures.
2. **CONFIRMED, not fixed — pre-existing gap, outside this issue's
   frozen write set.** `_fetch_or_halt`'s `sys.exit` propagates
   uncaught through `roster_watchdog()`'s `auto_respawn=True` loop
   (`_auto_respawn_check()` -> `_spawn_one()` -> `issue_workspace()`/
   `checkout_issue_branch()`, `spawn.py:1678`, no `try/except`
   anywhere in that chain). This risk already existed before this
   issue via the pre-existing `sys.exit` sites in these two functions
   (missing-origin, clone-failure, branch-checkout-failure) — this
   change adds 4 more trigger points (fetch failures, which are more
   common than those pre-existing conditions), raising how often a
   single crashed roster entry's auto-respawn attempt can kill the
   entire watchdog scan mid-loop (skipping anomaly reports for every
   later roster key and skipping `_watchdog_state_save`). Fixing
   `roster_watchdog()`/`_auto_respawn_check()`'s error handling is a
   different function outside this issue's frozen write set
   (`issue_workspace()`/`checkout_issue_branch()` only, per the
   proposal) — per the scope-exceeded rule, not fixed here. Left as a
   next step (below) for a follow-up issue: wrap the `_spawn_one()`
   call in `_auto_respawn_check()` in `try/except SystemExit`, treating
   it as a failed respawn attempt rather than a fatal watchdog crash.
3. **PLAUSIBLE, accepted risk, not fixed.** The new `remote set-head
   origin -a` call (both the original site and its `after=` callback)
   is itself fire-and-forget — if it silently fails (distinct from the
   fetch it follows), the same permanent-`origin/HEAD`-pollution
   mechanism as finding 1 could still occur. Not fixed: the proposal's
   own Rationale scoped fail-closed detection specifically to the
   fetch's returncode/stderr (Rationale 대안2, rejected broadening
   beyond the one measured failure string), and never proposed
   fail-closed treatment for `set-head` itself — extending fail-closed
   to `set-head` would be a scope decision the approved proposal didn't
   make. Left as-is, consistent with the approved design's boundary.
4. Checked and found clean (hunt agent's own report, verified by
   re-reading the relevant lines directly): the `-q` fetch flag
   addition at `checkout_issue_branch()`'s call site changes no
   caller-visible behavior (output was already discarded everywhere);
   the `if`/`elif` branch ordering in `checkout_issue_branch()` always
   prefers an existing local branch and never force-syncs it; the 4
   original tests would fail under literal pre-fix code (not false
   positives — independently re-verified in this record via the
   `git stash push -- spawn.py` before/after run, see "Verification
   run"); `PATH` restoration in the stderr-wrapper test is `try/finally`-
   guarded even on assertion failure; no write touches the user's own
   `cwd`/`src` checkout, and no locally-existing issue branch is
   force-reset.

Disposition: finding 1 fixed in this session (in-scope, same function,
same file, no signature change). Finding 2 is a real but out-of-scope
elevated risk, documented as a next step. Finding 3 is an accepted,
proposal-consistent scope boundary. Finding 4 found nothing further.

## Rationale for deviations

Two deviations from `## What will be done`, both driven by the
mandatory phase-2 hunt (hunt finding 1) rather than a mid-build
scope-exceeded stop:

1. **`_fetch_or_halt` gained an `after=` parameter, and the
   fresh-clone call site interleaves the `set-head` call through it,
   instead of the proposal's plain "call the helper, then call
   `set-head` after."** The proposal's step 3 said to add the
   `set-head` call "새 헬퍼 호출 직후" (right after the new helper
   call) — literally, after the fail-closed halt decision. The hunt
   found this ordering silently drops `set-head` forever whenever the
   first post-clone fetch fails, because the reuse branches never call
   `set-head` either. The fix keeps the same helper, the same 4 call
   sites, and the same frozen `issue_workspace`/`checkout_issue_branch`
   signatures — only the internal sequencing of one call site changed,
   to make the fix survive the exact failure class it's meant to
   handle.
2. **A 5th regression test was added, beyond the proposal's planned 4.**
   `test_set_head_attempted_even_when_fresh_clone_fetch_fails` exists
   specifically to catch the ordering bug in deviation 1 — none of the
   4 originally-planned tests would have caught it (they test the fetch
   fail-closed behavior and the branch-tracking behavior separately;
   the bug is in how those two behaviors compose on one call site).

Both deviations stay inside the proposal's frozen write set
(`spawn.py`, `test_spawn.py`; `issue_workspace()`/
`checkout_issue_branch()` signatures unchanged) and the proposal's own
constraints (no force-sync of locally-existing branches, `_base()`
untouched, `src`/`cwd` untouched) — neither is a scope-exceeded stop.

## Verification run

`python3 -m unittest test_spawn.py -v`: 175 tests, 41 errors — all 41
pre-exist on the unmodified branch (confirmed via `git stash push --
spawn.py test_spawn.py` then re-running the baseline suite: 170 tests,
same 41 errors, same failure signature — `rulebook_checkout()` failing
to copy git hook templates in this sandbox, unrelated to this issue's
write set). All 5 new `WorkspaceSyncFailClosed` tests pass. Confirmed
each of the 4 originally-planned tests fails against the pre-fix
`spawn.py` (temporarily reverted just `spawn.py` via `git stash push --
spawn.py`, re-ran `test_spawn.WorkspaceSyncFailClosed`: 3 of 4 error/
fail as expected — `_fetch_or_halt` doesn't exist yet, and the
origin-only-branch test finds no origin-only commit in the log; the
4th, the local-branch-preservation regression guard, passes both
before and after by design, since it guards a case the fix doesn't
touch). Confirmed the 5th (hunt-driven) test fails against the pre-fix
call-ordering and passes with the fix (see Hunt finding 1).

Manual origin/HEAD check (proposal's optional manual-confirm bullet):
the full `issue_workspace()` path couldn't be exercised via a direct
Bash invocation in this sandbox — the function's credential-helper
`git config` call embeds a literal `!f() { ... }; f` shell-function
string as a config value, which this sandbox's command-safety layer
flags for interactive approval, unavailable in this headless session.
Worked around by (a) replicating the exact git command sequence
(`clone` -> `set-url` -> `fetch` -> `remote set-head origin -a`)
directly against two distinct real repos (a "src" repo checked out on
a feature branch, and a separate "github" repo with `main` as its real
default) to confirm the sequence itself corrects `origin/HEAD` from
`feature-wip` to `main`, and (b) the automated regression test
`test_set_head_attempted_even_when_fresh_clone_fetch_fails`, which
*does* call the real `issue_workspace()` end-to-end (unittest runs
don't hit the same Bash-level approval gate, since the credential-
helper string never appears in a literal shell command Claude Code
issues) and asserts the same thing.

## Open findings

Hunt finding 2 (pre-existing `sys.exit`-through-watchdog-loop risk,
widened by this change's added fetch-failure trigger points) is real
but out of this issue's frozen write set — not a blocking defect in
what was delivered, but a documented follow-up. No other open findings.

## Next steps

Follow-up issue candidate: wrap the `_spawn_one()` call inside
`_auto_respawn_check()` (`spawn.py:1678`) in `try/except SystemExit`,
so a `sys.exit` from a respawn attempt's `issue_workspace()`/
`checkout_issue_branch()` (this issue's fail-closed fetch, or any of
the function group's pre-existing hard-failure exits) is treated as a
failed respawn attempt rather than killing `roster_watchdog()`'s entire
scan loop mid-iteration. Not proposed or built here — outside this
issue's frozen write set (hunt finding 2).

## Open-finding resolution path

The one open finding (hunt finding 2) resolves via the follow-up issue
described above — no action required on this PR to land it, per the
scope-exceeded rule (finish what the proposal covers, stop, report).
