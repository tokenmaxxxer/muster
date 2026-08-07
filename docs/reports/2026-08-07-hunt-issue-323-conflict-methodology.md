---
proposal: docs/issue-323/proposals/conflict-methodology.md
---

# Hunt record — issue-323-conflict-methodology

## before-landing — stance 3: assume the resolution-detection rule cannot hold — find state nothing maintains

Verdict: FINDING — has_resolution_record's grep pattern is an unanchored substring match, so it treats any record that happens to contain another issue number as a *substring* of its own text (e.g. "issue-323", "issue #34" mentioned in passing) as a valid resolution for a completely different, unrelated issue pair (e.g. issue 3 vs issue 34, or issue 3 vs issue 323). No word-boundary or delimiter check exists; the pattern `issue #${issue_b}\|issue-${issue_b}` matches anywhere grep finds the digits as a substring of a longer number or within a larger sentence, so the "record must name the other issue as resolved" invariant the spec claims is not actually enforced — it degrades to "record contains these digits anywhere."
Kind: silent-failure
Seed: scripts/check-write-set-conflicts.sh (has_resolution_record, lines ~54-64), docs/specs/parallel-conflict-methodology.md
cap_seconds: 120
tier: default
diff_stat_lines: ~350
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:02:00Z

### Reproduce
```
echo "See issue-323 for details, mentioned incidentally about issue #34 too." > /tmp/x.md
grep -q "issue #3\|issue-3" /tmp/x.md && echo "MATCHED (false positive for issue 3)"
```
(Substituting the exact pattern the script builds for issue_b=3: `"issue #${issue_b}\|issue-${issue_b}"` = `issue #3\|issue-3`.) This demonstrates that has_resolution_record(3, 34) or has_resolution_record(3, 323) would report a resolution as "found" purely because the record's text contains "issue-323" or "issue #34" as a substring — not because the record actually names issue 3 as resolved with those issues.

### Observed
`MATCHED (false positive for issue 3)` — the grep matches and would cause has_resolution_record to return 0 (resolved) even though no actual cross-reference to issue 3 exists in the text.

### Expected
The grep should anchor on a word/number boundary (e.g. `issue #3\b` / `issue-3\b` or an explicit non-digit lookahead) so that issue "3" is not silently satisfied by mentions of "issue-323", "issue-34", "issue #300", etc. As written, any two issues whose numbers are substrings of a third issue's number (very common — "3" is a substring of 30, 34, 43, 323, etc.) can have unresolved write-set conflicts silently marked RESOLVED whenever either record happens to mention that unrelated, larger issue number.
