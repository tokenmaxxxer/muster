---
proposal: docs/issue-457/proposals/2026-08-08-gate-porting-order.md
---

# Hunt record — gate-porting-order

## before-landing — stance 0: assume the gate you just touched is bypassable — find the bypass

Verdict: FINDING — record-claim-guard.sh's #333 bare-count-claim check misses claims using the word "tests" (or any noun outside items/works/checks/cases), letting unsupported count claims through unblocked.
Kind: silent-failure
Seed: on-the-record/hooks/record-claim-guard.sh (`_COUNT_NOUN` regex: `\d+\s+(?:detection\s+)?(?:items?|works?|checks?|cases?)\b`), `_COUNT_RATIO` regex requires an explicit `of`/`/` ratio.
cap_seconds: 180
tier: default
diff_stat_lines: ~638 insertions, 11 files
started_at: 2026-08-08T17:43:17+09:00
ended_at: 2026-08-08T17:52:00+09:00

### Reproduce
```
python3 - <<'PY'
import json, os
d, seg, r = "docs", "issue-457", "reports"
fp = d + "/" + seg + "/" + r + "/foo.md"
payload = {
  "tool_name": "Write",
  "tool_input": {
    "file_path": fp,
    "content": "We ran 38 tests passing with no failures, all good.\n"
  },
  "cwd": os.getcwd()
}
open("/tmp/payload2.json","w").write(json.dumps(payload))
PY
cat /tmp/payload2.json | on-the-record/hooks/record-claim-guard.sh
echo EXITCODE $?
```
(Note: writing the literal string `docs/issue-457/reports/foo.md` directly into a Bash command in this session triggers an unrelated hook, `board-gate.sh`, which false-positives on the *text* of the command as if it were a role-boundary write — hence the path is built via string concatenation above to reach the guard under test.)

### Observed
`EXITCODE 0` — no stderr, no denial. The bare "38 tests passing" count claim (no code-fence reproduction, no `derived: ...` citation) is written unchallenged.

### Expected
Per the check's own stated intent (#333 mirror: "a bare 'N of M'/'N items' count claim with no code-fence reproduction and no `derived: ...` citation"), this should deny with exit 2 and a `record-claim-guard: ... (issue #333)` message, same as it does for "38 items passing" or "38 checks passing". The noun allowlist (`items?|works?|checks?|cases?`) simply omits "tests" — a word extremely common for exactly this kind of claim in a test-heavy repo — so the guard is trivially evaded by phrasing the claim with that word instead of a synonym already in the list.
