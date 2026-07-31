# incident-response-rulebook

Rulebook for the `incident-response` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-4 promotion and
generated as skeleton scaffolding by issue-167.

- **decides**: 장애 후 무엇을 배웠고 재발을 무엇으로 막을 것인가
- **use_when**: 장애 종결 직후
- **produces**: timeline, blameless postmortem, action items w/ owner+deadline
- **write_scope**: ['docs/issue-<n>/postmortems/**']
- **hand-off**: 용량 부족이 원인이면 → capacity-planning; 계측 부재가 원인이면 → observability

## Install

```
claude plugin marketplace add tokenmaxxxer/incident-response-rulebook
claude plugin install incident-response
```

## Layout

- `incident-response/.claude-plugin/plugin.json` — plugin manifest
- `incident-response/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `incident-response/hooks/directive.sh` — SessionStart role directive
- `incident-response/hooks/record-fields-gate.sh` — this role's record required-field gate
- `incident-response/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `incident-response/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `incident-response/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
