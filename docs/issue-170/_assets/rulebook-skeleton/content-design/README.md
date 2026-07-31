# content-design-rulebook

Rulebook for the `content-design` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 문구가 사용자의 실제 결정을 돕는가
- **use_when**: 플로우에 새 카피/마이크로카피가 걸릴 때
- **produces**: copy draft, rationale per string, A/B alternative (if applicable)
- **write_scope**: []
- **hand-off**: 화면/플로우 구조 자체가 바뀌어야 하면 → interaction-design

## Install

```
claude plugin marketplace add tokenmaxxxer/content-design-rulebook
claude plugin install content-design
```

## Layout

- `content-design/.claude-plugin/plugin.json` — plugin manifest
- `content-design/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `content-design/hooks/directive.sh` — SessionStart role directive
- `content-design/hooks/record-fields-gate.sh` — this role's record required-field gate
- `content-design/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `content-design/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `content-design/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
