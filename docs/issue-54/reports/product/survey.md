# Survey — issue-54: structural-context reporting

## Background

`orchestrate/commands/run.md` (main, single conversation loop, "contract v3") defines the
orchestrator's per-turn obligations. Two obligations already exist and are relevant:

- **Issue-34** (landed, `docs/issue-34/reports/coding.md`): step 5 ("PR 을 설명한다") requires the
  orchestrator to actually read the proposal file or diff before asking for approval/merge, and to
  fill a minimum item list — what is changing, why, (on merge) what changed, how it was verified.
  This is a *content-explanation* obligation: it makes sure the orchestrator doesn't relay an
  unread PR link as a bare yes/no prompt.
- **Issue-44** (landed, `docs/issue-44/reports/coding.md`): step 2 requires the orchestrator to
  state a role classification (feasibility / product / ux-design / coding) with a one-line reason
  before an issue is even filed, using a lookup table of request-type → leading role. This is a
  *routing-explanation* obligation: it makes sure the orchestrator doesn't silently default every
  request to `coding`.

Neither obligation, as currently written, requires the report to say which of the user's original
requests an item belongs to, where in that item's own lifecycle it sits, or what happens after the
current step. Both are about explaining *what a single item is*, not about *where that item sits
relative to the rest of the running conversation*.

## Problem (restated without a solution)

During live operation, per-item reports (a PR number, an issue number, a background-agent
completion) that state only the item and its outcome forced the user to reconstruct context on
their own — mid-session the user had to ask "what was #48 again?" This happens because the
orchestrator can have several issues/flows in flight at once (parallel role sessions, phase-1 and
phase-2 issues interleaved, batched wake decisions), and a bare "PR #48 is open, approve?" gives no
anchor to which of the user's original asks it serves, how far along that ask is, or what the user
is signing up for next by approving or rejecting it. The cost lands entirely on the user: they must
hold the mapping from item IDs to original intent in their own head, across an arbitrarily long,
interruption-heavy session (background role sessions complete asynchronously and unpredictably).

The problem is not "the orchestrator doesn't produce enough text" — issue-34 and issue-44 already
added required explanation. It is specifically the *absence of a structural anchor*: no field ties
an item back to (a) the flow it serves, (b) its position in that flow's stage sequence, (c) what
comes next. This is a situation-awareness gap (per issue #43's HCI literature framing —
Endsley's L1/L2/L3), not a missing-detail gap.

## Constraints carried into this issue

1. **Issue-34 obligation stands and must not be duplicated.** The what/why/(what
   changed/how verified) minimum item list for approval/merge requests is already required. Any
   new schema field must compose with it, not restate it.
2. **Issue-44 obligation stands and must not be duplicated.** The role-classification line
   (which role leads, one-line reason) is already required at issue-creation time. The new schema
   must not re-ask "which role" — stage position is a different axis (lifecycle stage of the
   item, not who is doing the work).
3. **Issue-43's read-only-view condition** (carried from its approved feasibility verdict,
   `docs/issue-43/reports/feasibility.md`): "the mission board [must be] strictly a read view over
   existing report files — no new mutable state that competes with
   `docs/issue-<n>/reports/<role>.md` as ground truth." Any structural-context schema this issue
   defines must be derivable by *reading* existing state (the GitHub issue, its title/body, open
   PRs, `docs/issue-<n>/reports/<role>.md` board files, `wakes.py`'s state) — it must not require a
   new file, database, or other mutable store to track "which flow owns this item" or "what stage
   is it in." The orchestrator already has this information available each turn (it read the issue
   to classify it in step 2, and reads the PR to explain it in step 5); the schema should say how to
   *report* it, not how to *store* it.
4. **Compactness.** This is a chat-loop report inside a human-in-the-loop conversation, not a
   document. The existing obligations already add required text per approval/merge turn; a
   structural-context requirement that duplicates prose per item (e.g., repeating the full original
   request verbatim every time) would defeat its own purpose by adding noise the user has to skim
   past to find the decision. The schema must default to terse, referential framing (point back to
   the flow, don't restate it) and must explicitly define how one turn covering several items at
   once (batched wakes, multiple concurrent PRs) composes without becoming O(items) restatement.

## Goals

- Define the minimal set of fields an orchestrator report needs to situate an item in its owning
  flow, show its stage position, and state what follows — without re-deriving new state.
- Make the schema explicitly additive/orthogonal to issue-34's content fields and issue-44's role
  field, not a replacement or a rewording of either.
- Make batched reporting (one turn, several items) compose via a shared header + per-item deltas,
  not per-item repetition.
- Produce acceptance criteria concrete enough that a later coding-stage issue can implement them
  as an edit to `orchestrate/commands/run.md` and be checked against them without further
  interpretation.
- Honor issue #43's read-only-view condition: the schema must not imply or require any new
  mutable state store; everything it asks the orchestrator to report must be derivable from
  already-existing state at report time.
