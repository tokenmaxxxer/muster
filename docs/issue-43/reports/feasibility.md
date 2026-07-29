---
subject: issue-43
role: feasibility
status: verdict-recorded
loop_state: verdict-recorded
verdict: conditional-go
market_argument_supplied: false
---

# issue-43 — feasibility: phase-2 verdict record

This is the board record for the feasibility role on issue #43 (per role-handoff contract v3
s19, WAKES-ON reads only this file). Phase-1 artifacts (survey and proposal) live under
`docs/issue-43/reports/feasibility/survey.md` and `docs/issue-43/proposals/feasibility.md`; this
file is the authoritative summary and verdict, not a replacement for them.

## what-was-done

Phase 2 of the feasibility role for issue #43: recorded this formal board record with the
resolved probes, reversibility classification, honest coverage gaps, verdict, conditions, and
measurement design, following the human approver's `APPROVE issue-43/feasibility` review comment
on PR #45.

## why

Phase 1 (survey + proposal, PR #45) produced the evidence and recommendation; the role-handoff
contract v3 requires the approved recommendation to be transcribed into this single board record
(`docs/issue-43/reports/feasibility.md`) because WAKES-ON reads only this file, not the phase-1
proposal/survey files, to drive the next step (opening the design issue).

## upstream-basis

- `docs/issue-43/reports/feasibility/survey.md` — six-angle survey, phase 1.
- `docs/issue-43/proposals/feasibility.md` — mechanism comparison, candidates, recommendation,
  reversibility analysis, phase 1.
- PR #45 review comment: `APPROVE issue-43/feasibility` (JiwonJung94), authorizing phase 2.
- `wakes.py` on `main` (read, not modified) — the existing state-diffing/`HUMAN_ONLY` model the
  technical probe and threat-model probe are evaluated against.

## next-steps

- Open the design issue for the orchestrate procedure per issue #43's stated phase-2 deliverable
  ("If this report is approved, a separate design issue for the orchestrate procedure follows"),
  carrying forward the four conditions listed below.
- Re-verify the three unverified survey angles (Devin/Cursor/Copilot Workspace, OpenHands/
  SWE-agent, AutoGen/CrewAI/LangGraph) with search access, before the design issue finalizes its
  mechanism choice (condition 4).

## open-finding-resolution-path

The one open finding carried forward — whether LangGraph's `interrupt()`/checkpointer pattern is
analogous to `wakes.py`'s sig-hashed state-diffing model — is not a blocker on this verdict (see
Honest coverage gaps below) but must be resolved by the design issue's own research phase before
that issue finalizes its mechanism choice, as condition 4 states. If re-verification confirms the
analogy, it strengthens the external precedent; if it refutes it, the design issue proceeds on
muster's own internal evidence (GitHub PR queues, HCI literature) alone, which this verdict
already treats as sufficient.

## market_argument_supplied: false

Stated explicitly, per the feasibility role directive: the issue's own motivating argument
(that a mission board / decision-queue batching / parking lot would make muster more usable) was
deliberately withheld from the research and proposal work in phase 1, and is withheld here too.
The verdict below rests only on the survey evidence and muster's existing architecture, not on
the issue author's stated preference for those three mechanisms.

## Phase-2 approval

PR #45 ("docs(issue-43): feasibility phase-1 — HITL orchestration mechanism survey") received an
`APPROVE issue-43/feasibility` review comment from the human approver (JiwonJung94), authorizing
phase 2 of the feasibility role: recording this formal verdict.

## Probes

- **technical**: pass — muster's `wakes.py` (main branch) already implements the durable-state,
  state-diffing wake pattern that the survey's strongest evidence (GitHub PR review-queue
  conventions, HCI situation-awareness literature) converges on: a `sig` (content hash of the
  evidence files under `docs/issue-<n>/reports/<role>.md`) per wake row, evaluated mechanically
  off files rather than conversation content, plus a hard-coded `HUMAN_ONLY` table the evaluator
  refuses to automate. All three proposed candidates (mission board, decision-queue batching,
  parking lot) are additive to this existing model — a read view, a presentation-layer batching
  UI, and an additional doc file, respectively — none requires new automation of a human decision
  or a second source of truth competing with `wakes.py`'s file-based ground truth.
- **prior_art**: pass — of the six surveyed angles, two returned fully verified findings without
  needing live search: GitHub PR review-queue conventions (draft PRs, `review-requested:@me`
  batching, digest notifications, issue-linking pinning the original ask, a stateful list keyed
  by item) and HCI situation-awareness literature (Endsley's L1/L2/L3 model, Sheridan's levels of
  automation, vigilance decrement, interruption/resumption cost, multi-agent fan-out). These are
  also the two angles most directly load-bearing for muster, since muster's human decisions are
  already GitHub PR acts. See the coverage gap below for the three angles that did not return
  verified findings.
- **legal_regulatory**: pass — no new data collection, no new external dependency, no new runtime
  or deploy surface identified anywhere in phase 1 (survey.md s"Deploy/runtime config surface").
  This is a docs/process change (a proposed design issue), not a product or data-handling change,
  so no regulatory exposure was found to investigate.
