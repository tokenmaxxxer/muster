# Research — issue-68: cross-issue mission board

Phase 1 (research + current-state survey + proposal) only. No edits made to
`orchestrate/commands/run.md` in this branch.

## Sources read

- `gh issue view 68`
- `docs/issue-43/reports/feasibility.md` (main) — mission-board feasibility verdict, CONDITIONAL-GO,
  4 conditions
- `docs/issue-54/reports/product.md` (main) — flow/stage/next schema, binding requirements
- `docs/issue-54/reports/ux-design.md` (main) — exact rendering forms for flow/stage/next
- `docs/issue-64/reports/feasibility.md` (main) — re-verification of #43's unverified angles,
  reaffirms mission-board design as-is
- `orchestrate/commands/run.md` (this branch, current content, in full)

## Key definitions

- **flow** — the user's original request that an item belongs to. Rendered as
  `[이슈 #<n>] <summary, ≤8 words>` on first mention in a turn; `[이슈 #<n>]` only on repeat
  mention in the same turn (issue-54 product record, requirement 1; compactness rule 2).
- **stage** — exactly one of six fixed values: `proposal` / `approval` / `implementation` /
  `verification` / `merge` / `close`. No new values may be invented. On failure/error, stage stays
  at the last-attempted value; the rework branch is expressed via `next`, not a seventh stage
  value (issue-54 product record req. 1; ux-design §5).
- **next** — one short clause per currently-open decision branch, capped at 2 clauses, predicting
  only the immediately next step (issue-54 product record req. 1).
- **loop_state** — a YAML frontmatter field already present in every
  `docs/issue-<n>/reports/<role>.md` board record (e.g. `loop_state: verdict-recorded`,
  `landed`, `reviewed`, `closed`). It is the authoritative, file-based state `wakes.py` diffs
  against; muster's existing convention is "ground truth lives in files/PR state, not a separate
  telemetry system" (issue-43 feasibility record, Measurement design section). No orchestrate
  procedure field currently derives a board-wide status grouping from `loop_state` — that
  derivation is exactly what issue #68 asks the orchestrate procedure to define.
- **item line format** (issue-54 ux-design §2, compact single-item form):
  `[이슈 #<n>] <flow 요약, ≤8단어> · <stage> → <next>`
  This is the exact form issue #68's acceptance criteria require the mission board to reuse.

## Where the orchestrate procedure file lives

Exact path: `orchestrate/commands/run.md` (only match for `run.md` in the repo, and the file
already defines the loop that references `loop_state`, `flow`/`stage`/`next`, and the board
convention `docs/issue-<n>/reports/<role>.md`).

## How status is currently derived in run.md (as of this branch)

Nothing in the current file computes or renders a cross-issue, cross-flow status-grouped view.
The existing structure is a single-conversation loop with per-turn, per-flow reporting only —
there is no step that aggregates across all open issues into running/waiting/done groups. This
confirms issue #68 (and the #43/#64 feasibility verdicts) are asking for genuinely new content in
step 5/6, not a fix to something already there.

## Current-state survey: `orchestrate/commands/run.md` structure

Frontmatter: `allowed-tools`, `description`, `argument-hint`.

Body (Korean, per repo convention for role-facing procedure text), numbered as:

- Preamble: sets `MUSTER=${CLAUDE_PLUGIN_ROOT}/..`, all commands go through
  `python3 $MUSTER/spawn.py`. States the session is a coordinating session (contract v3); roles
  wake from issues, work on `issue-<n>/<role>` branches, return only via PR; the board is
  `docs/issue-<n>/reports/<role>.md`, and only what's merged to `main` counts as the board.
- **`## 당신의 루프 (사용자와의 대화 안에서)`** ("Your loop, inside the conversation with the
  user") — 6 numbered steps:
  1. Requirement → issue drafting, confirm before `gh issue create`.
  2. Classify which role leads (feasibility/product/ux-design/coding) with a stated rationale,
     via a lookup table; explicit ban on silently defaulting to `coding`.
  3. Decide who to wake: `spawn.py wake -C <repo>` reads the board, propose the role WAKES-ON
     points to.
  4. Spawn — always in the background via `spawn.py <role> ... --issue <n> -C <repo>
     run_in_background`.
  5. **Explain the PR** — read and summarize proposal/merge PRs before asking for approval;
     mandates the 4-item summary (what/why/what-changed/how-verified) AND, as a structurally
     separate block, the **flow/stage/next** fields (issue-54): flow header/body rules, the exact
     single-item compact line `[이슈 #<n>] <flow 요약, ≤8단어> · <stage> → <next>`, and the
     multi-item flow-grouped block form.
  6. **Relay the user's decision** — if 2+ pending decisions, render a globally-numbered queue
     (not per-flow numbering, not persisted — a per-turn rendering convenience); otherwise map
     decision → `gh pr comment` / `gh pr comment ... "APPROVE issue-<n>/<role>"` /
     `gh pr merge --merge --delete-branch` / `gh pr close`.
- **`## 띄우기 전에 확인할 것`** ("Before spawning, check") — 3 preconditions: role fit against
  `roles/<role>.json` catalog, an issue must exist, and repo bootstrap prerequisites (remote,
  `docs/specs/approvers.md`, agent collaborator access), all confirmed with the user, none silent.
- **`## 하지 않는 것`** ("What this procedure does not do") — orchestrator never writes board
  records directly (that's the role's job), never edits a role's PR directly (feedback only via
  comment). Also documents `drive` mode, `ps`/`kill` management commands, and `clean`.

Step 5 (and its extension into step 6 for `next`'s branch outcomes) is exactly where issue-54's
schema was integrated, and per the product record's own scope note, is also the natural
integration point for a mission board: both are read-only renderings computed at report time from
existing state, both reuse the same `[이슈 #<n>] <summary> · <stage> → <next>` primitive, and the
board is a strict superset view (across issues) of what step 5 already renders per-flow within one
turn.

## Frozen write set confirmation

Exactly one file: `orchestrate/commands/run.md`. This research report and the accompanying
proposal (`docs/issue-68/proposals/board-proposal.md`) are the only artifacts phase 1 writes; no
edit was made to `orchestrate/commands/run.md` itself, and no other file was touched.
