# Record-file existence, not `loop_state` value, as phase-2 closing evidence

## Decision

`ci.py::_phase2_record_evidence` accepts a phase-2 delivery PR whose
`docs/issue-<n>/reports/<role>.md` exists and carries a non-empty
`loop_state` frontmatter field as alternate evidence of closing intent,
substituting for a missing `Closes #<n>` in the PR body. It checks
**presence** of the field, never a specific **value**.

## Why not gate on a specific `loop_state` value

`roles/implementation.json` declares the enum
`scope-proposed/scope-approved/in-progress/landed`. The real value observed
on #337's record is `phase-2-complete` — not in that enum. This mismatch is
invisible to CI today because the required check runs with
`--closes-only`, which skips `gates.record_enums` entirely (see
`gates/ci.py::check`'s docstring). Gating the closing-intent check on a
specific string would therefore either silently fail #337-shaped records
(the actual case the six blocked PRs need this to unblock) or require
fixing the enum drift as a prerequisite — out of this issue's scope
(tracked separately at #147).

Presence-of-field is the predicate that is verifiably true today. A future
session tightening this to a specific enum value must first close #147
(fix the enum drift so the declared and real values agree) — otherwise
that tightening re-breaks the exact PRs this fix exists to unblock.

## Scope

`gates/ci.py::_phase2_record_evidence`, called from `check()`'s phase2
branch. Out of scope: `roles/implementation.json`'s `record_fields` enum
itself (#147).
