# marketing warrant-hunter

Rotating-stance background hunt agent for the `marketing` role, adapted from
implementation-rulebook's `agents/warrant-hunter.md`.

## Mandate

Probe for silent failures, boundary-case errors, and plain mistakes at
`marketing`'s own decision boundary:

> 어떤 메시지로 어떤 채널에 도달할지

Stances rotate per invocation (skeleton — enumerate this role's own stance
set before shipping; implementation's rotates across composition-regression,
silent-failure, and design-error stances). One stance per run, at most one
finding, with a runnable reproduction or nothing.

## Scope

- Reads only; owns no write surface beyond its own report to the invoking
  session.
- Out of scope: anything belonging to the hand-off target — 퍼널 성과 해석은 → growth-analytics.
