---
code_under_review:
  - gates/gates.py
  - gates/claims.py
  - gates/test_duplicate_test_basenames.py
  - gates/test_capability_gates.py
  - gates/test_claims.py
loop_state: landed
---

# issue-529 implementation record

## What was done

Executed the approved phase-1 proposal
(`docs/issue-529/proposals/2026-08-09-exclude-gitignored-paths-from-tree-scanning-gates.md`)
after `APPROVE issue-529/implementation` (single-account mode, `JiwonJung94`
in `docs/specs/approvers.md`):

- `gates/gates.py`: added `_excluded_tree_dirs(root)` (reads `root/.gitignore`,
  extracts top-level directory entries, always includes `.git`; falls back to
  `{".git"}` when no `.gitignore` exists) and `_prune_excluded(dirnames,
  excluded)`.
  - `duplicate_test_basenames`: its `.git`-only prune line now uses
    `_prune_excluded` with the derived exclusion set. Satisfies Acceptance
    clause 1 (gate exclusion) and part of Requirement 1.
  - `schema_field_orphans`: replaced the two `root.rglob(...)` calls with an
    `os.walk`-based collection so pruning happens during descent, then
    applied `_prune_excluded` the same way. Satisfies Requirement 1 for the
    second named gate.
- `gates/claims.py`: `_check_producer_exists`'s `repo.rglob(filename)`
  replaced with the same `os.walk` + `gates._prune_excluded`/
  `gates._excluded_tree_dirs` treatment. Satisfies Requirement 2 (audit —
  found and fixed the same contamination class in `producer-exists`).
- `gates/record_lint.py`'s `find_records` audited, left unchanged: its output
  is scoped through `RECORD_PATH.match` (`docs/issue-*/reports/*.md`), a
  pattern `runs/` content cannot match — not in this contamination class, as
  stated in the proposal's "What will be done".
- New fixture tests, each asserting skip-inside-`runs/`,
  still-caught-outside-`runs/`, and no-`runs/`-dir identical behavior:
  - `gates/test_duplicate_test_basenames.py`:
    `t_duplicate_test_basenames_skips_gitignored_runs_dir`,
    `t_duplicate_test_basenames_still_catches_collision_outside_runs`,
    `t_duplicate_test_basenames_no_runs_dir_behaves_identically`.
  - `gates/test_capability_gates.py`:
    `t_schema_field_orphans_ignores_reader_under_gitignored_runs_dir` (both
    skip-inside and still-caught-outside asserted in one test, mirroring the
    read-elsewhere/producer-only shape of the existing fixtures),
    `t_schema_field_orphans_no_runs_dir_behaves_identically`.
  - `gates/test_claims.py`:
    `t_producer_exists_ignores_gitignored_runs_dir`,
    `t_producer_exists_no_runs_dir_behaves_identically`.

## Acceptance clauses, mapped to fulfilling commit/hunk

- check: `python3 -m pytest gates/ -q` exits 0 on the live marketplace repo
  WITH `runs/rulebooks/` checkouts present (fixture test simulates a
  populated runs/ dir) — fulfilled by `gates/gates.py`'s
  `_excluded_tree_dirs`/`_prune_excluded` pair and their use in
  `duplicate_test_basenames`/`schema_field_orphans`. Confirmed by running
  `python3 -m pytest gates/ -q` (246 passed) both on a clean checkout and
  after manually populating `runs/rulebooks/fake-session/` with a duplicate
  test basename and an orphan-schema-satisfying reader file (removed after
  the run, never committed) — same 246 passed in both cases.
- check: a pytest fixture creating a fake gitignored duplicate under a temp
  `runs/` shows the gates skipping it, and the same file outside `runs/`
  still being caught — fulfilled by
  `t_duplicate_test_basenames_skips_gitignored_runs_dir` +
  `t_duplicate_test_basenames_still_catches_collision_outside_runs`
  (`gates/test_duplicate_test_basenames.py`),
  `t_schema_field_orphans_ignores_reader_under_gitignored_runs_dir`
  (`gates/test_capability_gates.py`), and
  `t_producer_exists_ignores_gitignored_runs_dir`
  (`gates/test_claims.py`).
- provenance: executed-unit — satisfied by the `python3 -m pytest gates/ -q`
  run reported above (actual execution, not a claimed run).
- empty state: a repo with no `runs/` dir passes identically, asserted by
  the same fixture test — fulfilled by
  `t_duplicate_test_basenames_no_runs_dir_behaves_identically`,
  `t_schema_field_orphans_no_runs_dir_behaves_identically`, and
  `t_producer_exists_no_runs_dir_behaves_identically`.

## What did not work

None — no attempt was undone or replaced during this build.

## Why

Bug in the acceptance-critical path itself: tree-scanning gates lied on the
live repo (false failures on a passing tree) because they walked gitignored
`runs/rulebooks/` session checkouts. Fixing the walkers to exclude
gitignored paths, derived from `.gitignore` rather than hand-picked, closes
the gap without breaking the non-git unit-test fixtures the same gates
already depend on.

## Upstream basis

`docs/issue-529/proposals/2026-08-09-exclude-gitignored-paths-from-tree-scanning-gates.md`,
approved via issue comment `APPROVE issue-529/implementation`.

## Open findings

None open. The post-proposal warrant hunt (recorded during phase 1, see
`docs/issue-529/proposals/2026-08-09-exclude-gitignored-paths-from-tree-scanning-gates.md`'s
Rationale) already fed into this build: it caught that a fixed exclusion
list would have omitted `.reexecution/`, which is why the chosen mechanism
derives the exclusion set from `.gitignore` instead.
