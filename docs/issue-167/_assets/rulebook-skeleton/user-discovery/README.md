# user-discovery-rulebook

Rulebook for the `user-discovery` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-4 promotion and
generated as skeleton scaffolding by issue-167.

- **decides**: 이 문제가 실제 사용자의 고통인가
- **use_when**: 가설 검증을 위해 사용자 인터뷰가 필요할 때
- **produces**: interview script, per-interview evidence log, pain-confirmed|not-confirmed verdict
- **write_scope**: []
- **hand-off**: 검증된 가설을 스펙화하면 → requirements-engineering

## Install

```
claude plugin marketplace add tokenmaxxxer/user-discovery-rulebook
claude plugin install user-discovery
```

## Layout

- `user-discovery/.claude-plugin/plugin.json` — plugin manifest
- `user-discovery/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `user-discovery/hooks/directive.sh` — SessionStart role directive
- `user-discovery/hooks/record-fields-gate.sh` — this role's record required-field gate
- `user-discovery/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `user-discovery/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `user-discovery/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
