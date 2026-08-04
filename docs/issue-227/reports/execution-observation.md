---
subject: issue-227
role: execution-observation
observed_role: implementation
observed_pr: 254
code_under_review: 144b413a1a2f4eff6458cf4bdc114622ddffdd4c
loop_state: observing
---

# Execution-observation record — issue #227, step 2

## Independence

This role did not author, edit, or execute any part of the observed
artifact, in this session or any other. `on-the-record/commands/run.md`,
`docs/handbooks/operations.md`,
`docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md`,
`docs/issue-227/proposals/implementation.md`,
`docs/issue-227/reports/implementation.md`, and
`docs/issue-227/reports/implementation/survey.md` were read only. Every
citation below that names a line in a file PR #254 wrote addresses the
blob at commit `144b413` extracted with `git show 144b413:<path>`, not
the working tree — two sibling merges (`564503f` for issue-258,
`b3ba234` for issue-245) shifted `run.md` by +13 lines after `144b413`,
so a HEAD-relative citation would not resolve to the reviewed text. No
gate function was run: `gates/flows.py::_pr_approved()` and
`spawn.py::approve_scope()` were neither executed nor read as evidence
of what the observed session did. The only path this branch writes in
phase 2 is `docs/issue-227/reports/execution-observation.md`; the
phase-1 paths were `docs/issue-227/reports/execution-observation/` and
`docs/issue-227/proposals/execution-observation.md`. Findings are
returned here and nowhere else: no issue was filed, no edit was made to
the observed role's write set, and no approval was rendered or relayed.

Everything after this section is verdict-bearing.

## What was done

Executed the approved observation plan
(`docs/issue-227/proposals/execution-observation.md:39-97`, approved via
issue comment
https://github.com/tokenmaxxxer/on-the-record/issues/227#issuecomment-5173982137):
rendered the three verdict levels against PR #254's produced artifacts,
and ran the plan's two gap-aimed checks — check A (drift across every
surface carrying the approval canon, `:61-75`) and check B
(documented-rule-vs-measured-operation, `:77-91`), the latter re-measured
today rather than inherited from the phase-1 survey. Nothing was
re-executed; no `src/` file was read as evidence.

## Why (the approval basis for this phase)

Issue #227's `## 실행 계획` lists step 2 as `execution-observation` of
step 1. Phase 2 of this observation opened on the issue-level comment
https://github.com/tokenmaxxxer/on-the-record/issues/227#issuecomment-5173982137
— body exactly `APPROVE issue-227/execution-observation`, author
`jjongkwann`, 2026-08-04T02:40:36Z — whose login is listed at
`docs/specs/approvers.md:2`. Single-account mode (this PR's author is
the same account), which contract v3 s19 and `protocol.md:239-246` name
as the path where the issue comment is the only approval channel.

## Upstream basis — what PR #254 is

