---
kind: coding-record
code_under_review: gates/ci.py, gates/test_closes_gate_ci.py,
  docs/issue-312/decisions/phase-is-an-issue-property.md
loop_state: landed
closed_checks:
  - check: "gates/test_closes_gate_ci.py full suite, 33/33 pass, including
      the two new acceptance tests (#304/#307 cross-role handoff shape
      reproduction; missing-approval refusal names role searched and
      approvals present), the reversed wrong-role test, and the
      warrant-hunter empty-role-suffix regression test."
    ref: gates/test_closes_gate_ci.py:1
  - check: "Live gate run against real, unmodified GitHub state: `python3
      gates/ci.py . --pr 307 --issue 304 --autodetect --closes-only`
      → \"게이트 통과\" (exit 0) — PR #307 (issue-304/implementation,
      body carries `Closes #304`) no longer misdiagnosed as phase1
      because issue #304's `APPROVE issue-304/architecture` now
      qualifies the whole issue for phase2. Re-run after the
      empty-role-suffix fix, still passes."
    ref: docs/issue-312/reports/implementation.md
resolved_findings:
  - finding: "warrant-hunter (before-landing, stance 3, docs/reports/2026-08-07-hunt-2026-08-07-closes-gate-issue-level-phase-and-evidence-bearing-refusal.md):
      a comment body exactly `APPROVE issue-<n>/` (empty role suffix) from
      an allowlisted login made `_approved_roles_on_issue` add the empty
      string to its role set, which is truthy in Python — permanently
      opening phase2 for the whole issue with no real role ever approved."
    resolution: "`_approved_roles_on_issue` (gates/ci.py) now skips a
      zero-length role token; added
      `t_phase_from_approval_empty_role_suffix_comment_is_phase1`
      (gates/test_closes_gate_ci.py) as the red/green regression proof."
---

# Phase 2 — closes-gate: phase is an issue property; evidence-bearing refusal (issue #312)

## What was done

