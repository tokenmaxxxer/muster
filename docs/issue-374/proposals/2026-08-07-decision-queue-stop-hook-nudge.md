---
status: proposed
files:
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/decision-queue-nudge.sh
  - test_decision_queue_nudge.py
  - protocol.md
  - protocol.ko.md
---

## Request

Items waiting on an operator decision (`gates/flows.py`'s
`decision_queue`) have no floor and no clock: nothing ages them,
nothing surfaces them, and the orchestrator can start unlimited new
work while they sit unread. Ten such items are live right now, oldest
4.7 hours. The data is already computed correctly (confirmed by
survey.md, which also rules out the queue under-reporting #289/#290/#301
— all three already carry a valid approval comment and are correctly
excluded). The fix is making the existing, correct data reach the
operator, not computing anything new.

## Constraints

- No new dependency, no new persisted state file, no schema change to
  `decision_queue` — `opened_at`/`age_hours` already exist and are
  already correct (issue's own framing: derived, not tracked).
- Must not require the orchestrator to opt in by remembering a step —
  the same failure mode (a written instruction nobody reads) already
  exists today as prose in `directive.sh` and was proven not to work.
- Must not turn every wait into an alarm (issue item 4): a queue item
  is normal operation, not a failure, until it has waited long enough
  that silence about it becomes the failure.
- Two-account/APPROVE-comment approval semantics (contract v3 s19) are
  out of scope — not touching `_pr_approved()`.

## Rationale

**Alternative considered and rejected: block the orchestrator from
starting new work whenever `decision_queue` is non-empty (a hard
gate, e.g. via `PreToolUse` on the role-spawning tool call).**
Rejected. `decision_queue` being non-empty is the *normal steady
state* of this system, not a fault condition — new proposals arrive
continuously and each takes real operator time to review; a hard block
would stall unrelated, time-sensitive new work behind an old item the
operator simply hasn't gotten to yet, and would give the operator no
way to say "I saw it, keep going" short of clearing the whole queue.
That inverts issue item 4's own framing ("an item waiting on them is
not a failure — it is the system working") into treating it as one.
The issue explicitly asks this trade-off to be argued, not assumed
either way — argued here: surfacing wins over blocking because the
actual defect named in the issue is invisibility ("nothing surfaces
it"), not unlimited-throughput ("nothing stops it"). A block also adds
a second unenforced human step (someone has to positively clear a
gate) exactly where this issue is trying to remove one.

**Alternative considered and rejected: a periodic/cron digest (e.g. a
`spawn.py watchdog`-tick email or Slack summary) instead of a Stop
hook.** Rejected because it requires new infrastructure (a delivery
channel, a schedule) this repo does not have, and because it decouples
the nudge from the moment it's actionable — the operator needs to see
the queue in the same conversation where they're about to approve the
next twenty issues, not in a side channel they may not be watching.
The Stop hook surfaces it exactly where the failure happened: inside
the orchestrator's own reply loop.

**Chosen approach: a `Stop` hook that reads `decision_queue` on every
orchestrator turn and injects a non-blocking reminder once items cross
an age threshold, escalating to a blocking `decision: "block"` only
past a second, much longer threshold.** This reuses the exact
mechanism `directive.sh` already established for `UserPromptSubmit`
(read live state, inject fresh text every turn, `ORCHESTRATE_OFF`
kill switch, `CLAUDE_ROLE` early-exit so a spawned role session never
triggers it) — the only change is the event (`Stop` instead of
`UserPromptSubmit`) and the data source (`spawn.py flows --json`
instead of static guidance text). Two tiers, not one, address item 4
directly:
- `age_hours >= 1` (below `WATCHDOG_SILENCE_MIN`'s 90-minute
  session-silence threshold, spawn.py:1472, chosen deliberately lower
  since a decision-queue item has no running session to also catch it)
  → `additionalContext` reminder, non-blocking: the orchestrator's next
  reply is not forced to change, but the queue is now in its context
  the same turn it would otherwise start something new.
- `age_hours >= 4` (matches the oldest item observed in the issue,
  4.7h, and in today's re-run, still 4.7h — the point at which a full
  day like the one the issue describes is clearly underway) →
  `decision: "block"` with `reason` naming the stale items by
  issue/PR/age, forcing one more turn where the orchestrator must
  address the queue in its reply before continuing. This is the one
  point where blocking is justified: not "any queue," but "a queue
  that has been silently aging for hours," which is what actually
  happened in the incident this issue documents.

## What will be done

- Add a `Stop` entry to `on-the-record/hooks/hooks.json`.
- Add `on-the-record/hooks/decision-queue-nudge.sh`: resolve the
  checkout the same way `directive.sh` does (reuse its resolution
  order rather than reimplementing it — extract the shared logic if a
  clean extraction is in scope; otherwise duplicate the same probe
  order, since duplicating four `if` checks is cheaper than
  introducing a shared-lib file this plugin doesn't otherwise have),
  run `python3 <checkout>/spawn.py flows --json -C <repo>` for the
  current repo, parse `decision_queue`, apply the two-tier logic
  above, and emit the correct hook JSON (`additionalContext` for tier
  1, `decision: "block"` + `reason` for tier 2). Empty queue or all
  items under 1h → hook exits 0 with no output, same as `directive.sh`
  exiting quietly. `ORCHESTRATE_OFF` and `CLAUDE_ROLE` gates carried
  over unchanged.
- Add `test_decision_queue_nudge.py`, following `test_flows.py`'s
  existing fixture-based pattern for `decision_queue`-shaped input,
  covering: empty queue (no output), one item under 1h (no output),
  one item in [1h, 4h) (additionalContext present, mentions the
  issue/PR/age), one item >= 4h (block decision, reason names the
  item), `ORCHESTRATE_OFF` kill switch, `CLAUDE_ROLE` early-exit. Also
  run the hook against the live repo (`spawn.py flows --json` against
  this actual checkout, not a fixture) once and confirm the ten live
  items surface — the issue asks explicitly for this and it is the
  acceptance artifact per #310 (see below).
- Add one paragraph to `protocol.md`/`protocol.ko.md` stating the
  contractual expectation this hook now enforces mechanically: a
  `Stop`-blocked turn on a stale decision-queue item must be answered
  by addressing the queue (approve, defer explicitly, or state why not
  yet) before continuing new work, mirroring the existing
  `directive.sh`-sourced "re-anchor what's waiting on you" instruction
  so the prose and the mechanism state the same rule.

## Out of scope

- Fixing `#290`'s post-approval-rejection state (found during the
  survey; belongs nearer #371, not this issue).
- Any change to `_pr_approved()`, `gates/flows.py`'s `decision_queue`
  computation, or its schema — confirmed correct and sufficient as-is.
- Batching/risk-classifying the queue for the operator (#319's scope).
- A persisted "queue was read" acknowledgment log — the Stop hook
  re-reads live state every turn; there is nothing to persist.
- Any change to how role-spawning itself is gated (no `PreToolUse`
  block on `spawn.py <role>` calls) — the trade-off argued above lands
  on surfacing, not blocking new work at the spawn point.

## How you'll know it worked

- `test_decision_queue_nudge.py` passes, covering both tiers, the
  empty case, and both kill switches — an executable artifact per
  #310, not prose.
- The same test's live-repo case, run against today's real state,
  shows the hook actually flagging the currently-live decision-queue
  items (ten today, oldest 4.7h) — the issue's own acceptance
  condition ("those ten flows are live and must appear").
- Manually toggling `ORCHESTRATE_OFF=1` and re-running the hook script
  produces no output, confirming the kill switch still works on the
  new event the same way it works on `UserPromptSubmit`.
- Generator (per #363): the two age thresholds (1h, 4h) and the tier-2
  block message are hand-written in `decision-queue-nudge.sh` from the
  values in this proposal — not generated from a template — so the
  generator is "fixed": the script and its test are read directly,
  not regenerated from a spec at test time.
