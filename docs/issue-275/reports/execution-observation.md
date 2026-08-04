---
kind: observation-record
observed_subject: issue-275 step 1 (role `implementation`), PR #276
loop_state: landed
closed_checks:
  - check: "Phase boundary: the phase-1 commit stages only the two phase-1
      homes (proposal + reports/implementation/{survey,scout-brief}.md),
      3 files, 603 insertions — no phase-2 content precedes the approval."
    ref: "git show fabd74b --stat"
  - check: "Approval provenance: issue-level comment id 5175585081,
      author `jjongkwann` (present in docs/specs/approvers.md), body
      exactly `APPROVE issue-275/implementation`, 2026-08-04T06:51:15Z —
      posted after PR #276 was opened (06:50:37Z) and before the first
      phase-2 commit (07:01:21Z). `gh pr view 276 --json reviews` is
      empty, so the single-account path is the operative one."
    ref: "gh api repos/tokenmaxxxer/on-the-record/issues/275/comments"
  - check: "F3 landed: the second comment fetch is gone — one
      `spawn._issue_comments` call remains in `_phase_from_approval`
      (issue-keyed) at gates/ci.py:162 @ cb6b46a, against two calls at
      gates/ci.py:157-158 @ cb6b46a~1."
    ref: "gates/ci.py:162 @ cb6b46a"
  - check: "F3 red-green is a real discriminator, judged statically from
      the diff: the new test mocks the PR-number branch to answer a
      qualifying comment and the issue-number branch to answer `[]`, so
      the deleted line is the only thing that could have produced
      `phase2` — pre-fix that arrangement unions the comment in, post-fix
      it cannot."
    ref: "gates/test_closes_gate_ci.py:199 @ cb6b46a"
  - check: "F4's pairing is real: the new case and the sibling
      multi-surface case use the identical body string `no closing
      keyword, see #245`, so the two assertions describe one scenario
      across the old and new predicates."
    ref: "gates/test_closes_gate_ci.py:344 and :363 @ cb6b46a"
  - check: "F2 KO/EN parity: seven claims compared side by side
      (workflow+`--closes-only` scope, issue/role from head branch,
      fail-closed, activation+PR #263 two-way measurement, approval-event
      phase with both modes, PR-thread exclusion, three-surface phase-1
      check) — no sentence in either language contradicts the other."
    ref: "docs/handbooks/operations.md:743-783 (KO) and :784-831 (EN) @ cb6b46a"
  - check: "F1 in-code citations resolve: test_spawn.py:3749 @ cb6b46a is
      `def test_follow_prioritizes_pending_session_end_over_pid_check`,
      the test the record names."
    ref: "test_spawn.py:3749 @ cb6b46a"
  - check: "The hunt's own fix holds: the F4 test comment cites
      `gates/ci.py:169`, and `def _phase1_mismatch` is at gates/ci.py:169
      @ cb6b46a (:165 @ cb6b46a~1) — the 165→169 correction is correct in
      the landed tree."
    ref: "gates/test_closes_gate_ci.py:350 @ cb6b46a"
  - check: "The blocked write is mechanically real, verified from the
      hook source rather than from the record's assertion: R4 requires
      the current branch to be exactly `issue-<n>/<CLAUDE_ROLE>` for any
      write under `docs/issue-<n>/`, and the header notes even
      `git log … -- docs/issue-49 | head` is refused as a board write."
    ref: "core/hooks/board-gate.sh:24-26, :112-113, :481-493"
  - check: "§20 item-6 habitat sweep (for this record's own finding):
      `grep -rlE '결함 클래스|defect class' docs` returns proposals,
      surveys and scout briefs only — zero matches at
      `docs/issue-<n>/reports/<role>.md` level, repo-wide."
    ref: "grep -rlE '결함 클래스|defect class' docs"
  - check: "Mechanical root cause of that absence: record-fields-gate.sh
      enforces §20 items 1-5 (what-was-done, why, basis, and — when
      loop_state is non-terminal — next-steps and open-finding resolution
      path) and does not check item 6."
    ref: "core/hooks/record-fields-gate.sh:8-11, :209"
