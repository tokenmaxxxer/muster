# Survey — issue #326: interrupted work must reach the operator as a question

## Scout skip record

Pure bugfix on an existing internal orchestration mechanism (`spawn.py`'s
push/PR relay) — no product-facing surface, no external category to
benchmark against. Scout condition "spec leaves no design decision open"
does not fully apply (idempotent-comment shape is a real choice, but it
already has an in-repo precedent to follow, see below), so this counts
as the pure-bugfix skip: fixing a silent failure path in an existing
function to match the behavior every sibling failure path in the same
file already has. Scouting external products for "how should a CI bot
comment on a stuck PR" would not change the shape available here — the
repo's own `_post_crash_comment` idiom is the fit.

## What the issue actually asks

Operator statement (paraphrased): when work started and did not finish,
the system must not go quiet — it must ask the operator to resume or
close, on the record. The worked example is PR #290: a session did the
work, `git push` was rejected (missing token scope), and nothing told
the operator — the surface reported `session-end: silent-failure` and a
human had to notice by manual inspection.

## Current state: three points that can each strand work, and how each is (or isn't) handled

1. **Inside a session, uncommitted work at session end**
   (`_spawn_one`'s post-processing, `spawn.py:3277-3290`) — classified
   `uncommitted-work` (`spawn.py:3293`), which is in
   `_ABANDONED_WORK_OUTCOMES` (`spawn.py:1874`). `_self_trigger_respawn`
   (`spawn.py:1876-1899`) fires **synchronously, same call**, and drives
   `_respawn_or_cap` (`spawn.py:1773`), which either respawns
   (≤`RESPAWN_MAX_ATTEMPTS`=2) or, once the cap is hit, posts an
   idempotent issue comment via `_post_crash_comment`
   (`spawn.py:1754-1771`). **Covered** — this path cannot go silent.

2. **Watchdog-observed crash** (roster entry still alive when a later
   `spawn.py watchdog` tick runs, `_auto_respawn_check`,
   `spawn.py:1832-1863`) — same `_respawn_or_cap`/`_post_crash_comment`
   machinery, entered from the watchdog trigger instead of the
   self-trigger. **Covered**, contingent on the watchdog actually being
   invoked again — outside this issue's write set (a scheduling gap, not
   a classification gap).

3. **The orchestrator's own post-session push relay,
   `ensure_pushed()`** (`spawn.py:2795-2841`) — called once, right after
   every session with an `issue` ends (`spawn.py:3290`). Its docstring
   states its own reason for existing: sandbox git egress is blocked in
   some environments, so "on-the-record 가 세션 종료 후 바깥에서
   릴레이한다" (relays from outside, after the session ends) — this is
   *itself* already understood in the codebase as the last-resort path
   for exactly the PR #290 scenario. Two failure exits inside it are
   **not** covered by anything above:
   - `git push` fails (`spawn.py:2818-2821`): prints to `stderr`
     (`f"[{role}] 호스트 push 실패: ..."`) and `return`s. Nothing is
     written to the issue, the ledger, or any file `spawn.py watchdog`
     or `closure_sweep.py` later reads. The branch's commits exist only
     on disk; no board artifact records that fact.
   - `gh pr create` fails after a successful push
     (`spawn.py:2836-2841`): same shape — `stderr` only, `return`.

   Both are dead ends: no respawn is attempted (there is no crashed
   process to respawn — the *session* already finished normally; only
   the orchestrator's own post-hoc relay failed), no comment is posted,
   and no later sweep re-derives this state, because `board()`
   (`spawn.py:1084`) only reads **merged** `docs/issue-<n>/reports/`
   records and `closure_sweep.find_violations`
   (`gates/closure_sweep.py:71-100`) only inspects subjects/roles that
   already have a board record *and* skips any subject where
   `spawn._pr_for_branch` returns `None` (`gates/closure_sweep.py:98-100`)
   — a branch with commits and no PR is invisible to it by construction.
   This is precisely the PR #290 shape: work done, push/PR-open rejected,
   silence.

## Overlap check against named related issues

- **#301 / #302** (both closed, `push-rejected` classification landed
  in `spawn.py`'s `session_end_verdict`/ledger machinery per
  `git log`): these give the **session's own** push attempt a distinct,
  visible outcome in the event log and ledger, for a session that is
  still alive to record it. They do not touch `ensure_pushed()` at all
  — `ensure_pushed` is the orchestrator's separate, later, outside-the-
  session relay attempt, called after the session has already exited.
  Confirmed by `grep -n "push-rejected" spawn.py` and reading
  `ensure_pushed`'s body: no `push-rejected` string appears inside it.
  No overlap in write set; #326's fix sits one hop downstream of what
  #301/#302 shipped.
