files:
- spawn.py (clean role handler, ~lines 2137-2180)
- test_spawn.py (new regression tests)

## Request

`spawn.py clean` deletes workspaces it already judged safe (no uncommitted
changes, no unpushed commits) via `shutil.rmtree`. When a workspace
contains read-only files (e.g. Go module cache under `.muster-cache/gomod`,
which `go mod download` lays down without write permission), `rmtree`
raises an unhandled `PermissionError` that kills the whole `clean` run,
leaving every later-sorted workspace unswept. Fix `rmtree` to retry after
chmod'ing offending paths writable, and isolate per-workspace failures so
one workspace's failure never stops the rest of the sweep.

## Constraints

- Pure bugfix per the issue; skip condition applies (see survey.md) — no
  scouting run, no design decision to weigh beyond an alternatives note.
- No new dependency, no env var, no schema/interface change.
- Must not weaken the existing safety judgment (uncommitted/unpushed
  check) — only the removal step changes.

## Rationale

Chose the stdlib `onexc`/`onerror` chmod-retry callback for `rmtree`
(Python's own documented pattern for this exact failure) over shelling
out to `rm -rf`. `rm -rf` would also survive read-only files (unlinking
only needs write permission on the parent directory on POSIX), but it
adds a platform dependency `spawn.py` doesn't otherwise have (no `rm` on
Windows) and turns a catchable Python exception into subprocess
exit-code/stderr parsing — that's strictly worse for the second half of
the fix, per-workspace failure isolation, which needs a catchable
exception to wrap in `try/except`. Rejected `rm -rf` for that reason.

## What will be done

- In the `clean` role handler (spawn.py:2137-2180), replace the bare
  `shutil.rmtree(w)` call with a version that passes an `onexc` (Python
  3.12+) or `onerror` (earlier) handler: on `PermissionError`, `os.chmod`
  the failing path to add write permission, then retry the original
  operation. Select handler kwarg by `sys.version_info` since
  `shutil.rmtree` rejects an unsupported kwarg with `TypeError`.
- Wrap the per-workspace removal body (the `rmtree` call plus the
  sibling-file glob/unlink loop) in `try/except Exception`, so a failure
  that survives the chmod retry is caught, printed as a kept/failed
  workspace (not silently swallowed), and the loop moves to the next
  workspace instead of aborting. Update the final `kept`/`removed` tally
  to reflect this (or add a `failed` counter) so the summary line stays
  accurate.
- Add regression tests to `test_spawn.py` covering: (1) a safe workspace
  containing a read-only file is fully removed by `clean` (chmod-retry
  path exercised); (2) a workspace whose removal fails even after retry
  does not abort processing of subsequent workspaces (failure isolation).

## Out of scope

- Changing the safety judgment (git status/log checks) that decides which
  workspaces are eligible for removal.
- Any change to other `spawn.py` roles or files outside the `clean`
  handler and its tests.
- Cross-platform (Windows) read-only handling beyond what `os.chmod` +
  stdlib `rmtree` already provide.

## How you'll know it worked

- New tests in `test_spawn.py` pass: a workspace with a read-only file is
  removed without raising, and a workspace that fails removal doesn't
  block cleanup of the rest.
- Full `python -m unittest test_spawn.py` (or equivalent existing test
  invocation) passes with no regressions in other `clean`-adjacent
  behavior (kept-workspace logging, tally line).
- Manual reasoning check: re-reading the fixed handler confirms no
  workspace's exception can escape the per-iteration `try/except`.
