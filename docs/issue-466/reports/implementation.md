---
code_under_review: HEAD
loop_state: phase-2-in-progress
---

# Implementation record — issue-466

Phase 2, approved via single-account `APPROVE issue-466/implementation`
issue comment (author == approver == JiwonJung94, contract v3 single-
account mode).

## Plan (from the approved proposal)

1. `on-the-record/hooks/decision-queue-stopgate.sh` (new)
2. `on-the-record/hooks/hooks.json` (add Stop entry)
3. `on-the-record/hooks/test_decision_queue_stopgate.py` (new)
4. `spawn.py`'s `checkout_issue_branch()` — stale-local-branch detection
5. `test_spawn.py` — two new red-green cases

## What was done

1. `on-the-record/hooks/decision-queue-stopgate.sh` (new) — reads
   `spawn.py flows --json`'s `decision_queue`, applies the two age
   tiers (>=1h additionalContext, >=4h block), silent below 1h or on an
   empty queue. `ORCHESTRATE_OFF`/`CLAUDE_ROLE` kill switches carried
   over from `stop-gate.sh`/`directive.sh`.
2. `on-the-record/hooks/hooks.json` — added the new script to the
   `Stop` array alongside `stop-gate.sh`/`role-test-claim-guard.sh`.
3. `on-the-record/hooks/test_decision_queue_stopgate.py` (new) — 7
   cases (empty, under-1h, 1-4h, >=4h, mixed-tiers, `ORCHESTRATE_OFF`,
   `CLAUDE_ROLE`); all pass (`python3 -m pytest
   on-the-record/hooks/test_decision_queue_stopgate.py -q` → 7 passed).
4. `spawn.py`'s `checkout_issue_branch()` (spawn.py:3023) — before
   reusing a local `issue-<n>/<role>` branch, checks
   `git rev-list --count <base>..<branch>`; if `0` (fully absorbed into
   base), `git checkout -B <branch> <base>` instead of resuming it as
   the stale ref (`-B` resets in place, works whether or not the branch
   is the currently-checked-out one — `branch -D` cannot delete the
   current branch, which the first implementation attempt hit — see
   What did not work). Any branch with a unique commit is reused
   unchanged, matching today's behavior.
5. `test_spawn.py` — two new cases in the existing real-git
   `WorkspaceSyncFailClosed` class: the issue-441 shape (local branch
   fully merged into base via a simulated remote merge + delete, must
   start fresh, and a subsequent commit is then ahead of origin/base —
   the concrete condition `ensure_pushed()` needs to have something to
   push) and the general 0-ahead stale-branch shape (independent of any
   specific issue history). Full suite: `python3 -m pytest test_spawn.py
   -q` → 277 passed (up from 275, both existing tests and the 2 new
   ones pass, no regressions).

Also ran `on-the-record/hooks/` full suite (`python3 -m pytest
on-the-record/hooks/ -q` → 33 passed) and validated `hooks.json` parses
as JSON after the edit.

## Why / upstream basis

Carries `docs/issue-374/proposals/2026-08-07-decision-queue-stop-hook-nudge.md`
and `docs/issue-428/proposals/2026-08-07-respawn-after-merge-and-silent-outcome.md`'s
already-approved-in-spirit design into #466's acceptance shape, per
`docs/issue-466/proposals/2026-08-08-decision-queue-stophook-and-respawn-branch-fix.md`.

## What did not work

- First attempt at #428's fix used `git branch -D <br>` followed by
  `git checkout -b <br> <base>` on finding a 0-ahead stale branch —
  broke when the stale branch was also the currently-checked-out one
  (`git branch -D` refuses to delete the current branch), which the
  general-stale-branch test case hit as a `SystemExit`. Switched to
  `git checkout -B <br> <base>`, which resets the branch in place and
  works in both cases.
- First attempt at the issue-441 fixture used
  `git branch -q -D -r origin/<br>` to simulate the remote branch
  deletion after merge — pointless (that remote-tracking ref never
  existed since `br` was never pushed) and left the sanity assertion
  failing (`rev-list --count` reported `1`, not `0`) because the
  simulated "merge" (`git fetch <work> br:base` into `origin`) never
  landed: `git fetch` refuses to update the ref of the currently
  checked-out branch in a non-bare repo. Fixed by `git checkout
  --detach` in `origin` before the fetch-as-push, then checking
  `base_branch` back out.

## Open findings

None open. Before-landing hunt (stance 3, `docs/reports/2026-08-08-hunt-decision-queue-stophook-and-respawn-branch-fix.md`)
found `decision-queue-stopgate.sh`'s `_checkout_resolve()` was missing
`directive.sh`'s self-clone fallback despite the file's own comment
claiming parity — resolved below.

## Next steps

None — items 1-5 built, tests run, finding resolved, ready to commit and push.

## Resolution path

resolved_findings:
- finding: decision-queue-stopgate.sh's `_checkout_resolve()` silently
  dropped directive.sh's self-clone fallback despite a comment claiming
  it resolves the checkout "the same way directive.sh does" — on a
  fresh machine with no existing checkout in any fixed lookup path, the
  Stop hook exits 0 with no clone attempt and no output, indistinguishable
  from an empty queue.
  source: docs/reports/2026-08-08-hunt-decision-queue-stophook-and-respawn-branch-fix.md
    (before-landing, stance 3)
  fix: added the same `mkdir -p "$(dirname "$own")" && git clone -q
    https://github.com/tokenmaxxxer/on-the-record.git "$own"` fallback
    block to `decision-queue-stopgate.sh` immediately before its final
    `return 1`, matching `directive.sh`'s block verbatim.
  verified: `python3 -m pytest on-the-record/hooks/ -q` → 33 passed
    (no test asserted the absence of a clone attempt, so no test needed
    updating).

## Doc placement

- No new env var, config key, dependency, or migration introduced —
  nothing to add to a handbook.
- No library-or-format choice over a named alternative beyond what the
  proposal's own `## Rationale` already recorded — no new ADR needed.
- No benchmark/investigation numbers produced.
