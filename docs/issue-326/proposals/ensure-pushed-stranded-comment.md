---
status: proposed
files:
  - spawn.py
  - test_spawn.py
---

## Request

The operator's complaint: when a session's work stops partway (started,
did not finish), the system currently produces no further output and
the operator has to notice by manual inspection — silence reads as
completion. The worked example is PR #290: a session finished its work,
`git push` was rejected for a missing token scope, and the stranded
branch never surfaced anywhere the operator would see it. The ask:
anything that started and did not finish must reach the operator as a
visible question — resume, or close with a reason — never silence.

## Constraints

- Per #310: acceptance must name an executable artifact that fails on
  regression — no prose-only discharge.
- Per #330: state what this reaches beyond its own acceptance, including
  already-on-disk state it invalidates.
- Per contract v3 s19 / role-handoff protocol: this is phase 1 —
  proposal only, no code in this turn.
- Write set stays inside `spawn.py` + `test_spawn.py`; no new files, no
  new dependency, no schema change.

## Rationale

**Chosen approach**: extend `ensure_pushed()`'s two existing failure
exits (`git push` fails at `spawn.py:2818-2821`; `gh pr create` fails at
`spawn.py:2836-2841`) to post one idempotent issue comment each, reusing
the exact pattern `_post_crash_comment` (`spawn.py:1754-1771`) already
establishes in this file: a fixed marker string, checked against
`_issue_comments()` before posting, so a repeated relay attempt against
the same stranded state never double-comments.

**Alternative considered and rejected**: build a new sweep (a sibling to
`gates/closure_sweep.py`) that periodically scans `git for-each-ref` for
remote `issue-*/<role>` branches with commits and no open PR, and
comments on any it finds. This is the more general fix — the survey
found it *would* also cover the deeper gap (a process that dies before
`ensure_pushed()` ever runs, so nothing local ever attempts the push at
all) — but it requires a new file, a new call class (`git for-each-ref`
against the remote, decoupled from `board()`), and a place to schedule
it, none of which are in evidence as already-solved problems the way
`_post_crash_comment`'s idiom is. Per the survey, the concrete gap
demonstrated by PR #290 is narrower: `ensure_pushed()` runs, and *its
own* push/PR-create attempt is what silently fails — the general sweep
would fix that too, but at several times the write-set size, for a
case this smaller fix already closes. Rejected for this issue on cost;
named explicitly in Out of scope so the boundary is not silently
widened later.

## What will be done

1. In `spawn.py`, add `_post_stranded_push_comment(root, issue, role,
   branch, reason, detail)` next to `_post_crash_comment`, following its
   exact shape: a marker constant (e.g.
   `[on-the-record] stranded-relay: {key}` where `key` is
   `f"{branch}:{reason}"`, so a push-failure and a later PR-create-failure
   on the same branch get distinct markers and both surface), a
   read-then-check against `_issue_comments(root, issue)`, then one
   `gh api repos/<slug>/issues/<n>/comments` call whose body states: the
   branch name, the reason (`push-failed` / `pr-create-failed`), the
   captured stderr detail (truncated, same `[:200]` convention already
   used at the print-site), and an explicit ask — resume by re-running
   the host push/PR-open, or close the issue with a reason — mirroring
   `_post_crash_comment`'s "사람이 개입해야 한다" closing line.
2. Wire both of `ensure_pushed()`'s dead-end `return`s
   (`spawn.py:2818-2821`, `spawn.py:2836-2841`) to call
   `_post_stranded_push_comment` with the appropriate `reason`/`detail`
   immediately before returning. No other control flow in
   `ensure_pushed()` changes; the success paths are untouched.
3. Add `test_spawn.py` coverage: one test mocking the host `git push`
   subprocess call to fail, asserting the `gh api .../comments` call
   fires with a body naming the branch and asking resume-or-close; one
   test mocking `gh pr create` to fail after a successful push, same
   assertion with the PR-create reason; one idempotency test calling
   `ensure_pushed` twice against the same failing state and asserting
   the comment-posting `gh api` call fires exactly once. These reuse the
   existing `mock.patch.object(spawn, "ensure_pushed", ...)` call sites
   listed in the survey only as *other* tests' isolation points — the
   new tests call `ensure_pushed` directly and patch `subprocess.run`,
   matching the pattern in `test_ensure_pushed_push_call_injects_token_too`
   (`test_spawn.py:1363-1396`).

## Out of scope

- The deeper gap named in the survey: a process that dies before
  `ensure_pushed()` is ever invoked (host crash mid-session, killed
  `spawn.py` process) leaves no code path anywhere to notice — no
  commits ever reach a remote, so nothing local can post a comment
  about them. Closing that requires an external, periodic sweep of
  remote branch state (the rejected alternative above), which is a
  separate, larger-write-set issue.
- Watchdog scheduling cadence (whether `spawn.py watchdog` ticks run
  often enough to catch a `crashed` roster entry) — already-covered
  machinery per the survey; this proposal does not touch it.
- Any change to `board()`, `closure_sweep.py`, the ledger schema, or
  `docs/specs/flows-schema.md` — none of them are read or written by
  `ensure_pushed()`, and this proposal adds no new consumer of them.
- Automated resume or automated close — per contract v3 ("GitHub
  closure is a human/orchestrator act"), the comment only asks; it never
  respawns or closes anything itself.

## How you'll know it worked

`python3 -m pytest test_spawn.py -k stranded_push -v` (the three new
tests named above) passes, and each fails if the comment call is
removed or the idempotency check is dropped — i.e. the tests are
regression-executable per #310, not a documentation promise. Concretely:
- `test_ensure_pushed_posts_comment_on_push_failure` fails if
  `ensure_pushed()` stops calling `gh api .../comments` when the host
  push fails.
- `test_ensure_pushed_posts_comment_on_pr_create_failure` fails
  symmetrically for the PR-create branch.
- `test_ensure_pushed_stranded_comment_is_idempotent` fails if a second
  call against the same failed state posts a second comment.
