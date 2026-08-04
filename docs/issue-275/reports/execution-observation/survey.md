# Current-state survey — issue #275 step 2 (execution observation)

Phase 1 artifact. No verdict language appears here or in this issue's
proposal; verdicts belong to phase 2's record
(`docs/issue-275/reports/execution-observation.md`) and open only after a
contract v3 §19 approval.

## Scope under observation

- **Role**: `implementation` (the observed role).
- **Session**: the single 2026-08-04 headless session that produced both
  phases on branch `issue-275/implementation` — phase 1 at
  `fabd74b3cfd62c00ccdc3aa28aa1672b39895227` (2026-08-04T06:50:19Z),
  phase-2 skeleton at `21f91f66af73f59bd1914cd8986083c8bfa4e104`
  (07:01:21Z), phase-2 work at
  `cb6b46adae81153930edef172386f42113df914f` (07:14:11Z).
- **Issue**: #275 — "closes-gate 후속 정비 — 승인 술어 계약 정합(F3
  fail-open) + 문서·증명 정비 (#271 관찰 F1~F4)", 4 requirements, execution
  plan step 1 `implementation` / step 2 `execution-observation`.
- **PR**: #276 — https://github.com/tokenmaxxxer/on-the-record/pull/276,
  head `issue-275/implementation`, base `main`, MERGED 2026-08-04T07:17:23Z
  as merge commit `236b66ecebe97a6e09a59b5334ac15d466338298`, +921/-10
  across 8 changed files (PR-level counts, both phases).

This survey observes **that** session's artifacts only. It is not an
observation of "recent work", not of issue #271 or PR #273 (the upstream
that raised F1-F4), and not of `gates/ci.py`'s present-day state as such.

## What was read this session, first-hand

| Artifact | Source read |
| --- | --- |
| Issue text and requirements | `gh issue view 275` |
| Issue-level approval comment | `gh api repos/tokenmaxxxer/on-the-record/issues/275/comments` → id 5175585081, `jjongkwann`, 2026-08-04T06:51:15Z, body exactly `APPROVE issue-275/implementation` |
| PR #276 metadata, body, review/comment state | `gh pr view 276 --json ...` → `reviews: []`, `comments: []`, `createdAt: 2026-08-04T06:50:37Z` |
| Commit list, authorship, trailers | `git log --format=... fabd74b~1..236b66e` |
| Phase-2 diff (code + docs) | `git show cb6b46a -- gates/ci.py gates/test_closes_gate_ci.py test_spawn.py docs/handbooks/operations.md` |
| Observed role's record | `docs/issue-275/reports/implementation.md` (239 lines, read in full) |
| Observed role's proposal | `docs/issue-275/proposals/2026-08-04-closes-gate-approval-scope-and-record-hygiene.md` (228 lines, read in full) |
| Observed role's phase-1 files (existence, provenance) | `docs/issue-275/reports/implementation/survey.md` (229 lines), `.../scout-brief.md` (147 lines) — both committed in `fabd74b` |
| Committed-tree line facts | `git show cb6b46a:gates/ci.py` and `git show cb6b46a~1:gates/ci.py`, grepped for the two predicates |
| Contract §20 text | `.../rulebooks/tokenmaxxxer-core/core/contract/role-handoff-contract.md:827-870` |

Nothing above is a re-execution of the observed role's task; every row is
either the observed role's own produced artifact or a GitHub fact about
how it was approved and landed.

## Current state as landed

**Timeline.** phase-1 commit 06:50:19Z → PR #276 opened 06:50:37Z →
issue-level `APPROVE issue-275/implementation` 06:51:15Z → phase-2
skeleton 07:01:21Z → phase-2 work 07:14:11Z → merged 07:17:23Z. Author
and approver are the same account (`jjongkwann`), which is on
`docs/specs/approvers.md` (two entries: `JiwonJung94`, `jjongkwann`) —
i.e. contract v3 §19's single-account path, exact-string issue comment.

**Landed write set (`cb6b46a`, 5 files):** `gates/ci.py` (+10/-6 net per
diffstat line count 10 changed), `gates/test_closes_gate_ci.py` (+41),
`docs/handbooks/operations.md` (+35 changed), `test_spawn.py` (2 comment
lines), `docs/issue-275/reports/implementation.md` (+221). The approved
proposal's `files:` header names a sixth path,
`docs/issue-271/reports/implementation.md`, which is absent from the
diffstat; the record's "Rationale for deviations" (`:134-156`) states it
was refused by `board-gate.sh` R4 (branch-scoped write ownership).

**Requirement-to-artifact map, as claimed by the record:**

| Issue requirement | Claimed landing site |
| --- | --- |
| 1 (F3, narrow approval input + red-green) | `gates/ci.py` `_phase_from_approval` (second `_issue_comments` fetch deleted), new test `t_phase_from_approval_pr_thread_comment_is_not_issue_level_is_phase1` |
| 2 (F2, KO/EN operations.md parity) | `docs/handbooks/operations.md` KO section rewrite + EN "issue/PR comment" → "issue comment" |
| 3 (F1, stale citations, style call made in proposal) | `test_spawn.py` comment (2 citations); the record's own `closed_checks` refs; **not** `docs/issue-271/...` |
| 4 (F4, behavioral red proof) | new test `t_phase1_mismatch_pre_271_body_only_gate_missed_commit_message_keyword` |

## Write surfaces and their unknowns — what this observation must resolve

These are the gaps this survey found; the scout sweep aims at them, and
the proposal turns them into named checks.

1. **Outcome surface — requirement coverage vs. the issue's four asks.**
   Requirement 3's ask was explicitly two-part (correct the citations
   *and* decide the sha-pinned style question in the proposal). One of the
   two named citation artifacts did not land. Unknown: whether the
   remaining shortfall is a scope deviation properly recorded, or a
   requirement left unmet — and by which standard that call is made.
2. **Trajectory surface — phase boundary and approval provenance.**
   Approval is 38 s after PR open and 18 s after the phase-1 commit.
   Unknown: whether any phase-2-shaped content sits inside the phase-1
   commit (which would move work across the §19 boundary), and whether the
   approval satisfies §19's single-account path on its own terms (exact
   string, issue-level, approvers.md account, not a bot).
3. **Step surface — proof quality of the two new tests.** F3's test is a
   mock-level discriminator; F4's is an assertion on a retained pre-#271
   helper with no commit-message input at all. Unknown: whether each
   actually pins what its requirement asked for, judged from the diff and
   the record's own red evidence rather than from a re-run.
4. **Record surface — §20 minimum content.** The record states one
   CONFIRMED hunt finding (`gates/test_closes_gate_ci.py:350`, stale
   self-citation). §20 item 6 attaches to confirmed findings: defect class
   plus whether that class was swept elsewhere. Unknown: whether the record
   discharges item 6 for *that* finding's class, as distinct from the
   `_issue_comments`-union sweep it does record.
5. **Self-consistency surface — citations inside the observed record.**
   The record's `closed_checks` refs are unpinned `file:line` claims about
   a tree that the same commit changed. Unknown: whether they resolve in
   the landed tree (`cb6b46a`), which is checkable from the commit's own
   content without reading present-day `src/`.

## Prior-observation continuity

Issue #275 exists because #271's execution-observation record raised
F1-F4; the same repo's #227 and #245 observation records are cited inside
the observed role's own proposal (`:104-113`, `:36-38`) as prior art on
citation drift and predicate coupling. Observation-of-observation
continuity — does this round's follow-up actually close what the prior
round opened — is therefore in scope for the outcome level.
