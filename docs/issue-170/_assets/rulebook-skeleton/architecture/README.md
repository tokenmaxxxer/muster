# architecture-rulebook

Rulebook for the `architecture` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 컴포넌트 경계·의존 방향
- **use_when**: 새 모듈 경계나 기존 경계 변경이 걸릴 때
- **produces**: ADR (context/decision/consequences), boundary diagram
- **write_scope**: ["docs/issue-<n>/decisions/**"]
- **hand-off**: 인터페이스 형태 세부는 → api-design; 성능 예산이 걸리면 → performance-engineering

## Install

```
claude plugin marketplace add tokenmaxxxer/architecture-rulebook
claude plugin install architecture
```

## Layout

- `architecture/.claude-plugin/plugin.json` — plugin manifest
- `architecture/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `architecture/hooks/directive.sh` — SessionStart role directive
- `architecture/hooks/record-fields-gate.sh` — this role's record required-field gate
- `architecture/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `architecture/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `architecture/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
