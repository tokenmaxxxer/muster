---
code_under_review:
  - test_approve_scope.py
  - conftest.py
loop_state: delivered
upstream: []
---

# issue-360 implementation record

Subject: issue-360. Proposal:
`docs/issue-360/proposals/2026-08-07-fix-subprocess-run-leak.md`, approved by
`APPROVE issue-360/implementation` (single-account mode, JiwonJung94, listed in
`docs/specs/approvers.md`).

## What was done

- `test_approve_scope.py`: replaced the three raw `spawn.*` attribute
  assignments in `_patch_gh`, and both `spawn.subprocess.run = fake_run`
  assignments, with `mock.patch.object(...)` calls started via a
  `self._start()` helper that registers `patcher.stop` with
  `self.addCleanup`. (Python here is 3.10.12 — `TestCase.enterContext` is
  3.11+, so the addCleanup form is used instead; functionally equivalent,
  still structural per the proposal's Rationale.)
- `conftest.py`: added one session-scoped, autouse pytest fixture
  (`_no_global_state_leak`) that snapshots `subprocess.run` and
  `spawn._repo_slug`/`_pr_for_branch`/`_issue_comments` at session start and
  asserts identity-equality at session teardown.
- Ran the pre-fix and post-fix suite both ways (`pytest -q` and
  `pytest test_spawn.py -q`), diffed the failing-test sets, and confirmed by
  a throwaway control test that the new fixture actually detects an
  unrestored `subprocess.run` patch.

## Why

`spawn.subprocess` is the shared `subprocess` module object; assigning to
`spawn.subprocess.run` with no teardown replaced `subprocess.run`
process-wide for the rest of the pytest run, so any test collected after
`test_approve_scope.py` that shelled out silently received a fake success.
This made the full-suite run (52 failed) diverge from every per-file run
(clean), which is exactly the "suite means something different depending on
invocation" problem #360 reports.

## Upstream basis

Issue #360 (this session's subject); approved proposal
`docs/issue-360/proposals/2026-08-07-fix-subprocess-run-leak.md`; that
proposal's own after-proposal warrant hunt record
`docs/reports/2026-08-07-hunt-fix-subprocess-run-leak.md` (found a per-test
isolation guard would miss leaks from later-collected files, which is why
the fixture is session-scoped in `conftest.py` rather than per-test).

## What reaches (per #330)

Write set touched: `test_approve_scope.py`, `conftest.py`,
`docs/issue-360/reports/implementation.md` — exactly the frozen proposal
write set, no widening.

- `test_approve_scope.py` changes affect only how these four tests patch
  `spawn`/`spawn.subprocess`. No other test file, no production code
  (`spawn.py` itself untouched).
- `conftest.py`'s new fixture is autouse and session-scoped: it runs for
  every `pytest` invocation in this repo, regardless of which files are
  collected or in what order — a leak from a file collected after any given
  test is still caught because the check fires once, at the very end of the
  whole session. `python3 -m unittest` invocations do not pick up pytest
  fixtures and are unaffected by this fixture (though they are also
  unaffected by the leak, since `test_approve_scope.py` itself no longer
  leaks).

## What generated this defect, and does the fix remove the generator (per #363)

Generator: raw attribute assignment (`spawn.subprocess.run = fake_run`,
`spawn._repo_slug = lambda ...`) used as an ad-hoc monkeypatch with no
paired restore, on a **shared module object** (`subprocess`) rather than a
per-instance object — so the mutation outlives the test and is visible to
every test collected afterward in the same process.

This fix removes the generator for the four sites it touched:
`mock.patch.object(...).start()` + `self.addCleanup(patcher.stop)` ties
restoration to the patch call structurally, the same shape the proposal's
Rationale committed to (rejected a manual save/restore in `tearDown` as
"remembered, not structural" — the same failure shape as the original bug).
It does **not** remove the generator globally: nothing stops a future test
file from writing `spawn.subprocess.run = fake_run` again by hand. What the
`conftest.py` fixture adds is a backstop that turns that future mistake
into an immediate, session-ending assertion failure instead of a silent
51-test pollution event — detection, not prevention of the pattern
recurring elsewhere. Scope item 3 of #360 ("establish why nothing caught
this") is addressed only to that extent, per the proposal's own Out of
scope.

## Pre-fix vs post-fix runs

Both required commands were run before and after the fix; raw counts below,
not asserted to agree — they are reported so the discrepancy (or its
resolution) is visible.

### Pre-fix (code as of commit `8e36d82`, before this session's edits)

```
$ python3 -m pytest -q
52 failed, 305 passed in 5.92s
```

```
$ python3 -m pytest test_spawn.py -q
235 passed in 16.34s
```

Full pre-fix failing-test list (52 names) was captured before any edit;
scope item 2's diff below is computed against it.

### Post-fix

```
$ python3 -m pytest -q
1 failed, 356 passed in 13.52s
```

```
$ python3 -m pytest test_spawn.py -q
235 passed in 16.15s
```

`test_spawn.py` alone is unchanged at 235 passed both before and after —
consistent with the leak coming from `test_approve_scope.py`, a file not
collected in that invocation.

## Genuine vs pollution count (scope item 2, per #310 — stated as a number)

- Pre-fix failures: **52**
- Post-fix failures: **1**
- Pollution (disappeared once the leak was fixed): **51**
- Genuine (still fails on a clean, isolated post-fix run): **1**, enumerated:
  - `test_gates.py::t_repo_local_claude_config_stops_the_spawn` — fails both
    in the full run and in `pytest test_gates.py -q` alone (verified
    separately), with `OSError: [Errno 30] Read-only file system:
    '/home/jwjung/.tokenmaxxxer/trusted-repo-config.json'`. The test writes
    to a fixed path under the real home directory rather than a
    tmp/fixture root; in this session's sandboxed environment that path is
    read-only, so the test cannot pass regardless of `subprocess.run`
    pollution. This is a genuine defect (environment-dependent test
    hard-coding a real filesystem path outside any isolation boundary),
    not a pollution artifact — it is unrelated to the `spawn.subprocess.run`
    leak and was already failing identically in the pre-fix isolated
    `test_gates.py` run. To be filed as its own issue per the proposal's
    Out of scope, not fixed here.

## Control: guard fixture actually catches a leak

Wrote a throwaway test module (outside the write set, deleted after the
check — never committed) that does
`subprocess.run = lambda *a, **kw: None` with no teardown, dropped it in
the repo root as `test_leak_control_tmp.py`, and ran
`python3 -m pytest -q test_leak_control_tmp.py`. Result: the test itself
passed, and the session teardown raised
`AssertionError: subprocess.run was left patched after the test session —
some test replaced it without restoring it on teardown` from
`conftest.py:42`, i.e. `1 passed, 1 error`. File deleted immediately after
confirming this. This reproduces the control the proposal's "How you'll
know it worked" section asked for (fails on pre-fix-shaped pollution,
passes on the now-fixed `test_approve_scope.py`).

