# knowledge-management-rulebook

Rulebook for the `knowledge-management` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-4 promotion and
generated as skeleton scaffolding by issue-167.

- **decides**: 개별 이슈의 교훈이 조직 차원에서 재사용 가능한 형태로 축적·색인되는가
- **use_when**: 여러 이슈의 회고가 쌓여 지식 큐레이션이 필요할 때
- **produces**: curated pattern-library entry, cross-issue index, supersession note (if replacing an older pattern)
- **write_scope**: ['docs/patterns/**']
- **hand-off**: 단일 이슈 회고 자체는 → issue-retrospective

## Install

```
claude plugin marketplace add tokenmaxxxer/knowledge-management-rulebook
claude plugin install knowledge-management
```

## Layout

- `knowledge-management/.claude-plugin/plugin.json` — plugin manifest
- `knowledge-management/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `knowledge-management/hooks/directive.sh` — SessionStart role directive
- `knowledge-management/hooks/record-fields-gate.sh` — this role's record required-field gate
- `knowledge-management/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `knowledge-management/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `knowledge-management/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
