# Decision: phase is a property of the issue, not of (issue, role)

Subject: issue-312

## Context

`gates/ci.py`'s `_phase_from_approval` derived phase from an exact
`APPROVE issue-<n>/<role>` match keyed to the *delivering* PR's own
head-branch role (the per-role reading adopted in
`docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`,
without considering cross-role handoff). PR #307 (`issue-304/implementation`,
carrying `Closes #304`) is the delivery for issue #304, whose only
approval is `APPROVE issue-304/architecture` (given to the proposing
role, PR #305). No role-matched approval existed for `implementation`,
so the gate inferred phase1 and told PR #307 to remove the `Closes`
line that makes it a valid phase-2 delivery.

Both stated sources of contract v3 s19 (`protocol.md` and this plugin's
own start-of-session protocol text) describe the `APPROVE
issue-<n>/<role>` string and describe it opening phase 2 for *that
role's own PR* — neither permits nor forbids a second role's PR
delivering on the strength of an approval given to a different role's
proposal. Architect-proposes/implementer-delivers is exactly the
role-handoff shape this plugin's own directives describe as normal.

## Decision

Phase is a property of the **issue**, not of the (issue, role) pair.
One qualifying approval event anywhere on the issue — an issue-level
`APPROVE issue-<n>/<any role>` comment from an `approvers.md` login, or
(unchanged) a PR review Approve on *this* PR from a differing
approvers.md login — puts the whole issue in phase 2 for every role's
delivery PR against it.

The per-role PR-review-Approve path is kept exactly as-is (issue #271):
reviewing *this* PR already scopes the approval to whatever role opened
it, so no cross-role ambiguity exists there. Only the issue-comment path
changes, from "role must match this PR's role" to "role may be any role
recorded on the issue" — the issue-comment path is the one that
predates the delivering PR and is exactly where a proposing role's
approval and a delivering role's PR can legitimately diverge.

This decision **supersedes**
`docs/issue-271/decisions/2026-08-04-phase-signal-and-surface-coverage-mechanism.md`'s
per-role reading of the issue-comment path — that decision did not
consider cross-role handoff.

## Alternatives considered

**Keep phase per-(issue,role), fix only the refusal message.** Rejected:
this makes the #304/#307 handoff — happening right now, unmodified, on
two open PRs — permanently illegal. `implementation` would need its own
`APPROVE issue-304/implementation` comment, which cannot exist before
`implementation` has opened a phase-1 PR of its own, which the handoff
model does not require it to do. Fixing only the message would leave the
refusal accurate but the block itself wrong.

**Derive phase from `gates/flows.py`'s per-role `loop_state`.** Rejected:
that path is display-only and carries no approver check — folding it
into the merge-blocking gate would let an unapproved role's own
`loop_state` transition open phase 2 for that role, a fail-open
regression strictly worse than today's default.

## Consequences

- `gates/ci.py::_phase_from_approval` now unions all `approved roles on
  the issue` with the PR-review-Approve signal; any non-empty union is
  phase2.
- A refusal that fires from the phase1-mismatch branch (closing keyword
  present while phase is genuinely phase1) now names the role searched
  for and the set of roles found approved on the issue, instead of
  stating the phase1 inference as an unexplained premise.
- Not addressed by this decision: how phase should be judged for a PR
  that took the contract v3 s19 pure-bugfix skip path, where no
  phase-1 proposal — and therefore no `APPROVE issue-<n>/<role>`
  comment — can structurally exist (observed live on issue #313/PR
  #317, reported as conditional-approval feedback on this issue after
  the APPROVE token). That is a distinct defect: this decision's
  "any role approved on the issue" test still returns phase1 (empty
  approval set) for a bugfix-skip issue, which is the current, unfixed
  behavior for that shape. See the phase-2 implementation record's
  "Rationale for deviations" section for why it is out of this
  proposal's approved write set rather than folded in here.
