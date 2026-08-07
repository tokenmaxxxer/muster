---
status: proposed
files:
  - gates/test_gates.py
  - gates/test_orphaned_references.py
  - gates/gates.py
  - gates/test_closes_gate_ci.py
  - test_gates.py
  - docs/issue-398/reports/implementation.md
---

## Request

`main` cannot collect its test suite: `gates/test_gates.py` (added by #330/PR
#337) and the root `test_gates.py` both resolve to pytest module name
`test_gates` (no `__init__.py` anywhere), so `pytest -q` errors out at
collection with zero tests run. Fix the collision, add a mechanical check
that catches this shape (duplicate test-module basename, no package
boundary) before merge, and state whether the "nothing runs the suite
pre-merge" gap is closed by this issue or tracked elsewhere.

## Constraints

- `gates/*.py` modules import each other via `sys.path.insert` + bare
  `import <name>` (no package-relative imports anywhere in the repo) — the
  fix must not change that convention.
- `python3 gates/test_gates.py` and `python3 test_gates.py` must keep working
  as standalone entry points (both files document this in their own
  docstrings).
- The new check must be able to fail on the collision shape *before* a merge
  happens — a file-tree-only check, not something needing the merged tree to
  exist (per the issue: "mechanically checkable from the file tree alone and
  does not need the merge to have happened").

## Rationale

Considered adding `gates/__init__.py` instead of renaming (survey.md,
"Alternatives considered", option 2). Rejected: it does resolve the basename
collision (pytest's `prepend` import mode would then key
`gates/test_gates.py` as `gates.test_gates`), but every `gates/*.py` test
file reaches its neighbor modules via
`sys.path.insert(...); import gates` (bare name), intending the *module*
`gates/gates.py`. Once `gates/` is a package and the repo root is also on
`sys.path` (which it is, from the root `test_gates.py`'s own
`sys.path.insert`), `import gates` would silently resolve to the *package*
`gates/` ahead of the module `gates/gates.py` on a later path entry —
breaking every `import gates` call in the suite. Renaming carries none of
that risk and matches the precedent already set by
`gates/test_closes_gate_ci.py`, itself renamed away from `test_gates.py` for
exactly this kind of reason (see its docstring, from #245/#271).

Also considered `pytest --import-mode=importlib` (survey.md, option 3) as a
global fix. Rejected as primary: it changes import semantics for every test
file in the repo, not just this collision, and it doesn't produce a check
that *fails* on the collision shape — it makes the shape stop mattering,
which does not satisfy the issue's acceptance criterion for a mechanical
check that goes red when the collision is reintroduced.

## What will be done

1. Rename `gates/test_gates.py` → `gates/test_orphaned_references.py`
   (matches its own docstring: "orphaned_references/reach_check 단위 테스트").
   Update its module docstring's run command and any cross-references
   (`gates/test_closes_gate_ci.py`, `gates/gates.py`, root `test_gates.py`,
   handbook/report text) that name the old path.
2. Add a check to `gates/gates.py` — mirroring the existing gate-function
   pattern (e.g. `orphaned_references`, `reach_check`) — that walks the repo
   tree, collects every `test_*.py`/`*_test.py` basename per directory that
   lacks `__init__.py` (i.e., every directory pytest would treat as
   contributing to the top-level, unqualified module namespace), and fails
   when the same basename appears under two such directories. Wire it into
   the gate the same way other structural checks are wired (see `gates.py`
   for the existing convention) so it runs pre-merge.
3. Add a test for the new check in `gates/test_gates.py` (the file this
   proposal keeps at that name — the CI-hygiene test file, not the renamed
   one) that reintroduces the collision shape in a temp directory tree and
   asserts the check goes red, and a companion case that asserts it passes
   on the current (post-rename) tree.
4. Confirm `python3 -m pytest -q` collects and passes on the resulting tree;
   report the count in the delivery report.
5. State plainly in the phase-2 delivery report whether item 3 (pre-merge
   suite gap) is closed by this issue: it is not — #290's phase-1 proposal
   PR (#295) is open and awaiting approval, phase 2 (actual CI wiring) has
   not started. Also state the #323/#324 finding from survey.md: their
   mechanism is scoped to file-*path* overlap and does not cover this
   file-*name* collision shape; extending them is out of scope here.

## Out of scope

- Building #290's CI job itself (tracked there, not here).
- Extending #323/#324's conflict-detection methodology to add the
  module-name dimension (flagged as a finding for those issues, not
  implemented here).
- `pytest --import-mode=importlib` or any other global import-mode change.
- Any other structural lint beyond the specific duplicate-test-basename
  shape named in the issue.

## How you'll know it worked

- `python3 -m pytest -q` on the resulting tree collects and passes; the
  delivery report states the count.
- The new check, run against a tree with the collision artificially
  reintroduced, fails; run against the current tree, passes. Both
  demonstrated with an actual test in `gates/test_gates.py`.
- The delivery report states plainly whether the pre-merge suite gap (item 3)
  is closed by this issue (it is not) and names what it's waiting on (#290 /
  PR #295 approval).
