# data-engineering-rulebook

Rulebook for the `data-engineering` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 파이프라인이 데이터를 안정적으로 이동·변환하는가
- **use_when**: 파이프라인 신설/변경이 걸릴 때
- **produces**: pipeline design, data-quality check list, failure-handling plan
- **write_scope**: []
- **hand-off**: 스키마 설계 자체는 → data-modeling

## Install

```
claude plugin marketplace add tokenmaxxxer/data-engineering-rulebook
claude plugin install data-engineering
```

## Layout

- `data-engineering/.claude-plugin/plugin.json` — plugin manifest
- `data-engineering/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `data-engineering/hooks/directive.sh` — SessionStart role directive
- `data-engineering/hooks/record-fields-gate.sh` — this role's record required-field gate
- `data-engineering/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `data-engineering/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `data-engineering/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
