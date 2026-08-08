---
proposal: docs/issue-473/proposals/2026-08-08-batch-c-reporting-discoverability-gates.md
---

# Hunt record — batch-c-reporting-discoverability-gates

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the planned `ci_reachable_gates` (issue #376) is a textual regex match on the literal string `gates.<name>(`, so any indirection around that spelling (module alias, `getattr`, wrapper) makes an actually-unreachable gate (the exact `record_enums`-past-`closes_only`-guard defect it exists to catch) report as "never called" (silently dropped, wrong finding text) rather than "reachable-after-guard", and conversely a call appearing only in a comment/docstring/dead branch before the guard line would textually "pass" a gate that is never really reached before the return. This is a fail-open regression on the exact defect class the gate is designed to catch, because the check does line-position text matching, not control-flow/call-graph analysis, despite the referenced sub-issue proposal explicitly promising to check "called at all" and "called before ... closes_only return."
Kind: design-error
Seed: docs/issue-473/proposals/2026-08-08-batch-c-reporting-discoverability-gates.md (Batch C wiring of ci_reachable_gates/schema_field_orphans into gates/ci.py before its closes_only early-return); underlying per-row design step 1 ("parses gates/ci.py's source for calls to gates.<name>(")
cap_seconds: 180
tier: default
diff_stat_lines: not yet built (proposal-stage; reproduction built from the proposal's stated algorithm)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:04:00Z

### Reproduce
Reimplemented the algorithm exactly as specified for `ci_reachable_gates` ("parses gates/ci.py's source for calls to `gates.<name>(` and reports ... whether it is (a) called at all, and (b) called before the `if closes_only: return bad` line") against synthetic `gates/ci.py`-shaped source snippets:

```
python3 repro.py
```
with cases:
- Case A: `bad += gates.record_enums(repo, {})` placed after `if closes_only: return bad` (the real, current shape of `gates/ci.py` lines 453-461) -> correctly flagged.
- Case B: same defect, but called through an aliased import (`import gates as g; ... g.record_enums(repo, {})`) -> NOT flagged.
- Case C: same defect via `getattr(gates, "record_enums")(repo, {})` -> NOT flagged.
- Case D: a mention of `gates.record_enums(repo, {})` inside a docstring positioned textually before the guard, with no real call anywhere -> NOT flagged (false pass), even though the gate is never actually invoked.

### Observed
```
Case A (expected: flag record_enums): ['record_enums: called past closes_only guard (line 3 > 1)', 'writeset: never called', 'smuggled_gate: never called']
Case B (alias bypass, same real defect): ['record_enums: never called', ...]
Case C (getattr bypass): ['record_enums: never called', ...]
Case D (dead-text false pass): ['writeset: never called', 'smuggled_gate: never called']
```
Cases B and C report "never called" (a different, non-actionable finding text that also misses the actual defect: reachable-past-guard) instead of catching the guard-position defect; case D shows the reverse direction — a gate mentioned only in dead text before the guard produces no finding at all, i.e. a silent pass for a truly-unreachable gate.

### Expected
A gate meant to catch "registered gate not reachable under `--closes-only`" should still catch that defect (or fail closed / report "cannot determine reachability") when the call is spelled through an alias or indirection, and should not certify reachability based on text that isn't a real call. As specified (plain regex over `gates.<name>(` text position), the check is trivially defeated by ordinary, non-adversarial Python refactors (import aliasing, dynamic dispatch) — not even an intentional evasion is required.
</content>
