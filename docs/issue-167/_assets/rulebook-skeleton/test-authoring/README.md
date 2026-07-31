# test-authoring-rulebook

Rulebook for the `test-authoring` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-4 promotion and
generated as skeleton scaffolding by issue-167.

- **decides**: 테스트 코드 자체가 격리성·fixture 전략 면에서 좋은 설계인가
- **use_when**: 신규/기존 테스트 스위트를 설계·리뷰할 때
- **produces**: suite architecture note, fixture strategy, smell list (Meszaros catalog refs)
- **write_scope**: ['test/**']
- **hand-off**: 실제 실행 결과 관찰은 → execution-observation

## Install

```
claude plugin marketplace add tokenmaxxxer/test-authoring-rulebook
claude plugin install test-authoring
```

## Layout

- `test-authoring/.claude-plugin/plugin.json` — plugin manifest
- `test-authoring/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `test-authoring/hooks/directive.sh` — SessionStart role directive
- `test-authoring/hooks/record-fields-gate.sh` — this role's record required-field gate
- `test-authoring/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `test-authoring/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `test-authoring/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
