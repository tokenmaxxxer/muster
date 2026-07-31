# refactoring-legacy-rulebook

Rulebook for the `refactoring-legacy` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-4 promotion and
generated as skeleton scaffolding by issue-167.

- **decides**: 기존 코드의 관찰 가능한 동작을 바꾸지 않고 안전하게 재구조화할 수 있는가
- **use_when**: 레거시/기존 코드에 손을 대야 할 때
- **produces**: refactoring plan, characterization tests, before/after behavior-equivalence note
- **write_scope**: ['src/**', 'test/**']
- **hand-off**: 신규 기능 구현이 섞이면 그 부분은 → implementation

## Install

```
claude plugin marketplace add tokenmaxxxer/refactoring-legacy-rulebook
claude plugin install refactoring-legacy
```

## Layout

- `refactoring-legacy/.claude-plugin/plugin.json` — plugin manifest
- `refactoring-legacy/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `refactoring-legacy/hooks/directive.sh` — SessionStart role directive
- `refactoring-legacy/hooks/record-fields-gate.sh` — this role's record required-field gate
- `refactoring-legacy/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `refactoring-legacy/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `refactoring-legacy/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
