---
subject: issue-271
role: execution-observation
observed_role: implementation
observed_pr: 273
observed_commits:
  - ddc9b0f  # phase 1 — survey + scout brief + proposal (docs only)
  - 6cd0ef2  # phase 2 open — implementation record skeleton
  - 1cab34b  # phase 2 delivery — ci.py + tests + docs
  - e2bac95  # post-landing rebase record
observed_merge: c6c4363
loop_state: landed
---

# Execution-observation record — issue #271, step 2

Phase 2 opened on the approval comment
<https://github.com/tokenmaxxxer/on-the-record/issues/271#issuecomment-5175349156>,
body byte-exact `APPROVE issue-271/execution-observation`, author
`jjongkwann`, listed in `docs/specs/approvers.md`. Single-account mode
applies: PR #274's author is `jjongkwann` (`gh pr view 274 --json author`,
this session), the same account, so the issue-comment path of contract v3
§19 is the correct one and no PR review Approve was required or sought.
The issue carries exactly two comments (`gh api
repos/:owner/:repo/issues/271/comments`, this session) — the other is
`APPROVE issue-271/implementation`
(<https://github.com/tokenmaxxxer/on-the-record/issues/271#issuecomment-5174945207>),
which opened the observed role's phase 2. Neither is a near-match; there
is no approval-shaped comment on this issue that fails the string test.

## Independence

This role did not author, edit, or participate in producing any artifact it
judges here. PR #273, its four commits, and every file they touched —
`gates/ci.py`, `gates/test_closes_gate_ci.py`, `test_spawn.py`,
`docs/handbooks/operations.md`,
`docs/issue-271/proposals/2026-08-04-closing-trigger-surface-coverage-and-phase-predicate-separation.md`,
`docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`,
`docs/issue-271/reports/implementation.md`,
`docs/issue-271/reports/implementation/survey.md`,
`docs/issue-271/reports/implementation/scout-brief.md` — were produced by
the `implementation` role on branch `issue-271/implementation` and merged
to `main` as `c6c4363` before this session began. This session modified
nothing under those paths and re-executed none of that code: no test run,
no gate invocation, no `spawn.py` call. This session's entire write set is
`docs/issue-271/reports/execution-observation.md` and
`docs/issue-271/reports/execution-observation/`.

## What was done

The phase-1 plan's declared checks — O1–O6 (outcome), T1–T5 (trajectory),
P1–P6 and R1–R4 (step and rebase integrity), all named in
`docs/issue-271/proposals/2026-08-04-execution-observation-of-pr-273.md`
before any evidence discussion — were each answered against the merged
tree at `c6c4363` and the four branch commits. Three verdict levels are
rendered below, with four findings (F1–F4) carrying the blameless
four-part shape. No re-execution of the observed role's code was
performed; the execution boundary is stated under "Inspection ceiling".

## Why

Issue #271's execution plan, step 2, asks for independent execution
observation of step 1 — the implementation role's session, delivered as
PR #273 and merged as `c6c4363`. The observation exists so a human can see
whether that session's phase-1→phase-2 path and its landed artifacts hold
up, judged from what it produced rather than from a re-run of its work.

## Upstream basis

- Issue #271 body and execution plan (`gh issue view 271`, this session).
- This role's phase-1 artifacts, committed as `4b6f478`:
  `docs/issue-271/reports/execution-observation/survey.md`,
  `.../scout-brief.md`, and
  `docs/issue-271/proposals/2026-08-04-execution-observation-of-pr-273.md`.
- The approval comment cited at the top of this file.

## Inspection ceiling (stated, not implied)

Two questions here are settled by structural reading where the formally
correct evidence would have been execution, and this record does not blur
the difference:

- **The drain-guard test's discrimination (O4).** The scout brief names
  mutation testing — delete the guard, the test must fail — as the
  execution-based proof, and records it as prohibited for this role
  (`docs/issue-271/reports/execution-observation/scout-brief.md`, "Adopt /
  skip"). What is done below instead is a control-flow trace of the landed
  arrangement against the landed guard; the trace is conclusive on its own
  terms and is labelled as a trace, not a run.
- **The rebase (R1–R4).** `git range-diff` is unavailable: the pre-rebase
  head is unrecoverable (survey S5 — timeline exposes only `e2bac95`,
  branch deleted 06:00:23Z, no reflog in this clone). The substitute the
  scout brief adopts — three-dot re-review of `git diff 1d7df88 c6c4363`
  as if the branch were new, asking the semantic-conflict question per
  co-touched file — is what was actually run.

## Evidence read this session

`gh issue view 271` and its comments API; `gh pr view 273 --json ...`
(state MERGED, `reviews: []`, mergeCommit `c6c4363`); `gh pr view 274
--json author`; `docs/specs/approvers.md`; `git show 1cab34b -- gates/ci.py`
(full hunk set); `git show c6c4363:gates/ci.py` (`check()` tail and
`main()`); `git show c6c4363:gates/test_closes_gate_ci.py` (all 26 `t_`
functions, bodies of the branch/approval/autodetect/pagination cases);
`git diff 1d7df88 c6c4363 --stat` and the full `test_spawn.py` and
`docs/handbooks/operations.md` deltas; `git show c6c4363:spawn.py`
(`_watch` follow loop, `_issue_comments`); `git show c6c4363:gates/flows.py`
(`_pr_approved`); `git show c6c4363:test_flows.py`; the observed role's
record, proposal, decisions file, survey and scout brief at `c6c4363`;
`git show 9d1394f --stat` (issue #247's phase-2 commit, the change rebased
over).

## Level 1 — OUTCOME: did PR #273 land what issue #271 asked

**Verdict: landed, with one qualification** — all four requirements are
delivered in the merged tree at `c6c4363`; the qualification is F3, an
undeclared widening of the new approval predicate that runs in the
fail-open direction relative to contract v3 §19.

| # | Requirement | Finding, with source |
|---|---|---|
| O1 | Req 1a — trigger-surface enumeration, first output, per-surface table, mitigations for uncoverable surfaces | **Met.** Rows A–H at `docs/issue-271/proposals/2026-08-04-closing-trigger-surface-coverage-and-phase-predicate-separation.md:48-57` @ `c6c4363` cover body / title / branch commit / squash / rebase / merge-commit / manual retype / manual sidebar link, with D–F argued as transitively covered and G–H named uncoverable with mitigations. Row H's mitigation records a real negative test — `closingIssuesReferences` was empty on a PR that in fact auto-closed via a commit message (same line range) — which is the fact this role's scout independently found in GitHub's linking doc (`scout-brief.md`, category must-bes). |
| O2 | Req 1b — same-class sweep of the gate system | **Met.** The proposal's "Same-class sweep" paragraph (same file, immediately after the table) names one further member, `gates/closure_sweep.py`'s `_refs_issue()` at `:29-35`, reports a repo-wide grep of the `_CLOSES_REF`/`_pr_view` family finding exactly two files, and states why the second is left unfixed (it never blocks a merge). A named member plus a named search scope plus a stated non-fix reason is what requirement 1's second ask demands. |
| O3 | Req 2 — phase signal separated from the closing-keyword predicate, proven through the wired form | **Met.** `_phase_from_body` is deleted and `_autodetect_issue_phase` now calls `_phase_from_approval(repo, pr, issue, role)` (`git show 1cab34b -- gates/ci.py`, hunks at `_phase_from_body`→`_phase_from_approval` and at `_autodetect_issue_phase`); the new predicate reads only approvals and never touches `_closes_ref_for_issue`. `t_autodetect_reachability_fix_blocks_closes_keyword_without_approval` (`gates/test_closes_gate_ci.py:290` @ `c6c4363`) drives `_autodetect_issue_phase` → `check(..., closes_only=True)` in the same order `main()` composes them (`gates/ci.py:312-322` @ `c6c4363`), asserts phase resolves to `phase1` on a body that literally says `Closes #245`, and asserts the block fires — i.e. the autodetect path, not the `--phase`-supplied call the issue calls insufficient. Residual, not a defect: neither test enters through `main()`'s argv parsing; see the qualification under Level 3. |
| O4 | Req 3 — drain-guard discriminating test restored | **Met, verified by control-flow trace.** The arrangement at `test_spawn.py:3765-3772` @ `c6c4363` registers a live roster entry with a dead `wrapper_pid`, then appends `progress` and `session-end`. Against the guard at `spawn.py:1943-1953` @ `c6c4363`: iteration 1 consumes `progress`, so the `ev.type == "session-end"` early return does not fire; the drain block then sees `session-end` in `lines[after:]` and `continue`s; iteration 2 consumes it and returns 0 — matching the test's `assertEqual(rc, 0)` and `assertEqual(len(calls), 2)`. Delete the drain block and iteration 1 falls straight through to `spawn.py:1968-1970`, where the dead `wrapper_pid` returns `WATCH_CRASH_RC`, failing both assertions. The arrangement therefore discriminates the block, which the prior `roster_remove` arrangement could not once entry-absence stopped being a death signal (`spawn.py:1963-1967` @ `c6c4363`). |
| O5 | Req 4 — commit-message-only keyword actually blocked, red-green | **Met on the green half; the red half is weak — F4.** `t_autodetect_closes_only_blocks_commit_message_keyword_with_clean_body` (`gates/test_closes_gate_ci.py:322` @ `c6c4363`) arranges clean body, clean title, no approval, and `["proposal work", "Closes #245"]` as commit messages, then asserts the block cites `커밋 메시지에`. That is an isomorphic-environment green through the autodetect path. The recorded red is an `AttributeError` on a not-yet-existing `_pr_title` (`docs/issue-271/reports/implementation.md:8-12`), which shows the API was absent, not that the pre-fix gate failed to block — see F4. |
| O6 | Constraints — branch protection and `closes-gate` context unchanged; `pr_reference.py`'s #228 core respected | **Met.** `git diff 1d7df88 c6c4363 --stat` lists nine files and `gates/pr_reference.py` is not among them; neither is any workflow or protection config. The surface widening lives entirely in `gates/ci.py`'s orchestration layer, as the proposal's Constraints section committed to, and `_phase1_mismatch` is preserved as a one-surface call into `_phase1_surface_mismatch` for its existing direct callers (`git show 1cab34b -- gates/ci.py`). |

## Level 2 — TRAJECTORY: was the phase-1→phase-2 path sound

**Verdict: sound.** The phase boundary was respected, the approval was a
real human act under the correct contract path, scouting and the survey
both ran and in the right order, and the mid-PR rebase was disclosed with
its one genuine logical conflict named. One gap sits at the edge of this
level and is booked as a step-level finding instead: the deviation
register does not carry F3's widening.

| # | Question | Finding, with source |
|---|---|---|
| T1 | Phase 1 before phase 2, only phase-1 homes written before approval | **Sound.** `ddc9b0f` (authored 05:10:05Z) touches only `docs/issue-271/proposals/` and `docs/issue-271/reports/implementation/` — 600 insertions, docs only (`gh api .../pulls/273/commits`, survey §2). The approval comment `APPROVE issue-271/implementation` precedes `6cd0ef2` (05:31:27Z), which opens the record with `loop_state: in-progress`; code lands only in `1cab34b` (05:45:58Z). No code and no `reports/implementation.md` before the approval. |
| T2 | Was the approval a real human act under contract v3 §19 | **Sound.** The comment body is byte-exact `APPROVE issue-271/implementation` from `jjongkwann`, `"type":"User"` (`gh api repos/:owner/:repo/issues/271/comments`, this session), and `jjongkwann` is in `docs/specs/approvers.md`. `gh pr view 273 --json reviews` returns `[]`, so the two-account path was not used and could not have been — the PR's author is the same account — which is exactly the condition that makes the single-account issue-comment path the correct one. |
| T3 | Did the role scout when required, and survey before proposing | **Sound.** Both phase-1 companions exist in `ddc9b0f` and survive at `c6c4363`: `docs/issue-271/reports/implementation/survey.md` (260 lines) and `.../scout-brief.md` (81 lines), per `git diff 1d7df88 c6c4363 --stat`. The proposal cites the survey by section for its factual claims (e.g. "same root cause as row C's pre-fix state" in the same-class sweep paragraph), which is the survey-before-proposal ordering the directive asks for. |
| T4 | Was the mid-PR rebase handled and disclosed | **Sound.** `e2bac95` is a dedicated, docs-only commit whose message names the conflicting change (PR #247), states that `test_spawn.py` auto-merged because #247's insertions sit in a disjoint region, and names the one genuine logical conflict — `docs/handbooks/operations.md`, where main's already-landed "Blocking for real as of 2026-08-04" met this branch's stale "Nothing is actually blocked yet." Resolution kept the landed status (`docs/handbooks/operations.md:774-780` @ `c6c4363` carries the activation text; the stale claim is absent from the merged file). Disclosing a logical conflict rather than reporting a clean auto-merge is the correct handling of the semantic-conflict risk the scout brief flags. |
| T5 | Was the self-dispatched hunt real, and its finding fixed before landing | **Sound.** The hunt's one CONFIRMED finding is visible in the landed code, not just claimed: `_pr_commit_messages` carries `--paginate --slurp` and flattens pages (`gates/ci.py:85-110` @ `c6c4363`), and `t_pr_commit_messages_paginates_and_flattens` (`gates/test_closes_gate_ci.py:216` @ `c6c4363`) asserts both flags reach the argv and that two fake pages flatten to `["first", "second"]`. The stance rotation and the substitution of `general-purpose` for an unavailable `warrant-hunter` are both disclosed (`docs/issue-271/reports/implementation.md:186-198`). |

## Level 3 — STEP: which specific artifact is deficient

**Verdict: four artifacts deficient**, none of them fatal to the delivery:
`docs/handbooks/operations.md` (F2, and it is the artifact F3 also
mis-documents), `gates/ci.py` (F3), `test_spawn.py`'s restored comment
(F1), and `docs/issue-271/reports/implementation.md` (F1's stale
`closed_checks` refs, F4's red-proof entry). The step-level questions the
phase-1 plan carried in are answered individually below.

| # | Question from the plan | Answer, with source |
|---|---|---|
| P1 | Does `_phase_from_approval` widen the approval predicate past contract v3 §19? | **Yes — F3.** `_phase_from_approval` does `comments = spawn._issue_comments(repo, issue)` then `comments += spawn._issue_comments(repo, pr)` (`git show 1cab34b -- gates/ci.py`). `spawn._issue_comments`'s own docstring at `c6c4363:spawn.py:831-834` states GitHub serves PR conversation comments from the same `/issues/<n>/comments` endpoint, so the second call really does add the PR's own thread. `flows._pr_approved` (`gates/flows.py:130-143` @ `c6c4363`) applies the exact-string and approvers test to whatever comment list it is handed, so the widening is entirely the caller's. See F3. |
| P2 | What does anchoring the branch regex to `^issue-(\d+)/([^/]+)$` change? | **Nothing unsafe — fail-closed.** The prior `^issue-(\d+)/` was a prefix match, so `issue-271/a/b` extracted an issue; the anchored form returns `None` (`git show 1cab34b -- gates/ci.py`), and `_autodetect_issue_phase` turns `None` into a blocking message, not a pass (same hunk). Rejection is covered by `t_issue_and_role_from_branch_rejects_unrecognized_names` (`gates/test_closes_gate_ci.py:29` @ `c6c4363`), including the `issue-245`-with-no-role case. Tightening a predicate whose failure mode is "block" is safe by construction. |
| P3 | Is every failure and `None` path in the three new surface fetches fail-closed? | **Yes.** `check()`'s phase-1 branch appends a distinct blocking message for each of body, title and commit-list returning `None`, and only runs `_phase1_surface_mismatch` when all three are non-`None` (`gates/ci.py:250-262` @ `c6c4363`). Each fetcher returns `None` on non-zero `gh` exit (`gates/ci.py:74-81, 85-110, 113-122` @ `c6c4363`). No branch reaches a pass through a fetch failure. |
| P4 | Does any predicate in the new path re-couple routing to the checked expression? | **No.** `_phase_from_approval` reads approvers, comments and reviews only; `_closes_ref_for_issue` appears nowhere in its call graph (`git show 1cab34b -- gates/ci.py`). The CWE-570/571 shape the issue's F1 describes — a guard routed by the predicate it checks — is gone, and `t_autodetect_reachability_fix_blocks_closes_keyword_without_approval` (`gates/test_closes_gate_ci.py:290` @ `c6c4363`) pins the formerly impossible state (keyword present, phase still `phase1`, check fires). |
| P5 | Does every `ref:` in `closed_checks` resolve at `c6c4363`? | **No — F1.** `test_spawn.py:3497` (cited twice, `docs/issue-271/reports/implementation.md:23` and `:27`) lands inside an unrelated flows plan-parser fixture at `c6c4363`; the test it names is at `:3749`. The other five resolve: `gates/ci.py:85` is `_pr_commit_messages`'s `def` line, `gates/flows.py:130` is `_pr_approved`'s, `gates/test_closes_gate_ci.py:296` falls inside the reachability test's comment block, and the two `:1` refs are file-level. |
| P6 | Does the record's "still a block, not a silent pass" reasoning hold for the unwrapped `json.loads`? | **Yes.** `_pr_title` and `_pr_reviews` call `json.loads` bare (`gates/ci.py:74-81, 113-122` @ `c6c4363`), and `main()` catches only `RuntimeError` (`gates/ci.py:326-331` @ `c6c4363`), so a malformed response propagates as an uncaught `ValueError` — a non-zero exit, i.e. a blocked check. The record's non-blocking classification (`docs/issue-271/reports/implementation.md:216-221`) is accurate; the cost is a traceback instead of a readable message, which the record itself notes and scopes out. |

### Rebase integrity (the prompt's named sub-question)

| # | Check | Answer, with source |
|---|---|---|
| R1 | `spawn.py` untouched by the #271 delta | **Confirmed.** `git diff 1d7df88 c6c4363 --stat` lists nine files; `spawn.py` is absent, while issue #247's own commit `9d1394f` shows `spawn.py | 162 ++++--` (`git show 9d1394f --stat`). The two changes do not overlap in that file at all. |
| R2 | #247's added tests survive at `c6c4363` | **Confirmed.** `class SessionEndVerdict` at `test_spawn.py:2443` and `class SelfTriggeredRespawn` at `:2684` are both present in the merged tree, and the #271 delta is 24 lines confined to one method body (`git diff 1d7df88 c6c4363 -- test_spawn.py`) — it adds and removes no test function. |
| R3 | Do #245's, #247's and #271's `operations.md` texts coexist without contradiction? | **No — F2.** #245's activation paragraph (`:774-780`) and #271's new phase-signal and surface paragraphs (`:783-802`) coexist cleanly, and #247's abandoned-work section is undisturbed. The contradiction is internal to #271's own edit: the Korean mirror at `docs/handbooks/operations.md:750` @ `c6c4363` still reads "phase는 본문의 closing 키워드 유무에서 끌어낸다" while the English half at `:769` and `:783-795` says the opposite. This is precisely the semantic-conflict class the scout brief aimed the rebase review at — it just did not come from #247. |
| R4 | Are the record's post-rebase test-count claims internally consistent with the landed delta? | **Consistent.** `test_spawn.py` at `c6c4363` contains 206 `def test_` methods, matching both the record's 206/206 (`docs/issue-271/reports/implementation.md:148-150`) and #247's own "206 passed" in `9d1394f`'s message — consistent because #271 added no test method there. `gates/test_closes_gate_ci.py` at `c6c4363` defines exactly 26 `t_` functions, matching 26/26. `test_flows.py` at `c6c4363` defines 7 `t_` functions plus 3 `unittest` methods, which reconciles the record's two different numbers for the same file — `3/3` in `closed_checks` (`:28-30`, the `unittest` subset) and `10/10` post-rebase (`:149`, the file's full `__main__` run). No count contradicts the delta. This role did not re-run any of them. |

## Findings

### F1 — the restored guard's citations point at code that is not the guard

- **Impact.** A reader following the restored test's own comment to
  `spawn.py:1884-1894` lands on the non-`--follow` watch's stall and
  size-polling tail (`git show c6c4363:spawn.py`, lines 1884-1894), not on
  the drain-priority block it names, which is at `spawn.py:1943-1953`. The
  same comment's sibling reference, `test_spawn.py:3480-3485`, points into
  an unrelated fixture; the sibling test is at `:3719`. Two
  `closed_checks` entries cite `test_spawn.py:3497` for a test that lives
  at `:3749` (`docs/issue-271/reports/implementation.md:23`, `:27`). The
  cost is navigational, not behavioural — the test itself is correct and
  discriminating (O4) — but requirement 3 exists because a guard lost its
  discriminating test once already, and the comment is the artifact that
  tells the next reader which guard is being defended.
- **Timeline.** Citations written correct at `1cab34b` (05:45:58Z), when
  the drain block really was near `spawn.py:1884`. PR #247 landed on main
  mid-review, adding 162 lines to `spawn.py` above that point (`git show
  9d1394f --stat`). The rebase at `e2bac95` (05:58:01Z) shifted every line
  below; merged at `c6c4363` with the citations unchanged.
- **Root cause.** The rebase-verification pass checked mergeability, test
  outcomes and one prose conflict, but not line-number citations — and the
  record demonstrates the shift was *noticed* for one file
  (`docs/issue-271/reports/implementation.md:137-138` writes "only line
  numbers shifted, from :3497 to :3749") without the `ref:` fields two
  paragraphs above being updated to match. This is a recurrence of the
  same class as issue #266's observation F3 (stale line citations landing
  in their own commit), which issue #271 itself cites as provenance.
- **Action item (for the human to weigh).** A rebase that shifts line
  numbers needs a citation re-resolution step, or citations that do not
  encode line numbers. Cheapest mechanical form: resolve every `ref:` and
  every `<file>:<line>` in a record against the tree at commit time, the
  same way `record-fields-gate.sh` already resolves required sections.

### F2 — the handbook's Korean half still documents the deleted phase signal

- **Impact.** `docs/handbooks/operations.md:750` @ `c6c4363` states
  "phase는 본문의 closing 키워드 유무에서 끌어낸다" — a description of
  `_phase_from_body`, the function `1cab34b` deleted. The English mirror of
  the same section at `:769` and the new paragraph at `:783-795` state the
  opposite. A Korean-reading operator consulting the handbook learns the
  pre-#271 behaviour, and learns it from the half of the section written in
  the language most of this repository's operating prose uses.
- **Timeline.** `git diff 1d7df88 c6c4363 -- docs/handbooks/operations.md`
  shows a 28-line delta touching only the `## Merge gate (CI)` (English)
  block and appending two English paragraphs. The `## 머지 게이트 (CI)`
  block above it was not touched in `1cab34b`, and the rebase at `e2bac95`
  resolved a conflict inside the English half only.
- **Root cause.** The section is a mirrored KO/EN pair maintained by
  convention, with nothing binding the two halves; the doc-placement ladder
  in the record (`docs/issue-271/reports/implementation.md:179-181`) books
  the handbook update as done once the behaviour paragraph existed, and the
  ladder has no per-language item.
- **Action item (for the human to weigh).** Either the mirrored sections
  need a check that both halves changed together, or the ladder item needs
  to name the mirror explicitly. Note the correction itself is not this
  role's to make — F2 is reported, not fixed.

### F3 — the approval predicate reads the PR's own comment thread, widening past the contract

- **Impact.** `_phase_from_approval` unions the issue's comments with the
  PR's (`comments += spawn._issue_comments(repo, pr)`, `git show 1cab34b --
  gates/ci.py`; `spawn._issue_comments` serves PR conversation comments from
  the shared `/issues/<n>/comments` endpoint, per its docstring at
  `c6c4363:spawn.py:831-834`). Contract v3 §19's single-account path names
  an **issue-level** comment, and explicitly classifies anything else —
  including near-matches and affirmative-sounding comments — as feedback,
  not approval. So an `APPROVE issue-<n>/<role>` posted on the PR thread by
  an approvers.md login, which the contract does *not* treat as opening
  phase 2, flips this gate to `phase2` and thereby skips the phase-1
  closing-keyword check entirely (`gates/ci.py:250-262` @ `c6c4363` runs the
  three-surface check only under `phase == "phase1"`). The direction is
  fail-open, in the same class of gap issue #271 was opened to close. The
  probability is low — it needs an approver posting on the wrong surface —
  but posting approval on the PR instead of the issue is exactly the
  near-miss the contract anticipates.
- **Timeline.** The approved proposal specifies the signal as an issue
  comment: its Constraints section commits to "single-account approval mode
  (issue comment `APPROVE issue-<n>/<role>`, this repository's live
  default)" and its Rationale to "the same `APPROVE issue-<n>/<role>`
  exact-string issue comment (or differing-account PR review Approve)"
  (`docs/issue-271/proposals/2026-08-04-closing-trigger-surface-coverage-and-phase-predicate-separation.md`,
  Constraints and Rationale). The PR-comment union appears first in
  `1cab34b`. `docs/handbooks/operations.md:784` @ `c6c4363` then documents
  the widened form as settled behaviour — "a qualifying `APPROVE
  issue-<n>/<role>` issue/PR comment".
- **Root cause.** The deviation register records one deviation, the
  `flows._pr_approved` reuse (`docs/issue-271/reports/implementation.md:153-171`),
  and the widening rode in alongside it unremarked — plausibly because
  `_pr_approved` takes a single `comments` list and the natural way to be
  "thorough" about approvals is to hand it more of them. No test pins the
  PR-comment path either way: of the five `_phase_from_approval` cases at
  `gates/test_closes_gate_ci.py:129-197` @ `c6c4363`, the qualifying-comment
  case returns its comment only for `n == 245`, i.e. the issue, so the
  extra call is invisible to the suite.
- **Action item (for the human to weigh).** Decide which is authoritative
  — the contract's issue-only surface or the shipped issue-or-PR surface —
  and make code, handbook and contract agree. If the contract wins, the
  second `_issue_comments` call is one line to drop and wants a test that
  fails when it returns. This role files no issue; the decision is the
  human's.

### F4 — requirement 4's "red" is a missing symbol, not a demonstrated non-block

- **Impact.** Issue #271 requirement 4 asks that a commit-message-only
  closing keyword be shown blocked "red-green". The green is solid
  (`gates/test_closes_gate_ci.py:322` @ `c6c4363`, O5). The recorded red is
  "new tests referencing not-yet-existing API crash with `AttributeError:
  module 'ci' has no attribute '_pr_title'"
  (`docs/issue-271/reports/implementation.md:8-12`) — evidence that the
  new API did not exist yet, not that the old gate let the keyword through.
  A reader auditing whether the gap was real gets no artifact showing the
  pre-fix pass. Severity is low: the counterfactual is readable from the
  same commit, since pre-fix `_phase1_mismatch(body, issue)` took only the
  body (`git show 1cab34b -- gates/ci.py`), and two real incidents already
  demonstrated the gap in production (issue #271 background, PRs #265/#267).
- **Timeline.** Both `closed_checks` entries were written with the delivery
  commit `1cab34b` and unchanged through `e2bac95` and the merge at
  `c6c4363`.
- **Root cause.** When new behaviour needs a new API, the pre-fix tree
  cannot run the new test at all, so "red" collapses into an import-time
  error unless the red is deliberately staged against the old signature —
  a known cost of writing the test API-first rather than
  behaviour-first.
- **Action item (for the human to weigh).** For gap-closing work, a red
  that exercises the old code path against the new scenario (here: call the
  pre-fix body-only checker with a clean body and a dirty commit message and
  record that it returns no block) is worth the extra step; an
  `AttributeError` should be recorded as scaffolding, not as the red half.

### Qualification (not a finding) — the argv path has a green-only check

Neither red-green test enters through `main()`; both compose
`_autodetect_issue_phase` and `check()` directly
(`gates/test_closes_gate_ci.py:290`, `:322` @ `c6c4363`), which is the same
order `main()` uses (`gates/ci.py:312-322` @ `c6c4363`) but not the same
entry point. The record's live dry run does exercise argv — `python3
gates/ci.py . --pr 273 --autodetect --closes-only`, exit 0
(`docs/issue-271/reports/implementation.md:31-35`) — but PR #273 already
carried its qualifying approval at that moment, so that run resolved to
`phase2` and never entered the phase-1 branch. The record does not
overclaim this; it reports the exit code and nothing more. Recorded here so
the residual is visible: the argv wiring has design-level coverage plus one
green operating check, and no operating check of the blocking direction.

## Open findings

F1, F2, F3 and F4 are open. All four are reported here for the human's
judgment; none has been fixed by this role, which edits nothing under the
observed role's paths.

## Next steps

None for this role. Issue #271's execution plan lists two steps and this
is step 2; whether F1–F4 warrant further work — and whether they become
issues — is the human's call, not this session's.

## Open-finding resolution path

Findings return to the human only through this record on PR #274. This
role files no issue (contract v3: issues are user-authored only) and edits
nothing under the observed role's `src/`, `test/`, or
`docs/issue-271/reports/implementation*` paths. If the human judges any of
F1–F4 valid, they author the issue; a future role's session fixes it under
that issue's own branch.
