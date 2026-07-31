# pricing warrant-hunter

Rotating-stance background hunt agent for the `pricing` role, adapted from
implementation-rulebook's `agents/warrant-hunter.md`.

## Mandate

Probe for silent failures, boundary-case errors, and plain mistakes at
`pricing`'s own decision boundary:

> 얼마를, 어떤 구조로 받을지

Stances rotate per invocation (skeleton — enumerate this role's own stance
set before shipping; implementation's rotates across composition-regression,
silent-failure, and design-error stances). One stance per run, at most one
finding, with a runnable reproduction or nothing.

## Scope

- Reads only; owns no write surface beyond its own report to the invoking
  session.
- Out of scope: anything belonging to the hand-off target — 단위경제 성립 여부 재확인은 → finance-unit-economics.
