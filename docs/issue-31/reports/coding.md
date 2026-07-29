---
kind: coding-record
loop_state: implemented-tested-pending-commit
what-was-done: "Phase-2 implementation of MUSTER_ROLE_MODEL per approved docs/issue-31/proposals/coding.md: spawn_cmd appends --model <value> when the env var is set, README documents it next to MUSTER_AGENT_GH_TOKEN, test_spawn.py SpawnCmd gains three covering cases. Tests pass (33/33). Verified via direct spawn.spawn_cmd calls that --dry-run does not exercise spawn_cmd in this codebase."
why: "Proposal approved; implementing exactly the frozen write set (spawn.py, README.md, test_spawn.py) with no scope drift."
upstream-basis: "docs/issue-31/proposals/coding.md (approved build proposal) and this file's own phase-1 survey below."
code_under_review: "TBD - filled in after commit"
next-steps: "Commit and push to issue-31/coding (updates PR #32)."
---

# Issue 31 - phase 2: MUSTER_ROLE_MODEL implementation

## What was done (phase 2)

- `spawn.py` (`spawn_cmd`, inserted right after the `--plugin-dir` loop,
  before the base `env` dict is built): read `MUSTER_ROLE_MODEL` via
  `os.environ.get`; if truthy, append `["--model", role_model]` to `cmd`.
  Unset/empty -> `cmd` is unchanged, matching prior behavior byte-for-byte.
  `doctor()`'s haiku probe (`spawn.py:1095-1136`, hardcoded
  `"--model", "haiku"`) was not touched.
- `README.md`: added a short paragraph right after the existing
  "Optional hardening" / `MUSTER_AGENT_GH_TOKEN` paragraph, documenting
  `MUSTER_ROLE_MODEL=<model>` and noting it does not affect the haiku
  probe.
- `test_spawn.py`: added three cases to the `SpawnCmd` class -
  `test_role_model_unset_is_unchanged`, `test_role_model_set_appends_flag`,
  `test_role_model_does_not_affect_haiku_probe` - each saving/restoring
  `os.environ["MUSTER_ROLE_MODEL"]` around the mutation, following the
  existing `test_core_dir_resolves_or_halts` pattern.

## Test run (phase 2)

Command: `python3 -m pytest test_spawn.py -q`
Result: `33 passed in 0.20s` (all existing `SpawnCmd` cases plus the three
new ones).

## --dry-run acceptance (issue #31)

`gh issue view 31` was readable this session. Its acceptance criterion
reads: `MUSTER_ROLE_MODEL=sonnet python3 spawn.py <role> "<task>" --dry-run`
should show `--model sonnet` in the composed command. Checked
`spawn.py`'s `--dry-run` branch (`spawn.py:1298-1300`): it prints
`role_settings(a.role)` (the merged role JSON settings) and returns
without ever calling `spawn_cmd` - `--dry-run` does not exercise the argv
this issue is about, in this codebase, today. This is a pre-existing gap
between the issue's acceptance wording and what `--dry-run` actually
inspects; not something phase-2 introduced or was scoped to fix (out of
scope per the approved proposal, which names `spawn.spawn_cmd(...)` calls
as the equivalent/actual acceptance mechanism instead).

Verified directly via `spawn.spawn_cmd`, per the proposal's own
"How we'll know it worked" wording:

```
$ python3 -c '<script calling spawn.spawn_cmd with MUSTER_ROLE_MODEL set/unset>'
set:    [..., '--verbose', '--model', 'sonnet']
unset:  [..., '--verbose']
```

Full argv with `MUSTER_ROLE_MODEL=sonnet`:
`['claude', '-p', '--settings', '/tmp/s.json', '--permission-mode', 'acceptEdits', '--output-format', 'stream-json', '--verbose', '--model', 'sonnet']`

Full argv unset:
`['claude', '-p', '--settings', '/tmp/s.json', '--permission-mode', 'acceptEdits', '--output-format', 'stream-json', '--verbose']`

Both match the proposal's acceptance criteria exactly.

## What did not work (phase 2)

none

---

# Issue 31 - survey: pin model for spawned role sessions (phase 1, unchanged below)

## What was done

Surveyed spawn.py's role-session command builder (`spawn_cmd`), the
`doctor()` haiku probe, README's `MUSTER_AGENT_GH_TOKEN` section, and the
existing `os.environ.get()` pattern used for optional config elsewhere in
spawn.py. Wrote this survey and a companion build proposal
(`docs/issue-31/proposals/coding.md`) for adding a `MUSTER_ROLE_MODEL` env
var that appends `--model <value>` to the role session command.

## Why

Phase-1 of the coding role (research, survey, proposal) precedes any edit
to `spawn.py`/`README.md` per contract v3 s11 - a build proposal needs a
grounded current-state survey and a frozen write set before implementation
starts, and a human Approve gates phase-2.

## Upstream basis

Issue #31 (coding subject). `gh issue view 31` could not be read in this
session (Bash permission denied for that specific call), so scope is
taken from the task brief handed to this session: pin the model used by
spawned role sessions via an env var, without touching the haiku probe.

## Open findings

