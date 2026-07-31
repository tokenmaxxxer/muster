# finance-unit-economics-rulebook

Rulebook for the `finance-unit-economics` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 단위경제상 성립하는가
- **use_when**: 가격/비용 구조가 걸린 결정일 때
- **produces**: unit economics model (CAC/LTV/margin), sensitivity note
- **write_scope**: []
- **hand-off**: 실제 가격 숫자 결정은 → pricing

## Install

```
claude plugin marketplace add tokenmaxxxer/finance-unit-economics-rulebook
claude plugin install finance-unit-economics
```

## Layout

- `finance-unit-economics/.claude-plugin/plugin.json` — plugin manifest
- `finance-unit-economics/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `finance-unit-economics/hooks/directive.sh` — SessionStart role directive
- `finance-unit-economics/hooks/record-fields-gate.sh` — this role's record required-field gate
- `finance-unit-economics/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `finance-unit-economics/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `finance-unit-economics/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
