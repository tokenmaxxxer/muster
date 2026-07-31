# technical-writing-rulebook

Rulebook for the `technical-writing` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 독자가 알아야 할 것을 어떻게 구조화할지
- **use_when**: 외부 공개 문서가 필요할 때
- **produces**: doc outline, draft, target-reader note
- **write_scope**: ["docs/**"] (외부공개 한정 — external-facing docs only)
- **hand-off**: 개발자 대상 온보딩이면 → devrel

## Install

```
claude plugin marketplace add tokenmaxxxer/technical-writing-rulebook
claude plugin install technical-writing
```

## Layout

- `technical-writing/.claude-plugin/plugin.json` — plugin manifest
- `technical-writing/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `technical-writing/hooks/directive.sh` — SessionStart role directive
- `technical-writing/hooks/record-fields-gate.sh` — this role's record required-field gate
- `technical-writing/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `technical-writing/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `technical-writing/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
