# issue-64 — proposal: updated mechanism-comparison conclusions, mission-board disposition

market_argument_supplied: false

## What changed vs. #43

Condition 4 of #43's conditional-go ("re-run the 3 unverified angles before the design issue
finalizes its mechanism choice") is now satisfied — see
`docs/issue-64/reports/feasibility/survey.md` for full citations.

1. **Devin/Cursor/Copilot Workspace** — #43's specific claim ("none is publicly documented as
   offering a cross-task queue view") is **refuted**. All three now ship a multi-session
   dashboard: Devin's Agent Command Center (Kanban: Running/Waiting for review/Done), Cursor's
   multi-agent panel + List Agents API, GitHub's Agents tab. What survives from #43: **none of
   the three supports batched approval across sessions in one action** — every dashboard is a
   list/queue view over still-individual per-item approvals.

2. **OpenHands/SWE-agent** — #43's claim **stands, confirmed**: single-agent-per-session
   action/observation loops, human confirmation gates before actions, no shipped first-class
   multi-session supervisory dashboard in either project (OpenHands' own UI is capped at ~9
   recent conversations; queueing infra exists only as an open RFC). No content-hash/state-diff
   analogue to `wakes.py`'s `sig` was found in either.

3. **LangGraph `interrupt()`/checkpointer vs. `wakes.py`** — the single most consequential
   unverified claim resolves to **partially confirmed, effectively refuted on the two
   architecturally load-bearing points**: durable pause/resume matches, but (a) checkpoint
   identity is thread/sequence-keyed, not content-hash-keyed, so LangGraph has no analogue to
   `wakes.py`'s "don't re-wake on unchanged evidence," and (b) there is no framework-enforced
   `HUMAN_ONLY`-equivalent — HITL placement is entirely a developer's per-node choice, whereas
   `wakes.py` hard-codes two decision types the system itself refuses to auto-resolve. AutoGen and
   CrewAI show the same shape (durable-ish pause, no diffing) or weaker (AutoGen's default HITL
   doesn't persist at all).

## Does #43's verdict change?

**No.** #43's CONDITIONAL-GO rested on the two angles that needed no live search (GitHub PR queue
conventions, HCI situation-awareness literature) plus muster's own architecture — the three
now-reverified angles were explicitly excluded from that verdict's evidence base per #43's
"Honest coverage gaps" section, and the verdict said as much: confirmation would strengthen
external precedent, refutation would leave muster's design resting on its own internal evidence
alone, "which this verdict already treats as sufficient." That is the outcome that materialized —
the LangGraph analogy is at best a partial match, so `wakes.py`'s content-hash-diffing and
hard-coded `HUMAN_ONLY` gate remain a novel design with no confirmed external precedent, not
borrowed prior art. This does not weaken the verdict; it removes a hoped-for external validation,
which #43 already priced in as non-blocking.

## Mission-board design: proceed, shape informed by new evidence

**Proceed as designed**, with two evidence-based refinements to carry into the design issue:

- **Adopt**: the dashboard *shape* that Devin/Cursor/Copilot Workspace converged on
  independently — a status-grouped (running/waiting-for-review/done) list view across concurrent
  sessions — is now confirmed as the category's actual solved pattern for angle 1, not a gap.
  muster's mission-board (a read-only aggregate over `docs/issue-*/reports/<role>.md` and
  `loop_state`) already matches this shape; no redesign needed, but the design issue can cite
  these three tools as precedent rather than treating the shape as novel.
- **Skip, reinforced**: none of the six survey targets across #43 and #64 — not the three
  commercial coding agents, not OpenHands/SWE-agent, not AutoGen/CrewAI/LangGraph — has any
  documented mechanism for batching a human's approval decision across multiple items into one
  action. This reinforces #43's condition 2 (batching must stay UI aggregation, never a
  bulk-approve act) with an added data point: nobody in this survey has built cross-session
  batch-approve, commercial or open-source. The design issue should not treat "build batch-approve
  because competitors have it" as a live option — no competitor has it.

No condition from #43 is weakened or dropped; condition 4 is now closed (evidence attached above).
The remaining three conditions (mission board as pure read view, batching as aggregation-only,
explicit parking-lot promotion criteria or dropping the parking lot) carry forward unchanged into
the design issue.

## Reversibility

Unchanged from #43: two-way door, high reversibility. This issue changed no code and no runtime
surface; it only supplies evidence. The mission-board mechanism itself remains a deletable read
view as characterized in #43.

## Deploy/runtime config surface

None. No code or config change in this issue.
