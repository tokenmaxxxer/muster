# legal-compliance-rulebook

Rulebook for the `legal-compliance` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 이 스펙/처리가 법·규제를 통과하는가
- **use_when**: 개인정보·라이선스·계약이 걸릴 때
- **produces**: compliance verdict, applicable regulation list, required mitigations
- **write_scope**: []
- **hand-off**: 전사 리스크 노출 규모 판단은 → risk-management

## Install

```
claude plugin marketplace add tokenmaxxxer/legal-compliance-rulebook
claude plugin install legal-compliance
```

## Layout

- `legal-compliance/.claude-plugin/plugin.json` — plugin manifest
- `legal-compliance/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `legal-compliance/hooks/directive.sh` — SessionStart role directive
- `legal-compliance/hooks/record-fields-gate.sh` — this role's record required-field gate
- `legal-compliance/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `legal-compliance/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `legal-compliance/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