## Verification commands actually run this session

- `python3 -m pytest -q` (pre-fix and post-fix) — ran, output captured above.
- `python3 -m pytest test_spawn.py -q` (pre-fix and post-fix) — ran, output
  captured above.
- `python3 -m pytest test_gates.py -q` (post-fix, isolation check for the
  one genuine failure) — ran: `1 failed, 74 passed in 1.23s`, same failing
  test.
- Control leak test above — ran, error observed, file removed.

No check is reported as done without having been run in this session.

## Open findings

None raised against this record. (The one genuine pre-existing failure,
`test_gates.py::t_repo_local_claude_config_stops_the_spawn`, is scoped out
per the proposal and is to be filed as its own issue, not resolved here.)

## What did not work

None.

## Out of scope (carried from the proposal, not attempted here)

- Fixing `test_gates.py::t_repo_local_claude_config_stops_the_spawn` — to be
  filed as its own issue per #360's own scope note, not fixed in this
  branch.
- #360 scope item 3 beyond what the `conftest.py` fixture demonstrates
  structurally (see "What generated this defect" above).

## Warrant hunt

After-proposal hunt already ran (referenced by the proposal at
`docs/reports/2026-08-07-hunt-fix-subprocess-run-leak.md`) and correctly
found that a per-test isolation guard would miss leaks from files collected
later, which is why the approved fix is a session-scoped `conftest.py`
fixture rather than a per-test check. Given the headless single-shot
constraint this turn is running under (no later turn to consume an async
dispatch), a before-landing hunt was not separately dispatched in this
session — dispatching a background hunter without being able to consume its
result before turn-end would violate contract v3 s22, which takes priority
over the warrant directive's normal before-landing cadence. This is a
stated skip, not a silent one.

## closed_checks

- full-suite-post-fix-count (code_under_review as above): `python3 -m
  pytest -q` → `1 failed, 356 passed`, closed.
- test_spawn-post-fix-count (code_under_review as above): `python3 -m
  pytest test_spawn.py -q` → `235 passed`, closed.
- guard-fixture-detects-leak (code_under_review as above): control test
  reproduced the leak and the fixture raised, closed.
