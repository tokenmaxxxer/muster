# Survey — issue-466 (class-B: #374 stop-hook, #428 respawn branch fix)

## Scope surveyed

`gh issue view 466` (full text, no comments); the #464 ADR
(`docs/issue-464/decisions/2026-08-08-board-state-into-orchestrator-loop.md`);
the #374 phase-1 proposal
(`docs/issue-374/proposals/2026-08-07-decision-queue-stop-hook-nudge.md`);
the #428 phase-1 proposal and survey
(`docs/issue-428/proposals/2026-08-07-respawn-after-merge-and-silent-outcome.md`,
`docs/issue-428/reports/implementation/survey.md`); `spawn.py`
(`checkout_issue_branch`, `ensure_pushed`, `_spawn_one`, `roster_watchdog`,
`_auto_respawn_check`, `_respawn_or_cap`); `gates/flows.py`'s
`decision_queue` block; `on-the-record/hooks/hooks.json` and every hook
script + its test under `on-the-record/hooks/`; `docs/issue-441/**` and
`docs/issue-58/**` (the two repro shapes named in issue #466's body) and,
because #58 turned out not to match, `docs/issue-60/**` and the
`ensure_pushed()` code comment that cites a real matching incident.

## What exists today

### #374 — decision queue has no floor

`gates/flows.py` already computes `decision_queue` correctly (confirmed
by the #374 survey referenced inside its own proposal): each entry has
`issue`, `pr`, `phase`, `role`, `opened_at` (PR `createdAt`), `age_hours`
(via `_age_hours()`), `awaiting`. Nothing reads this list except a human
running `spawn.py flows --json` by hand, or `spawn.py flows`'s own
`print(f"decision_queue: {len(...)}건")` printer (`gates/flows.py:453-454`)
— also human-pull, not push. There is **no hook** in
`on-the-record/hooks/hooks.json` on the `Stop` event that reads it; the
existing `Stop` entries are `stop-gate.sh` (structural check on the
orchestrator's own last message, issue #411) and
`role-test-claim-guard.sh` — neither touches `decision_queue`. The #374
proposal (`docs/issue-374/proposals/2026-08-07-...md`, `status: proposed`
in its frontmatter) designed a `decision-queue-nudge.sh` Stop hook in
full — two age tiers (`age_hours >= 1` → non-blocking
`additionalContext`, `age_hours >= 4` → `decision: "block"`), reusing
`directive.sh`'s checkout-resolution probe order, `ORCHESTRATE_OFF` and
`CLAUDE_ROLE` gates, and a `test_decision_queue_nudge.py` test file name.
That script, its test, and the `hooks.json` wiring were never written —
confirmed: `on-the-record/hooks/` has no `decision-queue-nudge.sh` or
`test_decision_queue_nudge.py`, and `hooks.json`'s `Stop` array has only
the two entries named above. This is exactly the #464 ADR's framing:
"#374 a Stop-hook (currently only proposed)."

Issue #466's acceptance names a **different** test file than the #374
proposal planned: `on-the-record/hooks/test_decision_queue_stopgate.py`
(not `test_decision_queue_nudge.py` at the repo root). The mechanism the
#466 proposal below plans reuses the #374 design's content wholesale but
targets #466's own acceptance filename and location.

### #428 — respawn inherits a dead branch

`checkout_issue_branch()` (`spawn.py:3023-3049`, confirmed by direct
read) does, in order:
1. `git rev-parse --verify -q issue-<n>/<role>` (local) exists →
   `git checkout` it unconditionally (`spawn.py:3034-3035`) — **no check
   that it is already fully merged into base**.
2. elif `origin/issue-<n>/<role>` exists → track it fresh
   (`spawn.py:3036-3041`).
3. else → branch fresh from base (`spawn.py:3042-3046`).

This is called from `_spawn_one()` at `spawn.py:3239` right after
`issue_workspace()` reuses the existing local clone (respawn path) and
`_acquire_spawn_claim()`. The #428 survey
(`docs/issue-428/reports/implementation/survey.md`) already reproduced
the mechanism directly with real git (clone → commit → push → merge into
base → delete remote branch → respawn onto the **same reused
workspace**): the local branch survives `--delete-branch` (that flag only
removes the *remote* branch), `git rev-list --count base..branch` is `0`
against it, and `checkout_issue_branch()` reuses it anyway — the
subsequent `ensure_pushed()` → `gh pr create` then fails with GitHub's
own "No commits between main and issue-<n>/<role>" once no new commits
land. The #428 proposal's planned fix (never implemented — confirmed:
`checkout_issue_branch()`'s current body at `spawn.py:3023-3049` has no
`rev-list`/merged check, and `test_spawn_fault_428.py` does not exist
anywhere in the repo) was: before reusing a local branch, check
`git rev-list --count <base>..<branch>`; if `0`, delete the stale local
branch and fall through to the fresh-from-base path.

`docs/issue-441/reports/execution-observation.md` documents this exact
failure live, not hypothetically: a second approval on issue-441
(2026-08-08T08:07:17Z) triggered a respawn onto `issue-441/architecture`,
which had already been merged (`d289d33`) and reset to `main`; the
`stranded-relay` system message at 08:08:40Z reads "No commits between
main and issue-441/architecture" — this is the live repro instance of
the mechanism the #428 survey reproduced synthetically. This is the
"issue-441 (stale branch equal to main, PR-create fails with 'no
commits')" shape named in #466's acceptance.

**Discrepancy found**: #466's body also names "issue-58 (branch+PR
already existed, silent failure)" as a second repro shape. Read directly:
`docs/issue-58/**` in this repo is about an unrelated issue —
`WebSearch`/`WebFetch` domain allowlisting (`WEB_ACCESS_DOMAINS`,
`role_settings()`), not branch/PR handling at all. `docs/issue-60/**` is
also unrelated (repo-level default `--model` config). Neither matches
"branch+PR already existed, silently." The closest real match found in
this repo is a code comment, not a docs/ folder: `ensure_pushed()`'s own
docstring (`spawn.py:3091-3093`) states the actual incident this exact
bug caused: `gh pr view <branch>` (used to decide whether to skip PR
creation) matches even a **merged past PR** of the same branch name, so
after a phase-1 PR merges, a phase-2 respawn's commits land with no PR
opened at all — "실측: #60 머지 후 phase 2 커밋이 PR 없이 남았다." The
comment cites issue #60, and `docs/issue-60/**`'s actual content does not
match either (that folder is about `--model` defaults, likely re-used
for two different real changes over the repo's history, or the comment's
"#60" is itself a mis-citation carried forward). `ensure_pushed()`
already carries the fix for *this exact* mechanism today — it filters
`gh pr list --head <branch> --state open` (only counts **open** PRs,
`spawn.py:3094-3097`), with the comment explicitly recording why: "머지된
과거 PR(phase 1)도 잡아서, phase 2 의 새 PR 생성을 조용히 건너뛰게 했다."
So the "branch+PR already existed, silent failure" shape is already
fixed in `ensure_pushed()`'s current code — there is no live gap left to
reproduce there matching that description under that mechanism.
Given issue #466's acceptance criterion is generic ("Respawn onto a
merged/deleted branch is detected and handled loudly" — no issue number
named in the acceptance line itself, only in the body prose), the phase-1
proposal below treats issue-441's shape as the primary, verified repro,
and treats "issue-58" as a naming discrepancy to flag rather than force
a synthetic second repro onto unrelated docs content — see the proposal's
Constraints section.

