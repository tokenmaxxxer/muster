# ux-engineering-rulebook

Rulebook for the `ux-engineering` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 디자인 결정 → 토큰/규칙 시스템화
- **use_when**: 화면 스펙이 여러 개 쌓여 시스템화가 필요할 때
- **produces**: token set (name/value/usage), rule doc, migration note for existing screens
- **write_scope**: []
- **hand-off**: 브랜드 정체성 결정이 필요하면 → brand-design; 접근성 기준 미달이면 → accessibility

## Install

```
claude plugin marketplace add tokenmaxxxer/ux-engineering-rulebook
claude plugin install ux-engineering
```

## Layout

- `ux-engineering/.claude-plugin/plugin.json` — plugin manifest
- `ux-engineering/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `ux-engineering/hooks/directive.sh` — SessionStart role directive
- `ux-engineering/hooks/record-fields-gate.sh` — this role's record required-field gate
- `ux-engineering/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `ux-engineering/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `ux-engineering/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
