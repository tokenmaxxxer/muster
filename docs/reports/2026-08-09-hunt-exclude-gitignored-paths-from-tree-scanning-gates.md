---
proposal: docs/issue-529/proposals/2026-08-09-exclude-gitignored-paths-from-tree-scanning-gates.md
---

# Hunt record — exclude-gitignored-paths-from-tree-scanning-gates

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the proposed `_EXCLUDED_TREE_DIRS` frozenset is a fixed name list that omits `.reexecution/`, a directory that IS in the live `.gitignore`, so the fix (once built) still fails to exclude a real gitignored path from the tree walk.
Kind: design-error
Seed: docs/issue-529/proposals/2026-08-09-exclude-gitignored-paths-from-tree-scanning-gates.md
cap_seconds: 60
tier: default
diff_stat_lines: proposal doc only (not yet built)
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:01:00Z

### Reproduce
```
cat .gitignore
```

### Observed
`.gitignore` contains:
```
runs/
__pycache__/
.router.lock
.warrant-hunt.*
.reexecution/
```
The proposal's planned `_EXCLUDED_TREE_DIRS = frozenset({".git", "runs", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache"})` (see "What will be done") does not include `.reexecution`. The proposal's own Rationale/What-will-be-done section frames the list as derived from "other known non-source top-level dirs already implied by `.gitignore`", i.e. it claims to be sourced from the repo's actual `.gitignore`, but it is hand-picked and diverges from it — `.reexecution/` is a real top-level gitignored entry that would still be walked, still contaminate `duplicate_test_basenames`, `schema_field_orphans`, and `_check_producer_exists` after the fix ships, exactly reproducing the false-failure/false-pass bug class the issue exists to close.

### Expected
The exclusion set (or its derivation) should track `.gitignore`'s actual top-level entries (or use `git check-ignore`/`git status --ignored` per-path checks) rather than a hardcoded name list disconnected from the file it claims to mirror, so any current or future gitignored top-level directory (e.g. `.reexecution/`) is excluded without requiring a matching manual edit to `_EXCLUDED_TREE_DIRS` every time `.gitignore` changes.