---

# Execution-observation record — issue #275, step 2

## Independence

This role did not author or edit the observed artifact this session. PR #276
and every commit in it (`fabd74b`, `21f91f6`, `cb6b46a`, merge `236b66e`) were
produced by the `implementation` role on branch `issue-275/implementation`
before this session began; this session has written only under
`docs/issue-275/reports/execution-observation*` and
`docs/issue-275/proposals/2026-08-04-observation-plan-for-pr-276.md` on branch
`issue-275/execution-observation`, and has run no test, gate, or script
belonging to the observed change. Every judgment below rests on the PR, its
commits and diff, the GitHub approval record, and the observed role's own
proposal and record — never on a re-execution, and never on today's `src/`
tree: where file content matters it is read at a named commit
(`git show <sha>:<path>`), which is the produced artifact.

## Why

Issue #275's execution plan step 2 is an independent observation of step 1.
The plan approved for this observation is
`docs/issue-275/proposals/2026-08-04-observation-plan-for-pr-276.md`; phase 2
opened on the issue-level comment `APPROVE issue-275/execution-observation` by
`jjongkwann` (listed in `docs/specs/approvers.md`), posted 2026-08-04T07:27:30Z
on issue #275, after this role's phase-1 PR #277 was opened — contract v3 §19
single-account path (PR author and approver are the same account).

The alternative considered for this record's own citation style, and rejected,
was the repo's dominant unpinned `file:line` convention: rejected because this
observation's subject includes citation drift, and the observed session's own
hunt caught a citation that went stale inside a single commit
(`gates/test_closes_gate_ci.py:350 @ cb6b46a`). Every citation below is pinned
to a commit or to a GitHub object id.

## What was done

Eleven checks (frontmatter `closed_checks`) against PR #276's commits, diff,
approval record, and the observed role's proposal and record; then the three
verdict levels below. No test was run and no observed-role artifact was
modified.

## Verdict — outcome

**Landed, with one requirement partially delivered and the shortfall recorded
in defensible form.** Requirement-by-requirement:

- **Requirement 1 (F3) — met.** `_phase_from_approval` no longer unions the
  PR's own comment thread: two `spawn._issue_comments` calls at
  `gates/ci.py:157-158 @ cb6b46a~1` become one issue-keyed call at
  `gates/ci.py:162 @ cb6b46a`, and the docstring's "이슈/PR 코멘트" is corrected
  to "이슈 코멘트" in the same hunk. The red-green pin the requirement asked
  for exists and discriminates: `gates/test_closes_gate_ci.py:199 @ cb6b46a`
  mocks the PR-number branch to return a qualifying comment while the
  issue-number branch stays `[]`, an arrangement in which the deleted line is
  the only path to `phase2`.
- **Requirement 2 (F2) — met.** The Korean and English merge-gate sections at
  `docs/handbooks/operations.md:743-783` and `:784-831 @ cb6b46a` carry the
  same seven claims, including the F3 exclusion in both
  (`:768-770` KO, `:812-815` EN); the stale KO sentence deriving phase from
  closing-keyword presence is gone, and the English side's own "issue/PR
  comment" phrase was corrected in the same commit rather than left to become
  the newly stale side.
- **Requirement 3 (F1) — partially met, shortfall documented.** The two
  in-code citations are corrected in `test_spawn.py @ cb6b46a` and resolve:
  `test_spawn.py:3749 @ cb6b46a` is the test the record names. The style
  question the requirement routed to the proposal was answered there, with the
  alternative stated and rejected
  (`docs/issue-275/proposals/2026-08-04-closes-gate-approval-scope-and-record-hygiene.md:92-113`).
  The two `docs/issue-271/reports/implementation.md` `ref:` corrections named
  in the same proposal's `files:` header and `:159-162` did not land — they are
  absent from `git show cb6b46a --stat` (5 files, none under `docs/issue-271/`).
  The blocker is mechanically real, verified independently of the record's
  assertion: `core/hooks/board-gate.sh:481-493` requires the current branch to
  be exactly `issue-<n>/<CLAUDE_ROLE>` for any write under `docs/issue-<n>/`,
  and its header (`:112-113`) records that even a piped `git log -- docs/issue-<n>/…`
  is refused as a board write. The record states the deviation with affected
  scope, evidence, conclusion, and a named continuation path
  (`docs/issue-275/reports/implementation.md:134-156`, `:223-229`).
