---
status: verdict
loop_state: closed
market_argument_supplied: false
approved_by: 'PR #67, "APPROVE issue-64/feasibility" (2026-07-29)'
---

# issue-64 — feasibility record

## What was done

Re-ran, with live WebSearch/WebFetch access, the 3 of 6 #43 survey angles that #43 left
unverified: (1) Devin/Cursor/Copilot Workspace plan-approval and cross-task queue UIs, (2)
OpenHands/SWE-agent event streams and human checkpoints, (3) AutoGen/CrewAI/LangGraph HITL
checkpoints, with a direct confirm/refute call on whether LangGraph's `interrupt()`/checkpointer
pattern is analogous to `wakes.py`'s content-hash-diffing wake model. Findings and citations are
below; full per-claim sourcing is in `docs/issue-64/reports/feasibility/survey.md`.

## Why

Issue #58 (merged) enabled WebSearch/WebFetch for all roles, closing the sandbox limitation that
made #43 file these 3 angles as an explicit unverified gap (#43's condition 4: re-run before the
design issue finalizes its mechanism choice). This record closes that condition and re-confirms
or revises the mission-board disposition against the new evidence before the design issue starts.

## Upstream basis

- `docs/issue-43/reports/feasibility.md` (merged) — the CONDITIONAL-GO verdict and its 4
  conditions, condition 4 being what this issue closes.
- Issue #58 (merged) — WebSearch/WebFetch tool-permission grant that made this re-verification
  possible.
- `docs/issue-64/reports/feasibility/survey.md` and `docs/issue-64/proposals/feasibility.md`
  (this branch, phase 1, approved via PR #67 comment "APPROVE issue-64/feasibility") — the
  research and proposal this record formalizes.

## Scope

Follow-up to issue #43 (merged: `docs/issue-43/reports/feasibility.md`). #43's conditional-go
left 3 of 6 survey angles unverified because the sandbox denied web access at the time. Issue #58
(merged) enabled WebSearch/WebFetch for all roles; this issue re-runs the 3 unverified angles with
live web research and updates the mission-board disposition accordingly. Full citations:
`docs/issue-64/reports/feasibility/survey.md`. Full proposal reasoning:
`docs/issue-64/proposals/feasibility.md`.

## Re-verified angles

### 1. Devin / Cursor / Copilot Workspace — plan-approval UI, cross-task queue view

#43's claim: none of the three is publicly documented as offering a cross-task queue view.

**Refuted for all three.** All now ship multi-session dashboards:
- Devin's Agent Command Center — Kanban (Running / Waiting for review / Done).
  Source: https://devin.ai/desktop
- Cursor's multi-agent panel + `GET /v0/agents` "List Agents" API.
  Source: https://aitechfy.com/blog/cursor-background-agents/ (secondary — direct docs.cursor.com
  fetch redirected)
- GitHub's repo-level "Agents tab" + `gh agent-task view` CLI (Copilot coding agent, GA Sept 2025).
  Source: https://visualstudiomagazine.com/articles/2026/01/29/hands-on-new-github-agents-tab-for-repo-level-copilot-coding-agent-workflows.aspx
  (secondary reporting), 2026-01-29

**Survives, narrower**: none of the three supports batched approval across sessions in one
action — every dashboard is a list/queue view over still-individual per-item approvals.

### 2. OpenHands / SWE-agent — event streams, human checkpoints

#43's claim: single-agent-per-session action/observation loops with a confirmation-mode gate;
neither known to have a first-class multi-session supervisory dashboard.

