# Proposal — issue #189: execution plan in the issue body

Status: proposal (phase 1). Defines requirements 1-5 down to acceptance criteria and decides
the requirement-4 gap. Does not edit `on-the-record/commands/run.md`, `gates/flows.py`, or
`docs/specs/flows-schema.md` — those edits are this issue's own step 2 (implementation),
per this issue's self-declared execution plan.

D1 (no loop syntax), D2 (closure is human), D3 (no `repo-status-board` repo changes) are
treated as fixed and are not re-argued here.

## 1. Plan agreement at issue-open time

**Requirements 1 acceptance criteria:**

1.1 Plan block grammar (binding on the implementation edit to `run.md`):
```
## 실행 계획
- [ ] step <N>  <role>[ ‖ <role2> ...]
```
One line per step, in ascending `<N>`. Roles on a line are joined by ` ‖ ` and run in parallel;
each `<role>` token must be a member of `spawn.py`'s existing `ROLES` tuple — no per-issue role
vocabulary invention. `## 실행 계획` is the exact, literal block header; parsing stops at the
next `##` heading or end of body (matches the issue's own worked example verbatim).

1.2 When the orchestrator's existing role-classification step (`run.md` step 2, already
mandatory) anticipates more than one role session for the issue, the orchestrator proposes a
plan in conversation, gets the user's explicit go-ahead, and only then writes it — via `gh issue
create --body` (new issue) or `gh issue edit --body` (issue already exists) — never silently.
For an issue classified as single-role, a plan is optional; requirement 4's data contract must
therefore treat "no plan block present" and "plan block present" as distinctly observable (see
4.1), not force every issue through plan negotiation to satisfy this schema.

1.3 The plan is written only into the issue body. No new file, board record, or comment is
created to hold it (this is the direction the issue proposes; scored against alternatives in
§4 below, and adopted).

## 2. Minimal, auditable edits

**Requirement 2 acceptance criteria:**

2.1 All plan edits go through `gh issue edit --body` (the only body-edit primitive `gh` has);
never issue delete+recreate, which would discard GitHub's own edit history.

2.2 A plan edit changes only the plan block (step add/remove/reorder, a role added to an
existing step's `‖` group, or a checkbox flip) in a given `gh issue edit` call — not bundled
with unrelated body rewrites — so the issue's per-revision history stays legible as
plan-only changes. GitHub tracks this edit history natively (verified: `docs/en/issues/
tracking-your-work-with-issues/using-issues/editing-an-issue`, and reachable programmatically
via GraphQL `userContentEdits` if ever needed, per community discussion #33551 — not required by
any acceptance criterion here, since nothing in this issue's scope needs to *consume* the
history programmatically; the web UI already exposes it for human review).

2.3 No new audit-trail artifact is introduced — GitHub's own edit history is requirement 2's
record, satisfying it without new state.

2.4 Checking off a step's box happens only after that step is complete (§3.1's definition), and
only the orchestrator edits the plan block — a spawned role session never calls `gh issue edit`
on the subject issue's plan (write scope stays with the orchestrating conversation, the same way
board records belong to roles and not to the orchestrator, just inverted).

## 3. No auto-progress

**Requirement 3 acceptance criteria:**

3.1 A plan step is "complete" when every role listed on its line has reached PR merge (phase 2)
for that subject/role branch. A `‖`-joined step completes only when all of its roles have merged.

3.2 On step completion, the orchestrator reports it (composing with the existing step-5 PR-explain
obligation) and does **not** spawn the next step's role(s) in the same action — spawning happens
only after the user's explicit go-ahead in that turn, per the existing step-6 principle that
approvals/merges/spawns happen only once the user has said so in the conversation, never on
silence.

3.3 This is a `run.md` prose addition, not a new hook or gate — matching D1's "no
machine-evaluated routing table" and the fact that step 3's "who's next" judgment has never been
code-enforced in this repo. No new blocking mechanism is added to physically prevent an
early spawn.

3.4 Issue #120's rule stands even with a plan recorded: the orchestrator still states its
reasoning for spawning a step, citing the plan and the board — the plan supplies the *order*,
not a replacement for stating *why now*.

## 4. Visibility in `flows --json` — the requirement-4 gap

### 4.1 The gap, confirmed against the actual code

`flows_payload` (`gates/flows.py:160`) enumerates subjects from `spawn.board(root).items()`
(`gates/flows.py:188`), and `board()` (`spawn.py:974`) reads only
`docs/issue-<n>/reports/<role>.md` files present in the local checkout — merged records only.
An issue with a written plan and zero merged role records produces **no** `flows[]` entry at
all today. This is the issue body's stated gap, confirmed by reading the code, not assumed.

### 4.2 Candidate solutions, scored (RICE)

| Candidate | Reach | Impact | Confidence | Effort | RICE |
|---|---|---|---|---|---|
| **A. Plan lives in the issue body; `flows[].plan` sourced by reading issue state directly** [issue's stated direction] | 2 | 3 | 3 | 1 | **18** |
| B. New board-record file for the plan, committed straight to `main` | 2 | 2 | 2 | 2 | 4 |
| C. New gate/hook exception letting plan writes bypass branch-scoping | 2 | 1 | 1 | 3 | 0.7 |

*(1-3 scale, RICE = Reach × Impact × Confidence ÷ Effort. Reach is an estimate — issues likely
to be multi-step going forward — held equal across candidates since it doesn't discriminate
between them; it is not measured data and is labeled as an assumption here, unlike the code
citations below.)*

Justification:
- **B and C both collide with `board-gate.sh`'s live invariant**, observed directly in this
  session: a same-branch attempt to touch another subject's `docs/issue-<n>/` tree was blocked
  with "every role output reaches main only through a PR the human merges — never a direct write
  from another branch" (contract v3 s10). A plan file under `docs/issue-<n>/` is board territory
  under that gate's own rule; making it write-able outside the branch-scoped PR flow means either
  re-authoring s10's invariant (C) or adding an undocumented, unreviewed exception for exactly
  one file (B) — real architectural cost neither candidate's impact justifies, and no precedent
  exists in this repo for a second "direct-to-main is fine here" carve-out beyond the one-time
  bootstrap case for `docs/specs/approvers.md` (`run.md`'s precondition-checking section, which
  is explicitly a pre-board-existence bootstrap, not a repeatable pattern).
- **A has no such collision**: the plan lives in GitHub issue state, which was never board
  territory to begin with, so nothing about s10 is touched.

RICE selects Candidate A by a wide margin, and it matches the issue's stated preference — this
proposal adopts it, with one mechanical elaboration the issue's preference section didn't spell
out (§4.3).

### 4.3 Mechanism (binding on the implementation edit)

- **No new `gh` API call class is required, and the schema's own call budget is not violated —
  it can improve.** `gates/closure_sweep.py:_issue_view` (`gates/closure_sweep.py:53-56`)
  already makes one `gh issue view <n> --json state` call per subject inside
  `find_violations()`, which `flows_payload` already invokes (`gates/flows.py:259-260`). This is
  exactly the "up to `S` calls — `gh issue view`, one per subject" already documented in
  `docs/specs/flows-schema.md` §4 — not a new cost. The recommended direction: replace it with
  **one repo-wide `gh issue list --json number,state,body` call**, the same optimization this
  file already applied once to PRs (`_pr_list_all`, `gates/flows.py:38-50`, whose own comment
  states it "replaces an O(subjects × roles) loop... for `flows`"). One repo-wide call both
  supplies `state` (subsuming `closure_sweep`'s per-subject calls) and `body` (for plan
  parsing) for every open issue in a single round trip — a call-count *improvement* over
  today's contract, not a regression. This specific refactor (whether `closure_sweep._issue_view`
  is changed to accept pre-fetched state, or `flows_payload` special-cases this) is
  implementation's call; the binding constraint is the call-count outcome, not the code shape.
- `flows_payload`'s subject enumeration expands from `spawn.board(root).items()` alone to the
  union of that and any **open** issue whose body contains a `## 실행 계획` block — this is what
  actually closes the "invisible before first merge" gap; adding the `plan` field alone, without
  this enumeration change, would not (a subject `board()` doesn't know about never enters the
  existing per-subject loop regardless of what fields that loop computes).