- **Requirement 4 (F4) — met.** `gates/test_closes_gate_ci.py:344 @ cb6b46a`
  asserts the retained pre-#271 predicate returns `[]` for the clean body, and
  the sibling case at `:363 @ cb6b46a` drives the post-#271 multi-surface path
  to block — on the *identical* body string `no closing keyword, see #245`,
  which is what makes the pair one scenario rather than two adjacent
  assertions. This replaces the `AttributeError`-shaped proof the requirement
  objected to.

## Verdict — trajectory

**Sound.** The phase-1 commit `fabd74b` stages exactly three files — the
proposal and the two `reports/implementation/` phase-1 files — and nothing
under `gates/`, `test_spawn.py`, `docs/handbooks/`, or the record
(`git show fabd74b --stat`), so no phase-2 work preceded the approval. The
survey-before-proposal and scout obligations are discharged by artifacts, not
by assertion: `docs/issue-275/reports/implementation/survey.md` (229 lines) and
`scout-brief.md` (147 lines) both exist and were committed in that same
phase-1 commit. Ordering is clean end to end: `fabd74b` 06:50:19Z → PR #276
opened 06:50:37Z → approval comment id 5175585081 06:51:15Z → `21f91f6`
07:01:21Z → `cb6b46a` 07:14:11Z → merged 07:17:23Z. The approval satisfies §19's
single-account path on its own terms — exact string `APPROVE
issue-275/implementation`, author `jjongkwann` present in
`docs/specs/approvers.md`, posted on issue #275 (an issue, not a PR, so
`/issues/275/comments` is genuinely the issue-level surface), with
`gh pr view 276 --json reviews` empty so no review-Approve path is in play. No
approval-shaped near-miss comment exists on the issue to report: the endpoint
returns exactly two comments, both exact-string approvals for their respective
roles.

## Verdict — step

**One deficiency, in the record rather than the code.** Finding F-A below. The
code, test, and documentation artifacts each hold up under the checks above,
including the observed session's own hunt fix: the F4 comment's
`gates/ci.py:169` citation is correct in the landed tree
(`def _phase1_mismatch` is at `gates/ci.py:169 @ cb6b46a`, `:165 @ cb6b46a~1`),
so the 165→169 correction the record claims (`:126-132`) is real and complete.

### Finding F-A — §20 item 6 is undischarged for the record's confirmed finding

- **Impact.** `docs/issue-275/reports/implementation.md` states one CONFIRMED
  finding (`:188-195`: a self-citation that went stale inside the very commit
  that wrote it). §20 item 6 attaches to exactly that situation and asks for
  two things — the defect class, and whether that class was checked for
  elsewhere. Neither appears in the record. The next reader therefore cannot
  tell whether the class recurs in the same changeset. It does have live
  habitats there: the record's own six `closed_checks` `ref:` fields
  (`:13, :16, :22, :26, :32, :40`) are unpinned `file:line` claims, four of
  them pointing into the two files the same commit rewrote — the same
  drift-prone shape as the caught instance. (All four resolve at `cb6b46a`;
  the exposure is future drift, not present error.) The one sweep the record
  does carry (`:212-216`, the `_issue_comments` union's other habitats in
  `gates/flows.py` and `spawn.py`) belongs to F3's class — the class of the
  fix, not the class of the finding.
- **Timeline.** 2026-08-04T07:14:11Z — `cb6b46a` commits the record carrying
  the confirmed finding at `:188-195` and the six unpinned `closed_checks`
  refs. 07:17:23Z — merged as `236b66e`. No later commit touches the record.
