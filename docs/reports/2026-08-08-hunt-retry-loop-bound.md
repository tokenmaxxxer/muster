---
proposal: docs/issue-507/proposals/2026-08-08-retry-loop-bound.md
---

# Hunt record — retry-loop-bound

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: FINDING — the "PreToolUse allow-with-additionalContext" behavior the K-th nudge requires has no precedent anywhere in the write set or repo; the proposal cites decision-queue-stopgate.sh's `additionalContext`/`{"decision":"block"}` vocabulary as reusable, but that vocabulary is Stop-event-only, and no PreToolUse hook file exists (or is listed to be written) demonstrating the actual PreToolUse allow/deny schema, so phase-2 has no source in the write set to copy from.
Kind: design-error
Seed: docs/issue-507/proposals/2026-08-08-retry-loop-bound.md ("Constraints" bullet 3, "What will be done" PreToolUse bullet)
cap_seconds: 60
tier: default (docs-only fast path)
diff_stat_lines: ~282 (2 files, both docs/)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:05:00Z

### Reproduce
```
grep -n "decision\|permissionDecision\|exit 2\|additionalContext" on-the-record/hooks/contract-guard.sh on-the-record/hooks/deliverable-guard.sh
grep -n "additionalContext" on-the-record/hooks/*.sh
```

### Observed
`contract-guard.sh` and `deliverable-guard.sh` (the existing PreToolUse deny hooks on Write|Edit|MultiEdit|Bash) deny via bare `exit 2` with no JSON `hookSpecificOutput` at all. Every `additionalContext` usage in the repo (`decision-queue-stopgate.sh`, `stop-gate.sh`, `role-test-claim-guard.sh`) is emitted under the `Stop` hook event, not `PreToolUse`. No file in the repo shows a `PreToolUse` hook exiting 0 while attaching `hookSpecificOutput.additionalContext` to nudge without blocking — the exact K-th behavior #507 needs.

### Expected
The proposal's "no new output shape invented" constraint implies a working example exists to copy; there isn't one for PreToolUse-allow-with-context in this repo, so the write set is missing either a reference/helper this hook can share, or the proposal should say this is a genuinely new PreToolUse output shape (contradicting "already used" in Constraints).
