---
status: proposed
files:
  - spawn.py
  - test/test_silent_failure_repros.py
---

## Request

`issue_workspace()` in `spawn.py` wraps its `.git/info/exclude`
credential-leak-guard write in a bare `except OSError: pass`. When that
write fails, the returned workspace has none of the guard entries
(`.mcp.json`, `.gitconfig`, …) and nothing tells the caller. Make the
failure surface a warning naming the workspace and the skipped entries
(refusing the spawn is acceptable if judged safer, but not required), and
update the existing repro test to assert the fixed behavior instead of the
broken one. Pure bugfix — this is a skip condition under scout-directive
("the change is a pure bugfix"), so no scouting/exemplar sweep was run;
see `docs/issue-450/reports/implementation/survey.md`.

## Constraints

- Acceptance (from issue #450): with the exclude write forced to fail,
  spawn output names the failure and the affected entries; with the write
  succeeding, behavior is unchanged (`test/test_spawn.py` stays green).
- `test/test_silent_failure_repros.py::test_attempt_1_exclude_write_swallowed_no_warning`
  is the check: it must be updated to assert the surfaced warning (red
  today per the issue), not left broken/skipped.
- No new dependency, no new env var.

## Rationale

Considered `sys.exit(...)` (refuse the spawn outright) instead of a
non-fatal warning, since `issue_workspace()` already uses `sys.exit` for
other hard failures nearby (origin mismatch, clone failure — spawn.py:2949,
2957). Rejected: the exclude guard is defense-in-depth against an
accidental `git add -A` credential leak, not a correctness requirement for
the clone itself — refusing every spawn on a transient permission blip
(e.g. a momentarily read-only `.git/info/`) would turn a soft-fail-safe
guard into a hard availability dependency, which is a bigger behavior
change than the issue asks for. The issue's own Acceptance only requires
surfacing, and explicitly leaves "refuse" as an option, not a mandate.
A non-fatal `print(..., file=sys.stderr)` warning matches the convention
already used elsewhere in `spawn.py` for non-halting diagnostics, keeps
the workspace usable, and still makes the gap visible to the caller/CI
output — which is what the issue is actually asking to fix (silence, not
availability).

## What will be done

- In `issue_workspace()`, narrow the `except OSError: pass` around the
  exclude-guard write to catch and report: on failure, print a warning to
  stderr naming the workspace path and the exclude entries that were not
  written (the `missing` list, or the full guard `lines` list if the
  failure happened before `missing` could be computed), then continue
  (the function still returns the workspace, matching current
  non-fatal-on-clone-success behavior).
- Update
  `test_attempt_1_exclude_write_swallowed_no_warning` in
  `test/test_silent_failure_repros.py` to assert the warning is present in
  captured stderr (workspace path + at least one skipped entry name) and
  that `issue_workspace()` still returns a valid workspace path.

## Out of scope

- `_watch()` follow-loop, `doctor()` cost-per-spawn, and
  `gates/issue_bundling.py` enforcement — separate candidate gaps from the
  #445 hunt, not this issue.
- Refusing the spawn outright (`sys.exit`) — left as a documented
  rejected alternative above, not built.
- Any other bare/narrow `except` block in `spawn.py` beyond this one.
- Reuse-path guard re-checking: `issue_workspace()`'s two early-return
  reuse branches (`src == work.resolve()`, `(work / ".git").exists()`,
  around spawn.py:2929/2932) never reach the exclude-guard block at all —
  a workspace whose guard write failed once stays unguarded and unwarned
  on every later reused spawn for the same issue/role, even after the
  underlying write-permission problem is gone (after-proposal warrant hunt,
  `docs/reports/2026-08-08-hunt-surface-exclude-guard-write-failure.md`).
  Pre-existing behavior, unchanged by this fix either way, and outside
  issue #450's stated Acceptance (which only covers the fresh-clone write
  path). Flagged here, not built — a candidate for a follow-up issue.

## How you'll know it worked

- `test/test_silent_failure_repros.py::test_attempt_1_exclude_write_swallowed_no_warning`
  passes against the fixed code (asserts the warning, not its absence).
- `test/test_spawn.py` full suite stays green (happy-path behavior
  unchanged).
