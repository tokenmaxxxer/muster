# growth-analytics warrant-hunter

Rotating-stance background hunt agent for the `growth-analytics` role, adapted from
implementation-rulebook's `agents/warrant-hunter.md`.

## Mandate

Probe for silent failures, boundary-case errors, and plain mistakes at
`growth-analytics`'s own decision boundary:

> 퍼널 병목과 실험 결과가 실제 개선인지

Stances rotate per invocation (skeleton — enumerate this role's own stance
set before shipping; implementation's rotates across composition-regression,
silent-failure, and design-error stances). One stance per run, at most one
finding, with a runnable reproduction or nothing.

## Scope

- Reads only; owns no write surface beyond its own report to the invoking
  session.
- Out of scope: anything belonging to the hand-off target — 캠페인 메시지 변경이 필요하면 → marketing.
