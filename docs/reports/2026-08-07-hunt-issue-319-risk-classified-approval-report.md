---
proposal: docs/issue-319/proposals/2026-08-07-risk-classified-approval-report.md
---

# Hunt record — issue-319-risk-classified-approval-report

## before-landing — stance 1: assume the gate/classifier just added is bypassable — find the bypass

Verdict: FINDING — a blank line (or any non-`- path` line) between entries in a proposal's `files:` block silently truncates the parsed write-set, dropping later files (including protected ones) and causing classify() to return "low" instead of the fail-closed "high".
Kind: silent-failure
Seed: gates/risk_report.py (~229 lines across gates/risk_report.py, test_risk_report.py, docs/handbooks/risk-classified-approvals.md)
cap_seconds: 180
tier: default
diff_stat_lines: ~229
started_at: 2026-08-07T05:14:00Z
ended_at: 2026-08-07T05:17:30Z

### Reproduce
Create `docs/proposals/test-bypass.md`:
```
status: proposed

files:
  - src/harmless.py

  - gates/gates.py
```
Then run:
```python
from pathlib import Path
import sys
sys.path.insert(0, ".../gates")
import risk_report as rr
text = Path("docs/proposals/test-bypass.md").read_text()
parsed = rr._parse_files(text)
print(parsed)                       # ['src/harmless.py']
print(rr.classify(parsed or [], 0, 0))  # low
```

### Observed
`_parse_files` returns `['src/harmless.py']` only — `gates/gates.py` (a
protected path under `PROTECTED_ROOT_DIRS`) is silently dropped because
`_FILES_BLOCK`'s regex (`^files:\s*\n((?:^\s*-\s*\S+\s*\n?)+)`) matches a
single contiguous run of `- path` lines and stops at the first blank line
(or any comment/non-list line), so everything after the break is never
captured. `classify()` then sees a non-empty, "successfully parsed" list
that omits the protected file and returns `"low"`.

### Expected
Per the module's own stated fail-closed principle ("write-set을 파싱할 수
없는 제안은 낮음이 아니라 high로 분류한다"), a `files:` block that cannot be
parsed in full (or that in fact contains a protected path) must not
silently degrade to a partial list that omits protected paths — it should
either fail to parse entirely (→ high) or capture the full list including
`gates/gates.py`, which would classify as `high`.
