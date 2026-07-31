# localization-rulebook

Rulebook for the `localization` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 다른 로케일에서도 산출물이 성립하는가
- **use_when**: i18n 대상 표면이 걸릴 때
- **produces**: locale-fitness verdict per target locale, string-external issue list
- **write_scope**: []
- **hand-off**: 카피 원문 자체를 다시 써야 하면 → content-design

## Install

```
claude plugin marketplace add tokenmaxxxer/localization-rulebook
claude plugin install localization
```

## Layout

- `localization/.claude-plugin/plugin.json` — plugin manifest
- `localization/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `localization/hooks/directive.sh` — SessionStart role directive
- `localization/hooks/record-fields-gate.sh` — this role's record required-field gate
- `localization/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `localization/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `localization/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