The #428 proposal's second half (surfacing `silent-failure`/`refused`
outcomes via `gh issue comment`, spawn.py's outcome block around
`spawn.py:3572-3637`) is **out of scope for #466** — #466's acceptance
text only asks for the branch-detection fix, not outcome-surfacing; the
#464 ADR's #428 row also only says "spawn.py fix plus an
on-the-record/hooks/** consumer-facing equivalent," matching the
branch-detection half only.

## Write set (frozen for the proposal)

- `on-the-record/hooks/decision-queue-stopgate.sh` (new) — the Stop hook
  script, same shape as the #374 proposal's planned
  `decision-queue-nudge.sh` (checkout resolution reused from
  `directive.sh`'s probe order, `ORCHESTRATE_OFF`/`CLAUDE_ROLE` gates,
  two-tier age logic reading `spawn.py flows --json`'s `decision_queue`).
- `on-the-record/hooks/hooks.json` — add one entry to the existing `Stop`
  array (alongside `stop-gate.sh`, `role-test-claim-guard.sh`).
- `on-the-record/hooks/test_decision_queue_stopgate.py` (new) — the
  red-green pair named in #466's acceptance, fixture-based like
  `on-the-record/hooks/test_pr_preflight.py`/`test_contract_guard.py`.
- `spawn.py` — `checkout_issue_branch()` (currently `spawn.py:3023-3049`):
  add the merged-branch detection (`git rev-list --count base..branch`)
  before step 1's unconditional reuse.
- `test_spawn.py` (repo root, existing file, ~confirmed present via
  `find`) — new test cases reproducing the issue-441 shape (stale local
  branch fully merged into base, respawn must not reuse it) using real
  local git fixtures, the same style as the #428 survey's manual
  reproduction and matching `test_spawn.py`'s existing pattern (e.g. its
  `PackageRegistryAccess` test class shape, confirmed present from the
  issue-58 coding record).
- `docs/issue-466/reports/implementation/*`, `docs/issue-466/proposals/*`
  — this survey, the scout-brief, and the phase-1 proposal.

## Open unknowns / gaps carried into the proposal

1. **"issue-58" repro naming discrepancy** — see Discrepancy above;
   resolved in the proposal by scoping the respawn test cases around the
   issue-441 shape (verified) and, for a second case, the still-live gap
   the #428 survey names as Fault 1's residual: a stale **local** branch
   equal-to-base at respawn time, independent of which specific past
   issue number first exposed it. If the human wants a literal
   `issue-58`-shaped scenario constructed, that needs their clarification
   — not guessed at from unrelated docs.
2. Whether `on-the-record/hooks/test_decision_queue_stopgate.py` should
   invoke `spawn.py flows --json` against a live repo (as the #374
   proposal's test plan did) or purely against a stubbed/fixture
   `decision_queue` list — the #466 acceptance line only says "red-green
   pair," not live-repo verification; phase-2 should decide based on
   whether a live-repo assertion is stable enough for CI (the #374
   proposal's own live case was checked manually, not asserted in CI).
3. Whether the #428 fix's stale-branch deletion needs an explicit
   `--force` guard or confirmation before `git branch -D` — not covered
   in the #428 proposal's "What will be done" beyond "delete the stale
   local branch"; phase-2 should specify the exact git call.
