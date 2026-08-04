---
kind: coding-record
code_under_review: gates/ci.py, gates/test_closes_gate_ci.py, test_spawn.py,
  docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md,
  docs/handbooks/operations.md
loop_state: landed
closed_checks:
  - check: "gates/test_closes_gate_ci.py red proof (pre-fix): new tests
      referencing not-yet-existing API crash with AttributeError: module
      'ci' has no attribute '_pr_title' (first-alphabetical test hit the
      missing surface immediately)."
    ref: gates/test_closes_gate_ci.py:296
  - check: "gates/test_closes_gate_ci.py green proof (post-fix): full
      suite, 26/26 pass, including the reachability-fix and
      requirement-4 commit-message regression tests driven through the
      actual --autodetect --closes-only orchestration
      (_autodetect_issue_phase then check())."
    ref: gates/test_closes_gate_ci.py:1
  - check: "test_spawn.py::WatchFollow.test_follow_prioritizes_pending_session_end_over_pid_check
      red proof: spawn.py:1884-1894 (drain-priority block) temporarily
      deleted, test fails AssertionError: 2 != 0 (WATCH_CRASH_RC fires
      instead of draining the pending session-end)."
    ref: test_spawn.py:3497
  - check: "same test green proof: spawn.py restored byte-identical
      (`git diff spawn.py` empty), full WatchFollow class re-run, 9/9
      pass."
    ref: test_spawn.py:3497
  - check: "test_flows.py — 3/3 pass, unchanged (flows._pr_approved is
      read-only reused, not modified)."
    ref: gates/flows.py:130
  - check: "live dry run of the actual wired invocation form, `python3
      gates/ci.py . --pr 273 --autodetect --closes-only`, against this
      session's own real PR — 게이트 통과 (exit 0), both before and
      after the pagination fix below."
    ref: gates/ci.py:1
  - check: "warrant-hunter dispatch (general-purpose, stance:
      silent-failure, rotated from issue-266's composition-regression)
      — one CONFIRMED blocking finding (commit-list pagination
      truncation, see Hunt section), fixed and re-tested in this same
      session before this record's commit; all other hunted paths
      (approval-fetch failure mode, title/commit None handling,
      surface-mismatch early-return, role threading) came back clean."
    ref: gates/ci.py:85
---

# Implementation record — issue #271

## Why

Phase 2, executing the approved proposal
(`docs/issue-271/proposals/2026-08-04-closing-trigger-surface-coverage-and-phase-predicate-separation.md`),
approved via issue-level comment `APPROVE issue-271/implementation`
(single-account mode, role-handoff contract v3, PR author and approver
both jjongkwann). Three independent 2026-08-04 observations (issues #245,
#262, #266) converged on the same gap: the plan-aware Closes gate only
inspects the PR body, missing the commit-message vector that twice
auto-closed an issue for real; a second, structural defect makes the
existing phase-1 "no closing keyword" check unreachable because phase
itself is derived from the same keyword predicate the check is supposed
to police.

## What was done

1. **`gates/ci.py` — approval-derived phase signal (requirement 2).**
   Added `_issue_and_role_from_branch` (captures the role segment
   alongside the issue number) and `_phase_from_approval` (phase2 iff a
   qualifying `APPROVE issue-<n>/<role>` comment or differing-account PR
   review Approve exists, via `flows._pr_approved` — see "Rationale for
   deviations"). `_autodetect_issue_phase` now uses this instead of
   `_phase_from_body` as the autodetect path's phase source; the old
   body-keyword-derived `_phase_from_body`/`_issue_from_branch` and their
   tests were removed rather than left as unreachable dead code (nothing
   outside `gates/ci.py`/its own tests referenced them — confirmed by
   repo-wide grep before removal).
2. **`gates/ci.py` — title/commit-message surface coverage (requirement
   1, rows B/C).** Added `_pr_title`, `_pr_commit_messages` (see pagination
   fix below), `_pr_reviews`. `_phase1_mismatch` (body-only, kept for its
   existing direct callers) is now a one-surface call into the new
   `_phase1_surface_mismatch(issue, surfaces)`, which `check()`'s
   `phase == "phase1"` branch now calls with all three surfaces (body,
   title, each commit message) — a fetch failure on any of the three
   fails closed (blocks), matching this file's existing
   "검사 불가는 통과가 아니다" convention.
3. **`gates/test_closes_gate_ci.py`** — rewritten: branch/role tests,
   `_phase_from_approval` unit tests (no-signal, qualifying comment,
   non-approver, wrong-role, differing-account PR review), surface-mismatch
   tests (title, commit message, first-match-wins), the reachability-fix
   red-green pair, and the requirement-4 commit-message regression driven
   through the real `--autodetect --closes-only` orchestration path (not
   a narrower `--phase`-supplied call — the exact gap the prior,
   insufficient requirement-2 proof left, per survey.md §2). 26 tests,
   all passing (closed_checks).
4. **`test_spawn.py`** — `test_follow_prioritizes_pending_session_end_over_pid_check`
   rearranged from "roster entry entirely removed" to "live entry, dead
   `wrapper_pid`" (matching the arrangement
   `test_follow_detects_dead_session_and_returns_crash_rc` already uses),
   restoring its ability to discriminate `spawn.py:1884-1894` — red-green
   proof in closed_checks. `spawn.py` itself is untouched (requirement 3
   asks only for the test to be restored).
5. **`docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`**
   — records both Rationale choices (approval-event phase signal;
   direct-surface-read over `closingIssuesReferences`) plus the
   `flows._pr_approved` reuse discovered at execution time (see
   "Rationale for deviations").
6. **`docs/handbooks/operations.md`**'s "Merge gate (CI)" section —
   updated same turn to describe the widened surface set (title +
   description + commit messages) and the approval-based phase signal,
   replacing the stale "phase from whether the body has a closing
   keyword" line.

## What did not work

- `_pr_commit_messages`'s first version called `gh api
  repos/<slug>/pulls/<n>/commits` with no pagination flag — expected: the
  full commit list; actual (warrant-hunter, silent-failure stance): the
  endpoint caps at 30 commits/page, so a PR with 31+ commits would have
  had any closing keyword in commit #31 onward silently unchecked —
  `returncode == 0` and `json.loads` both succeed on the truncated first
  page, so no failure signal fires. Fixed by adding `--paginate --slurp`
  (matching `spawn._issue_comments`'s existing fix for the identical
  gap, spawn.py:836) and flattening pages before mapping to messages; a
  new test (`t_pr_commit_messages_paginates_and_flattens`) proves the
  flags are actually passed and multi-page output is flattened.
- The record-fields-gate.sh PreToolUse hook refused this record's first
  Write (missing an explicit `## Open findings` heading) — expected: the
  loop_state/what-was-done/why fields alone would satisfy §20; actual:
  §20 also requires an open-findings section (and, while non-terminal,
  next-steps/resolution-path) even for a fresh skeleton. Added all three
  headings to the skeleton before the first commit.
