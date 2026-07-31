# capacity-planning-rulebook

Rulebook for the `capacity-planning` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-4 promotion and
generated as skeleton scaffolding by issue-167.

- **decides**: 향후 수요 성장 대비 자원이 충분하며 언제 증설해야 하는가
- **use_when**: 용량 예측/증설 시점 결정이 걸릴 때
- **produces**: capacity forecast, expansion trigger thresholds, cost note
- **write_scope**: []
- **hand-off**: 성능 자체의 병목 원인 분석은 → performance-engineering

## Install

```
claude plugin marketplace add tokenmaxxxer/capacity-planning-rulebook
claude plugin install capacity-planning
```

## Layout

- `capacity-planning/.claude-plugin/plugin.json` — plugin manifest
- `capacity-planning/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `capacity-planning/hooks/directive.sh` — SessionStart role directive
- `capacity-planning/hooks/record-fields-gate.sh` — this role's record required-field gate
- `capacity-planning/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `capacity-planning/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `capacity-planning/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
