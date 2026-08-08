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

## before-landing — stance 0: assume the gate is bypassable -- find the bypass

Verdict: FINDING — path-spelling variants of the same target (trailing slash, `./`, `//`) hash to distinct signatures, so identical-file retry denials never accumulate toward K/2K and the abort gate never fires.
Kind: silent-failure
Seed: on-the-record/hooks/retry-loop-bound.sh (_target()/_signature() use raw tool_input string, no path normalization)
cap_seconds: 180
tier: default
diff_stat_lines: n/a (pre-landing hunt against working tree)
started_at: 2026-08-08T22:24:16+09:00
ended_at: 2026-08-08T22:34:00+09:00

### Reproduce
```
export CLAUDE_ROLE=  # unset role-session bypass
export OTR_RETRY_BOUND_STATE_DIR=/tmp/rb-state-test
export OTR_RETRY_BOUND_K=2
cd on-the-record/hooks
SID=s1
for variant in "/tmp/target.txt" "./target.txt" "/tmp/./target.txt" "//tmp/target.txt" "/tmp//target.txt"; do
  python3 -c "
import json
print(json.dumps({'session_id':'$SID','tool_name':'Write','tool_input':{'file_path':'$variant'},'tool_response':'PreToolUse:Write hook error: [contract-guard: refused — nope]'}))
" | bash retry-loop-bound.sh post
done
cat /tmp/rb-state-test/s1.json
```

### Observed
Five separate signatures are created, each with `"count": 1`:
```
{"be62a740...": {"count": 1, ..., "target": "/tmp/target.txt"},
 "183120a4...": {"count": 1, ..., "target": "./target.txt"},
 "6ed96f82...": {"count": 1, ..., "target": "/tmp/./target.txt"},
 "9883f7a8...": {"count": 1, ..., "target": "//tmp/target.txt"},
 "26d8aea2...": {"count": 1, ..., "target": "/tmp//target.txt"}}
```
A subsequent `pre` check for any of these path spellings returns rc=0 (allowed, no nudge, no abort) because no single signature's count ever reaches K=2, even after 5 identical-target denials.

### Expected
All five requests target the same file on disk; the gate's own design doc states "Identical target => identical signature" — they should collapse into one signature with count=5, triggering the K-nudge (and, with more retries, the 2K abort). Instead `_target()` in retry-loop-bound.sh takes the raw `file_path`/`path`/`command` string verbatim with no normalization (no `os.path.normpath`/`realpath`), so trivial path-spelling differences silently reset the counter to 0 every time, defeating the loop bound entirely for this common retry pattern.
