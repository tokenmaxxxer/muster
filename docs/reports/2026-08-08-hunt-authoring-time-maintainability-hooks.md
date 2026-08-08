---
proposal: docs/issue-512/proposals/2026-08-08-authoring-time-maintainability-hooks.md
---

# Hunt record — authoring-time-maintainability-hooks

## after-proposal — stance 4: write set cannot carry the described work — find a build-needed path files: omits

Verdict: FINDING — proposal item 5 requires wiring `closure_sweep.accumulation_trend()` into `spawn.py`'s `roster_watchdog()`/`_board_wide_sweep()` tick, but `spawn.py` is absent from the `files:` frontmatter list.
Kind: design-error
Seed: docs/issue-512/proposals/2026-08-08-authoring-time-maintainability-hooks.md (new file, phase-1 proposal-only PR)
cap_seconds: 60
tier: default
diff_stat_lines: 1 file changed (proposal doc only, ~230 lines)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:05:00Z

### Reproduce
```
sed -n '/^files:/,/^---/p' docs/issue-512/proposals/2026-08-08-authoring-time-maintainability-hooks.md
grep -n "roster_watchdog\|find_violations\|find_uncovered" spawn.py | sed -n '1,10p'
grep -n "accumulation_trend" docs/issue-512/proposals/2026-08-08-authoring-time-maintainability-hooks.md
```

### Observed
The `files:` frontmatter lists exactly:
```
on-the-record/hooks/hooks.json
on-the-record/hooks/call-shape-guard.sh
on-the-record/hooks/accumulation-claim-guard.sh
on-the-record/hooks/test_call_shape_guard.py
on-the-record/hooks/test_accumulation_claim_guard.py
gates/accumulation.py
gates/test_accumulation.py
gates/closure_sweep.py
gates/test_closure_sweep.py
docs/specs/enforcement-boundary.md
```
`spawn.py` does not appear. But item 5 of "What will be done" states the new
`closure_sweep.py::accumulation_trend(repo)` count "reports the counts
alongside `find_violations()`'s existing observe-only output on each
`roster_watchdog()` tick — same wiring as `find_violations`/`find_uncovered`."
Both `find_violations()` and `find_uncovered()` are only ever called and
printed inside `spawn.py`'s `_board_wide_sweep(root)` (called from
`roster_watchdog()`, spawn.py:1871-1896) — `closure_sweep.py` never invokes
itself on a schedule. There is no other tick mechanism that would surface
`accumulation_trend()`'s output without a `spawn.py` edit that calls it and
prints its result the same way `violations`/`uncovered` are printed today.

### Expected
`spawn.py` should be listed in `files:` (as an edited file, adding the
`accumulation_trend()` call plus a print statement inside
`_board_wide_sweep()`), since phase-2 implementation cannot deliver "same
wiring as `find_violations`/`find_uncovered`" without touching it.
</content>
