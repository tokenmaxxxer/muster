# pr-communications-rulebook

Rulebook for the `pr-communications` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 메시지가 외부에 어떻게 읽힐지
- **use_when**: 외부 커뮤니케이션이 걸릴 때
- **produces**: communications plan, key message, risk/Q&A prep
- **write_scope**: []
- **hand-off**: 캠페인 성격 메시지는 → marketing

## Install

```
claude plugin marketplace add tokenmaxxxer/pr-communications-rulebook
claude plugin install pr-communications
```

## Layout

- `pr-communications/.claude-plugin/plugin.json` — plugin manifest
- `pr-communications/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `pr-communications/hooks/directive.sh` — SessionStart role directive
- `pr-communications/hooks/record-fields-gate.sh` — this role's record required-field gate
- `pr-communications/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `pr-communications/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `pr-communications/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