- **Post-landing rebase (2026-08-04), PR #273 vs latest `origin/main`.**
  PR #247 (self-triggered abandoned-work respawn) landed on `main` mid-PR,
  putting this branch's PR into merge conflict — expected: a purely
  mechanical/textual conflict from #247's unrelated `spawn.py`/
  `test_spawn.py` edits landing first; actual: `test_spawn.py` auto-merged
  cleanly (#247's `SessionEndVerdict`/`SelfTriggeredRespawn` insertions
  sit in a disjoint region of the file from this branch's
  `test_follow_prioritizes_pending_session_end_over_pid_check` rearrangement
  — only line numbers shifted, from :3497 to :3749), but
  `docs/handbooks/operations.md` carried a genuine **logical** conflict:
  `origin/main` (issue-245's F3 wrap-up, already landed via PR #272)
  states the closes-gate is "**Blocking for real as of 2026-08-04**"
  (registered as a required status check), while this branch's own
  "Merge gate (CI)" paragraph — drafted before that activation landed —
  still said "**Nothing is actually blocked yet**." Resolved by keeping
  the landed activation status as ground truth (the board is what is
  merged to main) and dropping this branch's now-stale
  not-yet-blocking claim, retaining the phase-signal/surface-coverage
  paragraphs unchanged. Re-ran `test_spawn.py` (206/206),
  `gates/test_closes_gate_ci.py` (26/26), and `test_flows.py` (10/10)
  post-rebase; all green, matching pre-rebase counts. Force-pushed the
  rebased branch to update PR #273 in place.

## Rationale for deviations

The approved proposal's "What will be done" item 1 described the
approval-check mechanism as newly hand-written: "add a phase-derivation
path that queries `spawn._issue_comments`/`spawn._approvers`... whether a
qualifying approval exists," modeled on `spawn.approve_scope`'s idiom.
Reading `gates/flows.py` at execution time (not surfaced by the survey)
showed `_pr_approved(pr, comments, approvers, subject, role)`
(`flows.py:130`) already implements exactly this contract — both the
single-account comment path and the two-account differing-reviewer path
— and is already the function the status board (`flows.status()`) uses
live to flag unapproved PRs. Swapped to reuse it rather than hand-writing
a duplicate: same signal the proposal's Rationale chose (an
`APPROVE issue-<n>/<role>` approval event, not closing-keyword presence),
different code path to read it. `gates/ci.py` gains an `import flows`
(the same layer `pr_reference.py` already imports from); no new
dependency direction. Full reasoning:
`docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`
§1.

