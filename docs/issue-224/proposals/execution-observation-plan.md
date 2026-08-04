---
subject: issue-224
role: execution-observation
observed_role: implementation
observed_pr: 255
code_under_review: c71faba05224f06cb3a10341c5ae3a8c720d487b
loop_state: phase-1-proposal
---

files:
- docs/issue-224/reports/execution-observation.md

## Request

Issue #224's `## 실행 계획` step 2: independent execution observation of
step 1, delivered by the `implementation` role as PR #255 (commits
`9eb1f71fa` phase 1, `c71faba05` phase 2), merged to `main` as
`d14d44da`. The invoking prompt names four focal points: the comment
pagination fix (`--paginate --slurp`), `_pr_list_all --limit 1000`,
`watch --follow`'s dead-session detection (`WATCH_CRASH_RC = 2` plus the
newly introduced `wrapper_pid` roster field, which is a departure from
the approved proposal and therefore needs its deviation justification
judged), and whether the requester's three phase-2 feedback items were
folded in as the record claims.

## Verdict levels to be rendered in phase 2

Declared here, before any evidence discussion, and rendered nowhere in
phase 1:

1. **Outcome** — did PR #255 and
   `docs/issue-224/reports/implementation.md` land what issue #224
   asked for: the three named defects fixed, and the issue's two
   delegated scope judgments ("제안이 판단", "제안이 비용을 보고 판단")
   actually made. Evidence: the issue body's three numbered defects and
   its two delegated observations, against the diff hunks at
   `c71faba05:spawn.py:830-857`, `c71faba05:gates/flows.py:44-58`,
   `c71faba05:spawn.py:1783-1848`/`:2781`, and against
   `docs/issue-224/proposals/query-watch-reliability.md:87-113`,
   `:150-163`.
2. **Trajectory** — was the phase-1 → phase-2 path sound: did the
   observed role scout when required, survey before proposing, and
   obtain a real human approval before doing phase-2 work. Evidence:
   commit timestamps (`9eb1f71fa` 2026-08-03T11:09:18Z, `c71faba05`
   2026-08-03T12:35:25Z), the approval comment
   https://github.com/tokenmaxxxer/on-the-record/issues/224#issuecomment-5166077886
   (2026-08-03T12:05:12Z) checked for exact-string equality and for
   author membership in `docs/specs/approvers.md`, PR #255's empty
   `reviews` array (single-account mode), and the phase-1 artifacts at
   `9eb1f71fa` including their skip records and `Sources:` block.
3. **Step** — which specific artifact, if any, is deficient. Evidence:
   the per-check list below. If no check resolves against the artifact,
   this level is written as "no deficient step", not omitted.

Any deficiency this observation reaches is written in the four-part
blameless shape (impact, timeline, root cause, action item), scaled to a
single finding, and returned only in this role's own record — never as
an edit to the observed role's files and never as a filed issue.

## Checks, and the evidence each is decided on

The scout brief's GAP LINE puts the field's must-be 1 (registry-entry
lifetime vs completion-record write time) and must-be 2 (regression test
must construct a reachable state) at the surfaces the survey could not
settle. C1–C3 aim there; C4–C8 cover the remaining focal points.

- **C1 — does the roster entry outlive the window the crash predicate
  is meant to tolerate?** Read the entry's removal site
  (`c71faba05:spawn.py:2901`, immediately after `rc = proc.wait()` at
  `:2900`) against the completion record's write site
  (`c71faba05:spawn.py:3003`), and both against the predicate's first
  disjunct (`roster_entry is None`, `c71faba05:spawn.py:1845`). The
  phase-2 finding, if any, is whatever that ordering yields; this
  proposal does not state it.
- **C2 — does the drain check cover the same window?** Read
  `c71faba05:spawn.py:1832-1836` against C1's interval: determine
  whether a `session-end` line exists on disk at any point inside it.
- **C3 — does the tail-window regression test construct a state C1's
  ordering permits?** Read
  `test_follow_tolerates_post_processing_tail_before_session_end`'s
  arrange block (`c71faba05:test_spawn.py`, the added
  `spawn.roster_register(...)` call) against C1's answer.
- **C4 — feedback item 1 (drain-before-liveness ordering).** Read the
  requester's text at
  https://github.com/tokenmaxxxer/on-the-record/pull/255#issuecomment-5166078117
  — which offers two acceptable responses, "same ordering as
  `session_end_verdict()`" or "a different design with its reason
  recorded" — against `c71faba05:spawn.py:1826-1836` and
  `docs/issue-224/reports/implementation.md:37-55`.
