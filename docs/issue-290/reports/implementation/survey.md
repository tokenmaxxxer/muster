# Survey — issue #290 (+ #294, same working system)

Scout skip: spec leaves no design decision open. Both issues state the
exact defect, the exact fix direction, and explicit acceptance criteria
(the reporting user already root-caused each item). No exemplar-scouting
question exists here — this is confirming/reproducing named defects and
applying the named fix pattern.

## Write set (confirmed by reading, not assumed)

- `.github/workflows/on-the-record-tests.yml` (new) — CI workflow running
  `pytest -q` (and `gates/test_closes_gate_ci.py`, already covered by
  pytest discovery) on the PR head, per `pytest.ini`
  (`python_functions = test_* t_*`).
- `test_approve_scope.py` — `test_matching_approver_writes_scope_approved`
  (line 57) and `test_failed_commit_rolls_back_and_does_not_fake_success`
  (line 98, "L:98" in the issue = this test's `fake_run` block) both do
  `spawn.subprocess.run = fake_run` with no teardown. `spawn.subprocess`
  is the real stdlib `subprocess` module object (confirmed: `spawn.py`
  does `import subprocess`), so this mutates it process-globally for the
  rest of the interpreter — any test after these in a combined run gets
  the stub. `test_spawn.py` already uses `unittest.mock.patch("spawn.subprocess.run", ...)`
  as a context manager (lines 267, 293) — the house pattern to copy.
- `test_gates.py:99` — `assert "커밋안됨" not in v or True` is tautological
  (`or True` makes it always pass regardless of the left operand).
- `on-the-record/commands/run.md` lines 229-230 — the acceptance step is
  literally `gh pr merge <n> --merge --delete-branch` with no check-read
  step before it.

## Confirmed reproduction

- `test_spawn.py` shows the correct pattern already in-repo
  (`mock.patch("spawn.subprocess.run")`, `mock.patch.object(spawn, ...)`),
  so the fix is "use the pattern that already exists here," not a new
  design.
- `.github/workflows/` contains only `plan-aware-closes-gate.yml`, which
  checks out `ref: main` (by design, for its own closes-only trust
  boundary — documented in its header comment) and only runs
  `gates/ci.py --closes-only`. It does not run `pytest` and is not a
  substitute — confirmed by reading the file. No other workflow exists in
  this repo (`find` for `*.yml` under `.github` returned only this one
  file). Issue #290 says core/rulebooks also have zero workflows; those
  are separate repos out of this write set (see Out of scope in the
  proposal).

## Out-of-tree scope noted but not owned here

Core repo and the 43 rulebook repos (T4's other half, and #291) are
separate repositories not checked out in this workspace — not part of
this proposal's write set. This proposal covers exactly the on-the-record
repo (T1, T2, T4-for-this-repo) plus the run.md acceptance-step wording
(#294), which is what was assigned.
