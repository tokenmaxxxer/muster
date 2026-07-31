# security-threat-model-rulebook

Rulebook for the `security-threat-model` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 신뢰 경계의 위협 표면
- **use_when**: 스펙에 신뢰 경계·인증·민감데이터가 걸릴 때
- **produces**: STRIDE table, mitigation list per threat, residual risk note
- **write_scope**: []
- **hand-off**: 구현 단계 취약점 점검은 → secure-coding; 법적 노출이면 → legal-compliance

## Install

```
claude plugin marketplace add tokenmaxxxer/security-threat-model-rulebook
claude plugin install security-threat-model
```

## Layout

- `security-threat-model/.claude-plugin/plugin.json` — plugin manifest
- `security-threat-model/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `security-threat-model/hooks/directive.sh` — SessionStart role directive
- `security-threat-model/hooks/record-fields-gate.sh` — this role's record required-field gate
- `security-threat-model/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `security-threat-model/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `security-threat-model/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
