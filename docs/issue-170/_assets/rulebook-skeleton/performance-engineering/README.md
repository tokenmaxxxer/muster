# performance-engineering-rulebook

Rulebook for the `performance-engineering` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 부하/지연 목표를 만족하는가
- **use_when**: 성능 예산이 걸린 설계/회귀일 때
- **produces**: performance budget, profiling evidence, bottleneck list
- **write_scope**: []
- **hand-off**: 용량 증설 타이밍이 걸리면 → capacity-planning

## Install

```
claude plugin marketplace add tokenmaxxxer/performance-engineering-rulebook
claude plugin install performance-engineering
```

## Layout

- `performance-engineering/.claude-plugin/plugin.json` — plugin manifest
- `performance-engineering/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `performance-engineering/hooks/directive.sh` — SessionStart role directive
- `performance-engineering/hooks/record-fields-gate.sh` — this role's record required-field gate
- `performance-engineering/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `performance-engineering/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `performance-engineering/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
