---
kind: coding-record
code_under_review: gates/ci.py, gates/test_closes_gate_ci.py, docs/handbooks/operations.md,
  test_spawn.py
loop_state: landed
closed_checks:
  - check: "F3 red-green: gates/test_closes_gate_ci.py's
      t_phase_from_approval_pr_thread_comment_is_not_issue_level_is_phase1
      proves a PR-thread-comment union no longer opens phase2 — a
      throwaway reconstruction of the pre-fix union logic against this
      test's exact mocks returns phase2 (red); current
      ci._phase_from_approval returns phase1 (green)."
    ref: gates/test_closes_gate_ci.py:199
  - check: "Full gates/test_closes_gate_ci.py suite: 28/28 pass (26 prior
      + 2 new, F3 and F4)."
    ref: gates/test_closes_gate_ci.py:1
  - check: "F4 behavioral red proof: ci._phase1_mismatch(clean_body, 245)
      == [] regardless of commit-message content, because the pre-#271
      predicate never inspected commit messages — non-vacuity confirmed
      by flipping to a dirty body and observing the same assertion would
      fail (AssertionError, not AttributeError)."
    ref: gates/test_closes_gate_ci.py:344
  - check: "F1 citation fix: test_spawn.py's WatchFollow class, 9/9 pass;
      spawn.py:1943-1953 and test_spawn.py:3719-3747 opened directly and
      confirmed to be what the corrected comment now claims."
    ref: test_spawn.py:3749
  - check: "Regression: test_flows.py 3/3 pass. Full `python3 -m
      unittest test_spawn` shows 53 pre-existing errors in classes this
      diff never touches (ProgressEvents, permission-denial/gate-marker
      classification), traced to a local rulebook-checkout git-template
      failure unrelated to this diff — see \"What did not work\"."
    ref: test_spawn.py:1
  - check: "warrant-hunter dispatch (general-purpose, stance:
      adversarial-self, rotated — least recently used of the four known
      stances after issue-271's silent-failure) — one CONFIRMED finding
      (a stale self-citation this same diff introduced at
      gates/test_closes_gate_ci.py:350), fixed and re-tested in this
      session before this record's commit; F1/F3/F4 and the docs wording
      were independently reproduced and verified NOT-A-BUG."
    ref: gates/test_closes_gate_ci.py:350
---

# Implementation record — issue #275

## Why

Phase 2, executing the approved proposal
(`docs/issue-275/proposals/2026-08-04-closes-gate-approval-scope-and-record-hygiene.md`),
approved via issue-level comment `APPROVE issue-275/implementation`
(single-account mode, role-handoff contract v3, PR #276 author and
approver both `jjongkwann`). Delivers F1-F4 from #271's
execution-observation record: F3, the fail-open gap where
`_phase_from_approval` unioned the PR's own conversation-thread comments
into the issue-level approval predicate contract v3 s19 defines; F2, the
Korean/English mirror divergence in `docs/handbooks/operations.md`; F1,
stale post-rebase line citations in a restored test's own comment; F4,
requirement 4's red proof being a missing-symbol crash rather than a
behavioral demonstration.

## What was done

1. **F3.** `gates/ci.py`'s `_phase_from_approval` no longer calls
   `spawn._issue_comments(repo, pr)` — it reads only
   `spawn._issue_comments(repo, issue)`. The function's own docstring,
   which previously said "이슈/PR 코멘트" (issue/PR comment), was
   corrected to "이슈 코멘트" (issue comment) and a sentence added naming
   the fixed defect. Added
   `t_phase_from_approval_pr_thread_comment_is_not_issue_level_is_phase1`
   to `gates/test_closes_gate_ci.py`, mocking the PR-number branch of
   `spawn._issue_comments` to return a qualifying comment while the
   issue-number branch stays empty, and asserting the result is
   `"phase1"`.
2. **F2.** Rewrote the Korean `## 머지 게이트 (CI)` section: removed the
   stale "phase는 본문의 closing 키워드 유무에서 끌어낸다" claim from the
   summary paragraph, and added Korean counterparts of the two
   English-only paragraphs (approval-event phase mechanism; three-surface
   phase-1 check), written to the post-F3-fix behavior (issue comment
   only). Also corrected the English section's own stale "issue/PR
   comment" phrase to "issue comment" and named the PR-thread exclusion
   explicitly — leaving that phrase unfixed while F3 landed in the same
   PR would have re-created the exact KO/EN divergence F2 exists to
   close, just with English now the stale side.
