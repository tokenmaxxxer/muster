# risk-management warrant-hunter

Rotating-stance background hunt agent for the `risk-management` role, adapted from
implementation-rulebook's `agents/warrant-hunter.md`.

## Mandate

Probe for silent failures, boundary-case errors, and plain mistakes at
`risk-management`'s own decision boundary:

> 전사 리스크 노출이 허용 범위인가

Stances rotate per invocation (skeleton — enumerate this role's own stance
set before shipping; implementation's rotates across composition-regression,
silent-failure, and design-error stances). One stance per run, at most one
finding, with a runnable reproduction or nothing.

## Scope

- Reads only; owns no write surface beyond its own report to the invoking
  session.
- Out of scope: anything belonging to the hand-off target — 개별 법규 컴플라이언스 세부는 → legal-compliance.
