---
code_under_review: [spawn.py, test_spawn.py, tests/fixtures/rulebooks/tokenmaxxxer-core/.claude-plugin/marketplace.json]
loop_state: landed
---

# implementation record — issue-282

## Approval

PR #283 (single-account mode): issue comment `APPROVE issue-282/implementation` posted by
`JiwonJung94` (listed approver, same account as PR author). String-exact match confirmed.

## What was done

- Rewrote `core_plugin_dirs()` (`spawn.py`) to read `<core_root()>/.claude-plugin/marketplace.json`
  and iterate its `plugins` list (mirroring `plugin_dirs()`'s `source` resolution, restricted to
  the string `"./name"` form per the proposal's Out-of-scope), `sys.exit`-ing loudly, naming the
  plugin and the expected path, when a declared plugin's `plugin.json` is missing.
- Updated the spawn banner (`spawn.py`, `spawn()`) to name the attached core plugins instead of
  only a role-plugin count.
- Added two tests to `test_spawn.py`:
  - `test_core_plugin_dirs_pins_five_plugin_set` — temp marketplace.json + 5 plugin dirs,
    asserts the returned set matches exactly.
  - `test_core_plugin_dirs_halts_on_missing_plugin_dir` — temp marketplace.json declares a
    plugin whose dir is absent, asserts `SystemExit` naming that plugin.

## Why

`core_plugin_dirs()` hardcoded a 4-name tuple that predated `warrant`'s promotion into core
(issue #282), so `warrant`'s scope-gate/hunt-guard/approval-freeze machinery never attached to
any role session, silently. Reading the plugin list from marketplace.json makes the marketplace
the single source of truth and halting loudly on a declared-but-missing dir turns a future
silent drop into an immediate, named failure instead of a repeat of this issue.

## Upstream basis

`docs/issue-282/proposals/plan.md` (approved via PR #283 / issue comment
`APPROVE issue-282/implementation`), itself grounded in issue #282's problem statement and
acceptance criteria.

## Doc-placement ladder

- No new env var / config key / dependency / migration / setup step → handbook: not applicable.
- Changed public behavior: `core_plugin_dirs()` internals + banner format — the proposal
  (`docs/issue-282/proposals/plan.md`) already records the rationale for the loudness-policy
  divergence from `plugin_dirs()`; no separate ADR needed (no library/format choice made).
- No benchmark/investigation numbers produced.

## Verification run (this session, once)

Ran `core_plugin_dirs()` against the real `tokenmaxxxer-core` checkout at
`/home/jwjung/tokenmaxxxer/tokenmaxxxer-core` (see reply for actual output) — returned all five:
core, terse, freelunch, scout, warrant.

Ran `python3 -m pytest test_spawn.py -k core_plugin_dirs -v` — both new tests passed (see reply).

## What did not work

None.

## Open findings

None.

## Rationale for deviations

The proposal's frozen write set was `spawn.py, test_spawn.py`. Making `core_plugin_dirs()`
require a real `marketplace.json` broke 36 pre-existing tests that spawn a role session against
`tests/fixtures/rulebooks/tokenmaxxxer-core/`, a fixture checkout that had a `core/` plugin dir
but no `marketplace.json` at all (the old hardcoded-tuple code degraded gracefully on a missing
file; the new marketplace-reading code cannot, by design — that is the point of the fix). Added
one file outside the stated set, `tests/fixtures/rulebooks/tokenmaxxxer-core/.claude-plugin/marketplace.json`,
declaring the single `core` plugin the fixture already provides — this restores prior fixture
behavior (only `core` resolves) rather than adding new scope. All 221 tests pass with it in
place; 0 pass without it (36 fail with `FileNotFoundError`).

## Hunt

Stance: not applicable — this is a small, mechanical two-function change (read marketplace.json
instead of a hardcoded tuple; sys.exit on missing dir) with no new external surface (no network,
no subprocess, no new input parsing beyond existing JSON already read elsewhere in this file by
`plugin_dirs()`). No probes dispatched; nothing to record as closed_checks.