- Observed role `implementation`, branch `issue-227/implementation`,
  PR #254, MERGED 2026-08-04T02:03:57Z as `a4eca54` (`gh pr view 254
  --json state,mergedAt,mergeCommit`).
- `75f32f0f` (2026-08-03T11:08:55Z) — phase 1: survey, scout brief,
  proposal (+366, 3 files).
- `681f61e4` (2026-08-03T12:24:15Z) — phase-1 rework (+163/−39, 2 files).
- `144b413` (2026-08-04T01:29:51Z) — phase-2 content (+140/−0, 3 files).
- `6fee354` (2026-08-04T01:41:05Z) — phase-2 record (+291, 1 file).

## Evidence read this session

Issue #227 body and all four issue comments (`gh api
repos/tokenmaxxxer/on-the-record/issues/227/comments`); PR #254 metadata
including `reviews` → `[]` and all four commit objects; the full diff of
`144b413` for all three files; `git show 144b413:on-the-record/commands/run.md`;
`docs/issue-227/reports/implementation.md` (291 lines, in full);
`docs/issue-227/proposals/implementation.md`; the PR-level rework comment
https://github.com/tokenmaxxxer/on-the-record/pull/254#issuecomment-5166178716;
`protocol.md:212-266`; `README.md:35-69`; `docs/handbooks/operations.md:115-136`
and `:305-340`; `docs/specs/approvers.md`; and today's issue comments on
#224, #227, #245, #246, #258, #262, #266.

## Check A — every surface carrying the approval canon

Five loci carry the `APPROVE issue-<n>/<role>` canon (located by grep
over `protocol.md`, `README.md`, `docs/handbooks/operations.md`,
`on-the-record/commands/run.md` this session). `144b413` wrote two of
them plus a new decision doc. Position of each, re-derived here rather
than inherited from the observed record's own clean check:

| Surface | Touched by `144b413`? | Consistent with the landed recipe? |
| --- | --- | --- |
| `protocol.md:219-222` (definition: exact whole-body token) | No | Yes — the recipe's comment A is exactly that token and nothing else (`144b413:run.md:204-205`), so the definition is narrowed by usage, never contradicted. |
| `protocol.md:239-246` (canonical location + "do not reintroduce a second signal location without updating all three together") | No | Yes, and the clause does not reach this change: both comments of the recipe are issue comments (`144b413:run.md:202-206`, `operations.md:318-322`), so no second signal location is introduced. `:241-242`'s claim that `run.md` and README follow the same canon still holds after `144b413`. |
| `README.md:41`, `README.md:63-64` | No | Yes — README already relays feedback and approval as two separate acts ("feedback as a comment, approval as an `APPROVE …` comment"), which is the same separation the recipe canonicalizes. |
| `docs/handbooks/operations.md:312-316` (English canon) | Yes — recipe + warn appended at `:318-334` | Yes. |
| `docs/handbooks/operations.md:124-127` (Korean canon, a second copy of the same rule inside the same file) | No | Canon itself agrees, but this copy carries neither the recipe nor the warn policy — see finding 3. |

Cross-file agreement between the two surfaces that were written was
re-derived independently, not inherited: order (A then B), the
token-only-forever rule, the issue-thread location, the near-miss
definition (contains literal `APPROVE`, not whole-body-identical), the
one-reply-never-repeated rule, and the issue-#224 parenthetical all
appear in both `144b413:run.md:202-215` and
`docs/handbooks/operations.md:318-334`. No divergence found — the same
conclusion the observed record reached at
`docs/issue-227/reports/implementation.md:223-227`, reached separately.

## Check B — the documented rule against today's measured operation

Measured today (2026-08-04, UTC), repo-wide across every issue with
activity today, read this session via `gh api
repos/tokenmaxxxer/on-the-record/issues/<n>/comments`:

| Issue | Comment | Time (UTC) | Author | Shape |
| --- | --- | --- | --- | --- |
| #258 | `#issuecomment-5173206686` | 00:31:49 | JiwonJung94 | token-only, 32 chars: `APPROVE issue-258/implementation` |
| #258 | `#issuecomment-5173254208` | 00:39:40 | JiwonJung94 | token-only, 36 chars: `APPROVE issue-258/conformance-review` |
| #224 | `#issuecomment-5173757435` | 02:04:03 | jjongkwann | token-only, 39 chars: `APPROVE issue-224/execution-observation` |
| #227 | `#issuecomment-5173758897` | 02:04:17 | jjongkwann | prose only, no `APPROVE` substring (재오픈 note) |
| #227 | `#issuecomment-5173982137` | 02:40:36 | jjongkwann | token-only: `APPROVE issue-227/execution-observation` |
| #262 | `#issuecomment-5173982238` | 02:40:37 | jjongkwann | token-only, 32 chars: `APPROVE issue-262/implementation` |
| #224 | `#issuecomment-5173983185` | 02:40:46 | jjongkwann | prose only, 76 chars (acceptance note) |

Three of the five token comments (#224 02:04:03, #227 02:40:36, #262
02:40:37) postdate the merge of `144b413` into `main` (`a4eca54`,
02:03:57Z), so they are the first live relays under the landed recipe.

