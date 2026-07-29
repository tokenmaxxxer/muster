# issue-64 — re-verification survey: the 3 unverified #43 angles, with live web access

market_argument_supplied: false

Same discipline as the issue-43 survey: the mission-board motivating argument is not consulted
while reading these findings. Each angle below was researched by an independent subagent with
WebSearch/WebFetch enabled (issue #58, merged). Citation format: Claim / Source / Date / Verdict
vs #43.

## 1. Devin / Cursor / Copilot Workspace plan-approval UIs

**#43's claim under test**: "all three front a synchronous plan-then-execute review step per
task, and none is publicly documented as offering a cross-task queue view that lets a human
batch approvals across several concurrently running agent sessions."

### Devin (Cognition Labs)
- Claim: Devin proposes a plan for complex tasks, reviewable before execution; "Agency mode"
  skips the wait and proceeds automatically.
  Source: https://skywork.ai/blog/devin-ai-software-engineer-cognition-labs/ — undated —
  partially confirms (plan approval is optionally synchronous, not always).
- Claim: Devin Desktop's "Agent Command Center" is a Kanban-style dashboard (Running / Waiting
  for review / Done) showing multiple concurrent sessions at once.
  Source: https://devin.ai/desktop — undated — **refutes** the "no cross-task queue view" half.
- Batch approval across sessions in one action: no evidence found. Answer: no/unclear.

### Cursor (Background Agents / Plan Mode)
- Claim: Plan Mode blocks — nothing executes until the human reviews and triggers the build.
  Source: https://cursor.com/docs/agent/plan-mode ; https://cursor.com/blog/plan-mode —
  undated (2.2-era) — confirms.
- Claim: Cursor runs up to 8 parallel background agents from one control panel and exposes a
  "List agents" API (`GET /v0/agents`) returning status/repo/branch/PR for all of a user's
  agents.
  Source: https://aitechfy.com/blog/cursor-background-agents/ (secondary — direct docs.cursor.com
  fetch redirected) — undated — **refutes** the "no queue view" half, moderate confidence.
- Batch approval: no documentation found; review stays per-PR. Answer: no/unclear.

### GitHub Copilot Workspace / Copilot coding agent
Legacy Workspace has been superseded by "Copilot coding agent" (GA Sept 2025).
- Claim: legacy Workspace had a blocking plan-review step; current coding agent moves the human
  gate to the PR stage — agent PRs require human approval before any CI/CD workflow runs.
  Source: github.blog "Agent pull requests are everywhere..." (secondary/aggregated) — undated —
  confirms for the legacy product; current product's gate is per-PR, not per-plan.
- Claim: a new "Agents tab" gives a repo-level dashboard of all Copilot coding-agent sessions,
  plus a `gh agent-task view` CLI.
  Source: https://visualstudiomagazine.com/articles/2026/01/29/hands-on-new-github-agents-tab-for-repo-level-copilot-coding-agent-workflows.aspx
  (secondary reporting) — 2026-01-29 — **refutes** the "no queue view" half.
- Batch approval: no batch-approval mechanism found; approval stays per-PR. Answer: no/unclear.

### Verdict on angle 1
The "synchronous plan-then-execute" half holds only loosely (Devin's Agency mode and Copilot's
shift to PR-level review both weaken "always synchronous"). The "no cross-task queue view" half
is **refuted for all three tools** — Devin's Agent Command Center, Cursor's multi-agent panel/List
Agents API, and GitHub's Agents tab are all publicly documented multi-session dashboards. A
narrower claim survives intact: none of the three is documented as supporting **batched approval**
across sessions in one decision point — each tool's approval action stays per-item even where a
multi-session list view exists alongside it. Several sources are secondary (blog/aggregated
reporting, not a direct primary-source fetch); flagged per-claim above.

## 2. OpenHands / SWE-agent event streams

**#43's claim under test**: "both projects are single-agent-per-session action/observation loops
with a confirmation-mode gate before destructive actions; neither is known to have a first-class
multi-session supervisory dashboard."

