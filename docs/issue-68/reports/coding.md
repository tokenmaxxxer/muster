# Coding record — issue-68: cross-issue mission board

code_under_review: orchestrate/commands/run.md
loop_state: landed

upstream: docs/issue-68/proposals/board-proposal.md (phase-1 proposal, approved via PR #71,
`APPROVE issue-68/coding`), docs/issue-68/reports/coding/research.md (phase-1 research)

## Why

Issue #68 asks the orchestrate procedure to define a mission-board rendering: a status-grouped,
read-only, at-a-glance view across all open flows (issues), so the user does not have to ask "what
did I request and where does each stand" per-flow. This builds on issue #43's feasibility verdict
(CONDITIONAL-GO, four conditions), issue #54's flow/stage/next schema and exact rendering forms,
and issue #64's re-verification of the status-grouped list-view shape.

## What was done (phase 2)

Applied the approved text from `docs/issue-68/proposals/board-proposal.md` verbatim to
`orchestrate/commands/run.md`: inserted a new `## 미션 보드 (Mission Board)` section between the
existing step 5 ("PR을 설명한다") and step 6 ("사용자의 결정을 중계한다"). Step 5 and step 6
keep their existing numbering and content unchanged — the loop stays numbered 1-6, with the board
section as unnumbered prose between them, exactly as proposed.

The inserted section covers, per the proposal's five binding constraints:

- **Render triggers** (explicit, not implicit): on user request, or at named transition points
  (after registering a new issue, after a role session's completion notice, after relaying a
  user decision) — never on every turn.
- **Inputs**: `loop_state` from `docs/issue-<n>/reports/<role>.md` merged to `main`, plus live
  GitHub issue/PR state (`gh issue view`, `gh pr view`, `gh pr status`). No new field is added to
  those report files, and no new stored artifact is created for the board itself.
- **Classification logic**: four groups, checked in priority order — parking-lot (not yet
  `gh issue create`d), waiting-for-human-decision, running, done.
- **Render format**: three status-group headers (Running / Waiting for human decision / Done),
  each rendered only if non-empty, every item using issue-54's exact compact form
  `[이슈 #<n>] <flow 요약, ≤8단어> · <stage> → <next>` verbatim — no invented alternate format.
- **Parking-lot section**: kept separate from the three status groups, listed last, with an
  explicit, checkable promotion criterion — an item enters the board only when `gh issue create`
  is actually run for it (per step 1); time elapsed, other items processing, or orchestrator
  judgment never promote it on their own.
- **No bulk-approve**: stated explicitly under "하지 않는 것" — the board only aggregates and
  displays; the waiting-for-human-decision group never triggers or represents a batched approval
  action, and all approvals still route through step 6's per-item mechanics.
- **No persisted board file**: stated explicitly — recomputed from the above inputs at every
  render, never written to disk.

Write set for this phase-2 edit: exactly `orchestrate/commands/run.md`, matching the proposal's
frozen write set (plus this record file, `docs/issue-68/reports/coding.md`, tracking the change).

## What did not work

Nothing — the proposal's text applied cleanly, matching the proposed diff with no deviation.

## Verification performed (closed_checks)

- Re-read the edited `orchestrate/commands/run.md` in full after the edit: confirmed step 5 and
  step 6 retain their original numbering and content unchanged, and the new
  `## 미션 보드 (Mission Board)` section sits between them as unnumbered prose (matches the
  proposal's "additive text only, no renumbering" requirement).
- Checked every example/format line in the inserted section uses the exact issue-54 compact form
  `[이슈 #<n>] <flow 요약, ≤8단어> · <stage> → <next>` with no alternate format introduced.
- Confirmed the section states: (a) explicit render triggers (on-request + named transition
  points, not "every turn"), (b) exactly three status groups plus a separate fourth
  parking-lot section, (c) that all inputs derive from `loop_state` + GitHub state with no new
  stored artifact, (d) that no bulk-approve action exists and decisions still route through step
  6, and (e) an explicit, checkable parking-lot promotion criterion (`gh issue create`, not
  "eventually").
- Confirmed the write set stays exactly `orchestrate/commands/run.md` (plus this record) — no
  other repo file was touched by this phase-2 edit.

## Hunt

Not dispatched — this is a text-only prompt-file edit (no code path, no runtime behavior)
applying an already-approved, fully-specified proposal verbatim, following the same reasoning as
issue-54's coding record for an equivalent prompt-file-only change. No new failure surface to
hunt.

## Open findings

None.