The task brief names the target function `_session_cmd`, but no such
function exists anywhere in this repo. The function that actually builds
the role session's argv/env is `spawn_cmd` (`spawn.py:1139`). This survey
and the accompanying proposal target `spawn_cmd` as the real function;
flagging the naming mismatch here so whoever reviews scope can confirm
that substitution is correct.

## Next steps

Await human Approve on `docs/issue-31/proposals/coding.md`. Then, in
phase-2: add the `MUSTER_ROLE_MODEL` read plus conditional `--model`
append inside `spawn_cmd` (`spawn.py:1139-1188`), document the var in
`README.md` near `README.md:43-46`, add a covering case to
`test_spawn.py`, and land via PR.

## Open-finding resolution path

Confirm with the human reviewer during Approve that `spawn_cmd`
(`spawn.py:1139`) is the intended target of the brief's `_session_cmd`
reference. If a different function is meant, re-scope before phase-2
touches any file.

## Where the role session command is built

There is no function literally named `_session_cmd` in this repo. The
function that builds the role session's argv/env is `spawn_cmd`:

- `spawn.py:1139` - `def spawn_cmd(settings_path: str, role: str,
  unattended: bool, core_plugins: list | None = None,
  plugins: list | None = None) -> tuple[list[str], dict[str, str]]:`
- `spawn.py:1156-1158` - builds the base argv:
  `cmd = ["claude", "-p", "--settings", settings_path, "--permission-mode",
  "acceptEdits", "--output-format", "stream-json", "--verbose"]`
- `spawn.py:1162-1165` - appends `--plugin-dir` for each role plugin and
  each core plugin.
- `spawn.py:1166` - starts the extra-env dict:
  `env = {"CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}`
- `spawn.py:1175-1185` - reads `MUSTER_AGENT_GH_TOKEN` from `os.environ`,
  falls back to `gh auth token`, and conditionally adds `GH_TOKEN` /
  `GIT_TERMINAL_PROMPT` to `env`.
- `spawn.py:1186-1187` - `if unattended: env["TOKENMAXXXER_UNATTENDED"] = "1"`.
- `spawn.py:1188` - `return cmd, env`.

This is the one place that assembles the `claude -p ...` argv for a role
session, so it is the natural insertion point for a `--model` flag. No
model flag is added to `cmd` today - the role session runs on the CLI's
default model.

## The haiku probe (leave untouched)

`doctor()` at `spawn.py:1095-1136` runs a throwaway probe session to check
that plugin hooks fire headless on the installed CLI version:

- `spawn.py:1119` - comment: "`--model haiku`: 프로브의 관심사는 훅 로딩이지
  모델이 아니다. 싸게 간다." (the probe cares about hook-firing, not the
  model; go cheap.)
- `spawn.py:1120-1124` - the `subprocess.run([...])` call that hardcodes
  `"--model", "haiku"`.

This call does not go through `spawn_cmd` - it builds its own argv inline.
An env-var-driven `--model` addition scoped to `spawn_cmd` cannot affect
it. Phase-2 must not touch `spawn.py:1095-1136`.

## Where README documents MUSTER_AGENT_GH_TOKEN

- `README.md:13` - "Role sessions run on the AGENT account
  (`MUSTER_AGENT_GH_TOKEN`), work on `issue-<n>/<role>` branches..."
- `README.md:43-46` - the "Optional hardening" paragraph: a separate agent
  identity via `export MUSTER_AGENT_GH_TOKEN=<pat>` (or a GitHub App) moves
  the agent/human split from the session layer to the account layer; "The
  default needs neither."

`MUSTER_ROLE_MODEL` should be documented as a sibling optional-config env
var near `README.md:43-46`.

## Existing pattern: how spawn.py already reads env vars

`spawn.py` consistently reads optional config via `os.environ.get(...)`
with a falsy/empty default, and only mutates behavior when the value is
present:

- `spawn.py:1175` - `agent_token = os.environ.get("MUSTER_AGENT_GH_TOKEN")`,
  then `if agent_token: env["GH_TOKEN"] = agent_token` (`spawn.py:1183-1185`).
- `spawn.py:778` - `gates.BASE = os.environ.get("GATE_BASE") or _base(cwd)`.
- `spawn.py:963` - `os.environ.get("TOKENMAXXXER_CORE")` as one of several
  candidate roots.
- `spawn.py:1223`, `spawn.py:1332` - `os.environ.get("MUSTER_WORK_DIR")`.
- `spawn.py:1318` - `os.environ.get("MUSTER_KEEP_SSH", "")` compared
  against a tuple of falsy strings to decide a boolean switch.

`MUSTER_ROLE_MODEL` should follow the same shape as `MUSTER_AGENT_GH_TOKEN`:
`os.environ.get("MUSTER_ROLE_MODEL")`, and only append `--model <value>` to
`cmd` when it is truthy.

## Frozen write set for phase 2

- `spawn.py` (edit `spawn_cmd`, `spawn.py:1139-1188`)
- `README.md` (add `MUSTER_ROLE_MODEL` note near `README.md:43-46`)
- `test_spawn.py` - already covers `spawn_cmd` behavior (`SpawnCmd` class,
  `test_spawn.py:29-89`; e.g. `test_flags` at `test_spawn.py:30-41`,
  `test_env_stamps` at `test_spawn.py:76-82`). A new test case for the
  `--model` flag belongs here.

No other files reference `spawn_cmd` or the haiku probe.
