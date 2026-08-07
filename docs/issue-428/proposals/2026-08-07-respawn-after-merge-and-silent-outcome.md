---
status: proposed
files:
  - spawn.py
  - test_spawn_fault_428.py
  - docs/issue-428/reports/implementation.md
---

## Request

Fix #428: (a) respawning an issue whose branch was already merged and
`--delete-branch`-deleted currently fails PR creation with "No commits
between main and issue-<n>/<role>" — reproduce the mechanism and make the
ordinary respawn-after-merge case work; (b) a session outcome of
`silent-failure` or `refused` must reach the operator without anyone
choosing to look at a log or the gitignored ledger.

## Constraints

- Two-phase contract v3 s19: this PR is phase 1 only (survey + proposal);
  no `spawn.py` edit lands until a listed approver's Approve.
- `runs/ledger.jsonl` stays gitignored — measurement data is not source;
  the fix cannot depend on committing it.
- Workspace reuse on respawn must be kept for genuinely in-progress
  sessions (survey's rejected-alternative: dropping reuse entirely
  resurfaces scope item 3's loss).
- No new external dependency; `gh` is already the project's only GitHub
  client.

## Rationale

The survey reproduced the actual mechanism with real git (not
`spawn.py` mocking): the stale ref that survives `--delete-branch` is the
**local** branch `issue-<n>/<role>` in the reused workspace, not a
leftover remote-tracking ref — `git fetch` in this git version already
auto-prunes deleted remote branches. `checkout_issue_branch()`
unconditionally reuses that local branch whenever it exists
(spawn.py:2918-2919), with no check for "already fully merged into base".

Considered and rejected: fixing this by adding `--prune` to the fetch
call alone. That only removes stale remote-tracking refs, and the
reproduction shows those are not the culprit here — `origin/<branch>` was
already gone after the plain fetch. A prune-only fix would leave the
reported failure fully reproducible, so it does not qualify as a fix for
this issue.

For the outcome-surfacing gap, considered and rejected: leaving it as an
orchestrator-side checklist item ("check the ledger after every spawn").
#424's precedent (`record-fields-gate`, `closes-gate`, `board-gate`) is
that this class of gap gets closed by removing the option, not by adding
advice — and the issue's own history is that the advisory shape
(`print(..., file=sys.stderr)`) already failed five times in one day.

## What will be done

1. `checkout_issue_branch()`: when a local `issue-<n>/<role>` branch
   exists, check `git rev-list --count <base>..<branch>` before reusing
   it. If it is 0 (branch fully absorbed into base — the merged-and-
   respawned case), delete the stale local branch and fall through to the
   fresh-from-base path, instead of checking it out. A branch with any
   unique commits (genuinely in-progress work) is still reused exactly as
   today — this only removes the case that is already indistinguishable
   from "nothing to do."
2. `ensure_pushed()`'s existing `pr-create-failed` / any `silent-failure`
   / `refused` outcome: post a `gh issue comment <issue>` carrying the
   outcome and (for `pr-create-failed`) the rejection reason, from the
   outcome-handling block currently at spawn.py:3512-3519 (still emits the
   existing stderr prints — this adds the comment, it does not replace
   the log line). This makes the bad outcome land on the GitHub issue
   itself, the surface the operator already reads without being told to,
   rather than only in a gitignored ledger line or a per-host log tail.
   Best-effort: if the `gh issue comment` call itself fails (e.g. no
   network), that failure is printed to stderr same as today — it does
   not newly block session-end, since blocking session-end on a
   notification side-channel would trade one silent-failure mode for a
   worse one (a session that can't even record it ended).
3. `test_spawn_fault_428.py`: exercise `checkout_issue_branch()` and
   `issue_workspace()` directly against a real local git remote/clone
   pair (same shape as the survey's shell reproduction, but calling the
   actual functions) to show the merged-and-respawned case now creates a
   fresh branch instead of reusing the stale one; and exercise the
   outcome-surfacing addition by forcing `outcome = "silent-failure"`
   through the real classify/print path with a stubbed `gh`, asserting
   the comment call happens.

## Out of scope

- Scope item 3's broader question ("where should commits be recoverable
  if a session can't open a PR at all") beyond what the fault-1 fix
  already preserves as a side effect (survey's Fault 3 section) — a
  dedicated recoverability path (e.g. a fallback branch name, an explicit
  "orphaned commits" notice) is follow-up work if the fault-1 fix turns
  out not to cover it in practice.
- `--prune` on the fetch call — surveyed and found not to address the
  observed failure; not worth the added remote round-trip cost for no
  behavior change.
- Any change to `#325`, `#414`, `#392`, or `#412` (issue's own Boundary
  section — different mechanisms, same class).
- Rewriting `ledger_write`/the ledger format itself.

## How you'll know it worked

- `test_spawn_fault_428.py` passes and is run (not just written): it
  drives `checkout_issue_branch()` through create → commit → push →
  merge-into-base → delete-remote-branch → respawn-with-same-workspace,
  and asserts the respawned branch is fresh (0 pre-existing commits, not
  the stale merged tip) and that a subsequent commit + PR-create path
  succeeds against a real local git remote.
- A forced `outcome = "silent-failure"` / `"refused"` run shows the `gh
  issue comment` call fired (stubbed `gh`, asserted invocation + body
  content), demonstrating the outcome is no longer print-only.
- `python3 -m pytest -q --ignore=gates` run clean on the branch (main's
  `gates/` subtree does not collect per #398 — reported as not run, not
  silently skipped).
