# marketing-rulebook

Rulebook for the `marketing` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 어떤 메시지로 어떤 채널에 도달할지
- **use_when**: 캠페인/포지셔닝이 걸릴 때
- **produces**: messaging doc, channel plan, target segment
- **write_scope**: []
- **hand-off**: 퍼널 성과 해석은 → growth-analytics

## Install

```
claude plugin marketplace add tokenmaxxxer/marketing-rulebook
claude plugin install marketing
```

## Layout

- `marketing/.claude-plugin/plugin.json` — plugin manifest
- `marketing/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `marketing/hooks/directive.sh` — SessionStart role directive
- `marketing/hooks/record-fields-gate.sh` — this role's record required-field gate
- `marketing/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `marketing/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `marketing/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
