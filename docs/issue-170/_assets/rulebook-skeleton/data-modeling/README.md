# data-modeling-rulebook

Rulebook for the `data-modeling` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 데이터를 어떤 관계/스키마로 모델링할지
- **use_when**: 스키마 신설/변경이 걸릴 때
- **produces**: schema/ERD, migration plan, normalization rationale
- **write_scope**: ["src/**"] (migrations only)
- **hand-off**: 파이프라인 이동/변환이 걸리면 → data-engineering

## Install

```
claude plugin marketplace add tokenmaxxxer/data-modeling-rulebook
claude plugin install data-modeling
```

## Layout

- `data-modeling/.claude-plugin/plugin.json` — plugin manifest
- `data-modeling/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `data-modeling/hooks/directive.sh` — SessionStart role directive
- `data-modeling/hooks/record-fields-gate.sh` — this role's record required-field gate
- `data-modeling/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `data-modeling/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `data-modeling/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