- `flows[].plan` (new, additive field): `null` when the issue body has no plan block (mirrors
  the existing `stage_derived`/`last_activity: null` idiom for "this wasn't present," rather than
  an empty list that would read as "plan present, zero steps"); otherwise a list of
  `{"step": <int>, "roles": [<str>, ...], "done": <bool>}`, parsed per §1.1's grammar. For a
  subject with a plan but no merged board record, the existing code already degrades the other
  `flows[]` fields sensibly with no further change: `_stage_for(None)` (`gates/flows.py:32-35`)
  already returns `("(none)", False)`, and `roles: []` falls out naturally from an empty board
  entry — the change is genuinely additive, not a restructure.
- `docs/specs/flows-schema.md` §2.2 gets one additive edit documenting `flows[].plan`. Per the
  schema's own §3 versioning policy ("a new field appended to an existing object... never bump
  `schema_version`"), this does **not** require a version bump — correcting the issue body's
  "필드 추가 = 버전 범프" framing against what the schema doc actually specifies. What the issue's
  constraint bullet gets right, and what stays true here: `repo-status-board` holds its own copy
  of this schema doc and needs it manually synced to learn about the new field regardless of
  version number — real, and out of scope here per D3 (separate issue, that repo).

### 4.4 Acceptance criteria

