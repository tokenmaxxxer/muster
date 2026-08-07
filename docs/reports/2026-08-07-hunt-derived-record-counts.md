---
proposal: docs/issue-333/proposals/derived-record-counts.md
---

# Hunt record — derived-record-counts

## after-proposal — stance 1: assume the gate just proposed is bypassable — find the bypass

Verdict: FINDING — the stated regex `\d+\s*(?:of|/)\s*\d+` only matches two-number ratio phrasing ("N of M" / "N/M"), so a bare single-number count assertion — the exact motivating example in the proposal's own Request section ("107 detection items exist") — has no second number/`of`//`/` to match against and is never flagged, letting a hand-typed undecided count slip through untagged.
Kind: design-error
Seed: docs/issue-333/proposals/derived-record-counts.md ("Outside fences, a line matching a count/ratio pattern (`\d+\s*(?:of|/)\s*\d+` ...) is a violation UNLESS ...")
cap_seconds: 60
tier: default (size:small)
diff_stat_lines: 2 new files (survey.md, proposal.md)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:00:50Z

### Reproduce
```python
import re
pat = re.compile(r'\d+\s*(?:of|/)\s*\d+')
print(bool(pat.search("107 detection items exist and nothing catches the drift.")))
print(bool(pat.search("The gate blocks 107 of 122 records.")))
```

### Observed
`False` for the bare single-count sentence ("107 detection items exist ...") — the same shape the proposal itself opens with as the motivating bad example — and `True` only for the two-number ratio form. A changed record asserting "We found 107 detection items." (no denominator, no `of`/`/`) passes the gate with zero violations, exactly the silent typed-number drift the proposal exists to stop.

### Expected
The gate (or its documented scope) should either flag bare single counts too, or the proposal should explicitly narrow its claimed coverage to ratios only instead of implying (via its own Request-section example) that standalone counts are also caught.
