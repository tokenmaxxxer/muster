---
status: landed
files:
  - roles/issue-retrospective.json
  - roles/release-engineering.json
---

## Request

Follow-up B of #515: `roles/issue-retrospective.json` and
`roles/release-engineering.json` have an empty `record_fields` and lack
the `loop_state` key entirely. Add it, drawing the state list from each
role's own rulebook methodology rather than inventing one; change no
other contract field.

## Constraints

- No other `record_fields` or top-level contract field changes.
- States must come from the role's rulebook, not be invented ad hoc.
- Existing `gates/` pytest suite must keep passing.

## Rationale

Considered inventing a generic `[in-progress, done]` pair for both roles
to satisfy the issue's bare `>=2 states` acceptance check. Rejected: the
issue explicitly requires checking each rulebook's methodology first, and
both rulebooks (checked out locally under
`/home/jwjung/tokenmaxxxer/rulebooks/`) already define an exact, named
`loop_state` vocabulary in their README's "Record vocabulary" section —
using a generic pair instead would silently diverge from the vocabulary
each role's own rulebook already treats as authoritative, defeating the
point of a "consistent with the rulebook methodology" fix.

## What will be done

- `roles/issue-retrospective.json`: set
  `record_fields.loop_state` to
  `["idle", "retrospecting", "candidate-round-done", "round-done"]`,
  per `issue-retrospective-rulebook/README.md`'s Record vocabulary
  section (terminal: `round-done`).
- `roles/release-engineering.json`: set
  `record_fields.loop_state` to
  `["idle", "readiness", "rollout", "steady", "incident"]`,
  per `release-engineering-rulebook/README.md`'s Record vocabulary
  section (settled: `steady`/`idle`).
- No other key in either file changes.

## Out of scope

- Any other role's `roles/*.json`.
- Changes to the rulebooks themselves.
- Any design decision about what the states *should* be — this proposal
  only transcribes what each rulebook already documents.

## How you'll know it worked

- `python3 -c "import json;[json.load(open(f'roles/{r}.json'))['record_fields']['loop_state'] for r in ['issue-retrospective','release-engineering']]"` exits 0 and each list has `>= 2` states.
- Existing `gates/` pytest suite still exits 0.
- Diff of both files touches only the `record_fields` key.

Proposal: docs/issue-522/proposals/2026-08-09-loop-state-keys.md
