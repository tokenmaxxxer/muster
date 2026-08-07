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

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `record_derived_counts_in` misses bare untagged count claims that use nouns outside its hardcoded allow-list (e.g. "findings", "instances", "records", "results"), letting them slip through unflagged.
Kind: silent-failure
Seed: gates/gates.py `_COUNT_NOUN = re.compile(r"\d+\s+(?:detection\s+)?(?:items?|works?|checks?|cases?)\b")` and `record_derived_counts_in`/`record_derived_counts` (docs/issue-333/proposals/derived-record-counts.md)
cap_seconds: 120
tier: default (size:21-200-lines)
diff_stat_lines: ~21-200 (gates/gates.py + test_gates.py)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:08:00Z

### Reproduce
Built a throwaway git repo with `origin/main` set up, committed a changed record at `docs/issue-333/reports/implementation.md` containing an untagged, unfenced count claim using nouns not in the allow-list, then called the gate function directly:

```python
import sys; sys.path.insert(0, '.')
from pathlib import Path
from gates.gates import record_derived_counts_in
print(record_derived_counts_in(Path('<scratch-repo>')))
```

Record body committed on the `work` branch (diffed against `origin/main`):
```
---
role: implementation
---
We reviewed 12 findings and confirmed 8 instances of drift across the records.
```

### Observed
`record_derived_counts_in` returns `[]` — no violation reported — even though "12 findings" and "8 instances" are exactly the kind of bare, untagged count claim the gate exists to catch (per its own docstring: "N of M"/"N items" 류 개수 주장이 코드펜스 재현이나 `derived: ...` 인용 없이 맨몸으로 타이핑되어 있는지 검사"). Verified separately in isolation that `_COUNT_NOUN.search("We reviewed 12 findings and confirmed 8 instances of drift across the records.")` returns `None` and `_COUNT_RATIO.search(...)` also returns `None` on that same string.

### Expected
Any bare numeric count claim over a noun describing a set of reviewed/found things (findings, instances, records, results, occurrences, runs, etc.) in a changed record, without a `derived: ...` tag or code-fence reproduction, should be flagged. Because `_COUNT_NOUN` only recognizes `item(s)`, `work(s)`, `check(s)`, `case(s)` (optionally prefixed by "detection"), any author (or model) who phrases an unverified count using a synonym outside that closed list produces a claim the gate is silently blind to — it reports success (empty list) exactly as it would for a genuinely clean record.
