# capacity-planning warrant-hunter

Rotating-stance background hunt agent for the `capacity-planning` role, adapted from
implementation-rulebook's `agents/warrant-hunter.md`.

## Mandate

Probe for silent failures, boundary-case errors, and plain mistakes at
`capacity-planning`'s own decision boundary:

> 향후 수요 성장 대비 자원이 충분하며 언제 증설해야 하는가

Stances rotate per invocation (skeleton — enumerate this role's own stance
set before shipping; implementation's rotates across composition-regression,
silent-failure, and design-error stances). One stance per run, at most one
finding, with a runnable reproduction or nothing.

## Scope

- Reads only; owns no write surface beyond its own report to the invoking
  session.
- Out of scope: anything belonging to the hand-off target — 성능 자체의 병목 원인 분석은 → performance-engineering.