**Confirmed.** OpenHands: append-only event stream, risk-tiered confirmation gate
(`UserRejectObservation`/"ConfirmRisky"), UI capped at ~9 recent conversations, queueing infra
exists only as an open RFC (#13275). Sources: https://docs.openhands.dev/sdk/arch/events ;
https://github.com/OpenHands/OpenHands/issues/7928 ; https://github.com/OpenHands/OpenHands/issues/13275.
SWE-agent/mini-swe-agent: append-only EventLog loop, per-action (not risk-tiered) confirmation
gate; no first-party supervisory dashboard (third parties — SWE-AF, LangChain's Open SWE — have
built one around it). Sources: https://github.com/swe-agent/mini-swe-agent/blob/main/src/minisweagent/agents/interactive.py ;
https://github.com/Agent-Field/SWE-AF ; https://www.langchain.com/blog/introducing-open-swe-an-open-source-asynchronous-coding-agent.
No content-hash/state-diffing analogue to `wakes.py`'s `sig` was found in either project.

### 3. AutoGen / CrewAI / LangGraph — HITL checkpoints vs. `wakes.py`'s sig-hashed diffing

#43's most consequential open question: is LangGraph's `interrupt()`/checkpointer pattern
directly analogous to `wakes.py`'s content-hash-diffing wake model?

**Partially confirmed, refuted on the two architecturally load-bearing points.**
- Confirmed: `interrupt()` durably pauses and a checkpointer persists state for resumption.
  Source: https://docs.langchain.com/oss/python/langgraph/interrupts
- Refuted: checkpoint identity is `thread_id` + monotonic checkpoint ID (sequence-keyed), not
  content-hash-keyed — LangGraph has no analogue to `wakes.py`'s "don't re-wake on unchanged
  evidence." Sources: https://docs.langchain.com/oss/python/langgraph/persistence ;
  https://medium.com/@abhishekjainindore24/langgraph-7-persistence-b05dc89d6660
- Refuted: no built-in re-wake suppression; resumption requires explicit `Command(resume=...)`.
  Source: https://medium.com/@areebahmed575/langgraphs-interrupt-function-the-simpler-way-to-build-human-in-the-loop-agents-faef98891a92
- Refuted: no framework-enforced `HUMAN_ONLY`-equivalent — HITL placement is entirely a
  developer's per-node choice. Source: https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt
- AutoGen and CrewAI show the same shape or weaker: AutoGen's default `UserProxyAgent` HITL
  doesn't persist across a wait at all without hand-rolled `save_state`/`load_state`
  (source: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/human-in-the-loop.html);
  CrewAI's `@human_feedback` durably pauses (SQLite-backed) but has no content-hash suppression
  (source: https://docs.crewai.com/en/learn/human-in-the-loop).

**Non-hedged verdict**: both designs solve "durably pause for a human, resume from persisted
state" with a superficially similar shape. The resemblance stops there — none of the three
frameworks has `wakes.py`'s core "don't re-wake on unchanged evidence" content-hash dedup, and
none has a framework-enforced hard gate equivalent to `wakes.py`'s hard-coded `HUMAN_ONLY` table
of decision types the evaluator refuses to auto-resolve. `wakes.py`'s content-hash diffing and
automation-refusal table remain a novel design with no confirmed external precedent, not borrowed
prior art.

## Does #43's verdict change?

**No.** #43's CONDITIONAL-GO rested on two angles that needed no live search (GitHub PR queue
conventions, HCI situation-awareness literature) plus muster's own architecture; the three
now-reverified angles were explicitly excluded from that verdict's evidence base, and #43 already
priced in that confirmation would strengthen external precedent while refutation would leave the
design resting on internal evidence alone — "which this verdict already treats as sufficient."
That is the outcome that materialized. Condition 4 ("re-run the 3 unverified angles before the
design issue finalizes its mechanism choice") is now **closed**. The other three #43 conditions
(mission board as pure read view, batching as aggregation-only, explicit parking-lot promotion
criteria or dropping the parking lot) carry forward unchanged into the design issue.

## Mission-board disposition: proceed as designed

**Proceed as designed**, with two evidence-based refinements:

1. **List-view shape confirmed, not novel.** Devin, Cursor, and Copilot coding agent converged
   independently on the same dashboard shape: a status-grouped (running / waiting-for-review /
   done) list view across concurrent sessions. muster's mission-board (a read-only aggregate over
   `docs/issue-*/reports/<role>.md` and `loop_state`) already matches this shape. No redesign
   needed — the design issue can cite these three tools as precedent rather than treating the
   shape as novel.
2. **No-bulk-approve reaffirmed.** None of the six survey targets across #43 and #64 — the three
   commercial coding agents, OpenHands/SWE-agent, or AutoGen/CrewAI/LangGraph — has any documented
   mechanism for batching a human's approval decision across multiple items into one action. This
   reinforces #43's condition 2 with a new data point: nobody surveyed, commercial or open-source,
   has built cross-session batch-approve. The design issue should not treat "build batch-approve
   because competitors have it" as a live option — no competitor has it.

## Reversibility

Two-way door, high reversibility (unchanged from #43). This issue changed no code and no runtime
surface — it supplies evidence only. The mission-board mechanism itself remains a deletable read
view.

## Deploy/runtime config surface

None. No code or config change in this issue.
