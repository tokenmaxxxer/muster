---
proposal: docs/issue-452/proposals/2026-08-08-ship-unenforced-clause-list.md
---

# Hunt record — ship-unenforced-clause-list


## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the planned "subset match" gate check is satisfiable by an empty (or near-empty) `on-the-record/UNENFORCED-CLAUSES.md`, so the gate cannot tell "correctly derived list" from "silently empty list."
Kind: silent-failure
Seed: docs/issue-452/proposals/2026-08-08-ship-unenforced-clause-list.md — planned `gates/test_boundary.py` case: "parses UNENFORCED-CLAUSES.md and asserts its mechanism rows are a subset match of the corresponding rows in docs/specs/enforcement-boundary.md (fails on drift)"
cap_seconds: 60
tier: default
diff_stat_lines: 0 (docs-only proposal, nothing built yet)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:01:30Z

### Reproduce
The proposal's own existing sibling check in `gates/test_boundary.py` (`check()`, lines 59-70) is the pattern the new case is explicitly modeled on: it computes `missing = [n in actual if n not in recorded]` and passes when `missing` is empty. The planned new case inverts direction (spec rows must appear in the shipped file) but the described logic is the same shape: "assert its mechanism rows are a subset ... of the corresponding rows in the spec." A subset check is one-directional — it only fails when the shipped file contains rows *not* in the spec (drift/typos), never when the shipped file is simply missing rows the spec has. Demonstrated in isolation:

```
python3 <<'PYEOF'
def missing(recorded, actual):
    return sorted(n for n in actual if n not in recorded)

recorded = {"a": "contract, CI-supplement", "b": "contract, CI-supplement"}
actual_empty = set()   # UNENFORCED-CLAUSES.md parsed to zero rows
print(missing(recorded, actual_empty))
PYEOF
```

### Observed
`[]` — an empty (or partially-truncated) `UNENFORCED-CLAUSES.md`, containing none of the spec's unenforced-clause rows, produces zero "missing" entries under a subset check, because the empty set is a subset of every set. The gate would report success.

### Expected
The gate must check set *equality* (or at least that the shipped file's rows are a superset covering every spec row whose verdict matches the extraction criteria — `contract, CI-supplement` or `out of scope — operator decision`), not a one-directional subset. As specified ("subset match"), a consumer could ship `on-the-record/UNENFORCED-CLAUSES.md` with the framing paragraph only and zero actual clause rows (or an editor could silently truncate it during a future edit), `gates/test_boundary.py` would still report "ok", and a zero-install consumer session reading the file would see no unenforced clauses listed — functionally identical to the pre-issue-441 state the whole proposal exists to fix, but now with a gate that appears green.
