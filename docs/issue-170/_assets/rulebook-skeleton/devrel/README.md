# devrel-rulebook

Rulebook for the `devrel` role (contract v3 role-handoff protocol), split off
per `docs/issue-160/proposals/role-taxonomy.md`'s round-3 promotion and
generated as skeleton scaffolding by issue-170.

- **decides**: 외부 개발자가 이 표면을 채택할 수 있는가
- **use_when**: 외부 개발자 대상 API/SDK가 걸릴 때
- **produces**: onboarding doc, sample code, adoption-friction list
- **write_scope**: ["docs/**"] (외부 개발자 한정 — external-developer-facing docs only)
- **hand-off**: API 표면 자체 재설계는 → api-design

## Install

```
claude plugin marketplace add tokenmaxxxer/devrel-rulebook
claude plugin install devrel
```

## Layout

- `devrel/.claude-plugin/plugin.json` — plugin manifest
- `devrel/hooks/hooks.json` — SessionStart + PreToolUse wiring
- `devrel/hooks/directive.sh` — SessionStart role directive
- `devrel/hooks/record-fields-gate.sh` — this role's record required-field gate
- `devrel/hooks/trailer-gate.sh` — commit `Subject: issue-<n>` trailer gate
- `devrel/hooks/handbook-trigger-gate.sh` — s21 handbook-sync gate
- `devrel/agents/warrant-hunter.md` — rotating-stance hunt agent
- `docs/specs/approvers.md` — Approve-authority allowlist (see below)

This is scaffolding, not a finished rulebook: fill in doctrine detail,
handoff enforcement, and any role-specific progress gate before treating
it as load-bearing.