## Doc-placement ladder

- [x] Format/mechanism decision (approval-event phase signal over
  branch-name/plan-state; direct-surface reads over
  `closingIssuesReferences`; the `flows._pr_approved` reuse deviation) →
  `docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`.
- [x] Standing-gate behavior change (widened inspected-surface set,
  approval-based phase signal) → `docs/handbooks/operations.md`, same
  turn as the code change.
- [x] Session recap → this reply, not docs/.
- [ ] No new env var, dependency, or migration introduced — nothing to
  route there.

## Hunt

Stance: **silent-failure** (rotated — issue-266's record, the most
recent implementation-role hunt found, used composition-regression,
itself rotated from issue-246's adversarial-self; issue-262 used
adversarial-self before that. silent-failure was last used at issue-228,
making it the least-recently-used stance in the observed rotation).
No registered `warrant-hunter` subagent type is available in this
harness (same gap prior records note) — `general-purpose` dispatched in
its place, foreground/synchronous, with an explicit silent-failure brief
(hunt for swallowed errors, dropped data, or checks that silently pass
when they should block) against the diff before this record's commit.

Findings:

1. **CONFIRMED, fixed.** `_pr_commit_messages` (`gates/ci.py:85`, at hunt
   time) omitted `--paginate`/`--slurp` on the commits-list `gh api`
   call — GitHub's default 30-commit page cap meant commit #31+ on a PR
   with many commits would never be scanned for a closing keyword,
   silently (no error, no block) reproducing the exact commit-message
   blind spot this feature exists to close. Fixed: pagination flags
   added, output flattened, new regression test added and passing (see
   "What did not work" and closed_checks).
2. Hunt points that came back clean (verified, not just asserted):
   `_phase_from_approval`'s failed/`None` reviews fetch degrades to "no
   approval" (fail-closed, never fail-open); `check()`'s title/commit
   `None` handling blocks on every call path including `closes_only=True`;
   `_phase1_surface_mismatch`'s early-return only fires on an actual
   match (a clean PR still checks every surface); `_autodetect_issue_phase`
   never leaves `role` silently `None` when `_phase_from_approval` is
   reached. Non-blocking: `_pr_title`/`_pr_reviews` don't wrap
   `json.loads` in try/except the way `_pr_commit_messages` does — a
   malformed-JSON response would raise uncaught rather than degrade to a
   blocking message; net effect is still a block (non-zero propagation),
   not a silent pass, so left as-is rather than expanding scope to
   harden a path with no observed failure mode.

## Next steps

None for this role — issue #271's own plan names `step 2
execution-observation` next; that is a different role's session, not a
continuation of this one.

## Open-finding resolution path

No findings remain open — the one hunt finding (commit-list pagination
truncation) was resolved, re-tested, and folded into this same commit
before landing (see Hunt and closed_checks above).
