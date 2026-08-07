# Survey — issue-398

## Reproduction

```
$ python3 -m pytest -q
ERROR collecting test_gates.py
import file mismatch:
imported module 'test_gates' has this __file__ attribute:
  gates/test_gates.py
which is not the same as the test file we want to collect:
  test_gates.py
Interrupted: 1 error during collection
```
Confirmed: `test_gates.py` (1153 lines, root) and `gates/test_gates.py` (125 lines,
added by #330/PR #337) both resolve to pytest module name `test_gates`. Neither
`test_gates.py`'s directory (repo root) nor `gates/` has `__init__.py`, so
pytest's default (`prepend`) import mode uses the bare basename as the module
name — the first one collected wins, the second collides.

## Write surface

- `pytest.ini`: `python_functions = test_* t_*` — both `test_*` and `t_*` are
  collected as test functions repo-wide.
- `conftest.py` (root): session-scoped autouse fixture, no bearing on import mode.
- `gates/test_gates.py`: docstring says it can run standalone
  (`python3 gates/test_gates.py`) and uses `t_*`-prefixed functions, plus a
  `sys.path.insert(0, str(Path(__file__).parent)); import gates` hack to reach
  `gates/gates.py` when run directly or collected by pytest.
- `gates/test_closes_gate_ci.py` already exists as a second gates/-local test
  file and was deliberately given a name distinct from any root file — its own
  docstring (written for #245/#271) states the reason: that session's approved
  write set did not include the root `test_gates.py`, so a separate file was
  used. This is precedent for "rename to a distinct basename" as the accepted
  pattern in this repo, not a one-off.
- No file in `gates/` or at root is a package (no `__init__.py` anywhere in
  the repo).
- Every `gates/*.py` module reaches its siblings via `sys.path.insert` +
  bare `import <name>` (e.g. `import gates`, `import ci`, `import pr_reference`),
  never `from gates import ...` or `import gates.gates`. This is load-bearing:
  these modules are written to run directly (`python3 gates/foo.py`) and
  under pytest collection from the repo root, both without a package
  qualifier.

## Alternatives considered for the collision (scope item 1)

1. **Rename `gates/test_gates.py` to a distinct basename.** Zero risk to the
   sys.path-hack import style already used throughout `gates/`. Matches the
   precedent already set by `gates/test_closes_gate_ci.py`.
2. **Add `gates/__init__.py`.** Turns `gates/` into a package. Pytest's
   `prepend` import mode would then collect `gates/test_gates.py` as
   `gates.test_gates`, resolving the basename collision without a rename.
   BUT: `gates/test_gates.py` and `gates/test_closes_gate_ci.py` both do
   `sys.path.insert(0, str(Path(__file__).parent))` then `import gates`,
   intending to reach the *module* `gates/gates.py`. With `gates/__init__.py`
   present and the repo root also on `sys.path` (root's own `test_gates.py`
   inserts the root ahead of `gates/` on `sys.path`), `import gates` would
   resolve to the *package* `gates/` before reaching `gates/gates.py` on a
   later path entry — a silent name shadow that breaks every
   `import gates` call across the test suite. Rejected: fixes the collision
   but breaks the existing intra-`gates/` import convention.
3. **`pytest --import-mode=importlib`.** Removes sys.path-based module naming
   entirely (pytest docs: importlib mode keys modules by file path, not
   basename), so same-basename files never collide regardless of package
   boundary. Would also fix this instance. Rejected as the *primary* fix
   because it is a global pytest behavior change with broader blast radius
   (affects every test file's import semantics, not just this collision) and
   does not address scope item 2 — it makes same-basename files load
   successfully rather than making the shape mechanically detectable, which
   the issue explicitly asks for.

## Item 3 — pre-merge suite gap

`#290` ("the test suite is decorative: no CI runs it") has an open phase-1
proposal PR, **#295** (`docs/issue-290/proposals/2026-08-07-ci-and-test-hygiene.md`),
awaiting human approval — phase 2 (the actual CI wiring) has not started.
`closes-gate` (`gates/gates.py`) is confirmed `--closes-only` by design, no
test-running step. So: nothing currently runs the suite before merge: the gap
is real, tracked in #290, not closed here, and #290/#295 is what's waiting
(a human APPROVE on that PR).

## Item — #323/#324 mechanism fit

Read both issues in full. #323 is about **file-path** overlap between
concurrent PRs (two sessions editing the same file, or worktree merge
conflicts) — resolved, if at all, by diffing write sets. #324 is about
serialization of independent work, dependent on #323's methodology. Neither
issue's text mentions module identity or basename collision; both frame
"conflict" as literal file-path intersection. A collision between
`test_gates.py` and `gates/test_gates.py` has **no path overlap** — #323's
mechanism, as scoped, would not have caught it; it needs the module-name
dimension the issue calls out, which is not currently in #323/#324's scope.
