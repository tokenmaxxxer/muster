---
proposal: docs/issue-464/proposals/2026-08-08-per-row-disposition-table.md
---

# Hunt record — per-row-disposition-table

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — `gates/test_boundary.py`'s `t_gate_porting_rows_are_ported_or_justified` treats any row containing the bare `#N` tag in `on-the-record/UNENFORCED-CLAUSES.md` as a valid "justification," regardless of the verdict text — so the phase-2 disposition rewrite this proposal plans for #369/#383/#325 (changing their verdict from "out of scope" to a mechanism citation) can be satisfied by garbage content and the gate will still report all-green.
Kind: silent-failure
Seed: docs/issue-464/proposals/2026-08-08-per-row-disposition-table.md, docs/issue-464/reports/architecture/survey.md (docs-only diff; gate exercised is `gates/test_boundary.py`, whose "eventual parity/disposition-table tests" the proposal explicitly says phase-2 output must match)
cap_seconds: 60
tier: default
diff_stat_lines: 2 files added (proposal + survey), docs-only
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:05:00Z

### Reproduce

```
cd on-the-record-issue-464-architecture
python3 - <<'PY'
from pathlib import Path
p = Path("on-the-record/UNENFORCED-CLAUSES.md")
orig = p.read_text(encoding="utf-8")
bad = orig.replace(
    "| #369 | `gates/ci.py` | the gate workflow always checks out `main`; the consumer-facing single-PR portion of this concern is already folded into `contract-guard.sh` per `docs/specs/enforcement-boundary.md`'s `closure_sweep.py` row — the remaining board-wide drift detection is out of scope per the operator's 2026-08-07 decision recorded there. |",
    "| #369 | `zzz` | asdf lorem ipsum totally unrelated nonsense, not a real disposition at all |"
)
p.write_text(bad, encoding="utf-8")
PY
python3 gates/test_boundary.py
```

(change reverted afterward — `git status --short on-the-record/UNENFORCED-CLAUSES.md` shows clean)

### Observed

```
ok - t_gate_porting_rows_are_ported_or_justified
...
9/9 passed
```

The gate passes with 9/9 even though the #369 row's verdict was replaced with nonsense unrelated to any real disposition. In `gates/test_boundary.py`, `t_gate_porting_rows_are_ported_or_justified` computes `justified = re.search(rf"\|\s*{tag}\s*\|", unenforced_text) is not None` — i.e. it only checks that the literal `#369` tag appears in some table row, never that the verdict text is a real disposition.

### Expected

When the phase-2 ADR this proposal schedules rewrites #369/#383/#325's `UNENFORCED-CLAUSES.md` verdicts to cite the new `roster_watchdog` mechanism, the gate should be able to distinguish a genuine mechanism-citation row from a vacuous or mistyped one — otherwise the proposal's own acceptance claim ("Every class-A row needs a mechanism-or-drop... per the issue's acceptance, gated by `gates/test_boundary.py`") does not hold: any placeholder text in the #369/#383/#325 rows satisfies the check just as well as a correct citation would.
