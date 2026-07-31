# market-analysis-rulebook

Rulebook for the `market-analysis` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 경쟁 구도에서 이 스펙이 서는가
- **use_when**: product 스펙 확정 후, 경쟁 구도가 걸린 결정일 때
- **produces**: five-forces summary, competitor list w/ evidence links, JTBD-landscape verdict
- **write_scope**: []
- **hand-off**: 가격 정책이 걸리면 → pricing; 포지셔닝 메시지가 걸리면 → marketing

## Install

```
claude plugin marketplace add tokenmaxxxer/market-analysis-rulebook
claude plugin install market-analysis
```

## Layout

- `market-analysis/.claude-plugin/plugin.json` — plugin manifest
- `market-analysis/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `market-analysis/hooks/directive.sh` — SessionStart role directive
- `market-analysis/hooks/record-fields-gate.sh` — this role's record required-field gate
- `market-analysis/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `market-analysis/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `market-analysis/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