3. **F1.** `test_spawn.py`'s
   `test_follow_prioritizes_pending_session_end_over_pid_check` comment:
   `spawn.py:1884-1894` → `spawn.py:1943-1953` (the drain-priority
   block), `test_spawn.py:3480-3485` → `test_spawn.py:3719-3747` (the
   sibling `test_follow_detects_dead_session_and_returns_crash_rc`). No
   code logic changed.
4. **F4.** Added
   `t_phase1_mismatch_pre_271_body_only_gate_missed_commit_message_keyword`
   to `gates/test_closes_gate_ci.py`, calling the still-live
   `ci._phase1_mismatch` with a clean body and asserting `== []` —
   demonstrating behaviorally that the pre-#271 single-surface predicate
   never inspected commit messages, replacing the original record's
   `AttributeError`-from-a-missing-symbol proof. Placed immediately
   before, and cross-referencing,
   `t_autodetect_closes_only_blocks_commit_message_keyword_with_clean_body`,
   which blocks the identical scenario through the real post-#271
   multi-surface path.

## What did not work

- Two of the proposal's frozen write-set items — the
  `docs/issue-271/reports/implementation.md` `ref:` corrections named by
  F1 and F4 — could not be completed on this branch: expected the file to
  be writable per the approved proposal's `files:` list; actual: the
  repo's `board-gate.sh` PreToolUse hook (contract v3 s10, rule R4)
  refuses any write under `docs/issue-271/` from a branch other than
  `issue-271/<role>`, unconditionally, regardless of merge state or
  content. Even a read-only `git log -- docs/issue-271/...` invocation
  issued mid-session while researching citation history was refused by
  the same gate for the same reason (its path scan does not distinguish
  a read subcommand from a write for `git`), confirming the restriction
  is enforced mechanically and not something this session could route
  around. See "Rationale for deviations."
- A full `python3 -m unittest test_spawn` run surfaced 53 pre-existing
  errors, all in test classes this diff never touches (`ProgressEvents`,
  permission-denial/gate-marker classification, etc.) — expected: no
  effect from a 2-comment-line change plus unrelated files; actual
  traceback (e.g. `test_spawn.ProgressEvents.test_writes_to_different_files_both_fire`)
  shows a `SystemExit` from `spawn.rulebook_checkout` failing a `git`
  template-hook copy under this sandbox's home directory — a local
  environment gap, not caused by or fixable within this PR's write set.
  The class this diff actually touches (`WatchFollow`) and the sibling
  `test_flows.py` both run clean (9/9, 3/3) in isolation.
- The hunt (adversarial-self stance) found one real, if minor, defect in
  this session's own diff before it was fixed: the new F4 test's
  cross-reference comment cited `gates/ci.py:165` for `_phase1_mismatch`
  — correct against HEAD but stale the moment this same diff landed,
  because F3's docstring expansion of `_phase_from_approval` (+4 net
  lines) pushed `_phase1_mismatch`'s `def` line down to `:169`. Fixed
  before commit (see Hunt).

## Rationale for deviations

The approved proposal's `files:` write set and its F1/F4 "What will be
done" items named `docs/issue-271/reports/implementation.md` for two
`ref:` corrections (both `test_spawn.py:3497` entries →
`test_spawn.py:3749`, and the F4 red-proof entry's `AttributeError`
description → a pointer at the new behavioral test). Attempting these
edits on this session's `issue-275/implementation` branch is refused by
`board-gate.sh`'s R4 rule (contract v3 s10): a write under
`docs/issue-<n>/` requires the current branch to be exactly
`issue-<n>/<role>` — `docs/issue-271/` is issue #271's own tree, not
issue #275's, and stays refused regardless of the target record's
`loop_state` or the fact that issue #271 is already merged. This is a
genuine gap between the approved proposal (which named a file this
session structurally cannot write) and the interaction contract's
branch-scoped board model, not something to route around by disabling or
bypassing a hook. Everything else in the proposal's "What will be done"
for F1 and F4 — the code-adjacent corrections in `test_spawn.py`'s own
comment, and the new `gates/test_closes_gate_ci.py` behavioral proof —
landed as specified. The two blocked `ref:` corrections in issue #271's
own record are a flagged follow-on: they need a session opened against
issue #271's own branch (or a fresh issue authorizing that write), not a
continuation of this one.

