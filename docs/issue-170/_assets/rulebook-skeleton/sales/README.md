# sales-rulebook

Rulebook for the `sales` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 리드/기회를 어떻게 진행시킬지
- **use_when**: 영업 프로세스 설계가 걸릴 때
- **produces**: sales playbook, stage definitions, qualification criteria
- **write_scope**: []
- **hand-off**: 메시지/포지셔닝 자체는 → marketing

## Install

```
claude plugin marketplace add tokenmaxxxer/sales-rulebook
claude plugin install sales
```

## Layout

- `sales/.claude-plugin/plugin.json` — plugin manifest
- `sales/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `sales/hooks/directive.sh` — SessionStart role directive
- `sales/hooks/record-fields-gate.sh` — this role's record required-field gate
- `sales/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `sales/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `sales/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
