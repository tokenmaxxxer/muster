---
code_under_review: 6fd3edc3bfb47c2afb24922a8faf44904a69af21
loop_state: phase-2-complete
---

# Implementation record — issue #229

Phase 2, executing the approved proposal (docs/issue-229/proposals/proposal.md,
approved via PR #230 issue-level comment `APPROVE issue-229/implementation`
from JiwonJung94, single-account mode, upstream basis for this build).

## What was done

- `spawn.py` clean handler: added `_chmod_retry(func, path, exc_info)`,
  passed as `onexc` (Python >=3.12) or wrapped for `onerror` (<3.12,
  selected via `sys.version_info`). On failure it chmods both the
  failing path and its parent directory writable (POSIX unlink/rmdir
  permission lives on the parent directory, not the file itself — the
  first test iteration proved this: chmod'ing only the file was not
  enough to reproduce/fix the real failure) and retries the operation.
- Wrapped the per-workspace `rmtree` + sibling-glob/unlink body in
  `try/except Exception`; a surviving failure is printed
  (`실패 (삭제 중 예외): ...`) and counted in a new `failed` tally,
  and the loop continues to the next workspace. Summary line now reads
  `정리 끝 — 지움 N, 남김 N[, 실패 N]`.
- Added `import stat` (new stdlib import, no new dependency).
- Added two regression tests to `test_spawn.py::Clean`:
  `test_readonly_file_is_removed_via_chmod_retry` and
  `test_failed_workspace_removal_does_not_abort_the_clean_loop`.

Why: `spawn.py clean` was dying with an unhandled `PermissionError` on
read-only files (e.g. Go module cache), aborting cleanup of all
later-sorted workspaces (issue #229).

## What will be done (from proposal)

- Replace bare `shutil.rmtree(w)` in the `clean` role handler (spawn.py
  clean block) with a chmod-retry `onexc`/`onerror` handler.
- Wrap per-workspace removal in `try/except` so one workspace's failure
  doesn't abort the sweep; add a `failed` counter to the summary line.
- Add regression tests to test_spawn.py: read-only file removed via
  chmod-retry; a failing workspace doesn't block subsequent removals.

## What did not work

- First cut of the read-only-file regression test chmod'd only the file
  to 0o444; `shutil.rmtree` still succeeded without error on this
  sandbox (unlink permission is governed by the parent directory on
  POSIX, not the file's own mode), so the test didn't reproduce the
  real bug. Switched to chmod'ing a containing directory to 0o555,
  matching how Go's module cache actually locks itself down — this
  reproduced the original `PermissionError`.
- That same directory-based repro then tripped the pre-existing
  git-status safety check (an untracked file inside the read-only-to-be
  directory made `git status --porcelain` non-empty, so `clean` judged
  the workspace unsafe and skipped it, keeping it instead of hitting
  `rmtree` at all). Fixed by committing the directory (via
  `.gitignore` + commit + push) before chmod'ing it read-only, matching
  the real-world case where the Go module cache is gitignored and
  never shows up in `git status`.
- The `_chmod_retry` handler's first version only chmod'd the failing
  `path` itself, matching the proposal's literal wording ("chmod'ing
  offending paths writable"). That alone did not fix the reproduced
  failure — the parent directory also had to be chmod'd, since POSIX
  file removal permission lives on the parent, not the file. Extended
  the handler to chmod both.

## Doc-placement ladder

- No new env var / config key / dependency / migration / setup step ->
  handbook entry not applicable.
- No library-or-format choice over a named alternative beyond what
  proposal.md's Rationale already recorded (stdlib onexc/onerror vs
  `rm -rf`) -> no additional docs/issue-229/decisions/ entry needed.
- No benchmark/investigation numbers produced -> no
  docs/issue-229/reports/ entry beyond this record.

## Hunt

Stance: adversarial-self (rotated). Probe: manually traced the
`try/except Exception` wrapping around the `rmtree` + sibling-unlink
body — confirmed no path from either can escape the per-iteration guard
and abort the `for w in ...` loop. Confirmed `_chmod_retry` is only
invoked by `shutil.rmtree`'s `onexc`/`onerror` machinery on an
exception raised during removal (any `Exception`, matching stdlib's own
contract, not narrowed to `PermissionError` — a deliberate choice: the
stdlib callback contract doesn't filter by exception type either, and
narrowing it here would just re-raise unhandled inside the callback for
every other case, which is equivalent to not handling it). Verified via
the two new tests: chmod-retry actually removes a read-only-directory
workspace (`test_readonly_file_is_removed_via_chmod_retry`), and a
workspace whose removal fails even after retry is isolated
(`test_failed_workspace_removal_does_not_abort_the_clean_loop`) while a
subsequent healthy workspace still gets removed.

closed_checks:
- name: rmtree-permission-retry
  code_sha: 6fd3edc3bfb47c2afb24922a8faf44904a69af21
- name: per-workspace-failure-isolation
  code_sha: 6fd3edc3bfb47c2afb24922a8faf44904a69af21

## Verification run

`python3 -m unittest test_spawn -v` — 162 tests, all passed (0
failures, 0 errors), including the 2 new `Clean` regression tests.

## Open findings

None outstanding.

## Next steps

None — commit, push to issue-229/implementation, done.

## Open-finding resolution path

No open findings to resolve; none outstanding.