What the measurement shows, stated plainly:

1. **The gate-relevant invariant holds, without exception.** 5 of 5
   token-bearing comments today are whole-body token-only. Taking the
   union of today's seven with the eight specimens in
   `docs/issue-227/reports/execution-observation/survey.md:124-133` (two
   overlap: `#224#issuecomment-5173757435`, `#227#issuecomment-5173758897`)
   gives 13 distinct relay comments — 9 token-only, 4 prose-only, and
   0 of the mixed token+prose shape issue #227 was opened about.
2. **The warn policy has had no occasion to fire.** Zero near-misses
   (comments containing `APPROVE` but not whole-body-identical) in the
   measured window, so the policy at `144b413:run.md:209-215` /
   `operations.md:327-334` is documented and untested in the field. Not a
   defect; a stated limit on what this observation can confirm.
3. **The conditional-approval case the recipe governs did not occur.**
   Where feedback and approval both appear on one issue, all three
   observed pairs are feedback-first-then-token, minutes-to-hours apart
   — #227 `#issuecomment-5163763980` (2026-08-03T07:59:58Z) →
   `#issuecomment-5166285829` (12:26:37Z); #227 today
   `#issuecomment-5173758897` (02:04:17Z) → `#issuecomment-5173982137`
   (02:40:36Z); #246 `#issuecomment-5165949228` (2026-08-03T11:52:01Z) →
   `#issuecomment-5166140486` (12:11:26Z) — whereas the landed recipe
   prescribes token-first (`144b413:run.md:207-208`,
   `operations.md:322-325`). See finding 2.

## Verdicts

### Outcome — landed, with one qualification

PR #254 landed what issue #227 asked. Item by item, each against the
artifact that settles it:

- **요구사항 1** (canonical conditional-approval form; order and location
  specified) — met. `144b413:run.md:202-208` states two issue comments in
  order, (a) body exactly the token with no text before or after under any
  circumstance, (b) immediately after on the same issue, carrying feedback
  and pointing at (a); mirrored at `operations.md:318-325`. Location
  (issue thread, not PR) is explicit in both.
- **요구사항 2** (confirm what the gate actually recognizes, and record the
  confirmation as evidence — explicitly by measuring a comment with text
  around the token) — met.
  `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md:41-56`
  records executed results with inputs and outputs: both real rsb #20/#23
  bodies → `False` from `_pr_approved()` and `SystemExit` from
  `approve_scope()`, a token-only control → `True` / `rc=0`, and a
  synthetic prose-before-token variant → `False`. The prose-before variant
  is the issue's "토큰 앞뒤에 텍스트가 붙은 코멘트" measurement. This role did
  not re-execute those runs — see "What this observation did not check".