- **threat_model**: pass — the proposal's own reversibility analysis (see below) is the threat
  containment argument: every candidate mechanism is additive and cannot become a bypass for the
  `HUMAN_ONLY` gate. The specific failure mode considered was a batching UI silently becoming a
  bulk-approve action, which would violate the "silence is not consent" / no-inferred-approval
  rule already in the role-handoff contract; the proposal's second condition (below) exists
  specifically to force the design issue to rule this out explicitly before implementation.

## Reversibility (technical finding)

Two-way door, high reversibility. All three candidate mechanisms are reversible without data
loss: a mission board is a read view (deletable), decision-queue batching is a presentation
layer over still-individual PR Approve acts (revertible to per-item flow), and a parking lot is
an additional doc file (droppable). This reversibility is the basis for a conditional-go verdict
on evidence gathered by survey rather than requiring a working spike/prototype before
recommending the design issue proceed.

## Honest coverage gaps

Three of the six survey targets — Devin/Cursor/Copilot Workspace plan-approval UIs,
OpenHands/SWE-agent event streams, and AutoGen/CrewAI/LangGraph human-in-the-loop checkpoints —
returned **no verified findings**. The research subagents' sandbox had WebSearch denied during
phase 1, so nothing beyond general/product-marketing-level awareness could be reported for these
three angles without fabricating specifics; the survey and proposal both flagged this explicitly
rather than presenting unverified claims as findings.

Specifically unverified:
- Whether Devin/Cursor/Copilot Workspace offer any cross-task queue view enabling a human to
  batch approvals across concurrently running agent sessions.
- Whether OpenHands/SWE-agent have any first-class multi-session supervisory dashboard beyond a
  single-agent-per-session confirmation gate.
- Whether LangGraph's `interrupt()`/durable-checkpointer pattern is actually analogous to
  `wakes.py`'s sig-hashed state-diffing wake model — this is the single most consequential
  unverified claim, since if confirmed it would be the strongest external precedent for the
  approach muster already takes, and if refuted it would mean muster's design has no confirmed
  external analogue at all.

Residual risk: the recommendation below does not rely on these three angles as evidence — the
two verified angles (GitHub PR queues, HCI literature) already independently support the
verdict. The risk carried forward is narrower: the design issue could still discover, once these
angles are re-verified with search access, a materially better or already-solved pattern (most
likely from LangGraph) that changes the *design*, even though it would not change this
feasibility verdict. This is why re-verification is a condition on the design issue, not a
blocker on this verdict.

## Verdict: CONDITIONAL-GO

Conditional go on opening the design issue for the orchestrate procedure (issue #43's stated
phase-2 deliverable), with the following conditions carried over from the approved proposal:

conditions:
- Design must specify the mission board strictly as a read view over existing report files — no
  new mutable state that competes with `docs/issue-<n>/reports/<role>.md` as ground truth.
- Design must show decision-queue batching cannot merge into, or substitute for, individual PR
  Approve acts — batching is UI aggregation only, never a bulk-approve action.
- Design must define parking-lot to issue-promotion criteria explicitly, or drop the parking lot
  in favor of filing a new issue immediately (simpler, already supported by the existing
  issue-per-unit-of-work model).
- The design issue must re-run the three unverified survey angles (Devin/Cursor/Copilot
  Workspace, OpenHands/SWE-agent, AutoGen/CrewAI/LangGraph) with search access before finalizing
  its mechanism choice, specifically to confirm or refute whether LangGraph's
  `interrupt()`/checkpointer pattern is directly analogous to `wakes.py`'s sig-hashed
  state-diffing wake model.

## Measurement design

As promised in the proposal, once any of the three candidate mechanisms is implemented from the
design issue, the following events should be collected to evaluate whether it delivers on the
survey's three original questions (wait-time productivity, drift guarding, status visibility):

- **Mission board**: page/view load events (who queried it, when, over which subset of open
  issues) and staleness of the underlying `loop_state`/report files at query time — collected as
  a log line wherever the view is rendered, keyed by issue number and role, sourced from the same
  files `wakes.py` already reads so no new state store is introduced.
- **Decision-queue batching**: count and latency of individual PR Approve acts per human batch
  session (session = a contiguous span of Approve actions with no other GitHub activity between
  them) — derivable from existing GitHub PR review timestamps, no new instrumentation needed;
  used to check the batching UI is not collapsing into fewer, larger approvals than individual
  human judgments would produce.
- **Parking lot**: count of entries logged vs. entries promoted to a new issue vs. entries that
  went stale/unaddressed, recorded in the parking-lot doc file itself (append-only log with
  timestamp and disposition), reviewed periodically to check the promotion criteria (condition 3
  above) are actually being applied rather than left to accumulate.

All three measurement sources are file- or GitHub-API-derived, consistent with muster's existing
"ground truth lives in files/PR state, not in a separate telemetry system" convention.
