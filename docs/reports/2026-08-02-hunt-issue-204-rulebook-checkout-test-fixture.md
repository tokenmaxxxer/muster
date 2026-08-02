---
proposal: docs/issue-204/proposals/rulebook-checkout-test-fixture.md
---

# Hunt record — rulebook-checkout-test-fixture

## after-proposal — stance 1: composition regression (conftest.py collision on TOKENMAXXXER_RULEBOOKS/TOKENMAXXXER_CORE or pytest collection/rootdir)

Verdict: FINDING — the repo's own documented non-pytest test invocations (`python3 test_gates.py` per README.md, and `python3 -m unittest test_spawn.py` per an existing issue-31 QA survey report) never import conftest.py, so its `TOKENMAXXXER_RULEBOOKS`/`TOKENMAXXXER_CORE` fixture defaults silently do not apply, and `rulebook_source`/`rulebook_checkout`/`core_root` fall through to the real github/network path instead of the fixture.
Kind: composition
Seed: root conftest.py (new, uncommitted) + tests/fixtures/rulebooks/* (new) on branch issue-204/implementation
cap_seconds: 90
tier: default
diff_stat_lines: 4 files changed, ~15 lines total (all new files, no existing file modified)
started_at: 2026-08-02T00:00:00Z
ended_at: 2026-08-02T00:20:00Z

### Reproduce
Script A (no conftest import — mirrors what `python3 test_gates.py` / `python3 -m unittest test_spawn.py` actually do):
```python
import json, os, sys
sys.path.insert(0, "/Users/jk/.tokenmaxxxer/work/on-the-record-issue-204-implementation")
import spawn
spec = json.loads((spawn.ROOT / "roles" / "execution-observation.json").read_text())
print("TOKENMAXXXER_RULEBOOKS set?", "TOKENMAXXXER_RULEBOOKS" in os.environ)
print("rulebook_source ->", spawn.rulebook_source(spec))
```

Script B (conftest imported first — mirrors what pytest does at collection):
```python
import json, os, sys
sys.path.insert(0, "/Users/jk/.tokenmaxxxer/work/on-the-record-issue-204-implementation")
import conftest
import spawn
spec = json.loads((spawn.ROOT / "roles" / "execution-observation.json").read_text())
print("TOKENMAXXXER_RULEBOOKS set?", "TOKENMAXXXER_RULEBOOKS" in os.environ, "->", os.environ.get("TOKENMAXXXER_RULEBOOKS"))
print("rulebook_source ->", spawn.rulebook_source(spec))
```
Run each with `python3 <script>.py`. (TOKENMAXXXER_RULEBOOKS/TOKENMAXXXER_CORE were confirmed absent from the ambient shell env before running — `printenv | grep -i TOKENMAXXXER` showed neither.)

Corroborating facts checked directly:
- `test_gates.py` defines `t_*`-prefixed tests (not `test_*`) and has `if __name__ == "__main__": tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")] ...`. `python3 -m pytest --collect-only -q test_gates.py` -> `no tests collected in 0.01s` (pytest's default `python_functions=test_*` does not see them at all; no pytest.ini/pyproject.toml/setup.cfg exists anywhere in the repo to change that default). README.md's documented self-check is literally `python3 test_gates.py`, which runs the `__main__` block directly — plain `python3`, no pytest, no conftest import.
- `test_spawn.py` ends with `if __name__ == "__main__": unittest.main()`; an existing issue-31 QA survey report documents `python3 -m unittest test_spawn.py` (stdlib unittest, no pytest) as an equivalent way this suite has actually been run.
- `spawn._spawn_one` -> `plugin_dirs(role, spec)` -> `rulebook_checkout(role, spec)`, and separately -> `core_plugin_dirs()` -> `core_root()` (spawn.py `_spawn_one`, `plugin_dirs`, `core_plugin_dirs`) — exactly the two functions the new conftest.py's own docstring names as what it exists to serve for `_spawn_one` sandboxed/network-free tests.

### Observed
Script A (no conftest import):
```
TOKENMAXXXER_RULEBOOKS set? False
rulebook_source -> {'source': 'github', 'repo': 'tokenmaxxxer/execution-observation-rulebook'}
```
Script B (conftest imported first):
```
TOKENMAXXXER_RULEBOOKS set? True -> /Users/jk/.tokenmaxxxer/work/on-the-record-issue-204-implementation/tests/fixtures/rulebooks
rulebook_source -> {'source': 'directory', 'path': '/Users/jk/.tokenmaxxxer/work/on-the-record-issue-204-implementation/tests/fixtures/rulebooks/execution-observation-rulebook'}
```

### Expected
The new conftest.py's stated purpose (its own docstring) is that role-session sandbox tests calling `_spawn_one` -> `rulebook_checkout`/`core_root` find the fixture tree by default, so those tests stay network-free regardless of how the suite is invoked. Because the fixture exists only as `conftest.py` (a pytest-only auto-import hook) and this repo has two other standing, documented ways to run the exact same test files that never trigger pytest's plugin system, any test that reaches `rulebook_checkout`/`core_root` without itself managing the two env vars (e.g. the `test_entry_carries_the_live_log_path` test in test_spawn.py, which mocks `spawn_cmd`/`ensure_pushed`/`roster_register`/`ledger_write`/`issue_workspace`/`checkout_issue_branch` but not `plugin_dirs`/`core_plugin_dirs`) silently resolves to the real github/network path instead of the fixture when run via `python3 -m unittest test_spawn.py` or `python3 test_gates.py` — the exact "network-free" guarantee the fixture exists to provide quietly does not hold under invocations this repo already documents as valid.
