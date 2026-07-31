# risk-management-rulebook

Rulebook for the `risk-management` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 전사 리스크 노출이 허용 범위인가
- **use_when**: 재무/운영/전략 리스크가 걸릴 때 (feasibility보다 넓은 범위)
- **produces**: ERM verdict, risk register entry, mitigation owner
- **write_scope**: []
- **hand-off**: 개별 법규 컴플라이언스 세부는 → legal-compliance

## Install

```
claude plugin marketplace add tokenmaxxxer/risk-management-rulebook
claude plugin install risk-management
```

## Layout

- `risk-management/.claude-plugin/plugin.json` — plugin manifest
- `risk-management/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `risk-management/hooks/directive.sh` — SessionStart role directive
- `risk-management/hooks/record-fields-gate.sh` — this role's record required-field gate
- `risk-management/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `risk-management/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `risk-management/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
