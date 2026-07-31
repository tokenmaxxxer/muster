# requirements-engineering-rulebook

Rulebook for the `requirements-engineering` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-4 promotion and
generated as skeleton scaffolding by issue-167.

- **decides**: 요구사항이 검증가능·일관·추적 가능하게 명세되었는가
- **use_when**: product 가설이 확정되어 정식 스펙으로 전환할 때
- **produces**: structured requirements doc, traceability matrix, ambiguity list resolved
- **write_scope**: []
- **hand-off**: 화면/플로우 설계는 → interaction-design

## Install

```
claude plugin marketplace add tokenmaxxxer/requirements-engineering-rulebook
claude plugin install requirements-engineering
```

## Layout

- `requirements-engineering/.claude-plugin/plugin.json` — plugin manifest
- `requirements-engineering/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `requirements-engineering/hooks/directive.sh` — SessionStart role directive
- `requirements-engineering/hooks/record-fields-gate.sh` — this role's record required-field gate
- `requirements-engineering/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `requirements-engineering/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `requirements-engineering/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