1. `flows --json` includes an entry for any **open** issue with a `## 실행 계획` block, even when
   `spawn.board()` has no record for that subject (the binding test for "visible from creation
   onward," not merely "field exists").
2. `flows[].plan` is `null` when no plan block exists, and a list of `{step, roles, done}`
   objects (per §4.3) when one does.
3. No new `gh` API call class is added; the total per-subject `gh issue view`-class call count
   stays at or below what `docs/specs/flows-schema.md` §4 already documents.
4. `docs/specs/flows-schema.md` is updated additively (§2.2 gets the new field documented);
   `schema_version` stays `1`.
5. No new file, board record, or gate/hook is added to satisfy this requirement.

## 5. Plan exhaustion → human-confirmed closure

**Requirement 5 acceptance criteria:**

5.1 "Plan exhausted" = every step in the recorded plan is complete (§3.1). The orchestrator
detects this from the plan block's checkbox state plus board state — no new signal.

5.2 On detecting plan-exhausted, the orchestrator reports it to the user as its own distinct
statement (composing with, not folded silently into, individual steps' own approval/merge
prompts).

5.3 `gh issue close` runs only after the user affirmatively confirms completion in that
conversation — silence is not confirmation, reusing the principle `run.md` already states for
its decision-queue relay rather than restating it as new prose.

5.4 `gates/closure_sweep.py`'s detect-only contract (`gates/closure_sweep.py:5-6`,
`OPEN_PR_ON_CLOSED_ISSUE` / `MERGED_DELIVERY_ISSUE_OPEN`) is unchanged — no new violation kind,
no code path gains the ability to close an issue itself.

5.5 No new gate — 5.1-5.3 are `run.md` prose additions (steps 5/6), consistent with D1/D2.

## Hypothesis package (pre-registered)

We believe requiring a proposed plan at issue-open time for anticipated multi-step issues
(§1.2) will make declaring parallel steps — available but never once used in this repo's
history (0/54 issues, per the issue body's own measurement, not independently re-run here) —
practical enough to actually get reached for, not just theoretically available.

- **Metric**: among the next 10 issues opened after this ships that turn out multi-step (plan
  with ≥2 steps), the count that declare at least one `‖` parallel grouping.
- **Decision rule**: **go** (keep the format as specified) if ≥1 of 10 declares a parallel step;
  **pivot** (keep the checkbox format, but revise `run.md`'s plan-proposal prompt to actively
  suggest parallelizable steps rather than leaving discovery to the user) if 0 of 10 do; **kill**
  the "always propose a plan for anticipated multi-step issues" mandate — make plan-writing fully
  opt-in — if fewer than 5 of those 10 issues even end up with a plan recorded at open time (the
  obligation itself going unused, an execution-observation-detectable signal, not a format
  question).
- **Guardrail metric**: average plan edits after the initial write stays ≤2 per plan across the
  same 10-issue window (calibrated to D1's cited precedent: issue-162's phase-2 follow-up
  (`docs/issue-162/reports/implementation.md`, an unplanned post-hoc rework session, confirmed
  by reading that file) was handled, per the issue body, by adding one line to the plan rather
  than a loop construct). Exceeding this while the primary metric looks fine is a reduced-trust
  result: it means plans are being drafted carelessly at open time and patched repeatedly,
  which requirement 1's "agree in conversation, then write" step exists to prevent.
- **ITWWS**: if go, and the guardrail holds — extend `run.md` step 3 ("누구를 깨울지") so the
  orchestrator's per-turn judgment explicitly reads the recorded plan first, not just the raw
  board, promoting the plan from "declared once" to "consulted every step." Deferred to a
  follow-up issue; not actioned until the 10-issue measurement window above resolves.

## Out of scope

- Any `repo-status-board` repo change (D3) — only this repo's `flows --json` data contract.
- New loop/repeat syntax (D1).
- Any automated `gh issue close` path (D2) — `closure_sweep` stays detect-only.
- Redefining the existing 6-value `stage` vocabulary or `_stage_for`'s mapping.
- A rendering/dashboard treatment of `plan` — that belongs to `repo-status-board`, a separate
  issue in that repo per D3.
- Making plans mandatory for issues classified single-role at step 2 (§1.2 keeps them optional
  there).

## Scope for the implementation stage (this issue's own step 2)

Implements: the `run.md` prose additions (§1-3, §5) and the `flows.py`/`flows-schema.md`
additive changes (§4), conformant iff all acceptance criteria in §1-§5 above hold. The
hypothesis package's metric/guardrail is not implementation's concern — it's checked later
(execution-observation, this issue's own step 3, and beyond, per the 10-issue window) once the
feature has real usage to measure.
