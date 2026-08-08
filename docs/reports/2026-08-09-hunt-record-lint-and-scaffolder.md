---
proposal: docs/issue-517/proposals/2026-08-09-record-lint-and-scaffolder.md
---

# Hunt record — record-lint-and-scaffolder

## after-proposal — stance 4: assume the write set this proposal freezes cannot actually carry the work — find a path the build will need that the proposal's `files:` list does not include.

Verdict: FINDING — proposal offers record-scaffold.sh as "a PreToolUse (or on-demand CLI) generator" but if built as a PreToolUse hook it must be registered in on-the-record/hooks/hooks.json, which is not in the frozen files: list.
Kind: design-error
Seed: docs/issue-517/proposals/2026-08-09-record-lint-and-scaffolder.md ("What will be done" bullet for on-the-record/hooks/record-scaffold.sh)
cap_seconds: 120
tier: default
diff_stat_lines: 2 files changed (docs-only, both newly created)
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:02:00Z

### Reproduce
grep -n "record-claim-guard" on-the-record/hooks/hooks.json
cat on-the-record/hooks/hooks.json

### Observed
Every existing hook script in on-the-record/hooks/ (self-update.sh, directive.sh, retry-loop-bound.sh, deliverable-guard.sh, contract-guard.sh, pr-preflight.sh, spec-index-preflight.sh, record-claim-guard.sh, stop-gate.sh, role-test-claim-guard.sh, decision-queue-stopgate.sh, report-framing-check.sh) has a corresponding entry under a lifecycle event (PreToolUse/PostToolUse/Stop/etc.) in on-the-record/hooks/hooks.json's "hooks" map with a "command" pointing at ${CLAUDE_PLUGIN_ROOT}/hooks/<script>. record-scaffold.sh has no such entry and hooks.json is absent from the proposal's files: list, so if the scaffolder is built as a PreToolUse-triggered hook (one of the two forms the proposal explicitly names) it would never actually fire in a plugin-installed session -- it would sit unregistered like an orphaned script, indistinguishable from every wired hook by directory location alone.

### Expected
on-the-record/hooks/hooks.json should be in the files: write set (or the proposal should commit unambiguously to the "on-demand CLI" form only, dropping the PreToolUse option), since the aggregator's own stated constraint is "must work in plugin-installed sessions" and plugin session wiring for hooks in this repo runs entirely through hooks.json.
