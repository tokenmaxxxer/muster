# issue-43 — current-state survey: human wait time, goal drift, status visibility

market_argument_supplied: false

The issue's own motivating argument (mission board / decision-queue batching / parking lot make
muster more usable) was deliberately not consulted while reading the specification or the
survey below. Those three ideas are treated as hypotheses in the proposal, not as pre-decided
conclusions.

## Method

Six independent research angles, one per named survey target class in the issue. Findings below
are compressed; full agent output is not reproduced verbatim, only the load-bearing claims.

## 1. Claude Code (background tasks, TodoWrite, Workflow phases)

- **Wait time**: `run_in_background` detaches a long tool call; the agent is notified on
  completion, explicitly forbidden from polling or fabricating results in the meantime. This
  frees the *agent's* turn, not the human's — no mechanism batches several pending approvals
  into one human decision point.
- **Drift**: `TodoWrite` — a maintained list of discrete items with status (pending/in_progress/
  completed) — is the primary anti-drift device: durable state the agent must sync to actual
  work, not a narrative. `Workflow`'s phase/pipeline model constrains drift structurally by
  routing work through fixed named phases. Gap: nothing stops the todo list itself from being
  silently reworded to match what was done rather than what was asked — no immutable "original
  goal" artifact separate from the mutable list.
- **Visibility**: `TodoWrite` is the single "what did I ask, what's the state" table; task
  notifications are discrete, auditable events. Gap: todos are session-scoped, not a persistent
  queryable board.
- **Reusability**: the transferable pattern is *durable-state-not-narrative* (TodoWrite). Not
  transferable: Claude Code's background-task notification resumes the *agent's own thread* on
  completion — it has no counterpart to "wake only on an external file changing," which is
  muster's actual model.

## 2. Devin / Cursor / Copilot Workspace plan-approval UIs

Live web search was unavailable to the research subagent in this sandbox (WebSearch denied).
No verified findings are reported for this angle — reporting invented API/UI specifics would
violate the survey's own evidence bar. What can be said without search: all three are broadly
known (via product marketing, not verified here) to front a synchronous "plan then execute"
review step per task, and none is publicly documented as offering a cross-task queue view that
lets a human batch approvals across several concurrently running agent sessions. This should be
treated as an open gap in this survey, not a finding, until re-run with search access.

## 3. OpenHands / SWE-agent event streams

Same tooling constraint — no verified findings. Architecturally, both projects are documented
(in general community knowledge, not verified live here) as single-agent-per-session action/
observation loops with a confirmation-mode gate before destructive actions; neither is known to
have a first-class multi-session supervisory dashboard. Flagged as unverified; not used as a
basis for the recommendation below.

## 4. AutoGen / CrewAI / LangGraph human-in-the-loop checkpoints

Same tooling constraint — no verified findings reported. LangGraph's `interrupt()` / durable
checkpointer design is widely known by name to persist "paused for human input" as graph state
rather than a blocked function call, which — if confirmed — would be the single most relevant
prior-art pattern for muster's "wake on state change" model. This is flagged explicitly as
**unconfirmed** and excluded from the recommendation's evidence base.

## 5. GitHub PR review-queue conventions

This angle needed no live search — it is directly observable in muster's own workflow and in
well-documented GitHub features.

- **Wait time**: Draft PRs exclude unfinished work from the reviewer's queue until the author
  pulls them in; `review-requested:@me` lets a reviewer batch-process many requests in one
  sitting instead of context-switching per notification; digest vs. per-event notification
  settings reduce ad hoc interruption. Merge queues decouple the approval decision from the
  mechanical completion of the merge.
- **Drift**: `Closes #43` issue-linking keeps the original ask pinned and visible for the PR's
  entire review life, independent of how many rounds of comments accumulate. PR templates force
  a restated goal at creation time.
- **Visibility**: the review-requests dashboard is a *stateful list keyed by item*, not a stream
  keyed by time — the open set is always current and filterable by staleness, which chat
  structurally cannot provide (chat has no persistent per-item state, only a message stream).

This is the single most load-bearing angle for muster specifically, since muster's own human
decisions already are GitHub PR Approve/merge/comment acts (role-handoff contract v3 s19).

## 6. HCI situation-awareness literature

- **Endsley's SA model** (1995): Level 1 perception (an event happened), Level 2 comprehension
  (what it means — contradicts another report, blocks something), Level 3 projection (forecast —
  at this rate X will miss its window). Most raw event/notification lists support only Level 1.
- **Sheridan's levels of automation**: as autonomy rises, the human's role shifts from control to
  monitoring — and humans are measurably poor at sustained monitoring.
- **Out-of-the-loop performance problem** (Endsley & Kiris 1995) and **vigilance decrement**
  (Mackworth 1948 onward): idle waiting is not neutral — it actively degrades a supervisor's
  ability to detect anomalies when one finally appears, within roughly 20–30 minutes.
- **Interruption/resumption cost** (Bailey & Konstan 2006; Trafton et al.): the cost of an
  interruption is dominated by *resumption* — re-establishing context — which argues for batching
  non-urgent notifications at natural decision boundaries rather than immediate push.
- **Multi-agent supervisory "fan-out"** (Olsen & Goodrich 2003: fan-out = neglect tolerance /
  interaction time; Crandall & Cummings): supervising many autonomous units at high fan-out
  requires aggregated, comparative status views, not per-unit logs, because attention must be
  triaged, not exhaustively read.
- **Design implication**: a queue of raw completion events only reaches SA Level 1. Reaching
  Level 2/3 requires aggregation across items, explicit flagging of contradictions/dependencies
  between reports, and staleness/projection indicators — not just a longer list.

## Muster's existing architecture (read from `main`, not from this issue's motivating argument)

- `wakes.py` (main branch) already implements the durable-state pattern the literature and the
  PR-queue angle both point to: WAKES-ON is evaluated mechanically off files under
  `docs/issue-<n>/reports/<role>.md` and `loop_state`, not off conversation content. It carries a
  `sig` (content hash of the evidence files) per wake row specifically to avoid re-waking on
  unchanged evidence — a primitive form of the "don't re-interrupt on stale state" principle from
  the interruption-cost literature.
- The same file hard-codes a `HUMAN_ONLY` table (approval gate, findings-resolved re-check,
  round-done value gate) that the evaluator explicitly refuses to automate, matching the issue's
  stated constraint that approval is a human-only act, never inferred from prose.
- There is currently **no cross-issue, cross-role aggregate view** — each role reads its own
  `docs/issue-<n>/reports/<role>.md`; nothing today answers "what did I (the human) request across
  all open issues, and where does each stand" in one place. This is the concrete gap the issue is
  asking about, and it matches the SA-Level-1-only gap identified in the HCI angle and the
  Claude-Code angle above.

## Deploy/runtime config surface

None foreseeable from this research-only issue — no new env vars, no new runtime surface. Any
config surface implied by mechanisms proposed below is deferred to the design issue the parent
issue explicitly gates on approval of this report.
