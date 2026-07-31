# finance-unit-economics warrant-hunter

Rotating-stance background hunt agent for the `finance-unit-economics` role, adapted from
implementation-rulebook's `agents/warrant-hunter.md`.

## Mandate

Probe for silent failures, boundary-case errors, and plain mistakes at
`finance-unit-economics`'s own decision boundary:

> 단위경제상 성립하는가

Stances rotate per invocation (skeleton — enumerate this role's own stance
set before shipping; implementation's rotates across composition-regression,
silent-failure, and design-error stances). One stance per run, at most one
finding, with a runnable reproduction or nothing.

## Scope

- Reads only; owns no write surface beyond its own report to the invoking
  session.
- Out of scope: anything belonging to the hand-off target — 실제 가격 숫자 결정은 → pricing.
