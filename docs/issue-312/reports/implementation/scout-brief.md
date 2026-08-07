---
role: implementation
subject: issue-312
loop_state: scout-brief
---

# Scout brief — closes-gate phase model (issue #312)

Non-product infra deliverable (an internal CI gate's phase predicate): no
external exemplar product applies, so the "field" scouted is this
repo's own prior art on the same mechanism — the closest available
substitute for a category of best-in-class systems, per the scout
directive's non-product framing. One angle, run against the survey's gap
(§2-3): does any other place in this codebase already resolve
issue-vs-role phase granularity, and does the contract text settle it?

## Findings

- `docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`
  adopted the `APPROVE issue-<n>/<role>` predicate deliberately, but its
  Rationale never treats "which role" as a design axis — it inherited
  the `<role>` slot from the approval-string's contract wording without
  considering a second role delivering against the same issue.
  Must-be: an approval signal must be tied to *a* role string (the
  contract requires the literal substring), but nothing in this decision
  commits to *whose* role.
- `gates/flows.py:318-326` (mission board) computes phase per role from
  that role's own `loop_state` — the one other place in the codebase
  with an opinion on phase granularity, and it is per-(issue,role), for
  a different purpose (board display, not a merge-blocking gate).
- `protocol.md:239-246` and this session's own start-of-session protocol
  text state the approval mechanism ("APPROVE issue-<n>/<role>") but
  only ever describe it opening phase 2 for *that role's own* PR — never
  a second PR by a different role riding on the first approval.

## Gap line

What contract v3 s19 covers: the approval *string shape* and the two
detection paths (issue comment / PR review). What it does not cover: a
second role's PR delivering against an issue whose only approval names a
different role. This is the gap the proposal's Rationale has to close —
not by inventing a reading of the contract it doesn't state, but by
naming the gap and picking a default for it.

## Adopt / skip

- Adopt: keep the approval-event predicate itself (issue #271's choice)
  — no defect was found there; closing-keyword-as-phase-signal is a
  strictly worse idea per #271's own rejected-alternatives list, still
  valid.
- Skip: extending role-matching to also examine other roles' loop_state
  (`gates/flows.py`) as a phase source for `ci.py` — that path is
  display-only, unauthenticated (no approver check), and mixing it into
  the merge-blocking gate would let an unapproved role's `loop_state`
  transition alone open phase 2, a strictly worse fail-open shape than
  today's fail-closed default.

Sources: internal repo files only (no web search — infra-internal
question, not a product-shaped scout target): `protocol.md`,
`gates/ci.py`, `gates/flows.py`, `gates/test_closes_gate_ci.py`,
`docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`.

Stages: 1 (internal-only sweep; no deepening round needed — the gap was
immediately decision-relevant and a second round would not change it).
