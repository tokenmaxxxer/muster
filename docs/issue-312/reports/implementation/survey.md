---
role: implementation
subject: issue-312
loop_state: survey
---

# Current-state survey — closes-gate phase misattribution on cross-role handoff (issue #312)

## Scope

Issue #312 asks for a phase-1 proposal only, and it explicitly asks the
session to *decide* a design question, not just patch a symptom — scouting
is not skipped: two shapes are live in the field (phase-per-issue vs.
phase-per-(issue,role)) and the contract text has to be read closely to
tell which one it actually commits to.

## 1. The write set that produced the bug

`gates/ci.py:144` `_phase_from_approval(repo, pr, issue, role)` derives
`phase` from a single predicate: `flows._pr_approved(pr_dict, comments,
approvers, subject, role)` (`gates/flows.py:130`), which requires either

- an issue-level comment whose body equals exactly `APPROVE
  issue-<n>/<role>` from an `approvers.md` login, or
- a PR review Approve from an `approvers.md` login differing from the PR
  author.

`role` comes from `_issue_and_role_from_branch()` (`ci.py:59-62`), which
reads the PR's own head branch — i.e. the role of the session that opened
*this* PR, not the role that produced the approval the issue actually
received. For PR #307 (branch `issue-304/implementation`), `role =
"implementation"`. Issue #304 carries exactly one approval, `APPROVE
issue-304/architecture` (posted against PR #305, the phase-1 proposal).
`_pr_approved` requires the needle `APPROVE issue-304/implementation` —
no match — so `_phase_from_approval` returns `"phase1"`.

`check()` (`ci.py:229-286`) then runs the phase-1 branch (`ci.py:253-267`)
against PR #307, which is a genuine phase-2 delivery carrying `Closes
#304`. `_phase1_surface_mismatch` (`ci.py:169-193`) finds the closing
keyword in the body and reports it as a phase-1 violation
(`ci.py:191-192`) — the message the issue quotes.

## 2. Is this a bug or an already-decided design, working as designed?

`docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`
is the decision record for the code at `ci.py:144`. It explicitly adopted
the `APPROVE issue-<n>/<role>` event, citing contract v3 s19, and its
"기각한 대안" section rejects branch-name and plan-state signals — it
never discusses role at all as a design axis; role is simply inherited
from the phrase `APPROVE issue-<n>/<role>` that contract v3 s19 already
uses for the phase-2-opening approval string.

`gates/test_closes_gate_ci.py`
`t_phase_from_approval_wrong_role_comment_is_phase1` (added under #271)
asserts, by name, that an approval naming a *different* role does not
open phase2 for this role. So the current shape is not an oversight in
`ci.py` — it is the literal, intended, and already-tested reading of
"`APPROVE issue-<n>/<role>`": one approval string, scoped to one role,
opens phase 2 for *that role's own* PR.

## 3. What contract v3 s19 actually says, read directly

Two independent sources state the contract, and both use `<role>`
unconditionally:

- `protocol.md:239-246`: "The canonical location for the `APPROVE
  issue-<n>/<role>` signal (contract v3 s19) is the **issue comment**...
  A PR review Approve is only the two-account hardened alternative, when
  the approving account differs from the PR's author." No branch on role
  identity between the approving session and the delivering session is
  mentioned.
- The session-start protocol text this very session was invoked with
  ("Interaction protocol for role 'implementation'... APPROVE
  issue-<n>/<role>... posted by an approvers.md account") describes
  phase-2 opening as an act that happens *per role session*: "Phase 2
  opens ONLY when a human approver... submits a PR review Approve; then
  do your actual work on the same branch, reported through the same PR."
  This is written from the perspective of one role's own PR getting its
  own approval to move from proposal to delivery within that PR.

Neither source ever describes a *second* PR, opened by a *different*
role, delivering against the *same issue* on the strength of the first
PR's approval. The contract's `<role>` slot is unambiguous about *what
string* opens phase 2 for a role's own PR; it is silent on whether a
second role's delivery PR against the same issue needs its own matching
approval, or may ride on an approval already given to a different role's
proposal for that issue. Architect-proposes/implementer-delivers is a
shape the contract text never enumerates as either supported or
forbidden — issue #312's framing ("if the contract is silent, that
silence is part of the finding") is accurate: this is silence, not a
choice contract v3 s19 already made and `ci.py` got wrong.

## 4. The two live PRs this session can check against, unchanged

- PR #305, `issue-304/architecture`, OPEN, phase-1 proposal for #304.
  Carries the sole approval on the issue: `APPROVE issue-304/architecture`.
- PR #307, `issue-304/implementation`, OPEN, phase-2 delivery for #304.
  Body: `Closes #304`. This is the exact configuration issue #312
  describes; both PRs are still open and unmodified, so the acceptance
  criterion's "re-run closes-gate against PR #307 unchanged" is directly
  runnable against live GitHub state without any fixture construction.

## 5. What downstream code already assumes about phase granularity

`gates/flows.py:318-326` (mission-board rendering, a different code path
than the gate) computes `phase = 1 if loop_state in (None,
"scope-proposed") else 2` **per role**, from that role's own record
frontmatter `loop_state` — i.e. the board already treats phase as a
per-(issue,role) fact for *display* purposes, consistent with each role
tracking its own loop_state independently. This is evidence for the
(issue,role) reading being the more deeply embedded assumption elsewhere
in the codebase, even though it is exactly the reading that makes
architect→implementer handoff unrepresentable at the closes-gate.

## 6. Write set this proposal will need (frozen ahead, for the phase-2 proposal)

- `gates/ci.py` — `_phase_from_approval` (evidence-gathering + phase
  decision) and its call site in `check()` (refusal-message construction
  for the phase-1 branch).
- `gates/test_closes_gate_ci.py` — the existing
  `t_phase_from_approval_wrong_role_comment_is_phase1` test encodes the
  per-role reading and will need to change name/assertion or be replaced
  under whichever model is chosen; new tests for the #304/#307
  reproduction and the refusal-text evidence assertion land here too.
- `docs/issue-312/decisions/` — the phase-model decision itself
  (issue-level vs. (issue,role)-level, with the contract-silence finding
  recorded), since it reverses/refines a choice `docs/issue-271/decisions/`
  already made without knowing about cross-role handoff.
