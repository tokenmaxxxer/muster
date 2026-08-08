---
proposal: docs/issue-501/proposals/2026-08-08-session-latency-breakdown.md
---

# Hunt record — session-latency-breakdown

## after-proposal — stance 2: assume this guard/measurement goes silent when its own input is malformed — make it go silent

Verdict: FINDING — the idle-gap grouping key `(issue, role)`, with `issue` extracted from `cwd` via `-issue-(\d+)-` and no repo component, silently merges unrelated same-numbered issues across different repos into one idle-gap series, producing a plausible-looking idle-time number for a gap that never happened between the two paired sessions.
Kind: design-error
Seed: docs/issue-501/proposals/2026-08-08-session-latency-breakdown.md, section "(d) Approval round-trip idle" — "for each `(issue, role)` pair with more than one session today ... sorted by `ts`, computed `idle = next_session_start - prev_session_ts`", where issue comes only from the `-issue-(\d+)-` regex on `cwd` (repo is not part of the key).
cap_seconds: 120
tier: default
diff_stat_lines: ~284 (docs-only, two new files)
started_at: 2026-08-08T09:00:00+09:00
ended_at: 2026-08-08T09:20:00+09:00

### Reproduce

Checked today's real ledger (`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/ledger.jsonl`, 124 rows): 0 issue-number collisions across the 4 repos touched today (verified programmatically), so the real dataset happens not to trigger this. Constructed the minimal case the described method does not guard against: two ledger rows, same issue number, same role, different repos, and ran the grouping/idle formula exactly as specified in the proposal.

```python
import re
from collections import defaultdict
pat = re.compile(r'-issue-(\d+)-')
rows = [
    {"ts": 1000000, "role": "implementation", "repo": "tokenmaxxxer-core",
     "cwd": "/home/jwjung/.tokenmaxxxer/work/tokenmaxxxer-core-issue-171-implementation",
     "duration_s": 200.0},
    {"ts": 1002000, "role": "implementation", "repo": "on-the-record",
     "cwd": "/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-171-implementation",
     "duration_s": 300.0},
]
groups = defaultdict(list)
for row in rows:
    issue = pat.search(row["cwd"]).group(1)
    groups[(issue, row["role"])].append(row)
for (issue, role), grp in groups.items():
    grp.sort(key=lambda r: r["ts"])
    for prev, nxt in zip(grp, grp[1:]):
        idle = (nxt["ts"] - nxt["duration_s"]) - prev["ts"]
        print("issue=%s role=%s: merged %s -> %s, idle=%ss" %
              (issue, role, prev["repo"], nxt["repo"], idle))
```

### Observed

```
issue=171 role=implementation: merged tokenmaxxxer-core -> on-the-record, idle=1700.0s
```

The method reports a 1700s idle gap "on issue 171" — indistinguishable in shape from a genuine same-repo approval-wait gap. The proposal's own table names issue 171 by number as one of the top-8 idle-tail issues driving its step-2 recommendation (max gap 3389s, "issue 171, implementation→implementation"). A same-numbered issue in a second repo on the same day would silently contaminate exactly that headline number, with no error, no NaN, no warning — just a wrong-but-plausible seconds figure attributed to the wrong pairing of sessions.

### Expected

The grouping key for inter-session idle should include `repo` (or the full project slug), not issue number alone — issue numbers are only unique within a repo, not globally. Absent that, the method should at minimum detect and exclude/flag pairs where `repo` differs between consecutive same-issue-number rows rather than silently computing an idle gap across them. Today's real ledger happens not to collide (verified: 0 collisions across 124 rows / 4 repos), so the defect is currently invisible — it is a property of the described method, not of today's particular data, and will silently corrupt the idle-tail numbers the first day two repos' issue numbers coincide.

## before-landing (step 2) — stance 3: assume the rule as written cannot hold — find the state nothing maintains

proposal: docs/issue-501/proposals/2026-08-08-session-latency-breakdown.md

Verdict: FINDING — the pre-registered "before/after" metric in operations.md depends on a ledger boundary ("after this practice has taken hold") that nothing writes or records, and `compute_idle_gaps()`/`median_idle_s()` take no time-window parameter to select it.
Kind: design-error
Seed: docs/handbooks/operations.md "Respawn batching" section (KO ~L1078, EN ~L1078 duplicate) + test/test_latency_report.py compute_idle_gaps()/median_idle_s()
cap_seconds: 120
tier: default
diff_stat_lines: 219 insertions, 1 deletion across 4 files
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:05:00Z

### Reproduce
```
python3 -c "
import sys; sys.path.insert(0,'test')
from test_latency_report import compute_idle_gaps
import inspect
print(inspect.signature(compute_idle_gaps))
"
grep -n "practice has taken hold\|adopted\|since_ts\|after_ts\|boundary_ts" docs/handbooks/operations.md test/test_latency_report.py
```

### Observed
`compute_idle_gaps(rows: list[dict]) -> list[dict]` has no time-window argument, and grepping for any marker of when the "respawn batching" practice was adopted (a timestamp, a ledger field, a file) returns nothing except unrelated "boundary" hits (sandbox filesystem/network boundary, unrelated docs). The operations.md text literally instructs a future reader to "re-run against a ledger window after this practice has taken hold" but no code or artifact records where that window starts — a future re-run has to guess which ledger.jsonl rows postdate adoption of the practice, which produces an arbitrary "after" measurement no one can audit or reproduce, silently.

### Expected
Either the practice's adoption should stamp something re-runnable (e.g. a marker row/timestamp in the ledger, or a documented cutoff date committed alongside the handbook change), or `compute_idle_gaps`/`median_idle_s` should accept a `since_ts` filter tied to that marker. As written, the "before/after" comparison this handbook section promises cannot be computed correctly by anyone who didn't personally witness the exact moment the practice started being followed.
