# Survey — issue #189: execution plan in the issue body

## Background / context

Step-level human confirmation (phase-1 scope approval, phase-2 merge) and parallel `spawn`
already exist and work (`spawn.py approve_scope`, `on-the-record/commands/run.md` step 4-6).
What doesn't exist is a place to write down, ahead of time, the *shape* of a multi-step issue —
which roles run in what order, which run in parallel — and to see that shape's progress as it
happens. Today "who's next" lives only in the orchestrator's per-turn judgment
(`run.md` step 3: "기계가 평가하는 라우팅 표는 없다" — no machine-evaluated routing table, per
issue #120/D1, confirmed at `docs/issue-120/proposals/coding.md`), and nothing records that
judgment before or after the fact.

The issue's own measurement (2026-08-02, `docs/issue-*/reports/`, as cited in the issue body,
not independently re-run by this survey): 54 issues, 48 (89%) closed with exactly one role,
5 (9%) used two or three roles, and no role has ever run twice on the same subject. Declared
parallel steps have never been used. This repo has barely exercised multi-step flows — the
value of a plan feature is less about managing repetition (there is none on record) and more
about making an unused capability (parallel steps, pre-agreed sequencing) practical to reach
for.

## Problem, stated without the proposed solution (JTBD)

The issue text already proposes a solution (issue-body checkboxes, edited via `gh issue edit`).
Restated in the customer's terms, before evaluating whether that's the right solution:

- **Job performer**: the orchestrating conversation (user + orchestrator), the moment an issue
  is going to need more than one role session.
- **Job**: agree on, and durably record, the step order and parallel grouping for that issue —
  and be able to see, at any point afterward, how far the issue has gotten against that
  agreed shape — without re-deriving "who's next" from scratch on every turn and without a
  record that can silently drift from what actually happened.
- **Circumstance**: role sessions work in isolated branches and reach `main` only through a
  human-approved PR merge (contract v3 s10); `spawn.board()` (`spawn.py:974`) reads only the
  local checkout's `docs/issue-<n>/reports/<role>.md` files, i.e. only what's merged. Anything
  that exists only as GitHub issue/PR state, not yet merged, is invisible to `board()` and thus
  to anything built on top of it.
- **Desired outcome**: from the moment the issue is filed — not from the first merge — the plan
  and its live progress are visible to the user and to `flows --json`'s consumer
  (`repo-status-board`), without inventing a second source of truth that can disagree with
  GitHub's own state.

## Where this sits on the opportunity-solution tree

- **Outcome**: multi-step issues in this repo execute against a structure that was agreed
  before work started, is auditable after the fact, and is observable in real time — instead of
  "who's next" being reconstructed, unrecorded, every turn.
- **Opportunity**: no durable, pre-declared plan exists for multi-step issues today, and even if
  one were written down, it would be invisible in `flows`/board terms until the first PR merges
  (the requirement-4 gap; see below).
- **Candidate solutions**: (a) plan as issue-body checkboxes, surfaced into `flows --json` as an
  additive field sourced by extending an already-existing per-subject `gh issue view` call
  [issue's stated preference]; (b) a new board-record file for the plan, committed directly to
  `main`; (c) a new gate/hook carve-out that lets plan writes bypass the branch-scoped board-gate
  invariant. Scored below (Requirement 4 section of the proposal).
- **Discriminating assumption**: a plan that lives only in GitHub issue state (not the merged
  board) can still reach `flows --json` without a new `gh` API call, a new gate, or a
  `schema_version` bump. This is checked against the actual code below, not assumed.

## What the code actually does today (checked, not assumed)

- `gates/flows.py:flows_payload` (`gates/flows.py:160-165`) builds `flows[]` from
  `spawn.board(root)` (`spawn.py:974-990`), which only reads `docs/issue-<n>/reports/<role>.md`
  files present in the local checkout — i.e. only merged records. This is the issue body's
  stated gap, confirmed: an issue with no merged role record yet produces **no** `flows[]` entry
  at all, plan or no plan.
- The six `stage` values (`proposal`/`approved`/`implementing`/`delivered`/`closed`, or raw
  `loop_state` with `stage_derived: false`) already come from `gates/flows.py:_stage_for`
  (`gates/flows.py:32-35`) and its `_STAGE_MAP`. No new stage vocabulary is needed for a plan
  field — a plan is a different axis (declared steps and their order) from stage (this record's
  own lifecycle position), matching how issue-54's `flow`/`stage`/`next` schema already treats
  "which flow" and "what stage" as orthogonal fields (`docs/issue-54/reports/product.md`).
- **A per-subject `gh issue view` call already exists and is already budgeted.**
  `gates/closure_sweep.py:_issue_view` (`gates/closure_sweep.py:53-56`) calls
  `gh issue view <n> --json state -q .state` once per subject, inside
  `closure_sweep.find_violations()` (`gates/closure_sweep.py:71-100`), which `flows_payload`
  already invokes for `hygiene.closure_sweep` (`gates/flows.py:259-260`). This is exactly the
  "up to `S` calls — `gh issue view`, one per subject" line already documented in
  `docs/specs/flows-schema.md` §4's call-count contract — it is not a call this issue would be
  adding, it is a call already being made and already priced into the schema's own budget.
  Extending that one call to also fetch `body` (instead of a second, separate per-subject call)
  keeps the total call count exactly where the schema already says it is.
- **Correction to the issue's stated constraint on versioning**: the issue body says "필드 추가 =
  버전 범프" (field addition = version bump). `docs/specs/flows-schema.md` §3 ("Versioning
  policy") states the opposite as the actual documented policy: "Additive changes — a new field
  appended to an existing object, a new optional key, a new section — never bump
  `schema_version`," and its own worked table lists "add `pr_url` field to `decision_queue[]`
  entries" as non-breaking. A new `flows[].plan` field is exactly this shape (a new key on an
  existing object) — no version bump is implied by the schema's own written policy. What *does*
  still hold from the issue's constraint bullet is the substantive part: `repo-status-board`
  holds its own copy of this schema doc and needs it manually synced to learn about the new
  field, independent of whether the version number moves — that sync is real, out of scope here
  per D3, and belongs to the separate issue in that repo.
