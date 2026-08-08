---
status: proposed
files:
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_decision_queue_stopgate.py
  - spawn.py
  - test_spawn.py
  - docs/issue-466/reports/implementation.md
---

## Request

Deliver the two class-B "shipped-hook" rows the #464 ADR
(`docs/issue-464/decisions/2026-08-08-board-state-into-orchestrator-loop.md`)
scheduled as follow-up: (1) #374 — the decision-queue Stop-hook the
2026-08-07 proposal only described, never built; (2) #428 — a respawned
session that inherits a merged/deleted prior branch and silently starts
empty, with a `spawn.py` fix plus a consumer-facing
`on-the-record/hooks/**` equivalent. Both already have full phase-1
design work sitting unbuilt in this repo's own history
(`docs/issue-374/proposals/2026-08-07-decision-queue-stop-hook-nudge.md`,
`docs/issue-428/proposals/2026-08-07-respawn-after-merge-and-silent-outcome.md`)
— this proposal's job is to carry that design into #466's acceptance
shape and file paths, not to redesign it. Full detail:
`docs/issue-466/reports/implementation/survey.md`,
`docs/issue-466/reports/implementation/scout-brief.md`.

## Constraints

- Two-phase contract: this issue lands phase 1 only (survey + this
  proposal); no `.py`/`.sh`/`.json` edit lands until an approver's
  Approve, per the `role-handoff` protocol.
- #466's acceptance names exact artifacts:
  `on-the-record/hooks/test_decision_queue_stopgate.py` wired into
  `on-the-record/hooks/hooks.json`, and `test/test_spawn.py` — the actual
  repo has this file at the root (`test_spawn.py`), not under `test/`;
  the write set above uses the real path, confirmed by `find`.
- #466's body names two respawn repro shapes: issue-441 (verified live in
  `docs/issue-441/reports/execution-observation.md`) and "issue-58." Read
  directly, `docs/issue-58/**` in this repo is the unrelated
  WebSearch/WebFetch-domain issue, not a branch/PR case — see survey.md's
  Discrepancy section. This proposal does not fabricate a synthetic
  issue-58 scenario against unrelated docs; it scopes the second test
  case to the still-general "stale local branch, zero commits ahead of
  base" shape the #428 survey already reproduced with real git (its
  `issue-999` fixture), independent of which issue number first exposed
  it, and flags the naming mismatch for the human to resolve if a
  literal issue-58 scenario is wanted.
- No new external dependency for either sub-item; `gh`/`git`/`python3`
  only, matching every existing hook and `spawn.py` itself.
- #428's outcome-surfacing half (`gh issue comment` on `silent-failure`/
  `refused`, the #428 proposal's item 2) is out of scope here — #466's
  acceptance text and the ADR's #428 row both only ask for the
  branch-detection fix.
- The Stop hook must not fire for spawned role sessions
  (`CLAUDE_ROLE` gate) and must respect `ORCHESTRATE_OFF`, matching every
  other orchestrator-only hook in the directory.

## Rationale

