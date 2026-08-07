---
proposal: docs/issue-290/proposals/2026-08-07-ci-and-test-hygiene.md
---

# Hunt record — ci-and-test-hygiene

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: NO FINDING
Seed: proposal and survey doc for issue 290 CI/test hygiene
cap_seconds: 60
tier: default
diff_stat_lines: 2 new files (docs only)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:01:30Z

Checked three candidate gaps in the frozen write set:
1. `pytest -q` from repo root does collect `gates/test_closes_gate_ci.py` (30 tests) without a
   separate invocation or conftest.py -- verified via `python3 -m pytest -q --collect-only`
   which lists all 30 `gates/test_closes_gate_ci.py::t_*` items alongside the root-level tests.
   `pytest.ini`'s `python_functions = test_* t_*` matches both, and pytest's default recursive
   discovery finds the subdirectory file; no separate workflow step is needed.
2. Searched all test files for raw (non-fixture) `subprocess.run =` / `spawn.subprocess.run =`
   monkeypatches: `grep -n "subprocess.run\s*=" test_spawn.py gates/test_closes_gate_ci.py
   test_gates.py`. Every occurrence in `test_spawn.py` and `gates/test_closes_gate_ci.py` is
   paired with `orig_run = subprocess.run` before and `subprocess.run = orig_run` (or
   `spawn.subprocess.run = orig_run`) inside a `finally:` block -- confirmed by reading
   test_spawn.py:3360-3450 and gates/test_closes_gate_ci.py:279-286. `test_flows.py` has zero
   `subprocess.run =` assignments (`grep -n "subprocess.run\s*=\|\.run =" test_flows.py` returns
   nothing). So test_approve_scope.py appears to be the only offender; the proposal's write set
   is not missing a sibling fix here.
3. `ast`-walked imports of spawn.py, test_spawn.py, test_gates.py, test_approve_scope.py, and
   gates/test_closes_gate_ci.py: only stdlib modules plus in-repo modules (spawn, gates, flows,
   ci, pr_reference, closure_sweep). No third-party package is imported, so no
   requirements/dependency file is needed for the new CI workflow to run `pytest -q`
   successfully (assuming pytest and pytest-asyncio, already present in this environment, get
   installed by the workflow's own setup step -- which is outside this stance's check).

No reproduction of a missing-file gap was found within the cap.
