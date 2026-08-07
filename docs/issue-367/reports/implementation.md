---
code_under_review: spawn.py, test_gates.py
loop_state: delivered
---

# issue-367: isolate the repo-config-trust test from the real home

Upstream basis: docs/issue-367/proposals/2026-08-07-isolate-repo-config-trust-test.md

## What was done

`spawn.require_no_repo_config` (spawn.py:876) now reads
`MUSTER_TOKENMAXXXER_HOME` and uses it in place of `Path.home() / ".tokenmaxxxer"`
when set, defaulting to the real path otherwise — same pattern as the
existing `MUSTER_WORK_DIR` override (spawn.py:2492, 2745). This is the only
function this change reaches; no other caller of `Path.home()` in spawn.py
was touched (settings/plugins reads at spawn.py:37,112,567,689,740 are
untouched — out of scope, not exercised by this test).

`test_gates.py::t_repo_local_claude_config_stops_the_spawn` now sets
`MUSTER_TOKENMAXXXER_HOME` to a per-iteration tmp dir, restores the prior
env value in `finally`, and asserts
`~/.tokenmaxxxer/trusted-repo-config.json` is byte-identical before and
after the test (not merely assumed untouched).

## Why

The test's pass/fail depended on whether the real `~/.tokenmaxxxer` was
writable — a property of the machine, not the code (#367, split from
#360). The fix removes that dependency and turns the "doesn't touch the
real home" claim into an assertion.

## Before/after, demonstrated

This sandbox's real `$HOME` is genuinely read-only (not synthesized):

- Before the fix (code stashed): `pytest test_gates.py::t_repo_local_claude_config_stops_the_spawn -q`
  → `OSError: [Errno 30] Read-only file system: '/home/jwjung/.tokenmaxxxer/trusted-repo-config.json'`,
  1 failed.
- After the fix (stash restored): same command → `1 passed`.
- Full `test_gates.py -q`: `75 passed`.
- Full suite `pytest -q`: `51 failed, 306 passed` — the 51 are the
  pre-existing #360 `subprocess.run`-leak pollution, unrelated to this
  change (unchanged count/shape from the issue's own report).

## Scope item 3 — suite-wide scan for the same shape

Searched: `grep -rn "Path.home()"` across the whole tree, plus a manual
check of every test-collecting file's real-home / `.tokenmaxxxer` /
`.claude` references (`test_gates.py`, `test_spawn.py`, `test_flows.py`,
`gates/test_closes_gate_ci.py`, `test_vocab_coherence_roles.py`).

Result:

- `test_flows.py`, `gates/test_closes_gate_ci.py`,
  `test_vocab_coherence_roles.py` — no `Path.home()` / real-home / `~/`
  references at all.
- `test_spawn.py` — every real-home-adjacent path it exercises already goes
  through the `MUSTER_WORK_DIR` env override (lines 1204-1215, 2374, 2437,
  2486, 2545, 2584), so it does not touch the real home during tests.
- `test_gates.py` — the fixed test was the only one of this shape; the
  fixed version only *reads* the real
  `~/.tokenmaxxxer/trusted-repo-config.json` (to assert it is unchanged),
  never writes it.

**List of remaining tests with this shape: empty.** This was the only
genuine instance.

## Generator (per #363)

The generator was the direct `Path.home()` call inside
`require_no_repo_config` with no env override — the same shape as the
already-fixed `MUSTER_WORK_DIR` call sites, just missing the override this
one instance had. This change removes the generator at this call site (adds
the override); it does not remove `Path.home()` calls elsewhere in
`spawn.py`, since the scan above found no other test exercising them
against the real home.

## What did not work

None.

## Open findings

None open. Closed check below.

## closed_checks

- suite-wide grep for `Path.home()` + manual real-home/`.tokenmaxxxer`/`.claude`
  check across all test-collecting files — code_sha: working tree at time of
  this record (see `spawn.py`, `test_gates.py` diff in this commit).
