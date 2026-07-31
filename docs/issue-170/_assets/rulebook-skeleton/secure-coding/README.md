# secure-coding-rulebook

Rulebook for the `secure-coding` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 구현이 공격에 견디는가
- **use_when**: 인증/입력처리 코드 랜딩 후
- **produces**: ASVS checklist, pentest finding list w/ severity
- **write_scope**: []
- **hand-off**: 설계 단계 위협표면 재검토가 필요하면 → security-threat-model

## Install

```
claude plugin marketplace add tokenmaxxxer/secure-coding-rulebook
claude plugin install secure-coding
```

## Layout

- `secure-coding/.claude-plugin/plugin.json` — plugin manifest
- `secure-coding/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `secure-coding/hooks/directive.sh` — SessionStart role directive
- `secure-coding/hooks/record-fields-gate.sh` — this role's record required-field gate
- `secure-coding/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `secure-coding/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `secure-coding/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