- `gates/ci.py::_phase_from_approval` no longer asks for a role-exact
  `APPROVE issue-<n>/<role>` match. It now unions two signals: (a) a new
  `_approved_roles_on_issue` scan of issue-level comments for `APPROVE
  issue-<n>/<any-role>` from an `approvers.md` login (any role token
  qualifies), and (b) the existing differing-account PR-review-Approve
  check (unchanged, still scoped to *this* PR, so no cross-role
  ambiguity there per issue #271). Either non-empty → phase2.
- `check()`'s phase1 branch: when `_phase1_surface_mismatch` fires, the
  refusal is extended with an evidence line naming the role the branch
  name implies and the actual set of approved roles found on the issue
  (or "없음"), e.g. `이 PR 의 role(implementation)에 대한 승인 코멘트를
  못 찾았다 — 이슈 #245 에 있는 승인: 없음`. When the issue already
  qualifies for phase2 (the #304/#307 shape), the phase1 branch is never
  entered at all — no refusal, not even a softened one.
- `gates/test_closes_gate_ci.py`: replaced
  `t_phase_from_approval_wrong_role_comment_is_phase1` with
  `t_phase_from_approval_any_role_comment_qualifies_the_issue_is_phase2`
  (asserts the reversed reading); added
  `t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`
  (issue #312 acceptance item 1, exact #304/#307 configuration) and
  `t_autodetect_missing_approval_refusal_names_role_searched_and_approvals_present`
  (acceptance item 2). All other existing tests pass unmodified.
- `docs/issue-312/decisions/phase-is-an-issue-property.md`: records the
  decision, the two rejected alternatives, and that it supersedes
  `docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`'s
  per-role reading.
- Live check (acceptance item 3): `python3 gates/ci.py . --pr 307
  --issue 304 --autodetect --closes-only` against real, unmodified
  GitHub state (PR #307, PR #305, issue #304) → `게이트 통과` (exit 0).

## Doc-placement ladder

- [x] Decision (phase model choice, superseding a prior decision):
  `docs/issue-312/decisions/phase-is-an-issue-property.md`.
- [x] Record (this file): `docs/issue-312/reports/implementation.md`.
- No env var, config key, new dependency, or migration was introduced —
  no handbook update applies.

## What this reaches beyond its own acceptance criteria (#330)

- Every other issue currently sitting on an architect-proposes /
  implementer-delivers handoff (an issue whose only approval comment
  names a role different from the delivering PR's branch role) is
  reclassified from phase1 to phase2 the moment this lands, without any
  code change on those issues' own branches — the phase test is now a
  property of the issue's approval history, read fresh on every gate
  run, not cached or issue-scoped in a way that needs backfilling.
- The reversed `t_phase_from_approval_any_role_comment_qualifies_the_issue_is_phase2`
  test permanently invalidates the old per-role assertion recorded in
  `docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`
  as still-true behavior — that decision's "role must match" reading is
  now explicitly superseded, not just silently outdated, per the note
  added to the new decision file.
- Does not touch `gates/flows.py::_pr_approved` or the mission-board
  status path (`flows.py:318,342`), which stay role-exact by contract —
  the mission board's per-role phase display for a cross-role-approved
  issue will still show the *delivering* role's own phase as
  unapproved, even though `gates/ci.py`'s merge gate now passes it. This
  is a known, accepted split (proposal's Out of scope): the board's
  reading and the gate's reading of "phase" are no longer the same
  question, and nothing in this change reconciles them.

## Hunt

Before-landing warrant-hunter dispatch (stance 3, "assume the rule as
written cannot hold — find the state nothing maintains"), 120s cap,
default tier. FINDING: an `APPROVE issue-<n>/` comment with an empty
role suffix from an allowlisted login made `_approved_roles_on_issue`
add `""` to its role set — truthy in Python — permanently opening
phase2 for the whole issue with no real role approved. Fixed in
`gates/ci.py::_approved_roles_on_issue` (skip zero-length role tokens)
and covered by
`t_phase_from_approval_empty_role_suffix_comment_is_phase1`; see
`resolved_findings` in this record's frontmatter and
`docs/reports/2026-08-07-hunt-2026-08-07-closes-gate-issue-level-phase-and-evidence-bearing-refusal.md`
for the hunter's own record.

## What did not work

None.

## Rebase onto main (post-landing, PR #314 unblock)

Main advanced ~40 PRs past this branch's fork point (through
`c71173b`, PR #410), leaving PR #314 `mergeStateStatus: DIRTY` /
`CONFLICTING`. Ran `git fetch origin` then `git rebase origin/main`.

- One real conflict, in `gates/test_closes_gate_ci.py`: both this
  branch's phase-2 commit and main's independent history had appended
  new test functions at end-of-file. Purely additive on both sides —
  resolved by keeping both blocks concatenated (no logic edited, no
  test dropped from either side). `gates/ci.py` merged clean
  (`자동 병합: gates/ci.py`, no conflict markers).
- Notably, main's history included `08b2808` (issue-398: rename
  `gates/test_gates.py`, add duplicate-test-basename gate) — the fix
  for the `gates/` module-name collision this task's brief said was
  "in flight" (#398). It landed before this rebase, so the collision
  this task expected to still block `gates/` collection was already
  gone in the rebased tree.
- Re-ran acceptance evidence against the rebased tree (not reused from
  before the rebase, per #390):
  - `python3 gates/test_closes_gate_ci.py` → **46 passed** (was 33/33
    pre-rebase; the increase is main's own test growth in the same
    file, now merged in, not a change to this issue's tests).
  - `python3 gates/ci.py . --pr 307 --issue 304 --autodetect
    --closes-only` against real, unmodified GitHub state → `게이트
    통과` (exit 0) — unchanged from the pre-rebase run.
  - `python3 -m pytest -q --ignore=gates` → **389 passed**, matching
    main's reported baseline exactly.
  - `python3 -m pytest -q gates` → **61 passed** — this collects and
    passes cleanly on the rebased tree; the brief's premise that
    `gates/` "still cannot collect" (#398) no longer holds here because
    #398's fix (`08b2808`) is now part of this branch's own history via
    the rebase.
- No conflict, edit, or re-run touched anything outside this issue's
  already-frozen write set (`gates/ci.py`, `gates/test_closes_gate_ci.py`,
  `docs/issue-312/decisions/phase-is-an-issue-property.md`,
  `docs/issue-312/reports/implementation.md`) — the rebase moved this
  branch's existing commits onto a new base and merged one additive test
  conflict; it did not add new files or new production code.
- Pushed the rebased branch with `git push --force-with-lease` (commit
  SHAs changed under rebase, so a fast-forward push was not possible).

## Open findings

- The #313/#317 pure-bugfix-skip phase-determination gap (see
  "Conditional-approval feedback" below) is a real, unaddressed defect
  outside this proposal's approved write set. It needs its own future
  issue/proposal — this session does not file issues.

## Rationale for deviations

No divergence from the approved proposal's `## What will be done`
occurred — every item there was implemented as written, inside the
frozen write set, with no alternative swap. The section below records a
scope boundary this session held under the binding conditional-approval
feedback, not a deviation from what was built.

## Conditional-approval feedback (binding, addressed by scope statement, not by code)

The issue's second comment (posted immediately after the `APPROVE`
token) raises a third, independent variant beyond the one this proposal
covers: a PR that took the contract v3 s19 **pure-bugfix skip** path
(issue #313 / PR #317) has, by construction, no phase-1 proposal and
therefore no `APPROVE issue-<n>/<role>` comment can ever exist on that
issue — so `_phase_from_approval` (both the old and this session's new
reading) returns phase1 forever, and the only way that PR's phase-2
gate was made to pass was a human hand-posting an approval comment that
defeats the entire point of the skip path (bypassing phase-1 authoring).

This is real and unaddressed by the approved proposal: the proposal's
frozen write set (`gates/ci.py`, `gates/test_closes_gate_ci.py`,
`docs/issue-312/decisions/phase-is-an-issue-property.md`,
`docs/issue-312/reports/implementation.md`) and its "What will be done"
say nothing about detecting or exempting the pure-bugfix skip shape, and
its Rationale weighs only the cross-role-handoff alternative space, not
a no-approval-possible one. Per the scope-exceeded rule, this session
does not fold a fix for that third variant into this delivery — doing
so would need a new design decision (how does the gate learn a PR took
the skip path at all, given nothing in `gates/ci.py`'s current inputs —
branch name, PR body/title/commits, issue comments, PR reviews —
records that fact) that the approved proposal never considered or
authorized. The new decision doc
(`docs/issue-312/decisions/phase-is-an-issue-property.md`, closing
"Consequences" paragraph) records this gap explicitly so it is not lost;
it is not filed as a new issue by this session, since issue-filing is
reserved to the user per the role-handoff contract; the user should be
made aware in the reply that #313/#317's variant needs its own future
issue.
