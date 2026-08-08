---
kind: survey
subject: issue-522
---

# Current-state survey — issue #522

## Write set (confirmed)

- `roles/issue-retrospective.json` — `record_fields` is `{}`, no `loop_state` key.
- `roles/release-engineering.json` — `record_fields` is `{}`, no `loop_state` key.

No other file needs to change. Confirmed by reading both files directly
(`cat roles/issue-retrospective.json`, `cat roles/release-engineering.json`):
both carry `"record_fields": {}` and no other field differs from the
pattern used by roles that already have `loop_state`.

## Existing pattern in `roles/*.json`

Sampled roles that already carry `record_fields.loop_state`:

- `roles/conformance-review.json`: `["reported"]` — single terminal state,
  matches its use_when ("보고" 산출물, no round structure).
- `roles/defect-verification.json`: `["cleared"]` — single terminal state.
- `roles/incident-response.json`: `["scope-proposed", "scope-approved",
  "in-progress", "landed"]` — multi-state progress→terminal, matches its
  multi-step postmortem workflow.

So the shape varies per role: it is drawn from each role's own rulebook,
not a fixed enum shared across all roles.

## Rulebook methodology for the two target roles

Both target roles' rulebooks are checked out locally at
`/home/jwjung/tokenmaxxxer/rulebooks/<role>-rulebook/README.md`, under
"## Record vocabulary" — this is the authoritative source for each role's
`loop_state`, not something to invent.

### `issue-retrospective`

`issue-retrospective-rulebook/README.md:98`:

> `loop_state`: `idle, retrospecting, candidate-round-done, round-done`
> (terminal: `round-done`, set only after the round-end value gates run —
> contract s18).

Four states, one terminal (`round-done`). Consistent with
`roles/issue-retrospective.json`'s `produces`: "timeline, lessons list,
one-line advisory" — a round-based retro workflow with value gates before
the record closes.

### `release-engineering`

`release-engineering-rulebook/README.md:72`:

> `loop_state`: `idle, readiness, rollout, steady, incident` (settled:
> `steady`/`idle`).

Five states, two settled/terminal (`steady`, `idle`). Consistent with
`roles/release-engineering.json`'s `produces`: "rollout checklist,
rollback plan, go/no-go verdict" — a release lifecycle that can settle
back to idle or reach steady-state post-rollout, or divert to `incident`.

## Alternative considered

Inventing a minimal two-state `[in-progress, done]` pair for both roles,
matching only the issue's bare acceptance check (`>=2 states`). Rejected:
the issue text itself says "check the rulebook before choosing states, do
not invent," and both rulebooks already define an exact, named
`loop_state` vocabulary — using anything else would silently diverge from
the rulebook that is the actual authority over the role's state machine.
