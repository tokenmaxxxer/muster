# partnerships-bd-rulebook

Rulebook for the `partnerships-bd` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 파트너십이 구조적으로 성립하는가
- **use_when**: 제휴/BD 딜 구조가 걸릴 때
- **produces**: deal structure verdict, term sheet outline
- **write_scope**: []
- **hand-off**: 법적 계약 검토는 → legal-compliance

## Install

```
claude plugin marketplace add tokenmaxxxer/partnerships-bd-rulebook
claude plugin install partnerships-bd
```

## Layout

- `partnerships-bd/.claude-plugin/plugin.json` — plugin manifest
- `partnerships-bd/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `partnerships-bd/hooks/directive.sh` — SessionStart role directive
- `partnerships-bd/hooks/record-fields-gate.sh` — this role's record required-field gate
- `partnerships-bd/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `partnerships-bd/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `partnerships-bd/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
