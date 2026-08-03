---
kind: proposal
subject: issue-227
date: 2026-08-03
---

# Proposal — codify the conditional-approval relay recipe

files:
- `on-the-record/commands/run.md` (step 6 relay recipe)
- `docs/handbooks/operations.md` (canonical-approval-location section)
- `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-form.md` (new)

## Request

Issue #227, paraphrased: the approval-gate recognizes only a comment whose
entire body is the exact string `APPROVE issue-<n>/<role>`, but the
orchestrator playbook gives the orchestrator no rule for what to do when the
user's decision is "approve, but fix X" — approval and feedback in the same
breath. Two real cases from the repo-status-board pilot (issues #20 and #23)
show the orchestrator posting the token as the first line of a comment that
also carries the conditional feedback, and phase 2 proceeding regardless.
The issue asks to: (1) codify the canonical two-part form for conditional
approval — a token-only comment plus a separate feedback comment, with order
and location specified; (2) confirm and record, with evidence, what the gate
actually safely recognizes; (3) state this issue's relationship to adjacent
code defect #224 without absorbing it.

## Constraints

- Do not change the approval gate's matching logic or code (`gates/flows.py`,
  `spawn.py`) — this issue is document/practice-side only.
- Do not invent a new approval grammar (e.g. `APPROVE-WITH-CHANGES`) — the
  canonical token stays the single, unmodified `APPROVE issue-<n>/<role>`.
- Stay clear of adjacent issue #224's territory (the `approve-scope`
  `/scope`-vs-`/role` code mismatch, and the 30-comment pagination gap) —
  name the relationship, don't fix the code.
- The recipe must work in the single-account default setup, where the PR
  author and the approver are the same account and GitHub blocks
  self-review-approval — so it cannot rely on the PR-review-Approve path.

## Rationale

**Chosen approach**: canonicalize a strict two-comment sequence on the
*issue* thread (not the PR) — comment A's body is exactly the token string,
nothing else, ever; comment B, posted immediately after, carries the
conditional feedback and points back at comment A rather than repeating any
part of the token. Token-first ordering means a session or a human scanning
the thread the instant comment A lands already sees a valid, unambiguous
approval — feedback landing a moment later never puts that in question.

**Rejected alternative 1 — loosen the matcher** (e.g. match only the first
line, or strip a recognized trailing block) so a single mixed comment still
counts as approval. Rejected because `docs/decisions/2026-07-29-permanently-
closed-alternatives.md` already closed the entire class of "parse the
comment to decide approval intent" after three separately-measured leaks,
settling on exact whole-body string equality specifically because "deciding
whether two strings are equal is not a language problem." Any matcher
generalization — even one as small as "ignore anything after the first
line" — reopens that exact surface (a comment could smuggle the token inside
a quoted excerpt, a code fence, or a reply-context blockquote and still
"approve" something nobody meant to approve). The gate's current strict
equality (`gates/flows.py:131-132`, confirmed by survey to reject *both*
real specimens verbatim) is the correct, deliberately-chosen behavior; this
proposal fixes what gets posted, not what gets read.

**Rejected alternative 2 — a new composite token** (e.g.
`APPROVE-WITH-CHANGES issue-<n>/<role>`) to let one comment carry both
meanings explicitly. Rejected per the issue's own constraint against new
approval grammar, and because it duplicates, with a second textual
convention, exactly what GitHub's own PR-review model already expresses
structurally via separate `state`/`body` fields (confirmed in scout:
docs.github.com/en/rest/pulls/reviews) — a second plain comment achieves the
same separation with zero new syntax to teach or to keep in sync across
`run.md`/`operations.md`/the gate.

**Rejected alternative 3 — rely on PR-review-Approve instead of the issue
comment entirely.** This is GitHub's own structured channel (state separate
from body — exactly what Kubernetes' Prow bot also does by keeping
`/approve`, `/lgtm`, and `/hold` as separate commands rather than one
expressive one; see scout brief) and `gates/flows.py`'s second detection
path already supports it. Rejected as the *default* because it is
structurally unavailable in the single-account setup this project actually
runs (GitHub disallows approving one's own PR review) — it remains the
documented alternative for the hardened multi-account configuration only,
unchanged by this proposal.

## What will be done

1. Add an explicit "조건부 승인" recipe to `on-the-record/commands/run.md`
   step 6, immediately after the existing "제안 승인" bullet: when the
   user's decision is approve-with-feedback, the orchestrator posts, in
   order: (a) `gh issue comment <issue-n> --body "APPROVE issue-<n>/<역할>"`
   verbatim with no other text, then (b) a second `gh issue comment` on the
   same issue carrying the feedback, referencing comment (a) rather than
   restating the token. State plainly that comment (a) must never carry
   trailing text, under any circumstance.
2. Mirror the same recipe, same ordering, into
   `docs/handbooks/operations.md`'s existing canonical-approval-location
   section (~line 309-364).
3. Add `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-
   form.md`: the chosen two-comment recipe; the three rejected alternatives
   and why; the empirical evidence that neither real specimen (rsb #20,
   #23) satisfies `gates/flows.py:131-132`'s strict equality, quoted
   verbatim; and the GitHub/Prow precedent with sources.
4. Cross-reference issue #224 by number (not by content) in both the new
   decision doc and the `run.md` addition: the `approve-scope` `/scope`-vs-
   `/role` mismatch and the comment-pagination cap are separate, code-side,
   tracked there.

## Out of scope

- Any edit to `gates/flows.py`, `spawn.py` (including `approve_scope`'s
  `/scope` literal), or any other matcher/regex code.
- A new approval token syntax.
- Fixing #224's `/scope`-vs-`/role` mismatch or the 30-comment pagination
  cap.
- Changing rsb's own deployed copy of these files directly (rsb is a
  separate repo; it picks up this recipe on its next rulebook update).
- Changing the single-account/multi-account setup or GitHub's self-review
  restriction.

## How you'll know it worked

- `run.md` step 6 and `operations.md` both state the same explicit
  two-comment recipe, with "comment A is token-only, no exceptions" spelled
  out in both places.
- The new decision doc exists, cites `gates/flows.py:131-132` by line, and
  quotes both real rsb comment bodies verbatim alongside the demonstration
  that neither satisfies strict equality.
- The doc names issue #224 as a related-but-separate, code-side item.
- No new approval syntax appears anywhere in the diff beyond the existing
  `APPROVE issue-<n>/<role>` token.
- A reviewer reading `run.md` step 6 alone, with no other context, can state
  correctly what to post when they want to approve with conditions attached.