## Doc-placement ladder

- [x] Standing-gate behavior change (approval predicate narrowed to
  issue-level comments only) → `docs/handbooks/operations.md`, same turn
  as the `gates/ci.py` change, both Korean and English sections.
- [x] Session recap → this reply, not docs/.
- [ ] No new env var, dependency, or migration introduced — nothing to
  route there.
- [ ] No format/wire-signature change — F3 narrows an internal
  predicate's input, not a public interface; the approved proposal's own
  Rationale already carries the alternative-and-reason record for this
  decision, so no new `docs/issue-275/decisions/` entry is needed.

## Hunt

Stance: **adversarial-self** (rotated — issue-271's record, the most
recent implementation-role hunt found, used silent-failure; before that
issue-247 used assume-broken, issue-266 used composition-regression, and
issue-262/246 used adversarial-self — adversarial-self is the least
recently used of the four known stances). No registered `warrant-hunter`
subagent type is available in this harness (same gap prior records
note) — `general-purpose` dispatched in its place, foreground/synchronous
(contract v3 s22 — this session is headless/single-shot, so the dispatch
had to be waited on and consumed within this same turn, never
backgrounded), with an explicit adversarial-self brief (assume the fix is
broken, try to break it; run real commands, don't just re-read the diff)
against the uncommitted diff before this record's commit.

Findings:

1. **CONFIRMED, fixed.** `gates/test_closes_gate_ci.py:350` (at hunt
   time, before the fix below) cited `gates/ci.py:165` for
   `_phase1_mismatch`'s `def` line — correct against HEAD but stale the
   instant this diff lands, because F3's `_phase_from_approval` docstring
   expansion (+4 net lines) pushes `_phase1_mismatch`'s `def` down to
   `:169` in the working tree. Fixed in this same session before this
   commit (165 → 169); re-ran `gates/test_closes_gate_ci.py`, 28/28 still
   pass.
2. Hunt points that came back **NOT-A-BUG** (independently reproduced,
   not just asserted): F3 — `grep` confirms `gates/ci.py` has exactly one
   `spawn._issue_comments` call left (issue-number only) and no other
   PR-number comment fetch anywhere in the file; a throwaway
   reconstruction of the pre-fix union logic against the new test's exact
   mocks reproduced `"phase2"` (red) pre-fix and `"phase1"` (green)
   post-fix; `_pr_reviews` (the two-account PR-review path) is untouched
   and hits a structurally different endpoint, so it can't alias with the
   issue-comments fetch. F4 — `grep` confirms `_phase1_mismatch` is never
   called from production code (only `_phase1_surface_mismatch` is, fed
   `[body, title, *commit_messages]` from `check()`), so "the pre-#271
   shape never sees commit messages" holds structurally, not just in the
   new test's mock. F1 — `spawn.py:1943-1953` and
   `test_spawn.py:3719-3747` opened directly and confirmed to be what the
   corrected comment now claims. Docs (F2) — both language sections'
   "issue comment, not PR comment" claims were checked against the fixed
   code's actual behavior and hold. Noted, out of scope: `spawn.py`'s
   `approve_scope()` (`:933-935`) has the same-shaped issue+PR comment
   union for a different, unrelated gate (`scope-approved`, issue
   #115/#224) — the approved proposal's own "Out of scope" already names
   this as a flagged follow-on, not a defect of this changeset.

## Open findings

None — the one hunt finding (a stale self-citation introduced by this
diff) was resolved and re-tested before this commit; see Hunt above.

## Next steps

None for this role on this issue. Two `ref:` corrections in
`docs/issue-271/reports/implementation.md` (part of F1 and F4) remain
undone — see "Rationale for deviations" — and need either a new
issue-271-branch session or a fresh issue authorizing that write, not a
continuation of this one.

## Open-finding resolution path

No findings remain open — the one hunt finding (a stale self-citation
introduced by this diff) was resolved, re-tested, and folded into this
same commit before landing (see Hunt and closed_checks above). The
blocked `docs/issue-271/` `ref:` corrections are not a "finding" in the
hunt sense — they are a structural scope gap recorded under "Rationale
for deviations," not a defect to resolve within this record.
