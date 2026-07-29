# Coding record — issue-65

loop_state: landed

## What was done
- `spawn.py`: `role_settings()` (spawn.py:299) now merges `WebSearch` and
  `WebFetch` into `s["permissions"]["allow"]` for every role, additive and
  dedup-safe (same pattern as the existing `allowedDomains` merges above
  it), unconditional — not gated on `sandbox.enabled`, since this layer is
  a CLI permission rule, not a sandbox boundary.
- `test_spawn.py`: new `WebToolPermissionAccess` class —
  `test_web_tools_allowed_for_every_role` (all 9 `roles/*.json`, both
  tools present in composed `permissions.allow`) and
  `test_role_declared_permissions_allow_entries_preserved` (a role's own
  `permissions.allow` entries survive the merge, mirroring issue-38's
  registry-host preservation test).
- `README.md`: renamed the issue-58 section to "Web access (issues #58,
  #65)", split into the two independent gating layers — sandbox network
  (issue #58) and tool permission (issue #65) — explaining both must be
  open for a web tool call to succeed.

## Why
Upstream basis: issue #65 body (mechanism already diagnosed by the
reporter: two independent gates — #58 fixed the sandbox NETWORK layer,
the TOOL-PERMISSION layer stayed closed). Grepped all `roles/*.json`
before writing anything: none declared a `permissions` key, so under
`--permission-mode acceptEdits` (spawn.py:1252) with no human to answer a
prompt, `WebSearch`/`WebFetch` had no allow rule and were auto-denied —
exactly the symptom the issue reports (3/3 denials in the issue-63 log)
even after #58 landed. `role_settings()` was confirmed as the sole
settings-composition site by tracing it as the function issue-38/#58
already extend for the same purpose. Fix scope: all roles (same operator
decision as #58's "option B", issue doesn't call for a per-role opt-in).

## What did not work
First draft of `test_role_declared_permissions_allow_entries_preserved`
restored `roles/coding.json` via `json.dumps(spec)` in its `finally`
block instead of the original raw text — this silently reformats the file
(compact single-line JSON replacing the pretty-printed original), which
would have landed as an unrelated diff. Caught via `git status --short`
before commit; fixed to save/restore the exact original file text.

## Verification
```
$ python3 -m pytest test_spawn.py -q
......................................................                   [100%]
54 passed in 2.70s
```
54/54 pass (was 52 before this change; +2 new). Ran twice — second run
confirms no state leakage from the file-mutation test.

No live spawn probe (doctor-style, per the issue's "Verify with a cheap
live probe" suggestion) was run — that needs a running Claude Code
session with a role actually invoked, out of reach in this environment.
The acceptance criterion "a spawned role session executes a WebSearch
without a permission denial" is validated only at the
settings-composition level (unit test), not end-to-end — stating this
boundary explicitly rather than claiming more than was run.

## Closed checks
- closed_checks: web-tools-allowed-for-every-role (verified via
  `role_settings(role)` output for all 9 `roles/*.json`; both `WebSearch`
  and `WebFetch` present).
- closed_checks: role-declared-permissions-preserved (a role's own
  `permissions.allow` entries survive the merge, not overwritten).
- closed_checks: roles/coding.json byte-identical to pre-change state
  after the full test run (`git status --short` clean on that path).

## Hunt
warrant-hunter not dispatched this turn: the change is a single ~9-line
additive merge inside an already-covered composition function, directly
mirroring an existing, tested pattern (#38/#58's domain merge) in the
same function body — no new I/O, no new external call, no new state
beyond what the existing `role_settings()` test coverage already
exercises.

## Open findings
None.
