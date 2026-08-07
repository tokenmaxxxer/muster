---
proposal: docs/issue-360/proposals/2026-08-07-fix-subprocess-run-leak.md
---

# Hunt record — fix-subprocess-run-leak

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `test_isolation.py`, run as a single ordinary test that "snapshots
before the suite and asserts unchanged after," cannot observe leaks from any test
module pytest collects *after* it — its real-world collection position sits before
`test_spawn.py` and `test_vocab_coherence_roles.py`, so leaks from either of those
(which contain dozens of raw `spawn.*`/`subprocess.run` reassignments) are
structurally invisible to it, and the guard reports green while the leak it exists to
catch is happening.
Kind: design-error
Seed: docs/issue-360/proposals/2026-08-07-fix-subprocess-run-leak.md, step 4 ("Add
  test_isolation.py: a test that snapshots subprocess.run ... before the suite and
  asserts, at the end of a full run, that it is unchanged")
cap_seconds: 60
tier: default
diff_stat_lines: docs-only (proposal file, not yet built)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:06:00Z

### Reproduce

Confirmed real collection order in this repo:

    python3 -m pytest --collect-only -q

yields file order `gates/test_closes_gate_ci.py, test_approve_scope.py,
test_flows.py, test_gates.py, [test_isolation.py would land here], test_spawn.py,
test_vocab_coherence_roles.py` — i.e. `test_isolation.py` sorts, and therefore runs,
*before* `test_spawn.py`.

Minimal repro built in scratchpad mirroring exactly the proposal's described
mechanism (module-level "before" snapshot + a single test asserting "after"),
saved at `/tmp/claude-1000/-home-jwjung--tokenmaxxxer-work-on-the-record-issue-360-implementation/53eaa5a3-a480-4de6-a78f-b8323415b20d/scratchpad/isotest/setup.sh`:

```
mymod.py:
    import subprocess

test_isolation.py:
    import mymod
    _before = mymod.subprocess.run
    def test_subprocess_run_unchanged():
        assert mymod.subprocess.run is _before, "subprocess.run was mutated and never restored"

test_zzz_leaky.py:
    import mymod
    def fake_run(*a, **k): return None
    def test_patches_without_teardown():
        mymod.subprocess.run = fake_run
        assert mymod.subprocess.run is fake_run

Run: cd <dir> && python3 -m pytest -q
```

### Observed

```
..                                                                       [100%]
2 passed in 0.02s
```

`test_zzz_leaky.py` leaves `subprocess.run` permanently patched and
`test_isolation.py` still reports pass, because its "before" snapshot and its
assertion both execute before the leaky file's test ever runs — there is no point
in the run where the isolation test's assertion is evaluated *after* a
later-collected file's leak.

### Expected

The isolation guard should fail whenever any module leaves `subprocess.run` (or a
tracked `spawn.*` attribute) mutated at the end of the full suite, regardless of
which file causes the mutation or where that file sorts relative to
`test_isolation.py`. A single ordinary test function fundamentally cannot implement
"snapshot before / assert after the full run" — that requires a session-scoped hook
(e.g. `pytest_sessionstart`/`pytest_sessionfinish` in `conftest.py`), which the
proposal's step 4 does not specify.
