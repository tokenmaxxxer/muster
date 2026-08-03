# Scout brief — issue #222

Mode: parallel (2 WebSearch calls in one turn), 1 stage — stopped at judge
point 1 (saturation: a second round would not change either build
decision below; this is an internal tooling hygiene fix, not a
product-facing surface, so the field to compare against is narrow).

## What was scouted

Two decisions the survey left open needed an external sanity check:
(1) item 2 — wire `record_fulfils_diff` into `ci.check()` vs. delete it
alongside the dead router scaffolding; (2) item 3 — whether a terminal
"closed" state should override an in-progress-shaped `loop_state` when
deriving `flows[].stage`, rather than being just another bucket in the
same map.

## Findings

- **Must-be: a small canonical status-category model with one
  non-transitioning terminal bucket.** Jira's status categories are
  Todo/In Progress/Done, and only a issue's terminal `Closed` status has
  no outgoing transitions. → adopt: `_stage_for`'s new `closed` value
  should short-circuit ahead of the `loop_state` map, not compete with it
  as just another dict entry — this matches how Jira/Linear model a
  closed item as strictly terminal regardless of what state it was in
  before closing.
- **Must-be: a gate that only exists in a dead dispatch path is
  equivalent to no gate.** No source distinguishes "registered" from
  "wired" — this is this repo's own vocabulary (`ALL` vs `ci.check()`),
  confirmed structurally by the survey (zero callers of `gates.check(names,
  ...)` anywhere, including tests) rather than from an external source.
- **Assumption (no source, stated as such):** CI/CD dashboards generally
  treat "gate defined but not invoked in the actual check path" as a
  wiring bug, not a design choice — general search results didn't
  surface a citable, specific source for this beyond generic CI
  monitoring best-practice pages, which mostly discuss build metrics
  dashboards, not gate-dispatch-list correctness. Not used as a cited
  finding; the survey's own reproduction (`ci.check()` returns `[]` on a
  false fulfils claim) carries the weight here instead.

## Adopt / skip

- Adopt: closed-overrides-everything terminal bucket (Jira/Linear
  pattern) for item 3's `_stage_for`.
- Skip: inventing a richer status-category taxonomy (e.g. Jira's
  per-project custom workflow categories) — this repo's `flows-schema.md`
  already froze exactly 5 values; the scouted pattern only confirms
  *how* `closed` should behave among them, not a reason to add more.

## Segment fit

Not a product surface — this is internal orchestration tooling scouted
against project-management/CI status-modeling conventions as the nearest
comparable kind, per the non-product scouting rule. Gap line: this
repo's `flows.py` already has the "raw fallback for unmapped states"
must-be (`stage_derived: false`); what it was missing is the
terminal-override rule for `closed`, which the scout confirms is the
standard shape.

Sources:
- https://www.herocoders.com/blog/understanding-jira-issue-statuses
- https://community.atlassian.com/forums/App-Central-articles/Understanding-Jira-Statuses/ba-p/3122343
