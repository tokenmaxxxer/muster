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

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `_GITIGNORE_TOP_LEVEL_DIR` requires a trailing `/`, so any valid `.gitignore` directory entry written without one (e.g. `build`, `node_modules`, `dist`) is silently NOT pruned; os.walk still descends into it and the gate scans its contents as if ungitignored.
Kind: silent-failure
Seed: gates/gates.py `_GITIGNORE_TOP_LEVEL_DIR = re.compile(r"^/?([\w.\-]+)/$", re.MULTILINE)` / `_excluded_tree_dirs` / `_prune_excluded`, applied in `duplicate_test_basenames`, `schema_field_orphans`, and gates/claims.py `_check_producer_exists`
cap_seconds: 180
tier: default
diff_stat_lines: (gates/gates.py + gates/claims.py, ~2 helpers + 3 call sites; not separately measured)
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:03:00Z

### Reproduce
```
python3 - <<'PY'
import gates.gates as g
from pathlib import Path
import tempfile, os

d = tempfile.mkdtemp()
Path(d, ".gitignore").write_text("build\n")   # valid gitignore syntax, no trailing slash
os.makedirs(Path(d, "build", "sub"), exist_ok=True)
Path(d, "build", "test_dup.py").write_text("def test_a(): pass\n")
os.makedirs(Path(d, "other"), exist_ok=True)
Path(d, "other", "test_dup.py").write_text("def test_b(): pass\n")

print("excluded set:", g._excluded_tree_dirs(Path(d)))
print("duplicate_test_basenames result:", g.duplicate_test_basenames(Path(d)))
PY
```

### Observed
```
excluded set: {'.git'}
duplicate_test_basenames result: ['중복 테스트 모듈 베이스네임: test_dup.py — build/test_dup.py, other/test_dup.py (...)']
```
`build/` was walked and flagged even though `.gitignore` lists `build` (a legitimate, commonly-used pattern — git treats a pattern without a trailing slash as matching both files and directories of that name). The helper's regex `^/?([\w.\-]+)/$` mandates a trailing slash, so this real gitignore entry is invisible to `_excluded_tree_dirs`, meaning any gitignored directory whose `.gitignore` entry omits the trailing slash (very common style, e.g. `node_modules`, `dist`, `build`) is scanned anyway by `duplicate_test_basenames`, `schema_field_orphans`, and `_check_producer_exists` — the exact contamination this proposal set out to exclude.

### Expected
`_excluded_tree_dirs` should recognize gitignore directory patterns regardless of trailing slash (or the proposal should explicitly document that only slash-suffixed entries are honored, which contradicts common `.gitignore` authoring style and undercuts the stated goal).
