---
status: approved
files:
  - spawn.py
  - test_gates.py
  - docs/issue-367/proposals/2026-08-07-isolate-repo-config-trust-test.md
  - docs/issue-367/reports/implementation.md
---

Skip condition: pure bugfix (scout-directive) — #367 is a test-isolation fix
with acceptance criteria fully specified in the issue text; no product or
design surface to scout.

## Request

`test_gates.py::t_repo_local_claude_config_stops_the_spawn` fails on any
machine where the real `~/.tokenmaxxxer` is not writable, because
`spawn.require_no_repo_config` unconditionally writes its trust-pin table to
`Path.home() / ".tokenmaxxxer" / "trusted-repo-config.json"`. Make the test
isolated from the real home, assert that isolation rather than assume it, and
scan the rest of the suite for the same shape.

## Constraints

- Fix must not change `require_no_repo_config`'s behavior when no override is
  set (default stays `Path.home()`).
- The test must demonstrably pass under a real read-only `$HOME` (this
  sandbox's `$HOME` already is read-only, giving a live before/after case
  without synthesizing one).
- Must assert (not assume) the real `~/.tokenmaxxxer/trusted-repo-config.json`
  is byte-identical before and after the test.

## Rationale

Chosen approach: add an env-var override (`MUSTER_TOKENMAXXXER_HOME`) read by
`require_no_repo_config`, following the existing `MUSTER_WORK_DIR` pattern
already used at spawn.py:2492/2745 for the same class of real-home write.

Rejected alternative: monkeypatching `Path.home` directly in the test (e.g.
via `unittest.mock.patch`). Rejected because this codebase's test style
(test_gates.py, test_spawn.py) never imports `unittest.mock` and instead uses
plain env-var overrides with try/finally restore — matching that convention
keeps the fix legible next to the `MUSTER_WORK_DIR` precedent instead of
introducing a new isolation mechanism for one test.

## What will be done

- `spawn.py`: `require_no_repo_config` reads `MUSTER_TOKENMAXXXER_HOME` (env)
  and uses it in place of `Path.home() / ".tokenmaxxxer"` when set; falls back
  to the real path otherwise.
- `test_gates.py`: the test sets `MUSTER_TOKENMAXXXER_HOME` to a tmp dir per
  iteration, restores the prior value in `finally`, and asserts the real
  `~/.tokenmaxxxer/trusted-repo-config.json` bytes are unchanged before vs.
  after the whole test.
- Scan the suite (`grep -rn "Path.home()"` plus a check of every test file's
  real-home/`.tokenmaxxxer`/`.claude` references) for the same shape and
  report the list.

## Out of scope

- The 51 unrelated `subprocess.run`-leak failures from #360 elsewhere in the
  suite.
- Any other `Path.home()` use in `spawn.py` (settings/plugins/work-dir) that
  is not exercised by a real-home write in a test.

## How you'll know it worked

- `pytest test_gates.py::t_repo_local_claude_config_stops_the_spawn -q`
  fails before the fix and passes after, both under this sandbox's real
  (read-only) `$HOME` — no synthetic HOME needed since the sandbox already
  demonstrates both states.
- `pytest test_gates.py -q` passes in full (75/75).
- The suite-wide scan for the same shape is reported as a list (or "none
  found, searched X").