- **Requirement 5 / D2 already has a working precedent to compose with.**
  `gates/closure_sweep.py` is detect-only ("아무것도 닫지 않는다... 계약 v3: GitHub 종결은
  사람/오케스트레이터의 몫", `gates/closure_sweep.py:5-6`) and already reports two violation
  kinds (`OPEN_PR_ON_CLOSED_ISSUE`, `MERGED_DELIVERY_ISSUE_OPEN`) without ever calling `gh issue
  close`. A "plan exhausted" signal composes with this as a third thing the orchestrator reports
  and asks about — not a new closure mechanism.
- **`on-the-record/commands/run.md`'s existing loop already has the seams this issue's
  requirements attach to**, and none of them are code-enforced gates — they are prose
  obligations on the orchestrating conversation, matching D1's "no machine-evaluated routing
  table" principle:
  - step 1-2 (issue drafting, role classification) is where requirement 1's plan agreement
    would naturally sit (before `gh issue create`, or immediately after, before spawning);
  - step 3 ("누구를 깨울지") already reads the board and states a reasoned judgment each turn —
    a recorded plan changes *what it reads*, not *whether a human judges*;
  - step 6 (relaying the user's decision) is where requirement 3's "no auto-spawn" already lives
    procedurally (spawning only happens after the user's explicit go-ahead) and where
    requirement 5's "plan exhausted → report → user confirms → close" would attach.

## Constraints carried into this issue (must not be re-litigated)

1. **D1 stands.** No loop syntax. The repo's only near-miss precedent for repetition — issue-162's
   phase-2 follow-up (`docs/issue-162/reports/implementation.md`), confirmed by reading that file
   to be an unplanned post-hoc rework session — was handled, per the issue body's own account, by
   adding one more plan line after the fact, not by a loop construct — this proposal must keep
   that path open, not design it away.
2. **D2 stands.** Closure is a human act, relayed by the orchestrator, never automatic —
   `closure_sweep`'s detect-only contract is the existing model to extend, not replace.
3. **D3 stands.** No `repo-status-board` repo changes here — only `flows --json`'s data
   contract, in this repo.
4. **contract v3 s10 stands.** Every role output reaches `main` only through a human-merged PR
   from the correctly-scoped branch (`board-gate.sh`, observed directly: a same-session attempt
   to touch another subject's `docs/issue-<n>/` tree from this branch was blocked). Any candidate
   that would need `main` writes from outside that flow, or a gate exception to allow them, has a
   real architectural cost — scored explicitly in the proposal, not waved through.
5. **Compactness / no new stored ground truth**, by analogy with issue #43's read-only-view
   condition already governing `flows`-adjacent design (cited in `docs/issue-54/reports/product/
   survey.md:52-60`): whatever this issue adds should be derivable from state that already
   exists (the issue body, `loop_state`), not a second place plan state can live and drift from
   GitHub's own record of it.

## Goals for the proposal

- Turn requirements 1-5 into acceptance criteria concrete enough for the implementation role
  (this issue's own step 2) to build against without further interpretation.
- Decide the requirement-4 gap with an explicit, scored comparison of candidate solutions
  (RICE), not just adopt the issue's stated preference by default.
- Keep every new obligation composing with the existing `run.md` loop and `flows`
  contract, rather than introducing a parallel mechanism.
- Register the go/keep/pivot rule this feature will actually be checked against once issues
  start using it, sized to what's really being decided (an internal workflow feature, not a
  user-facing growth bet).
