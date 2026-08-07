---
proposal: docs/issue-335/proposals/2026-08-07-fixture-shape-contracts.md
---

# Hunt record — fixture-shape-contracts

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING — `tests/support/shape_contracts.py` cannot be imported as `tests.support.shape_contracts` from `test_spawn.py` in this environment because a namespace package `tests/` (no `__init__.py`) at repo root collides with an unrelated regular package literally named `tests` (with `__init__.py`) already reachable on `sys.path` via user site-packages; the regular package wins the name and the import fails, and the proposal's write set has no `tests/__init__.py` (or equivalent import-mode/pytest config fix) to force the repo-local `tests` directory to resolve as a real package instead of silently losing to whatever `tests` happens to be importable first.
Kind: design-error
Seed: docs/issue-335/proposals/2026-08-07-fixture-shape-contracts.md (write set: tests/support/shape_contracts.py, tests/fixtures/golden/gh_paginate_slurp_sample.json, test_spawn.py, docs/handbooks/test-fixture-shape-contracts.md, docs/issue-335/reports/implementation.md)
cap_seconds: 60
tier: size:docs-only (docs-only diff so far; structural build-path check run per instruction)
diff_stat_lines: docs-only diff so far (survey.md, scout-brief.md, proposal.md)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:06:00Z

### Reproduce
```
mkdir -p tests/support
printf 'def dummy():\n    return True\n' > tests/support/shape_contracts.py
printf 'from tests.support import shape_contracts\n\ndef test_import_works():\n    assert shape_contracts.dummy() is True\n' > test_import_probe.py
python3 -m pytest -q test_import_probe.py
```

### Observed
```
ImportError while importing test module '.../test_import_probe.py'.
test_import_probe.py:1: in <module>
    from tests.support import shape_contracts
E   ModuleNotFoundError: No module named 'tests.support'
```
Confirmed cause: `python3 -c "import sys; sys.path.insert(0,'.'); import tests; print(tests.__path__)"` resolves `tests` to `/home/jwjung/.local/lib/python3.10/site-packages/tests` (an unrelated installed package that happens to be named `tests` and has an `__init__.py`), not to the repo's `tests/` directory — `find tests -name "__init__.py"` in the repo returns nothing, confirming there is currently no `tests/__init__.py` anywhere. A directory containing `__init__.py`, found anywhere on `sys.path`, resolves as a regular package and wins outright over a namespace-package portion contributed by an earlier `__init__.py`-less `tests/` directory, so the repo's own `tests/` tree is shadowed rather than merged.

### Expected
The proposal's write set should include making `tests/` (and `tests/support/`) a real package (e.g. `tests/__init__.py`, `tests/support/__init__.py`) or otherwise pin pytest's `--import-mode`/rootdir handling, so that `import tests.support.shape_contracts` in `test_spawn.py` is guaranteed to resolve to the repo's own module rather than silently depending on no other package named `tests` being importable in whichever environment the suite runs in.