**#374 — event-driven Stop hook vs cron/timer-based polling.** Rejected
alternative: a periodic tick (e.g. a cron job or a `spawn.py watchdog`
polling loop) that emails/Slacks a digest of aged `decision_queue` items.
Rejected for the same reason the #374 proposal already argued and this
survey re-confirms: it requires new infrastructure this repo does not
have (a delivery channel, a schedule daemon) and decouples the nudge from
the moment it is actionable — the operator needs to see the stale queue
in the same conversation where they are about to spawn twenty more
issues, not in a side channel. The `Stop` hook fires exactly where the
failure happens (inside the orchestrator's own reply loop, right before
it would otherwise move on), reusing infrastructure (`hooks.json`'s
existing `Stop` array, `directive.sh`'s checkout resolver) that already
exists and is already tested elsewhere in the directory.

**#428 — auto-detect-and-start-fresh vs hard-fail vs prompt-the-user.**
Three shapes considered for what `checkout_issue_branch()` should do on
finding a local `issue-<n>/<role>` branch:
- *Hard-fail* (refuse to spawn, `sys.exit()`, if the local branch exists
  and is 0-ahead of base). Rejected: this converts a fully recoverable,
  common case (a routine respawn onto a just-merged issue) into a manual
  intervention every single time, for no benefit — there is nothing left
  to recover, the branch's content is already in `main`. It would also
  regress every ordinary two-round issue (phase 1 merges, phase 2
  respawns) into a blocked state.
- *Prompt-the-user* (pause and ask before deciding). Rejected: `_spawn_one`
  runs unattended in the orchestrator's automated loop; there is no
  synchronous human on the other end of this code path to prompt, and
  adding one would contradict the same "advisory shape already failed"
  reasoning the #428 proposal used to reject an advisory fix for its
  outcome-surfacing half.
- *Auto-detect-and-start-fresh* (check `git rev-list --count
  base..branch`; if `0`, delete the stale local branch and fall through
  to the existing fresh-from-base path) — **chosen**, because it is the
  behavior every other branch in `checkout_issue_branch()` already
  exhibits for the "nothing to resume" case (the `else` branch, line
  3042-3046), just reached correctly instead of masked by a false-
  positive "local ref exists = resume" check. It matches the codebase's
  own precedent (`roster_watchdog`/`_auto_respawn_check`'s
  classify-before-act pattern, scout-brief.md) rather than inventing a
  new failure mode, and it is loud by construction: a fresh branch means
  the next spawn message states "지금 브랜치는 방금 새로 만들어졌다" (or
  equivalent), not a silent no-op the operator has to notice via a
  GitHub PR-create-failed error hours later.

## What will be done

1. `on-the-record/hooks/decision-queue-stopgate.sh` (new): the #374
   proposal's `decision-queue-nudge.sh` design, renamed to #466's
   acceptance-named counterpart file. Same mechanism: resolve the
   on-the-record checkout via `directive.sh`'s existing probe order, run
   `python3 <checkout>/spawn.py flows --json -C <repo>`, parse
   `decision_queue`, apply the two age tiers (`age_hours >= 1` →
   `additionalContext` reminder naming the stale issue/PR/age,
   `age_hours >= 4` → `decision: "block"` forcing one more turn), stay
   silent (exit 0, no output) below tier 1 or on an empty queue. Kill
   switches (`ORCHESTRATE_OFF`, `CLAUDE_ROLE`) carried over unchanged.
2. `on-the-record/hooks/hooks.json`: add one entry to the existing `Stop`
   array, alongside `stop-gate.sh` and `role-test-claim-guard.sh`.
3. `on-the-record/hooks/test_decision_queue_stopgate.py` (new): a
   red-green pair following the directory's subprocess-driven convention
   (invoke the shell script with a crafted `STOP_PAYLOAD`/env, assert
   stdout+exit). Red case: an aged `decision_queue` fixture (one item
   under 1h, one in [1h,4h), one over 4h) drives the script through all
   three branches — asserting no output for the under-1h item alone, an
   `additionalContext` mentioning issue/PR/age for the 1-4h case, and a
   `decision: "block"` for the >=4h case; green case: an empty queue and
   the `ORCHESTRATE_OFF=1`/`CLAUDE_ROLE` set cases all produce clean exit
   0 with no output.
4. `spawn.py`'s `checkout_issue_branch()` (currently `spawn.py:3023-3049`):
   before the existing local-branch-exists branch (line 3034) reuses a
   local `issue-<n>/<role>` ref, add a check —
   `git rev-list --count <base>..<branch>`; if the count is `0` (branch
   fully absorbed into base), `git branch -D` it and fall through to the
   existing fresh-from-base path (line 3042-3046) instead of checking it
   out. A branch with any commit unique to it (genuinely in-progress
   work) is reused exactly as today — unchanged behavior for the common
   case. Print a stderr line naming what happened (branch was stale,
   started fresh) so the respawn is loud in the session log even before
   any PR-create step could fail.
5. `test_spawn.py`: two new red-green cases against real local git
   fixtures (same style as the #428 survey's manual reproduction —
   clone/branch/commit/push/merge-into-base/delete-remote-branch/
   respawn-onto-reused-workspace), calling `checkout_issue_branch()`
   directly, not shelling out: (a) the issue-441 shape — local branch
   fully merged into base, respawn must create a fresh branch, not check
   out the stale one, and a subsequent commit + `ensure_pushed()` call
   must succeed instead of hitting "No commits between main and
   issue-<n>/<role>"; (b) the general stale-branch shape from the #428
   survey's own `issue-999` fixture (0-ahead local branch surviving
   `--delete-branch`), asserting the same fresh-branch outcome — kept
   separate from (a) since it exercises the mechanism without depending
   on any specific past issue's history.

## Out of scope

- #428's `gh issue comment` outcome-surfacing half (the proposal's item
  2) — not named in #466's acceptance text.
- `--prune` on `_fetch_or_halt`'s fetch call — the #428 survey already
  found this does not address the actual (local-branch) culprit.
- Reworking `ensure_pushed()`'s open-PR filter (`spawn.py:3094-3097`) —
  already correctly fixes the "branch+PR already existed" mechanism per
  its own code comment (survey.md's Discrepancy section); nothing to
  change there.
- A literal issue-58-numbered fixture — flagged as a naming discrepancy,
  not fabricated; see Constraints.
- Any change to `decision_queue`'s computation or schema in
  `gates/flows.py` — the #374 proposal already confirmed it correct and
  sufficient as-is, unchanged by this proposal.
- Batching/risk-classifying the decision queue, or gating role-spawning
  itself on a non-empty queue — both explicitly out of scope per the
  #374 proposal's own Rationale, carried forward unchanged.

## How you'll know it worked

- `on-the-record/hooks/test_decision_queue_stopgate.py` passes and is
  wired into `on-the-record/hooks/hooks.json`'s `Stop` array — #466's
  own acceptance line for the first sub-item, verified by running the
  test file directly (not just present on disk) and by `hooks.json`
  containing the new entry.
- `test_spawn.py` gains and passes the issue-441-shaped and general
  stale-branch-shaped red-green cases described above, run via
  `python3 -m pytest test_spawn.py -q` — #466's acceptance line for the
  second sub-item ("gains red-green cases reproducing the issue-441 ...
  shape"; the issue-58 shape is addressed via the general case per the
  Constraints discrepancy note, pending human clarification if a literal
  issue-58 scenario is still wanted).
- Manually toggling `ORCHESTRATE_OFF=1` and re-running
  `decision-queue-stopgate.sh` against a live `decision_queue` produces
  no output, confirming the kill switch works on the new event the same
  way it works elsewhere in the directory.
- A respawn against a reused workspace whose local branch is already
  fully merged into base now logs a visible "started fresh" line and
  succeeds through to a real PR, instead of failing silently or with an
  opaque GitHub "no commits" error days later — the shape #466's body
  calls "detected and handled loudly."

Refs #466.