### OpenHands (formerly OpenDevin)
- Claim: OpenHands models agent-environment interaction as an append-only event stream that all
  components read from and append to.
  Source: https://docs.openhands.dev/sdk/arch/events — undated — confirms.
- Claim: the Conversation component persists the event log durably and supports rewinding to any
  prior event.
  Source: https://docs.openhands.dev/sdk/arch/events ; https://docs.openhands.dev/sdk/guides/convo-persistence
  — undated — refines (durability wasn't addressed by #43's wording, doesn't contradict it).
- Claim: a confirmation-mode feature (`UserRejectObservation` / "ConfirmRisky" policy) pauses for
  approval before risky/destructive actions; routine actions proceed autonomously.
  Source: https://docs.openhands.dev/sdk/arch/events ; https://www.emergentmind.com/topics/openhands-agent-framework
  — undated — confirms.
- Claim: the UI is currently hardcoded to show only the last ~9 conversations (open issue asking
  for pagination); no first-class multi-session supervisory/queue dashboard exists — just a
  conversation-history list.
  Source: https://github.com/OpenHands/OpenHands/issues/7928 — open issue — confirms.
- Claim: OpenHands Cloud has queue/backpressure infrastructure (`PendingMessageService`) and an
  RFC (#13275) proposing scheduled/event-driven automations — movement toward multi-conversation
  infra, but proposed/partial, not a shipped supervisory dashboard.
  Source: https://github.com/OpenHands/OpenHands/issues/5655 ; https://github.com/OpenHands/OpenHands/issues/13275
  — open issues/RFC — inconclusive/confirms (emerging gap, not yet a refutation).
- No content-hash/state-diffing mechanism found to suppress re-prompting on unchanged state — not
  found, reported explicitly rather than guessed.

### SWE-agent (Princeton/Stanford)
- Claim: core loop is a stateless Agent emitting Actions, run by a Conversation object with an
  append-only EventLog, executed against a Workspace returning Observations.
  Source: https://dev.to/truongpx396/swe-agent-deep-dive-build-your-own-guide-ade (secondary,
  community deep-dive) — undated — confirms.
- Claim: mini-swe-agent (SWE-agent's lightweight sibling) has an interactive mode requiring the
  human to confirm/reject every proposed command, not just destructive ones.
  Source: https://github.com/swe-agent/mini-swe-agent/blob/main/src/minisweagent/agents/interactive.py
  — undated — confirms an approval gate exists, but nuances #43: SWE-agent's gate is per-action,
  not risk-tiered like OpenHands'.
- Claim: no multi-session supervisory dashboard of SWE-agent's own; third-party projects
  (SWE-AF fleet system, LangChain's "Open SWE") have built such things around it, but that is
  outside SWE-agent proper.
  Source: https://github.com/Agent-Field/SWE-AF ; https://www.langchain.com/blog/introducing-open-swe-an-open-source-asynchronous-coding-agent
  — undated — confirms.
- Claim: SWE-agent uses `cache_control` prompt caching and a `last_n_observations` window to bound
  context — standard LLM-provider prompt-prefix caching, not content-hash state-diffing.
  Source: https://github.com/SWE-agent/SWE-agent/blob/main/README.md — undated — inconclusive on
  the diffing sub-question (#43 didn't claim this either way); no diffing mechanism found.

### Verdict on angle 2
**Confirmed on all main points.** Both are single-agent-per-session action/observation loops with
human confirmation gates before actions execute, and neither has a shipped first-class
multi-session supervisory dashboard. One nuance to fold in: OpenHands' gate is risk-tiered
(fires only on flagged risky actions) while SWE-agent's/mini-swe-agent's gates every action — a
distinction #43's wording ("gate before destructive actions") only cleanly fits OpenHands. No
content-hash/state-diffing analogue to `wakes.py`'s `sig` was found in either project.

## 3. AutoGen / CrewAI / LangGraph HITL checkpoints — the interrupt()/checkpointer analogy

**#43's most consequential open question**: is LangGraph's `interrupt()`/durable-checkpointer
pattern directly analogous to `wakes.py`'s sig-hashed state-diffing wake model?

`wakes.py` (main, read for ground truth) evaluates WAKES-ON mechanically off files under
`docs/issue-<n>/reports/<role>.md` and `loop_state`; each wake row carries a `sig` — a content
hash of the evidence files — specifically so the system does not re-wake on unchanged evidence,
plus a hard-coded `HUMAN_ONLY` table of decision types the evaluator refuses to automate.

- Claim: `interrupt()` raises `GraphInterrupt`, halting node execution; a checkpointer persists
  the graph state (including the interrupt payload) for later resumption.
  Source: https://docs.langchain.com/oss/python/langgraph/interrupts — undated — confirms the
  "pause + persist" half only.
- Claim: every run is scoped to a `thread_id`; each checkpoint is identified by a unique,
  monotonically increasing checkpoint ID — resuming means "load latest checkpoint for this
  thread_id," not "compare content hashes of evidence files."
  Source: https://docs.langchain.com/oss/python/langgraph/persistence ;
  https://medium.com/@abhishekjainindore24/langgraph-7-persistence-b05dc89d6660 — undated —
  **refutes** the sig-hashed mechanism specifically: identity is sequence/thread-based, not
  content-diffed.
- Claim: `interrupt()` is purely call/event-triggered — a node hits it, execution stops, and
  resumption is an explicit `Command(resume=...)`. There is no built-in "state unchanged since
  last interrupt, don't interrupt again" — a developer would have to hand-roll that.
  Source: https://medium.com/@areebahmed575/langgraphs-interrupt-function-the-simpler-way-to-build-human-in-the-loop-agents-faef98891a92
  ; https://reference.langchain.com/python/langgraph/types/interrupt — undated — **refutes**: no
  analogue to `wakes.py`'s re-wake suppression.
- Claim: no built-in registry of decision types LangGraph itself refuses to auto-resolve — HITL
  placement is entirely the developer's per-node choice.
  Source: https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt
  ; https://docs.langchain.com/oss/python/langgraph/interrupts — undated — **refutes**: no
  framework-enforced `HUMAN_ONLY`-equivalent; LangGraph is a general primitive, not a policy.
- Claim: AutoGen's `UserProxyAgent` HITL blocks execution in-memory and explicitly cannot be
  saved/resumed while waiting; durable resumption requires terminating the run and manually
  persisting/reloading team state via `save_state`/`load_state`.
  Source: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/human-in-the-loop.html
  — undated — refutes/inconclusive: AutoGen's default HITL is weaker than muster's model (no
  diffing, no durable pause primitive without extra engineering).
- Claim: CrewAI Flows support a `@human_feedback` decorator pausing execution with SQLite-backed
  flow-state persistence across the wait; no evidence of content-hash suppression of repeat
  prompts.
  Source: https://docs.crewai.com/en/learn/human-in-the-loop ; https://blog.crewai.com/a-missing-layer-in-agentic-systems/
  — undated — refutes on the diffing dimension, same shape as LangGraph: durable pause/resume
  yes, sig-hashed evidence-diffing no.

### Direct verdict (per the issue's explicit demand for a non-hedged line)
The `interrupt()`/checkpointer pattern **IS PARTIALLY** analogous to `wakes.py`'s sig-hashed
state-diffing model: both durably pause a process and resume it from persisted state, but the
resemblance stops there. LangGraph/CrewAI/AutoGen key persistence on thread/run identity and
sequence (or, in AutoGen's default case, don't persist at all), not on content hashes of evidence
files — none of them has `wakes.py`'s core "don't re-wake on unchanged evidence" behavior. None
has a framework-enforced `HUMAN_ONLY`-style hard gate either; HITL placement is a fully
developer-configured choice in all three frameworks, whereas `wakes.py` hard-codes two decision
types the system itself is contractually forbidden from auto-resolving. The two designs solve
"pause for a human, resume later" with a superficially similar shape; the content-hash dedup and
the automation-refusal table are both absent from the LangGraph primitive and its peers.

## Deploy/runtime config surface

None foreseeable — this is a re-verification of research angles, not a code or config change.
