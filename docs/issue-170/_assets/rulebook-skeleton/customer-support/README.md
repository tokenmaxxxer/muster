# customer-support-rulebook

Rulebook for the `customer-support` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 문의를 어떤 우선순위/SLA로 처리할지
- **use_when**: CS 플로우/SLA 설계가 걸릴 때
- **produces**: support playbook, SLA table, escalation path
- **write_scope**: []
- **hand-off**: 반복 문의가 제품 결함이면 → product-discovery

## Install

```
claude plugin marketplace add tokenmaxxxer/customer-support-rulebook
claude plugin install customer-support
```

## Layout

- `customer-support/.claude-plugin/plugin.json` — plugin manifest
- `customer-support/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `customer-support/hooks/directive.sh` — SessionStart role directive
- `customer-support/hooks/record-fields-gate.sh` — this role's record required-field gate
- `customer-support/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `customer-support/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `customer-support/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
