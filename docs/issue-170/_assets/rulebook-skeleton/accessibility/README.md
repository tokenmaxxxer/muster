# accessibility-rulebook

Rulebook for the `accessibility` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 화면/토큰이 WCAG를 만족하는가
- **use_when**: 신규 인터랙션 패턴·색상 토큰 도입 시
- **produces**: WCAG success-criterion checklist w/ pass/fail per criterion
- **write_scope**: []
- **hand-off**: 카피 자체의 이해 가능성이면 → content-design

## Install

```
claude plugin marketplace add tokenmaxxxer/accessibility-rulebook
claude plugin install accessibility
```

## Layout

- `accessibility/.claude-plugin/plugin.json` — plugin manifest
- `accessibility/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `accessibility/hooks/directive.sh` — SessionStart role directive
- `accessibility/hooks/record-fields-gate.sh` — this role's record required-field gate
- `accessibility/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `accessibility/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `accessibility/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