- **#310**: acceptance must name an executable artifact that fails on
  regression. Applied below via a `test_spawn.py` test that asserts the
  `gh api .../comments` call fires on push/PR-create failure and does
  not duplicate on a second failed attempt.
- **#330**: the change must state what it reaches beyond its own
  acceptance criteria, including already-on-disk state it invalidates.
  Addressed in the proposal's own text — this change touches only
  `ensure_pushed`'s two failure exits; it adds a new `gh api` comment
  call class (same shape as `_post_crash_comment`'s, already an
  established call class) and does not change `board()`,
  `closure_sweep.py`, the ledger schema, or any existing on-disk
  record's meaning.

## What is deliberately not covered (informs Out of scope)

- A session/orchestrator process that dies **before** `ensure_pushed()`
  ever runs (host crashes mid-session, or the whole `spawn.py` process
  is killed) — no commits reach a remote, no code path anywhere runs to
  notice. This is a process-liveness gap, not a classification gap, and
  is out of this issue's frozen write set (`ensure_pushed` cannot detect
  its own non-invocation). It would need a periodic external sweep
  (e.g. extending `closure_sweep.py` to enumerate remote branches
  independent of `board()`/`_pr_for_branch`), which is a materially
  larger write set than the two dead-end `return`s this survey found —
  named here so the boundary is explicit, not silently absorbed.
- Watchdog cadence itself (point 2 above) — already covered by existing
  machinery contingent on a tick actually running; scheduling that tick
  is a different concern (out of this issue).

## Existing idiom to reuse (chosen approach, feeds Rationale)

`_post_crash_comment` (`spawn.py:1754-1771`) is the established pattern
for "tell the operator work is stuck, exactly once, on the record": a
fixed marker string checked against `_issue_comments()` before posting
(read-then-check idempotency, same as `approve_scope`'s comment check
and `closure_sweep.post_sweep_comments`'s digest marker), then one
`gh api repos/<slug>/issues/<n>/comments` call. `ensure_pushed()`
already has `root`, `issue`, `role`, and (on the push-failure branch)
the branch name and the local commit ahead-count `n` in scope — enough
to compose a comment naming the exact stranded branch and asking
resume-or-close, mirroring `_post_crash_comment`'s body shape.

## Files this survey found relevant (not yet a write set — that is the proposal's job)

- `spawn.py` — `ensure_pushed` (`:2795-2841`), `_post_crash_comment`
  (`:1754-1771`), `_issue_comments`/`_repo_slug` (`:903-948`) as reused
  helpers.
- `test_spawn.py` — existing `ensure_pushed` tests at `:1363-1396`,
  `:1515`, `:1669`, `:1725`, `:3182`, `:3266`, `:3339` (mock/patch
  points to match, so a new test doesn't collide with existing
  monkeypatches).

Sources: read directly from this checkout — `spawn.py`, `gates/closure_sweep.py`,
`test_spawn.py`; `gh issue view 301`, `gh issue view 302`, `gh issue view 310`,
`gh issue view 330`; `git log --oneline -- spawn.py | grep -i 301` style checks
confirming #301/#302 landed in `session_end_verdict`/ledger, not `ensure_pushed`.
