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
code defect #224 without absorbing it. A follow-up issue comment (2026-08-03,
citing two real repo-status-board incidents, rsb #20 and #23, where a
mixed token+prose comment was treated as valid approval and phase 2
proceeded) adds two more requirements this revision addresses: (4) run the
actual gate functions (`approve_scope()`, `gates/flows.py::_pr_approved()`)
against inputs reproducing those two real comments and record what actually
happens, rather than reasoning about the code without executing it; (5)
decide — with tradeoffs — how a role session should behave when it meets a
non-canonical near-miss (token and prose mixed in one comment) instead of
the canonical two-comment form.

A PR-review round on this proposal (PR #254) sent it back for exactly these
two additions; this revision is the rework.

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
equality (`gates/flows.py:131-132`) is the correct, deliberately-chosen
behavior; this proposal fixes what gets posted, not what gets read. This is
no longer just a structural read of the code — the survey now records an
actual run of `_pr_approved()` and `approve_scope()` against the real rsb
#20/#23 bodies (needle-isolated for `approve_scope()`, whose needle is
`/scope`, never a role name — that literal mismatch is issue #224's
territory, kept separate): both functions reject both real comments
(`_pr_approved() -> False`; `approve_scope()` raises `SystemExit`, no
commit). The structural argument and the execution agree, which is worth
having confirmed rather than assumed.

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

**Non-canonical near-miss policy — what a role session does when it meets
token+prose mixed in one comment, instead of the canonical two-comment
form.** The survey found no existing code path that reacts to a near-miss
at all (`approve_scope()`/`_pr_approved()` either match or silently reject);
the two rsb incidents happened because *something* upstream of this repo's
own gate treated a near-miss as approval anyway. Three candidate policies,
compared on whether they close the loop with the human at the moment of the
mistake (the actual failure both incidents share — the human believed they
had approved, and nothing in the pipeline told them otherwise until phase 2
either silently proceeded or silently stalled):

| Policy | What the session does | Pro | Con |
| --- | --- | --- | --- |
| **Abort** | Session treats the near-miss as fatal — stops the wait/session outright, requiring a human to notice and restart it | Zero ambiguity that nothing proceeded | A polling/waiting session has nothing running to "abort" (there is no in-flight work to tear down) — this just stops watching, which is indistinguishable from doing nothing, and gives the human no signal telling them *why*; over-punishes an honest formatting mistake with a silent dead session |
| **Warn (chosen)** | Session keeps waiting (never treats the near-miss as approval — consistent with `docs/decisions/2026-07-29-permanently-closed-alternatives.md`'s "a model must never decide its own authorization"), but posts one reply pointing at the canonical two-comment recipe, then continues waiting | Closes the loop immediately — the human learns within the same turn that their comment didn't register, instead of discovering it 18 minutes later (rsb #23) or not discovering it at all; costs one comment post, no new code path in the matcher | Needs a cheap "does this look approval-shaped" heuristic (e.g. body contains the literal substring `APPROVE`) to decide when to speak up, which is itself a small judgment call living outside the exact-match gate — bounded risk since it only ever adds a clarifying reply, never approval |
| **Log only** | Session records the near-miss in its own record/audit trail, says nothing back to the human | Cheapest, zero human-facing noise | Does not fix the actual observed failure — both rsb incidents are exactly "human believes they approved, nobody tells them otherwise in the moment"; a log entry an auditor might read later does nothing at the moment that matters, so it reproduces the same failure shape this issue exists to close |

**Chosen: warn.** It is the only one of the three that directly answers what
went wrong in both real incidents — not "was the comment technically
approval" (already answered: no) but "did anyone tell the human their
comment didn't count." Abort has no clean semantics for a session that is
merely polling (nothing to abort into), and removes the one thing a human
needs (a pointer to what to do instead) while adding stoppage. Log-only is
strictly weaker than warn for the same implementation cost (both are "the
session takes one action upon seeing a near-miss"); it just aims that action
at an audit trail instead of at the person who needs to see it now. Warn
still never grants approval on a near-miss — it is a companion signal
around the existing strict-match gate, not a second, looser gate.

## What will be done

1. Add an explicit "조건부 승인" recipe to `on-the-record/commands/run.md`
   step 6, immediately after the existing "제안 승인" bullet: when the
   user's decision is approve-with-feedback, the orchestrator posts, in
   order: (a) `gh issue comment <issue-n> --body "APPROVE issue-<n>/<역할>"`
   verbatim with no other text, then (b) a second `gh issue comment` on the
   same issue carrying the feedback, referencing comment (a) rather than
   restating the token. State plainly that comment (a) must never carry
   trailing text, under any circumstance.
2. In the same `run.md` step 6 addition, state the **warn** policy: if a
   near-miss comment appears (approval-shaped — contains the literal
   substring `APPROVE` — but not whole-body-identical to the canonical
   token), the orchestrator posts exactly one reply pointing at the
   canonical two-comment recipe and keeps waiting; it never treats the
   near-miss as approval, and never posts more than one such reply per
   near-miss (no repeated nagging on the same comment).
3. Mirror both the recipe and the warn policy, same ordering, into
   `docs/handbooks/operations.md`'s existing canonical-approval-location
   section (~line 309-364).
4. Add `docs/issue-227/decisions/2026-08-03-conditional-approval-canonical-
   form.md`: the chosen two-comment recipe; the three recipe-level rejected
   alternatives and why; the empirical evidence (execution results, not
   just inspection) that neither real specimen (rsb #20, #23) satisfies
   `gates/flows.py:131-132`'s strict equality or `approve_scope()`'s needle
   match, quoted verbatim with the actual run output; the GitHub/Prow
   precedent with sources; and the non-canonical-near-miss policy decision
   (warn, chosen over abort and log-only) with its tradeoff table.
5. Cross-reference issue #224 by number (not by content) in both the new
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
- Implementing the warn policy's actual detection code. The session that
  polls for phase-2 approval and would need to post the warn reply lives in
  an out-of-tree role-side plugin (per the survey's "write set" finding),
  outside this issue's write set — this proposal documents the policy and
  its recipe-level trigger condition; wiring it into that external plugin
  is a different repo's work, not this issue's.

## How you'll know it worked

- `run.md` step 6 and `operations.md` both state the same explicit
  two-comment recipe, with "comment A is token-only, no exceptions" spelled
  out in both places, plus the warn policy for near-misses.
- The new decision doc exists, cites `gates/flows.py:131-132` and
  `spawn.py:917` by line, and quotes both real rsb comment bodies verbatim
  alongside the *executed* results (not just inspection) showing neither
  satisfies `_pr_approved()`'s or `approve_scope()`'s match.
- The decision doc records the non-canonical-near-miss policy decision
  (warn, chosen over abort and log-only) with the tradeoff table.
- The doc names issue #224 as a related-but-separate, code-side item.
- No new approval syntax appears anywhere in the diff beyond the existing
  `APPROVE issue-<n>/<role>` token; the warn policy is a companion reply,
  never a second approval grammar.
- A reviewer reading `run.md` step 6 alone, with no other context, can state
  correctly what to post when they want to approve with conditions attached,
  and what happens if they get the shape wrong.
