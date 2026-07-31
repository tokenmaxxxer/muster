# pricing-rulebook

Rulebook for the `pricing` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 얼마를, 어떤 구조로 받을지
- **use_when**: 신규 가격 정책이 걸릴 때
- **produces**: pricing verdict, tier structure, rationale vs alternatives considered
- **write_scope**: []
- **hand-off**: 단위경제 성립 여부 재확인은 → finance-unit-economics

## Install

```
claude plugin marketplace add tokenmaxxxer/pricing-rulebook
claude plugin install pricing
```

## Layout

- `pricing/.claude-plugin/plugin.json` — plugin manifest
- `pricing/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `pricing/hooks/directive.sh` — SessionStart role directive
- `pricing/hooks/record-fields-gate.sh` — this role's record required-field gate
- `pricing/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `pricing/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `pricing/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
