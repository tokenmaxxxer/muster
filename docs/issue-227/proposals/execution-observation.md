---
kind: proposal
subject: issue-227
date: 2026-08-04
---

# Proposal — independent execution observation of issue #227 step 1 (PR #254)

files:
- `docs/issue-227/reports/execution-observation.md` (new, phase-2 only — this
  role's sole phase-2 artifact)

This role writes nothing else. It does not touch `on-the-record/commands/run.md`,
`docs/handbooks/operations.md`, `docs/issue-227/decisions/`, or any file under
`docs/issue-227/reports/implementation*` — those are the observed role's, and
this role did not author them.

## Request

Issue #227's execution plan, step 2: `execution-observation` of step 1. Step 1
is the `implementation` role's phase-1→phase-2 run on branch
`issue-227/implementation`, delivered as PR #254 (MERGED `2026-08-04T02:03:57Z`,
merge commit `a4eca54`), which landed commit `144b413` (three documents,
+140/-0) and commit `6fee354` (its own record, +291).

The invoking prompt narrows what step 2 must cover, on top of the standing
three-level judgment:

1. **Mutual agreement of the three documents** — `on-the-record/commands/run.md`,
   `docs/handbooks/operations.md`, and
   `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md`.
2. **Consistency with the contract text** — `protocol.md` §5 (`:217-246`),
   including invariant 4 (`protocol.md:255-257`).
3. **Measurement of today's live relays** — whether the actual approval
   comments on issues #224, #245, #246 (and #227 itself) match the landed
   two-comment recipe, measured against the specimens recorded in
   `docs/issue-227/reports/execution-observation/survey.md`.

## Which verdict levels will be rendered, and against what evidence

Stated here, before any judgment exists — nothing in this proposal is a
verdict, provisional or otherwise. Phase 2 will address all three levels of
the standing verdict, writing "not applicable, because X" for any level that
does not apply rather than omitting it.

| Level | Question phase 2 answers | Evidence it will be answered from |
| --- | --- | --- |
| **outcome** | Did PR #254 land what issue #227 asked — 요구사항 1 (canonical two-comment form, order and location specified), 요구사항 2 (gate behaviour confirmed empirically and recorded as evidence), 요구사항 3 (#224 relationship named without absorbing it), plus the follow-up comment's (a) detection-logic-vs-doc agreement and (b) non-canonical-form handling decision; and did it honour both 제약 (no matcher-logic change, no new approval grammar)? | `git show 144b413` diff text (read in full this session); `gh issue view 227` body and `#issuecomment-5163763980`; the decision doc's landed text; commit-message claims in `144b413`/`6fee354` cross-checked against the diff. |
| **trajectory** | Was the phase-1→phase-2 path sound — did phase 1 survey before proposing, did scouting run, was there a real human approval event under contract v3 s19, and did the phase-2 work stay inside the approved proposal's write set? | Commit sequence `75f32f0f` → `681f61e4` → `144b413` → `6fee354` on PR #254; `docs/issue-227/proposals/implementation.md` "What will be done" / "Out of scope"; the approval comment `#issuecomment-5166285829` (2026-08-03T12:26:37Z, `jjongkwann`, in `docs/specs/approvers.md`), `gh pr view 254 --json reviews` → `[]`, and single-account mode per `protocol.md:239-246`. |
| **step** | Which specific artifact, if any, is deficient — checked per artifact: the `run.md` bullets, the `operations.md` mirror, the decision doc, and the observed role's own record `docs/issue-227/reports/implementation.md`. | The same diff and record text, plus the two gap-aimed checks below. |

## Rationale — what the checks are, and why these

The scout brief (`docs/issue-227/reports/execution-observation/scout-brief.md`)
found the field's must-bes 1–4 (independence, evidence-first record, sourced
timeline, primary-vs-contributing cause) already covered by this role's
directive and this repo's prior observation records, and identified must-bes
5 and 6 as the gap this observation should aim at. The plan therefore adds two
checks beyond the standing three-level verdict:

**Check A — duplicate-copy drift across every surface carrying the rule, not
only the ones the change touched.** Docs-as-code/SSOT practice treats
un-synchronized copies of one rule as the defect class to look for
(scout brief, Docsie/Paligo/Kong). The recipe now exists in three places; two
adjacent canon surfaces carrying the same approval canon — `README.md:41,64`
and `protocol.md:239-246` — were not touched by `144b413`, and
`protocol.md:245-246` carries an explicit "do not reintroduce a second signal
location without updating all three together" clause with a cited prior
failure (issue-126). Phase 2 will read all five surfaces and state whether the
untouched two are consistent with the landed recipe, and whether that clause
reaches this change at all. The observed record's own clean check
`run-md-operations-md-wording-agreement`
(`docs/issue-227/reports/implementation.md:223-227`) covers two of the five;
this check covers the rest, and independently re-derives the two it covers
rather than inheriting the conclusion.

