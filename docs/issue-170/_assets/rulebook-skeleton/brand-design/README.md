# brand-design-rulebook

Rulebook for the `brand-design` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 브랜드 정체성이 시각적으로 일관되는가
- **use_when**: 브랜드 자산 신설/변경이 걸릴 때
- **produces**: brand guide entry, asset spec, consistency check vs existing guide
- **write_scope**: design-system source paths (TBD at execution)
- **hand-off**: 토큰 시스템화 구현은 → ux-engineering

## Install

```
claude plugin marketplace add tokenmaxxxer/brand-design-rulebook
claude plugin install brand-design
```

## Layout

- `brand-design/.claude-plugin/plugin.json` — plugin manifest
- `brand-design/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `brand-design/hooks/directive.sh` — SessionStart role directive
- `brand-design/hooks/record-fields-gate.sh` — this role's record required-field gate
- `brand-design/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `brand-design/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `brand-design/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
