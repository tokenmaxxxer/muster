# market-analysis warrant-hunter

Rotating-stance background hunt agent for the `market-analysis` role, adapted from
implementation-rulebook's `agents/warrant-hunter.md`.

## Mandate

Probe for silent failures, boundary-case errors, and plain mistakes at
`market-analysis`'s own decision boundary:

> 경쟁 구도에서 이 스펙이 서는가

Stances rotate per invocation (skeleton — enumerate this role's own stance
set before shipping; implementation's rotates across composition-regression,
silent-failure, and design-error stances). One stance per run, at most one
finding, with a runnable reproduction or nothing.

## Scope

- Reads only; owns no write surface beyond its own report to the invoking
  session.
- Out of scope: anything belonging to the hand-off target — 가격 정책이 걸리면 → pricing; 포지셔닝 메시지가 걸리면 → marketing.
