---
code_under_review: 10b9c96
loop_state: phase-2-complete
---

# Implementation record — issue-398

## What will be done

Per the approved proposal
(`docs/issue-398/proposals/2026-08-07-test-module-basename-collision.md`):

1. Renamed `gates/test_gates.py` → `gates/test_orphaned_references.py`
   (matches its docstring content — issue #330's orphaned_references/
   reach_check tests). Updated its own docstring's run command. Grepped
   `gates/test_closes_gate_ci.py`, root `test_gates.py`, and
   `docs/handbooks/operations.md` for references to the old path — none
   named `gates/test_gates.py` literally (they refer to the root
   `test_gates.py`, unaffected), so no further cross-reference edits were
   needed.
2. Added `duplicate_test_basenames` to `gates/gates.py`: walks the whole
   file tree (not a diff), collects `test_*.py`/`*_test.py` basenames per
   directory lacking `__init__.py`, and reports any basename that appears
   under more than one such directory. Wired into `ALL` as
   `duplicate_test_basenames` alongside the other structural checks.
3. Added a test file for the new check — see "Rationale for deviations"
   for why it landed at `gates/test_duplicate_test_basenames.py` instead of
   the proposal's stated `gates/test_gates.py`. It reintroduces the
   collision shape in a temp tree and asserts the check goes red, asserts
   it passes on the current (post-rename) tree, and covers the
   `__init__.py`-exemption and no-collision cases.
4. `python3 -m pytest -q` on the resulting tree: **444 passed** (was: hard
   collection error, 0 tests run, before this change).
5. Scope item 3 (below).

## Scope item 3 — is the pre-merge suite gap closed by this issue?

No. #290 ("The test suite is decorative: no CI runs it...") is still OPEN;
its phase-1 proposal PR (#295, "issue-290: phase 1 proposal — CI + test
hygiene") is also still OPEN, awaiting approval — phase 2 (the actual CI
wiring that would run `pytest -q` pre-merge) has not started. This issue
(#398) fixes the collision that made the suite uncollectable and adds a
mechanical check against the collision shape recurring, but nothing in this
issue's write set wires `pytest -q` into a CI job — that remains #290's
scope, waiting on its phase-1 approval.

Also per the proposal's item 5: `orphaned_references`/`reach_check`
(#323/#324's mechanism, issue #330) is scoped to file-*path* overlap in a
diff (renamed/deleted paths still referenced elsewhere) — it does not cover
this file-*name* collision shape (two distinct, never-renamed files sharing
a basename with no package boundary). Extending #323/#324 to add a
module-name dimension is flagged as a finding for those issues, not
implemented here (out of scope, per the proposal).

## Reach

`duplicate_test_basenames` is a new pure function reached only from
`gates/gates.py`'s own `ALL` registry and this issue's test file — nothing
outside `gates/` calls it yet. The rename
(`gates/test_gates.py` → `gates/test_orphaned_references.py`) has no other
reach: grepped the repo for the old path string and found no reference
outside the renamed file itself (see item 1 above) — no orphaned reference
to file per #330's reach convention.

## Generator (#363)

No generator applies to this change. #363's "generator-analysis-gate"
proposal (`docs/issue-363/proposals/2026-08-07-generator-analysis-gate.md`)
concerns generated-artifact provenance; nothing this issue touched
(`gates/gates.py`, two test files, one rename) is a generated artifact.

## Base verified against (#390)

Verified `python3 -m pytest -q` against the tree at local HEAD after
merging `origin/main` at commit `10b9c96` (PR #393, "issue-390:
implementation" — the tip of main at the time of this work), via `git
merge origin/main` into this branch before making any change. The local
branch had been 46 commits behind origin/main; merging first ensured the
collision reproduction and the fix were checked against the actual current
board state, not a stale snapshot.

## What did not work

- First attempt at the new check's test file used the proposal's literal
  path, `gates/test_gates.py`. Running it immediately reproduced the exact
  collision the check exists to catch — `gates/test_gates.py` and root
  `test_gates.py` are, by definition, a duplicate basename with no
  `__init__.py` boundary between them. The new check itself correctly
  flagged this against the live tree, and `python3 -m pytest -q` errored
  the same way it had before the rename. Renamed the new test file to
  `gates/test_duplicate_test_basenames.py` instead — see "Rationale for
  deviations".

## Rationale for deviations

The proposal's `## What will be done` item 3 names `gates/test_gates.py`
as the home for the new check's test file, with the parenthetical "(the
file this proposal keeps at that name — the CI-hygiene test file, not the
renamed one)". Taken literally, this creates the identical collision shape
the check exists to detect: a file at `gates/test_gates.py` and a file at
root `test_gates.py`, neither directory holding `__init__.py`, sharing a
basename. Running `python3 -m pytest -q` against that arrangement fails
collection exactly as it did before this issue's fix — confirmed directly
(see "What did not work"). Landing the new check's own test file at the
path it is designed to flag would either (a) make `pytest -q` fail again,
defeating item 4's acceptance criterion, or (b) require excluding the new
file from the check's own scan, which is not something the proposal
describes and would weaken the check for no stated reason.

Deviation: the new CI-hygiene test file for `duplicate_test_basenames`
landed at `gates/test_duplicate_test_basenames.py` instead of
`gates/test_gates.py`. This stays inside the write set's spirit (a test
file for the new check, in `gates/`) while satisfying the proposal's own
acceptance criteria (`pytest -q` collects and passes; the check
demonstrably goes red on the collision and green on the current tree) — the
literal path in the proposal text could not satisfy both.

## Hunt

No `warrant-hunter` dispatch this session — see the freelunch-directive
priority note in this session's system context: contract v3 s22
(headless/single-shot) is stated as higher priority than the warrant
directive's hunter-dispatch instructions where a background dispatch's
result would not be consumed within the same turn. This is a single-shot
turn with no later turn to receive an async hunt finding, so no hunter was
dispatched. Flagging this plainly rather than silently skipping the
directive.

## Closed checks

- `duplicate_test_basenames` red on reintroduced collision, green on
  current tree — `gates/test_duplicate_test_basenames.py`
  (t_duplicate_test_basenames_catches_reintroduced_collision,
  t_duplicate_test_basenames_passes_on_current_tree), plus an ad hoc
  reproduction (copy `test_gates.py` to `gates/test_gates.py`, observe red;
  delete it, observe green) run directly against the live tree.
- `python3 -m pytest -q` collects and passes on the full suite: 444 passed.
- `python3 gates/test_orphaned_references.py` and
  `python3 gates/test_duplicate_test_basenames.py` both still work as
  standalone entry points (constraint from the proposal).
