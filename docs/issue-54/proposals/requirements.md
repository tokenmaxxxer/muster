# Requirements — issue-54: structural-context reporting

Status: proposal (phase 1). This document defines requirements and acceptance criteria only. It
does not edit `orchestrate/commands/run.md` — that edit is reserved for a separate coding-stage
issue, per issue #54's stated split ("A follow-up coding stage (same issue) applies them to
orchestrate/commands/run.md").

## 1. Minimal reporting schema

Three fields, each a single short clause, attached to any orchestrator report about an item (an
issue, a PR, a role-session completion):

| Field | Answers | Source (read-only) | Distinct from issue-34 / issue-44? |
| --- | --- | --- | --- |
| **flow** | Which of the user's original requests does this item serve? | The GitHub issue number + a short (≤ 8 word) restatement of the user's original ask, taken from the issue that was filed in step 1 of the loop (or the issue title if already filed) | Yes — issue-34's fields explain *this item's own content* (what/why/how); flow explains *which parent request it belongs to*. Issue-44's role field says *who is doing the work*; flow says *what it's being done for*. |
| **stage** | Where is this item in its lifecycle? | One of: `proposal` / `approval` / `implementation` / `verification` / `merge` / `close` — read directly off which loop step produced the report (step 5's two branches: phase-1 proposal-explain vs phase-2 merge-explain) and off `loop_state` already recorded in `docs/issue-<n>/reports/<role>.md` when present | Yes — a new axis (lifecycle position), not previously reported at all. Does not restate issue-44's role classification (which stays fixed per issue; stage moves as the same issue advances). |
| **next** | What happens once this stage is resolved (in either direction)? | One short clause per branch actually available at this point: what an Approve leads to, what a Reject/changes-requested leads to. Derived from the fixed stage-transition sequence (proposal → approval → implementation → verification → merge → close) and the relay actions already defined in loop step 6 (comment / APPROVE / merge / close) | Yes — no equivalent field exists today; step 6 defines the *mechanics* of relaying a decision, but nothing today tells the user what those mechanics lead to before they decide. |

These three fields are additive to, and always reported alongside, the existing issue-34 minimum
item list (what/why/what-changed/how-verified) and the existing issue-44 role-classification line
where that line is still live in the same turn (typically only at issue-creation time, step 2).
They must not be merged into or reworded as substitutes for those fields — they answer a different
question (position in the larger picture, not content of this item).

### Field composition example (single item, prose form — illustrative only, not run.md text)

```
flow: issue #48 ("clean skips workspaces with a live roster session")
stage: approval (proposal → [approval] → implementation → verification → merge → close)
next: Approve → role implements and opens a phase-2 PR; Reject → PR closes, issue stays open for rework
---
[existing issue-34 fields: what / why / how]
```

## 2. Compactness rules

1. **One line per field, no restatement of content already covered by issue-34/issue-44 fields.**
   `flow` is an issue number plus a restatement capped at 8 words — not the full original request
   text. `stage` is one word from the fixed six-stage vocabulary — no free text. `next` is capped
   at one short clause per branch (at most two branches: proceed / stop-or-rework) — not a forecast
   of the whole remaining flow.
2. **No restating a flow the user already has fresh in view.** If the immediately preceding report
   in the same conversation turn already named the same flow, the orchestrator may refer to it by
   issue number only ("same flow, #48") rather than repeating the 8-word restatement. Full
   restatement is required only on first mention per flow within a turn, or after enough
   intervening items that the anchor could plausibly be lost (operationally: whenever a different
   flow was reported in between).
3. **No new prose sections.** The three fields sit as a compact header/prefix to the existing
   issue-34 explanation, not as an additional narrative paragraph.
4. **Fixed vocabulary, not open text, for `stage`.** Six values only, matching the sequence issue
   #54 specifies (proposal / approval / implementation / verification / merge / close). This keeps
   the field scannable and prevents it from becoming a place to smuggle in extra unstructured
   status prose.

## 3. Batched-decision composition

When one orchestrator turn reports on multiple items (parallel role sessions completing together,
several PRs open at once, a multi-row wake batch):

- Group items **by flow first**. Each distinct flow gets a header stated once: `flow: issue #N
  (<restatement>)`.
- Under each flow header, list each item as a single line: `stage → item-specific next`, using the
  existing issue-34 what/why fields inline per item as already required.
- If two or more items share the same flow *and* the same stage (e.g., two PRs both awaiting
  approval under the same issue), their `next` clause may be stated once for the group rather than
  repeated per item, provided the branch outcomes are actually identical (Approve/Reject lead to
  the same next step for both). If outcomes differ, state `next` per item.
- Items belonging to different flows are never merged under one header, even if they happen to
  share a stage — `flow` is always the top grouping key, because the point of this schema is to
  prevent cross-flow confusion, which is exactly what a stage-first grouping would risk.

This keeps the added text at O(flows) headers + O(items) single-line stage/next entries, not
O(items) full restatements — satisfying the compactness rule above even under a large batch.

## 4. Acceptance criteria

A future edit to `orchestrate/commands/run.md` satisfies this requirements record if and only if:

1. Every report the orchestrator makes about an item under loop step 5 ("PR 을 설명한다") includes
   a `flow` reference (issue number + restatement, or the short-form issue-number-only reference
   per compactness rule 2) that identifies which of the user's original requests the item serves.
2. Every such report includes a `stage` value drawn from exactly the six-value vocabulary
   (proposal / approval / implementation / verification / merge / close), matching the item's
   actual current position as derivable from which step produced the report and/or the item's
   recorded `loop_state`.
3. Every such report includes a `next` clause stating what happens for each decision branch
   actually open to the user at that point (at minimum: what proceeding leads to, what
   stopping/reworking leads to), without forecasting beyond the immediately next stage.
4. The three fields are visually/structurally distinguishable from (not interleaved word-for-word
   into) the existing issue-34 what/why/what-changed/how-verified fields, so a user can visually
   locate "where does this fit" separately from "what is this."
5. The three fields never duplicate the issue-44 role-classification line — `run.md` text must not
   reintroduce a role/classification question inside this schema.
6. When a single turn reports on multiple items, the edited `run.md` text specifies (per section 3
   above) that items are grouped by flow first, with shared `next` only permitted within a
   flow+stage group when outcomes are identical — i.e., the text must not permit or default to
   per-item full restatement of `flow` for every item in a batch.
7. No part of the added text requires or implies a new stored artifact (file, table, database) to
   track flow/stage/next — the edit's own prose must state or make evident that all three fields
   are computed at report time from state the orchestrator already reads (the issue, its title/
   body, the PR/proposal being explained, and `docs/issue-<n>/reports/<role>.md`/`loop_state`
   where present).
8. The compactness caps (≤ 8-word flow restatement on first mention, issue-number-only on repeat
   within a turn, one word for stage, at most two short branch clauses for next) are stated as
   explicit limits in the edited text, not left as unstated convention.
9. The edit integrates into the existing step 5 (and step 6, for the `next` field's branch
   outcomes) rather than introducing a new, separately-numbered loop step — this is a report-shape
   change to already-mandated reporting points, not a new obligation with its own trigger.

## 5. Honoring issue #43's read-only-view condition

Issue #43's approved feasibility verdict conditions any board/reporting-adjacent design on: "the
mission board [must be] strictly a read view over existing report files — no new mutable state
that competes with `docs/issue-<n>/reports/<role>.md` as ground truth." This requirements record
satisfies that condition because:

- `flow` is sourced from the GitHub issue (title/body), which already exists once step 1 files it
  — nothing new is written to derive it.
- `stage` is sourced from which loop step is producing the report, plus `loop_state` already
  present in `docs/issue-<n>/reports/<role>.md` when the role has recorded one (see e.g.
  `docs/issue-34/reports/coding.md`'s `loop_state: landed`, `docs/issue-44/reports/coding.md`'s
  `loop_state: landed`) — this is an existing convention, not a new file or field this issue
  invents.
- `next` is sourced from the fixed, already-existing stage sequence stated in issue #54 itself and
  the relay mechanics already defined in loop step 6 (comment / APPROVE / merge / close) — it is a
  restatement of existing procedural knowledge, computed at report time, not a new persisted
  value.
- No acceptance criterion above asks for a new file, board, queue, or log. Acceptance criterion 7
  makes this an explicit, checkable requirement rather than an implicit assumption.
- The schema is purely a *reporting shape* (what the orchestrator says out loud in the
  conversation), not a state-mutation action — it does not add any new write path, and does not
  change what step 6 is authorized to do (comment / APPROVE / merge / close remain the only
  state-changing actions, unchanged by this issue).

## Out of scope

- No actual edit to `orchestrate/commands/run.md` text (reserved for the coding stage).
- No new file format, board view, or persisted schema for flow/stage/next (would violate issue
  #43's read-only-view condition; also unnecessary since all three fields are point-in-time
  computed).
- No change to the six-stage vocabulary's meaning or issue-54's stated stage sequence — this
  document adopts it as given.
- No revision of issue-34's or issue-44's existing obligations — both are treated as fixed
  constraints this schema must compose with, not renegotiate.
