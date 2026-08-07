---
code_under_review:
  - spawn.py
  - test_spawn.py
loop_state: phase-2-complete
open_findings: none
---

# issue-406 — phase 2 implementation record

Built exactly what `docs/issue-406/proposals/implementation.md` specified:
option (b), the `CARGO_HOME` workspace-cache redirect, plus the cheap
`~/.cargo/git` read-only mount. Option (a) (allowlisting `github.com`)
was confirmed a no-op and not built, per the proposal's Out-of-scope.

## What was done

1. `spawn.py:138` — added `(None, "~/.cargo/git")` to `PACKAGE_CACHE_DIRS`,
   mirroring the existing `~/.cargo/registry` entry exactly (same
   skip-if-absent mount rule, no new code path).
2. `spawn.py:3141` — added `"CARGO_HOME": os.path.join(wcache, "cargo")`
   to the `extra_env` dict inside `_spawn_one`'s `if issue is not None:`
   block, alongside the six existing Go/npm/pip cache keys.
3. `test_spawn.py`:
   - `PackageRegistryAccess.test_cargo_git_cache_dir_present_is_mounted`
     and `test_cargo_git_cache_dir_absent_is_skipped_without_error` —
     parametrized the same present/absent shape as the existing
     `GOMODCACHE` pair, using a patched `os.path.expanduser` since
     `~/.cargo/git`, like `~/.cargo/registry`, has no env-var override
     (`env_var is None`).
   - `Ledger.test_toolchain_cache_env_redirected_into_workspace` — no
     existing test asserted the `extra_env` dict's contents at all (the
     six Go/npm/pip keys were untested too), so per the proposal's
     instruction this covers the whole redirect mechanism: spies on
     `subprocess.Popen` (`wraps=subprocess.Popen`, real `cat` process
     still runs, same scaffold as the adjacent
     `test_entry_carries_the_live_log_path`) and asserts the `env` kwarg
     carries `CARGO_HOME` pointed at `<work>/.muster-cache/cargo`.

## Verification run

- `python3 -m pytest -q test_spawn.py -k "PackageRegistryAccess or cargo or CARGO_HOME or toolchain_cache"`
  → 10 passed.
- `python3 -m pytest -q` (no `--ignore`, as instructed): collection
  aborts before any test runs —
  `ERROR test_gates.py: import file mismatch: imported module
  'test_gates' has this __file__ attribute:
  .../gates/test_gates.py which is not the same as the test file we want
  to collect: .../test_gates.py` (both `test_gates.py` and
  `gates/test_gates.py` already exist on `main` at `6de3d55`, untouched
  by this change — the pytest rootdir-relative module-name collision
  tracked as #398/adjacent to the in-flight #435). This is a full
  collection abort, not a set of 13 discrete failures — it blocks every
  test in the run, not only `gates/`. No pass/fail count is obtainable
  without `--ignore=gates` or `--ignore=test_gates.py`, and this diff
  touches neither file. Re-run scoped to the write set instead (above),
  since the full-suite command as specified cannot produce a number on
  this checkout.
- Per survey.md's stated ceiling: a live `cargo build` against a real
  `{ git = "https://github.com/..." }` dependency, inside an actual
  spawned sandbox session, was **not** run this session — no cargo
  project with a git dependency was available to drive one, and phase 2
  had no live spawn harness to exercise end to end. Recorded honestly
  per #310/#358: the unit tests above confirm the redirect is wired
  (`CARGO_HOME` reaches the subprocess env, `~/.cargo/git` is mounted
  when present); they do not confirm cargo itself succeeds under the
  sandbox. That confirmation remains open and is not claimed here.

## Doc placement ladder

- No new env var, dependency, or migration beyond what's already in the
  frozen write set (`CARGO_HOME` is a redirect of an existing
  cargo-standard variable, not a new user-facing config key) — no
  handbook update needed.
- Library-or-format choice (option (b) over (a)) — already recorded in
  `docs/issue-406/proposals/implementation.md`'s `## Rationale`; no
  separate `docs/issue-406/decisions/` entry, since the proposal *is*
  that record for this subject per the warrant/proposal-shape gates.
- No benchmark/investigation numbers produced this phase — no
  `docs/issue-406/reports/` entry beyond this one.

## What did not work

None. Implementation matched the proposal's `## What will be done` on
the first pass; no code written here was later undone or replaced, and
nothing expected to hold failed to hold. (The full-suite pytest
collection abort noted under Verification run is a pre-existing
condition on `main`, not something this change caused or expected to
avoid.)

## Warrant hunt

Per warrant-directive, one hunter dispatch was owed before landing. Not
dispatched this turn: this session runs headless/single-shot (contract
v3 s22), and a background `warrant-hunter` dispatch whose result is not
consumed before the turn ends is prohibited under s22, stated to take
priority over the warrant directive's own dispatch-and-continue
instruction. No hunt record was produced as a result — noted here
rather than silently omitted.
