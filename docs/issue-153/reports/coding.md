# Coding record — issue-153

loop_state: landed

## code_under_review

- `spawn.py` — `role_settings()` allow-list block (formerly spawn.py:419-428)
- `test_spawn.py` — `WebToolPermissionAccess`

## What was done

Implemented the approved phase-1 proposal (`docs/issue-153/proposals/coding.md`,
approved via `APPROVE issue-153/coding` on issue #153):

- `role_settings()`'s existing `permissions.allow` loop (previously
  `WebSearch`/`WebFetch` only) extended to also append `Read`, `Grep`,
  `Glob`. Merge-not-replace semantics unchanged (same `setdefault` +
  `if tool not in allow` guard as the existing entries).
- Comment above the block updated to state the extended rationale: these
  are read-only tools; `sandbox.filesystem.allowRead/denyRead` still governs
  which paths are reachable, unchanged by this layer; `Bash` sub-patterns
  are explicitly excluded (cannot be scoped to read-only, per survey
  section 3).
- `test_spawn.py::WebToolPermissionAccess` gained
  `test_read_only_tools_allowed_for_every_role`, asserting `Read`/`Grep`/
  `Glob` are present in `role_settings(role)["permissions"]["allow"]` for
  every role file — same shape as the existing `WebSearch`/`WebFetch`
  assertion.

## Why

Issue #153: headless spawned sessions run `--permission-mode acceptEdits`
with no one to answer a permission prompt; legitimate read-only tool calls
outside the sandbox's known set were silently denied, burning turns on
retries. Same precedent and call site as the #58/#65 WebSearch/WebFetch
fix.

## Upstream basis

`docs/issue-153/proposals/coding.md` (frozen phase-1 proposal),
`docs/issue-153/reports/coding/survey.md` (phase-1 survey), approval
comment `APPROVE issue-153/coding` on issue #153.

## Out of scope (unchanged from proposal)

- `Bash`-invoked read-only patterns (`python3 -c`, `ugrep`, `rg`) — not
  allow-listed; needs its own evidence-backed follow-up if the sibling
  repo's logs confirm a real pattern.
- `sandbox.filesystem.*` boundaries and `write_scope` (#149) — untouched.

## Confirmation run

`python3 -m pytest test_spawn.py -k WebToolPermissionAccess -q` — 3 passed
(the 2 pre-existing web-tool tests + the new read-only-tools test).

## What did not work

Nothing — single-unit change, matched the frozen proposal exactly.

## closed_checks

- Merge-not-replace regression: `test_role_declared_permissions_allow_entries_preserved`
  (pre-existing, unmodified) still passes after the extension — confirms
  the new tools compose with a role's own declared `permissions.allow`
  entries rather than overwriting them. code_sha: this commit.

## open findings

None.