- **Root cause.** §20 item 6 is enforced by nothing mechanical:
  `core/hooks/record-fields-gate.sh:8-11` requires a what-was-done section, a
  why section, a basis, and — when `loop_state` is non-terminal — next-steps
  and an open-finding resolution path, and stops there; item 6 is checked by no
  gate. The gap is systemic rather than particular to this session: a sweep of
  the whole `docs/` tree (`grep -rlE '결함 클래스|defect class' docs`) returns
  proposals, phase-1 surveys and scout briefs only, and zero
  `docs/issue-<n>/reports/<role>.md` records in either language.
- **Action item.** For the human to judge on PR #277 and, if valid, file: a
  one-line defect-class label plus a habitat sweep for confirmed findings —
  applied at minimum to the citations the same diff introduced (the six
  `closed_checks` refs, and the citations inside the two new test comments at
  `gates/test_closes_gate_ci.py:200-208` and `:345-358`) — and, since the
  omission is repo-wide, an extension of `record-fields-gate.sh` to check item
  6 whenever a record states a confirmed finding. This role files no issue;
  under contract v3 issues are user-authored only.

**Defect class and other habitats for F-A itself (§20 item 6, applied to this
record).** Class: a record stating a confirmed finding without item 6's class
label and habitat sweep. Swept repo-wide this session with
`grep -rlE '결함 클래스|defect class' docs` — no `reports/<role>.md` record in
this repository carries such a label, so the class is repo-wide and this
record's finding is one instance of it, not an outlier.

### Non-deficiency notes (checked, nothing to report)

- **F4's test in isolation supplies no commit-message input.** Raised as an
  unknown by this observation's survey (§ "Write surfaces", gap 3) and closed
  as not a defect: `ci._phase1_mismatch(body, issue)` has no commit-message
  parameter to supply — that absence *is* the behavior requirement 4 asks to
  demonstrate — and the identical body string shared with the sibling case at
  `gates/test_closes_gate_ci.py:363 @ cb6b46a` binds the two assertions into
  one scenario.
- **PR #276's title still reads "phase 1 … (제안)" while it landed phase-2
  code.** Checked against the repo's own pattern rather than assumed to be a
  slip: `gh pr list` shows #268 and #270 titled "phase 1 …" for PRs that also
  carried their phase-2 work, so this is the house pattern, not a deviation
  introduced here.

## Concrete basis for the next reader

Observed: PR #276 (https://github.com/tokenmaxxxer/on-the-record/pull/276),
commits `fabd74b` (phase 1), `21f91f6` (phase-2 skeleton), `cb6b46a` (phase-2
work), merged as `236b66e`. Observed role's record:
`docs/issue-275/reports/implementation.md`; its proposal:
`docs/issue-275/proposals/2026-08-04-closes-gate-approval-scope-and-record-hygiene.md`.
This role's phase-1 artifacts: `docs/issue-275/reports/execution-observation/`
(`survey.md`, `scout-brief.md`) and
`docs/issue-275/proposals/2026-08-04-observation-plan-for-pr-276.md`. This
record's `loop_state` is `landed`; one finding (F-A) is open in the sense that
its action item belongs to the human, not to this role.

`docs/issue-271/` was out of evidentiary reach from this branch
(`core/hooks/board-gate.sh` R4), so nothing here rests on reading issue #271's
own tree; the F1-F4 texts were taken from issue #275's body and from the
observed role's own proposal and record, which quote the `ref:` lines at stake.

## Open findings

- **F-A** — §20 item 6 undischarged in `docs/issue-275/reports/implementation.md`
  for its confirmed hunt finding (`:188-195`); repo-wide class, evidence and
  action item above.

## Next steps

None for this role on this issue: step 2 of issue #275's execution plan is
complete with all three verdict levels recorded. F-A returns to the human on
PR #277.

## Open-finding resolution path

F-A is owned by the human approver on PR #277. This role neither edits the
observed artifact — `docs/issue-275/reports/implementation.md` belongs to the
`implementation` role's write area — nor files issues; under contract v3
issues are user-authored only. If the human judges F-A valid, the concrete
follow-ups are the two named in its action item: a class label plus habitat
sweep for the confirmed finding in that record, and a `record-fields-gate.sh`
check for §20 item 6, the latter being the only one that closes the repo-wide
recurrence rather than the single instance.
