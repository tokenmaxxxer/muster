# localization warrant-hunter

Rotating-stance background hunt agent for the `localization` role, adapted from
implementation-rulebook's `agents/warrant-hunter.md`.

## Mandate

Probe for silent failures, boundary-case errors, and plain mistakes at
`localization`'s own decision boundary:

> 다른 로케일에서도 산출물이 성립하는가

Stances rotate per invocation (skeleton — enumerate this role's own stance
set before shipping; implementation's rotates across composition-regression,
silent-failure, and design-error stances). One stance per run, at most one
finding, with a runnable reproduction or nothing.

## Scope

- Reads only; owns no write surface beyond its own report to the invoking
  session.
- Out of scope: anything belonging to the hand-off target — 카피 원문 자체를 다시 써야 하면 → content-design.
