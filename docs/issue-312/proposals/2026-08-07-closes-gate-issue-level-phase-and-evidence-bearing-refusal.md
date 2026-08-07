---
status: proposed
files:
  - gates/ci.py
  - gates/test_closes_gate_ci.py
  - docs/issue-312/decisions/phase-is-an-issue-property.md
  - docs/issue-312/reports/implementation.md
---

# closes-gate: phase is a property of the issue; refusals report what they judged (issue #312)

## Request

`gates/ci.py`'s closes-gate ties phase to an exact `APPROVE
issue-<n>/<role>` match keyed off the *delivering* PR's own head-branch
role. When one role proposes (gets `APPROVE issue-<n>/architecture`) and
a different role delivers (`issue-<n>/implementation`, carrying `Closes
#<n>`), the gate finds no role-matched approval, calls the delivery PR
"phase1", and tells it to strip the `Closes` line that makes it a valid
phase-2 PR — the exact, currently-live shape of PR #307 against issue
#304. Separately, when the gate does refuse for a real missing-approval
case, it states its inferred conclusion ("phase-1 violation") without
saying what it searched for or what it found, so the refusal sends the
reader to fix the wrong thing.

## Constraints

- Contract v3 s19's `APPROVE issue-<n>/<role>` approval-string shape is
  not renegotiable here — it is stated in `protocol.md` and this
  session's own start-of-session protocol text, and issue #312 does not
  ask to change the string.
- The fix must not create a new fail-open path: an unapproved issue must
  still block phase-2 delivery.
- `_pr_approved` (`gates/flows.py:130`) is shared with the mission-board
  status path (`flows.py:318,342`) and is out of this issue's write set
  — any change stays inside `gates/ci.py`.

## Rationale

**Contract v3 s19 is silent on cross-role handoff, not opposed to it.**
The survey (`docs/issue-312/reports/implementation/survey.md` §3) read
both stated sources of the contract directly: both describe the
`APPROVE issue-<n>/<role>` string and both describe it opening phase 2
for *that role's own PR*. Neither source describes, permits, or forbids
a second role's PR delivering against the same issue on the strength of
an approval given to a different role's proposal. Architect-proposes/
implementer-delivers is exactly the role-handoff shape this plugin's own
name and directives describe as normal (`RECORD: ...contract v3 s19`
governs *how a role's own two phases open*, not *whether phase is
per-role at all*) — so treating the contract's silence as an implicit
"no" and requiring a second `APPROVE issue-304/implementation` comment
before implementation may deliver would mean the implementation role
redoing phase 1 for work an approver already licensed, contradicting the
handoff shape the contract elsewhere assumes exists.

**Considered and rejected: keep phase per-(issue,role), fix only the
message.** This is the alternative the current code and
`docs/issue-271/decisions/...` already embody, and it is a defensible
reading of the contract text taken in isolation. Rejected because it
makes the #304/#307 handoff — happening right now, unmodified, on two
open PRs — permanently illegal: implementation would need its own
`APPROVE issue-304/implementation` comment, which cannot exist before
implementation has opened a phase-1 PR of its own, which the handoff
model does not require it to do. Fixing only the message would leave the
refusal accurate but the block itself wrong — the acceptance criterion
("the gate does not report it as a phase-1 closing-keyword violation")
would still fail.

**Considered and rejected: derive phase from `gates/flows.py`'s
per-role `loop_state`.** The scout brief (§Skip) found this path is
display-only and carries no approver check — folding it into the
merge-blocking gate would let an unapproved role's own `loop_state`
transition open phase 2 for that role, a fail-open regression strictly
worse than today's default.

**Decision: phase is a property of the issue.** One qualifying approval
event anywhere on the issue — an issue-level `APPROVE issue-<n>/<any
role>` comment from an `approvers.md` login, or (unchanged) a PR review
Approve on *this* PR from a differing approvers.md login — puts the
whole issue in phase 2 for every role's delivery PR against it. The
per-role review-Approve path is kept exactly as-is (issue #271):
reviewing *this* PR already scopes the approval to whatever role opened
it, so no cross-role ambiguity exists there. Only the issue-comment path
changes from "role must match this PR's role" to "role may be any role
recorded on the issue" — because the issue-comment path is the one that
predates the delivering PR and is exactly where a proposing role's
approval and a delivering role's PR can legitimately diverge.

## What will be done

- `gates/ci.py` `_phase_from_approval`: instead of asking
  `flows._pr_approved` for one exact `APPROVE issue-<n>/<role>` needle,
  scan the issue's comments for `APPROVE issue-<n>/<any-role-token>`
  from an `approvers.md` login (regex over the existing comment list —
  no new fetch), independent of the branch's own role; keep the PR
  review Approve path as today (still checked against `pr_dict`,
  differing-account rule unchanged). Return `phase2` if either matches,
  else `phase1`, and also return (or make available to the caller) the
  evidence used: the role this PR searched under, and the distinct set
  of roles found approved on the issue (possibly empty).
- `gates/ci.py` `check()`'s phase-1 branch: when
  `_phase1_surface_mismatch` fires, append the evidence line to the
  refusal — which role/subject combination the gate looked for approval
  under and which approvals (role strings) exist on the issue, e.g. `이
  PR 의 role(implementation)에 대한 승인 코멘트를 못 찾았다 — 이슈
  #304 에 있는 승인: architecture` for a genuinely missing case, or (once
  the phase model changes) no refusal at all for the #304/#307 shape,
  since `architecture`'s approval now qualifies.
- `gates/test_closes_gate_ci.py`: replace
  `t_phase_from_approval_wrong_role_comment_is_phase1` (asserts the
  per-role reading this proposal reverses) with a test for the new
  issue-level reading; add the two acceptance tests verbatim from issue
  #312 — the #304/#307 configuration reproduction (issue with `APPROVE
  issue-<n>/<roleA>`, phase-2 PR on `issue-<n>/<roleB>` carrying `Closes
  #<n>`, asserting no phase-1 closing-keyword violation) and a refusal-
  text test asserting the message names the role searched for and the
  approvals present when genuinely unapproved.
- `docs/issue-312/decisions/phase-is-an-issue-property.md`: record this
  decision, its silence-in-contract finding, and that it supersedes the
  per-role reading `docs/issue-271/decisions/...` adopted without
  considering cross-role handoff.
- Live check (issue #312's third acceptance item): re-run
  `python3 gates/ci.py . --pr 307 --issue 304 --autodetect --closes-only`
  (or the equivalent explicit-flags form) against the real, unmodified
  PR #307 and report the result in the phase-2 record.

## Out of scope

- Changing the `APPROVE issue-<n>/<role>` string shape itself, or the
  PR-review differing-account rule.
- Touching `gates/flows.py`'s `_pr_approved` or the mission-board status
  path — `ci.py` builds its own issue-level scan rather than reusing
  `_pr_approved`, since `_pr_approved` is role-exact by contract and is
  shared code this issue's write set does not own.
- A same-role re-approval requirement (e.g. requiring both architecture
  and implementation to each get their own comment) — rejected above as
  contradicting the handoff shape the contract's silence permits.

## How you'll know it worked

- `python3 gates/test_closes_gate_ci.py` passes, including the two new
  acceptance tests (#304/#307 reproduction; refusal-text evidence).
- A live `gates/ci.py --pr 307 --issue 304 --autodetect --closes-only`
  run against real GitHub state (PR #307, #305 unmodified) either passes
  or fails with a message naming the evidence — not a phase-1
  closing-keyword misdiagnosis — and that transcript lands in the
  phase-2 implementation record.
