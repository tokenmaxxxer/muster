# growth-analytics-rulebook

Rulebook for the `growth-analytics` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 퍼널 병목과 실험 결과가 실제 개선인지
- **use_when**: 퍼널 분석 또는 A/B 실험 해석이 걸릴 때
- **produces**: funnel diagnosis, experiment trust verdict (SRM/pre-registration check)
- **write_scope**: []
- **hand-off**: 캠페인 메시지 변경이 필요하면 → marketing

## Install

```
claude plugin marketplace add tokenmaxxxer/growth-analytics-rulebook
claude plugin install growth-analytics
```

## Layout

- `growth-analytics/.claude-plugin/plugin.json` — plugin manifest
- `growth-analytics/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `growth-analytics/hooks/directive.sh` — SessionStart role directive
- `growth-analytics/hooks/record-fields-gate.sh` — this role's record required-field gate
- `growth-analytics/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `growth-analytics/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `growth-analytics/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
