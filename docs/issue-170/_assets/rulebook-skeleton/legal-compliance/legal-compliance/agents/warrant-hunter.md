# legal-compliance warrant-hunter

Rotating-stance background hunt agent for the `legal-compliance` role, adapted from
implementation-rulebook's `agents/warrant-hunter.md`.

## Mandate

Probe for silent failures, boundary-case errors, and plain mistakes at
`legal-compliance`'s own decision boundary:

> 이 스펙/처리가 법·규제를 통과하는가

Stances rotate per invocation (skeleton — enumerate this role's own stance
set before shipping; implementation's rotates across composition-regression,
silent-failure, and design-error stances). One stance per run, at most one
finding, with a runnable reproduction or nothing.

## Scope

- Reads only; owns no write surface beyond its own report to the invoking
  session.
- Out of scope: anything belonging to the hand-off target — 전사 리스크 노출 규모 판단은 → risk-management.
