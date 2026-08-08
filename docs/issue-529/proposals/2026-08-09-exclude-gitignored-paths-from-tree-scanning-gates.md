---
status: proposed
files:
  - gates/gates.py
  - gates/claims.py
  - gates/test_duplicate_test_basenames.py
  - gates/test_capability_gates.py
  - gates/test_claims.py
---

## Request

Tree-scanning gates (`duplicate_test_basenames`, `schema_field_orphans`) walk the raw filesystem and pick up gitignored session checkouts under `runs/rulebooks/` on the live repo, producing false failures/flaky verdicts that a clean checkout doesn't reproduce. Fix the walkers to exclude gitignored paths (at minimum `runs/`), and audit the rest of `gates/` for the same contamination class.

## Constraints

- `gates/test_capability_gates.py`'s two `schema_field_orphans` tests and all four of `gates/test_duplicate_test_basenames.py`'s tests build plain `tempfile.TemporaryDirectory()` fixtures with no git repo — the fix must not require these to become git repos to keep passing.
- Acceptance (issue #529) requires: `pytest gates/ -q` exits 0 on the live repo with `runs/rulebooks/` populated; a fixture proving the gate skips a fake duplicate/orphan planted under a temp `runs/` while still catching the same shape outside `runs/`; an empty-state fixture (no `runs/`) passing identically; provenance `executed-unit`.

## Rationale

Considered a git-ls-files-based rewrite of both gates, mirroring `subprocess_call_shape_divergence` (`gates/gates.py:1002`), which already solves this correctly for arbitrary `.gitignore` entries by enumerating tracked files through `git ls-files` instead of walking the filesystem. Rejected as the primary fix: both target gates' existing unit tests construct plain non-git tempdirs and call the gate functions directly (confirmed — no `git init` anywhere in `test_duplicate_test_basenames.py`, and `t_schema_field_orphans_*` in `test_capability_gates.py` use bare `tempfile.TemporaryDirectory()`); a pure git-ls-files rewrite would make `git ls-files` fail/return empty against those fixtures, silently breaking 6 existing passing tests to fix a gap the issue's acceptance criteria don't actually require (the acceptance fixtures test a fake `runs/` dir under a real or simulated tree, not arbitrary `.gitignore` coverage).

Chosen instead: directory-name exclusion pruned during the walk itself, with the exclusion set *derived from the repo's actual `.gitignore`* (its top-level entries, e.g. `runs/`, `.reexecution/`, `__pycache__/`) rather than hand-picked — a hardcoded guess risks silently missing a real gitignored directory `.gitignore` already names (confirmed during the post-proposal warrant hunt: a first draft of this proposal's fixed list omitted `.reexecution/`, which is in the live `.gitignore` and would have kept contaminating the walk after the fix shipped). This stays a no-git-dependency-for-tests mechanism — the `.gitignore` file is read directly, not through `git` — so it satisfies the issue's literal minimum ("exclude gitignored paths (at minimum `runs/`)") without touching the non-git fixtures, and self-updates when `.gitignore` gains a new top-level entry instead of requiring a matching manual edit every time. This is the same shape `os.walk`'s existing `.git`-pruning line already uses in `duplicate_test_basenames` — extending that line's exclusion set, not replacing its mechanism.

## What will be done

- `gates/gates.py`: add a shared `_excluded_tree_dirs(root)` helper that reads `root/.gitignore` (when present) and extracts its top-level directory entries (lines ending in `/`, stripped of the trailing slash and any leading `/`) into a set, always including `.git`; falls back to `{".git"}` alone when no `.gitignore` exists (matching current non-git tempdir fixtures, which have no `.gitignore` and no `runs/`, so behavior there is unchanged). Add a `_prune_excluded(dirnames, excluded)` helper built on that set.
  - `duplicate_test_basenames`: replace its `.git`-only prune line with `_prune_excluded`.
  - `schema_field_orphans`: replace the two `root.rglob(...)` calls with an `os.walk`-based collection so directory pruning applies during the walk (current post-hoc `.git`-only filter on `rglob` results can't prune before descending); apply `_prune_excluded` the same way.
- `gates/claims.py`: `_check_producer_exists`'s `repo.rglob(filename)` gets the same `_prune_excluded`-based `os.walk` treatment (via a small local helper or importing `gates`'s) so a copy under `runs/` can't satisfy `producer-exists` — closing the false-pass variant of this class per the issue's audit requirement.
- `gates/record_lint.py`'s `find_records` is audited and left unchanged: its output already passes through `RECORD_PATH.match` scoped to `docs/issue-*/reports/*.md`, a pattern `runs/` content structurally cannot match, so it's not in this contamination class; this will be stated in the record rather than silently skipped.
- New tests in `gates/test_duplicate_test_basenames.py`, `gates/test_capability_gates.py`, and `gates/test_claims.py`: for each of the three fixed gates, a fixture that plants a colliding/orphaned/faked-producer file under a `runs/` subdirectory of the tree and asserts (a) it's skipped, (b) the same shape placed outside `runs/` is still caught, and (c) a tree with no `runs/` dir at all behaves identically to today.
- Run `python3 -m pytest gates/ -q` once after the change and report the actual exit code/count.

## Out of scope

- Rewriting `duplicate_test_basenames`/`schema_field_orphans` onto `git ls-files` (alternative A) — left as a possible follow-up issue if full arbitrary-`.gitignore` coverage is later wanted; not needed to satisfy #529's acceptance criteria.
- Any change to `subprocess_call_shape_divergence` or `record_lint.py` — audited, found not to need a fix (see Rationale/What will be done).
- Any change to CI wiring, `.gitignore` itself, or how `runs/` is created/populated.
- Nested/wildcard `.gitignore` patterns beyond simple top-level directory entries (e.g. `**/*.log`, negated patterns) — only top-level directory names are parsed out for exclusion; full gitignore-pattern semantics is what alternative A (`git ls-files`) would cover, and is out of scope per the Rationale.

## How you'll know it worked

- `python3 -m pytest gates/ -q` run against a fixture-populated `runs/rulebooks/` directory exits 0.
- The three new fixture tests (duplicate-basename, schema-orphan, producer-exists) each assert: skip-inside-`runs/`, still-caught-outside-`runs/`, and identical behavior with no `runs/` dir present.
