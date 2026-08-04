---
kind: decision
date: 2026-08-03
status: landed
subject: issue-227
---

# Conditional-approval relay — canonical two-comment recipe

## Decision

When a human's decision is approve-with-feedback in the same breath, the
canonical form is two separate comments on the **issue** thread (not the
PR), posted in order: comment A's body is exactly the token string
`APPROVE issue-<n>/<role>` and nothing else, ever; comment B, posted
immediately after, carries the feedback and points back at comment A
rather than repeating any part of the token. Token-first ordering means a
valid approval already stands the instant comment A lands; feedback
landing a moment later in comment B never puts that in question. No new
approval grammar is introduced — the token is unchanged from contract v3
s19's `APPROVE issue-<n>/<role>`.

Companion policy for a near-miss (token and prose mixed in one comment,
instead of the two-comment form): the session that meets it **warns** —
posts exactly one reply pointing at the canonical recipe and keeps
waiting, never treats the near-miss as approval, never repeats the reply
on the same comment.

## Why (adopted — two-comment sequence, not a looser matcher)

`docs/decisions/2026-07-29-permanently-closed-alternatives.md` already
closed the entire class of "parse the comment to decide approval intent"
after three separately-measured leaks, settling on exact whole-body string
equality specifically because "deciding whether two strings are equal is
not a language problem." Loosening `gates/flows.py:131-132`'s matcher —
even minimally, e.g. first-line-only matching — reopens that surface (a
comment could smuggle the token inside a quoted excerpt, a code fence, or
a reply-context blockquote and still "approve" something nobody meant to
approve). This decision fixes what gets posted, not what gets read.

**Empirical evidence (executed, not just inspected)**: `gates/flows.py::
_pr_approved()` (needle `f"APPROVE {subject}/{role}"`, `gates/flows.py:131`;
match `c["body"].strip() == needle and c["login"] in approvers`,
`gates/flows.py:132`) fed the two real `repo-status-board` comments
verbatim — rsb #23 (`"APPROVE issue-23/implementation\n\n조건부 승인 —
PR #24 리뷰 코멘트(2차 교차 검토 4건)를 phase 2에서 반영할 것."`) and rsb
#20 (`"APPROVE issue-20/finance-unit-economics\n(phase 2 반영 사항 —
승인자 피드백 2건: ① ... ② ...)"`) — both return **`False`**; a
token-only control returns `True`; a synthetic prose-before-token variant
also returns **`False`**. `spawn.py::approve_scope()` (needle
`f"APPROVE {subject}/scope"`, `spawn.py:917`), needle-isolated to the same
rsb shapes (suffix swapped from the real subject/role to the literal
`/scope` this function hardcodes — see "Related" below), raises
**`SystemExit`** and commits nothing for both rsb shapes and the
prose-before variant; only the token-only control reaches `rc=0` and
writes `scope-approved`. Both real gate functions in this repo reject
both real mixed comments outright. Whatever let phase 2 proceed in both
rsb cases was not either function in this repo — it was a
human/orchestrator judgment call or an out-of-tree check, which is
exactly the contract-vs-practice gap this issue closes. Full run detail:
`docs/issue-227/reports/implementation/survey.md`.

**Rejected alternative — a new composite token** (e.g. `APPROVE-WITH-
CHANGES issue-<n>/<role>`). Rejected per the issue's own constraint
against new approval grammar, and because it duplicates, with a second
textual convention, exactly what GitHub's own PR-review model already
expresses structurally via separate `state`/`body` fields (scout:
docs.github.com/en/rest/pulls/reviews) — a second plain comment achieves
the same separation with zero new syntax.

**Rejected alternative — rely on PR-review-Approve instead of the issue
comment.** GitHub's own structured channel, and `gates/flows.py`'s second
detection path already supports it (mirrored by Kubernetes Prow's
`/approve`/`/lgtm`/`/hold` as separate commands, per the same scout).
Rejected as the *default* because it is structurally unavailable in the
single-account setup this project actually runs — GitHub disallows
approving one's own PR review. It remains the documented alternative for
a hardened, agent-account-separated configuration only.

## Why (adopted — warn, not abort or log-only, for a non-canonical near-miss)

No existing code path reacts to a near-miss at all — `approve_scope()`
and `_pr_approved()` either match or silently reject. The two rsb
incidents share one actual failure: the human believed they had approved,
and nothing in the pipeline told them otherwise until phase 2 either
silently proceeded or silently stalled. Three candidates, compared on
whether they close that loop:

| Policy | What the session does | Pro | Con |
| --- | --- | --- | --- |
| Abort | treats the near-miss as fatal, stops the wait/session outright | zero ambiguity that nothing proceeded | a polling session has nothing in-flight to tear down — this just stops watching, indistinguishable from doing nothing, and gives the human no signal why |
| **Warn (chosen)** | keeps waiting, posts one reply pointing at the canonical recipe, never treats the near-miss as approval | closes the loop immediately — the human learns within the same turn instead of 18 minutes later (rsb #23) or never; costs one comment, no new matcher path | needs a cheap "does this look approval-shaped" heuristic (literal substring `APPROVE`) — a small judgment call outside the exact-match gate, bounded to only ever adding a clarifying reply, never approval |
| Log only | records the near-miss in the session's own record, says nothing back | cheapest, zero human-facing noise | does not fix the observed failure — a log entry nobody reads in the moment reproduces the same failure shape |

Warn is the only one that directly answers what went wrong in both real
incidents. It never grants approval on a near-miss — a companion signal
around the existing strict-match gate
(`docs/decisions/2026-07-29-permanently-closed-alternatives.md`'s "a
model must never decide its own authorization" still holds: the session
never decides the near-miss counts, it only tells the human it didn't).

## Related, not superseded: issue #224

`spawn.py:917`'s `approve_scope()` hardcodes the literal suffix `/scope`
rather than the role name — a code-side string mismatch — and issue
comment fetch has no `--paginate`, so a token past the 30th comment is
invisible to the gate. Both are issue #224's territory: code defects,
tracked and fixed there, not touched by this decision.
