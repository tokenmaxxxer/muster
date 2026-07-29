# issue-43 — proposal: mechanism comparison and recommendation

market_argument_supplied: false

## Mechanism comparison

| System | Wait-time handling | Drift guard | Status visibility | Durable state (vs. blocking call) |
|---|---|---|---|---|
| Claude Code (TodoWrite, background tasks, Workflow) | agent-side async only; no human batching | todo list synced to real state; no immutable goal artifact | session-scoped todo table | no — resumes agent's own thread, not external state |
| Devin/Cursor/Copilot Workspace | unverified (search unavailable) | unverified | unverified | unverified |
| OpenHands/SWE-agent | unverified (search unavailable) | unverified | unverified | unverified |
| AutoGen/CrewAI/LangGraph | unverified (search unavailable); LangGraph `interrupt()`/checkpointer widely *reputed* to persist pause state, unconfirmed here | unverified | unverified | unconfirmed |
| GitHub PR review queue | draft PRs + batched `review-requested:@me` + digest notifications | issue-linking (`Closes #43`) pins original ask through all review rounds | stateful list keyed by item, not by time | yes — queue state lives in GitHub, not in a conversation |
| HCI / situation-awareness literature | idle wait is not neutral — vigilance decrement; batch non-urgent interrupts at decision boundaries | n/a (theory, not a system) | Endsley L1/L2/L3 — most systems above only reach L1 | n/a |
| muster (`wakes.py`, current) | none — human wakes are ad hoc per issue | none beyond the issue text itself | none cross-issue; per-role report files only | yes — sig-hashed board state, human-only gates hard-coded |

Three of six survey targets returned **no verified findings** because the research subagents'
sandbox denied WebSearch. This is reported as a gap, not glossed over. The two angles that
returned full evidence (GitHub PR queues, HCI literature) are the ones most directly load-bearing
for muster anyway, since muster's human decisions are already GitHub PR acts and its wake
mechanism is already a state-diffing evaluator, not a chat parser.

## Candidates compatible with muster's contract (human-only approval, board-driven wakes)

Evaluated as hypotheses, including the three floated in conversation — none accepted here as a
conclusion; all still need the design issue's own scrutiny.

1. **Mission board (cross-issue aggregate view)** — a generated read-only view over
   `docs/issue-*/reports/*.md` and `loop_state` fields, rendering "what did I request, where does
   each stand" in one place. Directly answers survey question 3. Compatible with the contract
   because it is a *view*, not a new state store — it reads what `wakes.py` already treats as
   ground truth, so it cannot itself become a second source of truth or a bypass for the
   human-only gates. Matches the PR-review-queue angle's core lesson (a stateful list keyed by
   item beats a stream keyed by time) and the HCI angle's Level-1 gap.

2. **Decision-queue batching** — grouping multiple pending human-only gates (approve, findings-
   resolved re-check, round-done value gate) so a human processes several in one sitting, mirroring
   `review-requested:@me` batch review and the interruption-cost literature's "batch at decision
   boundaries" finding. Risk: muster's `HUMAN_ONLY` table already refuses automation of these
   gates by design (`wakes.py` s`HUMAN_ONLY`) — a batching UI must remain a presentation layer over
   still-individual GitHub PR Approve acts, never a bulk-approve action, or it would violate the
   "silence is not consent" / no-inferred-approval rule already in the role-handoff contract.

3. **Parking lot for side-discoveries** — a place to log findings that arrive off-goal during
   parallel agent runs without letting them alter the active goal inline, addressing survey
   question 2 (drift). Matches the Claude-Code angle's identified gap (no immutable goal artifact
   separate from the mutable todo/board) and the SA literature's Level-2 comprehension need
   (flagging contradictions/off-scope items rather than silently merging them into the record).
   Needs a explicit rule for when a parked item should be promoted to a new issue rather than
   pulled into the current one, or it just becomes a second unbounded todo list.

No candidate here requires a new automation of a human decision; all three are compatible with
`wakes.py`'s existing separation of mechanically-judged rows from `HUMAN_ONLY` rows.

## Recommendation

**Conditional go** on opening the design issue for the orchestrate procedure, with conditions:

- Design must specify the mission board strictly as a read view over existing report files —
  no new mutable state that competes with `docs/issue-<n>/reports/<role>.md` as ground truth.
- Design must show decision-queue batching cannot merge into, or substitute for, individual PR
  Approve acts — batching is UI aggregation only.
- Design must define parking-lot → issue promotion criteria explicitly, or drop the parking lot
  in favor of just filing a new issue immediately (simpler, already-supported by the existing
  issue-per-unit-of-work model).
- Re-run the three unverified survey angles (Devin/Cursor/Copilot Workspace, OpenHands/SWE-agent,
  AutoGen/CrewAI/LangGraph) with search access before the design issue finalizes its mechanism
  choice, specifically to confirm or refute whether LangGraph's `interrupt()`/checkpointer pattern
  is directly analogous to `wakes.py`'s sig-hashed state-diffing wake model — if confirmed, it is
  the strongest external precedent for the approach muster already takes.

## Reversibility

All three candidate mechanisms are two-way doors: a mission board is a read view (deletable with
no data loss), decision-queue batching is a presentation layer (revertible to per-item flow), and
a parking lot is an additional doc file (droppable). This is why the verdict above is conditional-
go rather than requiring a full spike: reversibility of every candidate is high, so evidence bar
is the survey above, not a working prototype.