- **요구사항 3** (state the relationship to #224 without absorbing it) —
  met, in all three written surfaces: decision doc `:102-108`,
  `144b413:run.md:213-215`, `operations.md:331-334`, each naming the
  `/scope`-vs-`/role` mismatch and the 30-comment pagination cap as
  code-side and #224's.
- **제약 1** (do not change the gate's own matching logic) — honoured. No
  source file appears in any of PR #254's four commits: `75f32f0f` 3 docs,
  `681f61e4` 2 docs, `144b413` 2 docs + `run.md`, `6fee354` 1 doc
  (`git show --stat` on each).
- **제약 2** (no new approval grammar) — honoured. The only token in the
  diff of `144b413` is the existing `APPROVE issue-<n>/<역할>`; the warn
  action is a reply comment, not a second grammar
  (`144b413:run.md:209-215`).
- **Follow-up (a)** (make the doc agree with the detection logic's actual
  strict behaviour) — met. Decision doc `:41-44` states the matcher as
  whole-body equality after `strip()`, and both written surfaces state the
  token-only-forever rule that follows from it (`144b413:run.md:204-205`,
  `operations.md:319-321`).
- **Follow-up (b)** (decide how a session meeting a non-canonical form
  behaves — abort / warn / log-only) — met as a decision, with the
  tradeoff table and chosen rationale at decision doc `:80-100` and the
  policy stated at `144b413:run.md:209-215`. **The qualification**: the
  requirement names the 역할 세션 (role session) as the actor
  (https://github.com/tokenmaxxxer/on-the-record/pull/254#issuecomment-5166178716),
  and what landed addresses the orchestrator. Finding 1.

### Trajectory — sound

The phase-1→phase-2 path holds at every checkpoint, by timestamp:

- **Surveyed and scouted before proposing.** `75f32f0f`
  (2026-08-03T11:08:55Z) carries
  `docs/issue-227/reports/implementation/survey.md` (+157),
  `.../scout-brief.md` (+74), and the proposal (+135) — the survey and
  scout artifacts exist as their own files in the phase-1 homes, not
  folded into the proposal.
- **The human's refusal was real and was answered.** The PR-level comment
  https://github.com/tokenmaxxxer/on-the-record/pull/254#issuecomment-5166178716
  (2026-08-03T12:15:13Z) says "현행 제안은 승인하지 않는다" and demands two
  additions; `681f61e4` (12:24:15Z, +163/−39) is the rework, and both
  demanded items appear in the reworked proposal
  (`docs/issue-227/proposals/implementation.md:30-36`, `:107-134`).
- **A real approval event preceded phase-2 work.** Issue comment
  https://github.com/tokenmaxxxer/on-the-record/issues/227#issuecomment-5166285829
  (2026-08-03T12:26:37Z, `jjongkwann`, body exactly `APPROVE
  issue-227/implementation`), account listed at `docs/specs/approvers.md:2`;
  `gh pr view 254 --json reviews` → `[]`, so single-account mode is the
  only path and the issue comment is it. Phase-2 content `144b413` was
  committed 2026-08-04T01:29:51Z — about 13 hours after the approval, and
  no phase-2 file exists in any commit before it.
- **The phase-2 work stayed inside the approved write set.** `144b413`
  touches exactly the three files the proposal's `files:` list names
  (`docs/issue-227/proposals/implementation.md:9-12`), and `6fee354`
  touches only the record. Nothing outside.
- **One event worth recording, not a defect.** PR #254's body carries
  `Closes #227` while the issue's 실행 계획 still had step 2 open, so the
  merge (`a4eca54`, 02:03:57Z) auto-closed the issue and the human
  re-opened it 20 seconds later
  (https://github.com/tokenmaxxxer/on-the-record/issues/227#issuecomment-5173758897,
  02:04:17Z), calling it "closes-gate 활성화 전 마지막 사례". Under the rule in
  force at merge time that is the known state issues #228/#245 track, not
  a deviation by this role.

### Step — which artifact is deficient

- `144b413:run.md:209-215` and `operations.md:327-334` (the warn policy):
  **the one deficient artifact**, and only in its addressee — finding 1.
  Its substance (never treat a near-miss as approval; one reply; no
  repeats) matches the approved proposal item 2
  (`docs/issue-227/proposals/implementation.md:146-152`) exactly.
- `docs/handbooks/operations.md:124-127`: carries the approval canon
  without the conditional-approval rule — finding 3, low severity.
- `144b413:run.md:202-208` / `operations.md:318-325` (the recipe): not
  deficient as written; its ordering clause has no field evidence behind
  it and an adjacent real shape it does not classify — finding 2.
- The decision doc: **not deficient.** Every line reference it makes to
  itself resolves — `:41-56` is the empirical-evidence block, `:80-100`
  the warn rationale, `:102-108` the #224 relationship (checked this
  session).
- The observed role's own record
  (`docs/issue-227/reports/implementation.md`): **not deficient.** All six
  `closed_checks` refs and every in-body citation resolve against the
  reviewed commit — `run.md:183` is the step-6 header, `:202-215` is
  exactly the two new bullets, `:209-215` is the warn bullet, `:219-221`
  is the pre-existing 승인·머지 gate, all verified with `git show
  144b413:on-the-record/commands/run.md`; `operations.md:318-334` resolves
  at HEAD as well. The refs read as wrong against today's `main` only
  because `564503f` and `b3ba234` shifted `run.md` afterwards — a property
  of unpinned line citations in this repo's record convention, not an
  error by this role.

## Finding 1 — the warn duty's addressee is not the actor the requirement named

**Impact.** The follow-up requirement asked what a **역할 세션** does on
meeting a non-canonical near-miss
(https://github.com/tokenmaxxxer/on-the-record/pull/254#issuecomment-5166178716:
"비정규 형태를 만난 역할 세션의 행동"). What landed states the duty in two
orchestrator-facing surfaces: `144b413:run.md:209-215` sits inside step 6,
"사용자의 결정을 중계한다" (`144b413:run.md:183`), which is the
orchestrator's relay step, and `operations.md:327-334` is the operations
handbook. The surface role sessions actually receive — `protocol.md`
§5, whose `:240-241` says role sessions "are told this at session start"
— carries no near-miss or warn text at all (grep for 조건부 / near-miss /
warn / two-comment over `protocol.md` and `README.md` this session: zero
hits). So the loop-closing rationale the decision doc gives for choosing
warn over log-only — "the human learns within the same turn instead of 18
minutes later (rsb #23)", decision doc `:80-100` — is realized only when
the orchestrator is the one that meets the near-miss. In both cited rsb
incidents the actor that proceeded on a near-miss was a role session.

**Timeline.** 2026-08-03T12:15:13Z the rework comment names 역할 세션 →
12:24:15Z `681f61e4`'s reworked proposal keeps "what a role session does"
in its rationale (`docs/issue-227/proposals/implementation.md:107-108`)
but assigns the action to "the orchestrator" in What-will-be-done item 2
(`:146-152`) → 12:26:37Z the human approves that proposal
(`#issuecomment-5166285829`) → 2026-08-04T01:29:51Z `144b413` lands the
orchestrator-facing text → 01:41:05Z the record's hunt finding 2
(`docs/issue-227/reports/implementation.md:198-211`) names the same actor
ambiguity and dispositions it non-blocking by citing the proposal's Out of
scope, which defers the detection **code**
(`docs/issue-227/proposals/implementation.md:180-185`), not the addressee.

**Root cause.** The actor changed between the requirement and the approved
plan, and no surface recorded that change as a decision. Because the
change entered at the proposal stage and the human approved that proposal,
this is not a phase-2 deviation — it is a requirement-to-plan drift that
the record's own hunt spotted and then closed against a scope clause about
a different question (code wiring vs. who the rule addresses).

**Action item** (for the human to judge; this role files nothing and edits
nothing here): either add one line to `protocol.md` §5 stating what a role
session does on a near-miss — treat as feedback and say so once — or add a
line to the decision doc recording that the warn duty is the
orchestrator's alone and the role session's duty stays "a near-match is
feedback, not approval" per contract v3 s19. Both targets are outside this
role's write set.

## Finding 2 — the ordering clause has no field evidence, and the adjacent real shape is unclassified

**Impact.** The recipe makes token-first ordering load-bearing — "토큰이
먼저이므로 (a)가 올라간 순간 이미 유효한 승인" (`144b413:run.md:207-208`),
"Token-first ordering means a valid approval already stands the instant
comment A lands" (`operations.md:322-325`). In all 13 measured specimens
(check B above plus
`docs/issue-227/reports/execution-observation/survey.md:124-133`) the
same-breath conditional approval the recipe governs never occurs; the
three feedback+approval pairs are all the reverse order, feedback comment
first and a token-only approval later. Nothing in the landed text says
that sequential shape is fine, so a reader checking a conforming relay
(#227 `#issuecomment-5173758897` → `#issuecomment-5173982137`, today,
36 minutes apart) against `run.md` finds it does not match the only
documented recipe.

**Timeline.** Recipe committed 2026-08-04T01:29:51Z (`144b413`), merged
02:03:57Z (`a4eca54`); the three post-merge approvals today are all
token-only and all conforming on the invariant that matters to the gate;
the feedback-first pair on #227 straddles the landing (02:04:17Z →
02:40:36Z).

**Root cause.** The recipe was derived from two out-of-repo incidents
(decision doc `:41-56`), both of which are the same-breath shape. The
in-repo dominant shape — feedback relayed first, approval posted later —
was outside the sample the recipe was written from, and the survey that
recorded it (`survey.md:139-142`) noted the ordering mismatch but was
phase-1 material for a different role.

**Action item** (human's call): one sentence in `run.md` step 6 and
`operations.md` stating that the ordinary sequential flow — feedback via
`gh pr comment`, approval later as a token-only issue comment — remains
canonical, and that the two-comment recipe governs the same-breath case.
Severity low: no measured relay was mis-gated by this gap.

## Finding 3 — one copy of the approval canon was left un-mirrored

**Impact.** `docs/handbooks/operations.md` states the canonical approval
location twice — Korean at `:124-127`, English at `:312-316`. The recipe
and warn policy landed only after the English one (`:318-334`). A reader
who reaches `:124-127` gets the token canon with no conditional-approval
rule, in the same file that carries it 190 lines later. Low impact: the
Korean-facing relay surface that actually drives the orchestrator is
`run.md`, which does carry it (`144b413:run.md:202-215`).

**Timeline.** Present from `144b413` (2026-08-04T01:29:51Z) onward;
`operations.md:124-127` is unchanged by that commit (`git show --stat
144b413`: `operations.md` +18, all in the `:318-334` block).

**Root cause.** The approved write set named a single section — "the
existing canonical-approval-location section (~line 309-364)"
(`docs/issue-227/proposals/implementation.md:153-155`) — and the second
copy sits outside it. This is the un-synchronized-duplicate class
`protocol.md:244-246` warns about for signal locations, here in a milder
form (a doc copy, not a signal location).

**Action item** (human's call): mirror the recipe at `:124-127` or make
that block cross-reference `:318-334`.

## What this observation did not check, and why

- **The empirical gate runs at decision doc `:41-56` were not
  re-executed.** Re-running the observed role's code is prohibited for
  this role; the artifact's record of the run is admissible, its
  reproducibility is not independently re-derived here.
- **`spawn.py:916` (issue #227 body) vs `spawn.py:917` (decision doc
  `:104`)** — a one-line divergence between two documents, not
  adjudicated. Settling it means reading `src/` as current-state
  evidence, which this role does not do.
- **The observed record's clean check `decision-doc-line-citations-current`
  (`docs/issue-227/reports/implementation.md:228-230`)**, which asserts
  `gates/flows.py:131-132` matches actual line content, is unverified here
  for the same reason. Its sibling checks that live in documents were
  verified and hold.
- **The hunt stance-rotation claim
  (`docs/issue-227/reports/implementation.md:165-179`)** was not audited
  against the sibling records it cites; nothing in this record depends on
  it.

## Open findings

1. **Finding 1 — the warn duty's addressee.** Confirmed against the
   artifacts (`144b413:run.md:183`, `:209-215`; `operations.md:327-334`;
   `protocol.md:239-246`). Not fixed here: every candidate edit lands in
   `protocol.md` or the observed role's decision doc, both outside this
   role's write set. This is the one worth the human's attention.
2. **Finding 2 — ordering clause vs. measured practice.** Confirmed by
   measurement (check B). Low severity, documentation-completeness.
3. **Finding 3 — `operations.md:124-127` un-mirrored.** Confirmed by
   direct read. Low severity.

**Resolution path.** All three return to the human on this role's PR and
are theirs to judge; under contract v3 issues are user-authored only, so
this role filed none. Findings 2 and 3 are absorbable by whatever issue
next touches those files. Finding 1 is the one that changes behaviour if
the human agrees with it.

## Next steps

1. Commit this record on `issue-227/execution-observation` and flip
   `loop_state` to `landed`.
2. Push and update PR #264, which carries this record as its sole phase-2
   artifact.
3. Stop. Merge or closure of that PR is the human's act.