- **C5 — feedback item 2 (exit-code value).** Read
  `c71faba05:spawn.py:1783` and
  `docs/issue-224/decisions/watch-crash-exit-code.md:10-56` against the
  requester's ask that the value be pinned and recorded, and situate the
  chosen `2` against the 1–127 / 128+N convention in the scout brief.
- **C6 — feedback item 3 (test file placement).** Read
  `c71faba05:test_flows.py:58-69` and
  `docs/issue-224/reports/implementation.md:66-83` against the
  requester's ask that the placement be settled and recorded.
- **C7 — deviation justification for `wrapper_pid`.** Read
  `docs/issue-224/proposals/query-watch-reliability.md:79-85` and
  `:124-132` (the approved wording, which names the existing `pid`
  field) against `docs/issue-224/reports/implementation.md:127-147` and
  `:254-274`, and against the containment claim that
  `roster_kill()`/`flows_payload()` keep reading `pid` unchanged
  (`c71faba05:spawn.py:1859`, `:2593`). Judged on two questions: was the
  deviation legitimately triggered, and is its recorded justification
  complete enough for the requester to have re-decided.
- **C8 — the two query fixes.** S1: read
  `c71faba05:spawn.py:830-857` and the two `IssueComments` tests for
  the flatten step and the zero-comment (`[[]]`) shape, against the
  externally documented `--slurp` semantics in the scout brief. S2:
  read `c71faba05:gates/flows.py:44-58` and
  `test_flows.py::PrListAllLimit` against the sibling
  `_issue_list_all()` idiom the proposal named.
- **C9 — record completeness.** Read
  `docs/issue-224/reports/implementation.md` for its own internal
  consistency (survey O10's "4 new tests" vs the three added
  `WatchFollow` tests) and for whether the phase-1 proposal's manual
  check (`query-watch-reliability.md:180-184`) was performed or
  explicitly waived.

## Rationale

**Alternative 1 (rejected) — re-run the test suites to confirm the
record's "184 tests, 41 errors" claim.** Rejected outright: re-executing
the observed role's task is prohibited for this role, and a re-run would
prove only what this sandbox does today, not what that session did.
Instead the claim is treated as documentary and cross-checked against
the independently-committed
`docs/issue-223/reports/implementation.md:81-85`, which records the same
41-error sandbox baseline (survey O11).

**Alternative 2 (rejected) — read the working tree's `spawn.py` for
context.** Rejected: the working tree shows what exists now, not what
the observed session produced. All code citations address the blob at
`c71faba05` (or the pre-change blob a hunk landed on) by SHA.

**Alternative 3 (rejected) — judge the two "same-family" candidates and
the "watch returns on every event" observation on their merits.**
Rejected as a scope error: issue #224 delegated those calls to the
proposal, so the admissible question is whether the judgment was made
and reasoned (C1 of the outcome level), not whether this role would have
decided the same way.

**Alternative 4 (rejected) — file follow-up issues for anything this
observation surfaces.** Rejected: under role-handoff contract v3 issues
are user-authored only. Findings return in this role's record on this
role's PR; the human files whatever they judge worth filing.

## What will be done

1. Write `docs/issue-224/reports/execution-observation.md` as the first
   act of phase 2, with the independence statement placed before any
   verdict language and `loop_state` updated at each transition.
2. Run C1–C9 against the cited artifacts, recording per check what was
   read and what it showed.
3. Render the three verdict levels — outcome, trajectory, step — each
   with its citation adjacent, and each written explicitly even where a
   level does not apply ("not applicable, because X").
4. Write any deficiency in the four-part blameless shape.
5. Commit the record on this branch and report it through this PR.

## Out of scope

- Any edit to `spawn.py`, `gates/flows.py`, `test_spawn.py`,
  `test_flows.py`, `docs/issue-224/proposals/query-watch-reliability.md`,
  `docs/issue-224/decisions/watch-crash-exit-code.md`, or
  `docs/issue-224/reports/implementation*` — the observed role's write
  set, untouchable by this role.
- Any execution of `spawn.py` or of the test suites.
- Filing issues, approving, merging, or relaying an approval.
- Re-deciding the scope calls issue #224 delegated to the proposal
  (Rationale alternative 3).

## How you'll know it worked

- `docs/issue-224/reports/execution-observation.md` exists and is
  committed on `issue-224/execution-observation`; an uncommitted record
  counts as not written.
- Its independence statement appears before the first verdict-bearing
  sentence in document order.
- All three verdict levels appear, each with a citation adjacent to the
  verdict, none silently omitted.
- Every check C1–C9 is answered from an artifact read this session, with
  a commit SHA, `file:line`, or comment URL naming the source; no check
  is answered from memory or from the working tree.
- Nothing outside `docs/issue-224/reports/execution-observation*` and
  `docs/issue-224/proposals/execution-observation-plan.md` is modified
  on this branch.