**Check B — documented-vs-operating gap, measured.** Auditors check whether a
documented policy is reflected in day-to-day operations, and treat
policy-that-is-not-enforced-at-the-point-of-action as a named gap rather than
a closed control (scout brief, nhimg/madsecurity/Drata). Two measurements,
both from evidence already collected in the survey:

- the eight live relay specimens on issues #224/#245/#246/#227, with their
  timestamps, compared shape-by-shape against the landed recipe (token-only
  comment A, then separate feedback comment B) — including the ordering
  question the survey recorded and left open, and the fact that seven of the
  eight predate `144b413`;
- whether the observed proposal's Out-of-scope deferral of the warn policy's
  detection code, and the observed record's own findings 1–2
  (`docs/issue-227/reports/implementation.md:183-211`), leave the
  documented-but-unenforced state named or unnamed in what landed.

Neither check re-executes the observed role's task: no gate function will be
re-run, no `src/` file will be read as evidence of what that session did, and
the recipe will not be re-derived or rewritten. Both checks read only the
observed session's produced artifacts plus GitHub's own record of the relay
comments.

## Constraints

- Never edit the observed artifact. Findings return only in this role's own
  record, on this role's PR; the human judges them there.
- No issue filing — under contract v3 issues are user-authored only. A
  confirmed deficiency becomes a finding with evidence, not a new issue.
- Every verdict-bearing sentence carries its citation (commit SHA,
  `file:line`, or comment URL) directly adjacent to the verdict.
- The independence statement precedes any verdict language in the record, by
  document order, not merely appears somewhere in it.
- Any deficiency finding carries the four-part blameless shape — impact,
  timeline, root cause, action item — scaled to a single finding.

## What will be done (phase 2, after an approval event)

1. Write `docs/issue-227/reports/execution-observation.md` as the first act of
   phase 2, opening with the independence statement and `loop_state`, updating
   `loop_state` at each transition.
2. Render the **outcome** verdict against issue #227's 3 요구사항 + 2 제약 and
   the follow-up comment's two added requirements, each citing the diff line
   or artifact that settles it.
3. Render the **trajectory** verdict against the four-commit sequence, the
   approved proposal's write set, and the approval event under contract v3
   s19 single-account mode.
4. Render the **step** verdict per artifact (`run.md` bullets,
   `operations.md` mirror, decision doc, the observed role's record), naming
   which artifact is deficient or stating that none is.
5. Report check A and check B with their measurements, each specimen cited by
   comment URL and timestamp.
6. Give every deficiency finding, if any, the four-part blameless shape.
7. Commit the record on this branch and push to the same PR.

## Out of scope

- Re-running `gates/flows.py::_pr_approved()`, `spawn.py::approve_scope()`, or
  any other gate function — the observed role's executed results are its
  artifact; re-execution is prohibited for this role and would not be
  independent evidence of what that session did.
- Any edit to the observed role's `src/`, `test/`, `docs/issue-227/decisions/`,
  `docs/issue-227/proposals/implementation.md`, or
  `docs/issue-227/reports/implementation*`.
- Proposing or writing the warn policy's detection code, or a fix for issue
  #224's `/scope`-vs-`/role` mismatch and pagination cap.
- Judging the `repo-status-board` incidents themselves (rsb #20, #23) — they
  are the observed role's cited input, in another repo; this observation
  judges how PR #254 handled them, not the incidents.
- Filing any follow-up issue.

## How you'll know it worked

- `docs/issue-227/reports/execution-observation.md` exists on this branch,
  committed, with the independence statement before the first verdict.
- All three verdict levels appear, none silently omitted (any inapplicable
  level written as "not applicable, because X").
- Every verdict-bearing sentence has a citation adjacent to it — a reader can
  check each verdict against the named SHA, `file:line`, or comment URL
  without re-deriving anything.
- Check A states, per surface, the drift position of all five surfaces
  carrying the approval canon.
- Check B reports the eight live relay specimens against the recipe with
  timestamps, and states plainly where the documented rule is and is not
  reflected in operations.
- No file outside `docs/issue-227/reports/execution-observation.md` is touched
  in phase 2.
