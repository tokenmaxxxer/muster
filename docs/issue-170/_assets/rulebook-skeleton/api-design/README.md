# api-design-rulebook

Rulebook for the `api-design` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 서비스 경계의 인터페이스 형태
- **use_when**: 여러 소비자가 걸리는 API 표면을 설계/변경할 때
- **produces**: interface spec (endpoints/schema/versioning), lifecycle/deprecation plan
- **write_scope**: []
- **hand-off**: 컴포넌트 경계 자체가 바뀌면 → architecture; 스키마 신설/변경이면 → data-modeling

## Install

```
claude plugin marketplace add tokenmaxxxer/api-design-rulebook
claude plugin install api-design
```

## Layout

- `api-design/.claude-plugin/plugin.json` — plugin manifest
- `api-design/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `api-design/hooks/directive.sh` — SessionStart role directive
- `api-design/hooks/record-fields-gate.sh` — this role's record required-field gate
- `api-design/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `api-design/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `api-design/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
