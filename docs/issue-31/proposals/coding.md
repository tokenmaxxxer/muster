---
kind: coding-proposal
loop_state: scope-approved
what-was-done: "Drafted this build proposal for MUSTER_ROLE_MODEL, grounded in docs/issue-31/reports/coding.md's survey of spawn_cmd, the haiku probe, and README's MUSTER_AGENT_GH_TOKEN section."
why: "A build proposal is required before src/README edits per contract v3 s11, so scope, constraints, and acceptance are fixed and human-approvable before implementation starts."
upstream-basis: "docs/issue-31/reports/coding.md (this repo, same commit) and issue #31 (could not be fetched via gh issue view 31 in this session; scope taken from the task brief)."
open-findings: "Task brief names _session_cmd; no such function exists. This proposal targets spawn_cmd (spawn.py:1139), the actual role-session command builder. See resolution path below."
next-steps: "Await human Approve (gh pr review --approve / merge per protocol.md s5) on this proposal, then implement per 'What will be done' below and open a phase-2 PR."
open-finding-resolution-path: "Reviewer confirms during Approve that spawn_cmd is the correct target for the _session_cmd reference; if not, this proposal is re-scoped before any implementation PR is opened."
---

files:
- `spawn.py`
- `README.md`
- `test_spawn.py`

## Request

When the environment variable `MUSTER_ROLE_MODEL` is set, `spawn_cmd`
(the function that builds the role session's `claude -p ...` command —
there is no `_session_cmd` in this repo; see survey) appends `--model
<value>` to the argv it returns. When `MUSTER_ROLE_MODEL` is unset (or
empty), no `--model` flag is added and behavior is unchanged from today.
The `doctor()` haiku probe (`spawn.py:1095-1136`, hardcoded `--model
haiku`) is left untouched — it builds its own argv independently of
`spawn_cmd` and must keep doing so. `README.md` gets a short note
documenting `MUSTER_ROLE_MODEL`, placed next to the existing
`MUSTER_AGENT_GH_TOKEN` documentation.

## Constraints

- The haiku probe (`spawn.py:1095-1136`, in particular the hardcoded
  `"--model", "haiku"` at `spawn.py:1121`) must not change in any way.
- No new dependencies — read the variable with the standard-library
  `os.environ.get`, matching the existing pattern used for
  `MUSTER_AGENT_GH_TOKEN` (`spawn.py:1175`) and `GATE_BASE`
  (`spawn.py:778`).
- Config is env-var only — no new CLI flag, no new role-JSON field, no
  config file. This mirrors how `MUSTER_AGENT_GH_TOKEN`,
  `MUSTER_WORK_DIR`, and `MUSTER_KEEP_SSH` already work.

## What will be done

1. In `spawn_cmd` (`spawn.py:1139-1188`), after the base argv is built
   (`spawn.py:1156-1158`) and before `--plugin-dir` entries are appended
   (or anywhere before `return cmd, env` at `spawn.py:1188` — exact
   position does not affect `claude`'s argv parsing), add:
   ```python
   role_model = os.environ.get("MUSTER_ROLE_MODEL")
   if role_model:
       cmd += ["--model", role_model]
   ```
2. In `README.md`, add one sentence in the "Optional hardening" paragraph
   area (`README.md:43-46`), documenting that `MUSTER_ROLE_MODEL=<model>`
   pins the model used by spawned role sessions (the haiku probe is
   unaffected).
3. In `test_spawn.py`, add a test case to the `SpawnCmd` class
   (alongside `test_flags` at `test_spawn.py:30-41` and `test_env_stamps`
   at `test_spawn.py:76-82`) asserting:
   - with `MUSTER_ROLE_MODEL` unset, `"--model"` is not in `cmd`;
   - with `MUSTER_ROLE_MODEL="sonnet"` set, `cmd[cmd.index("--model") + 1]
     == "sonnet"`.
   Test must save/restore `os.environ` around the mutation, following the
   pattern already used in `test_core_dir_resolves_or_halts`
   (`test_spawn.py:56-74`).

## Out of scope

- Any change to `doctor()` or the haiku probe.
- Validating that the given model name is a real/known model — `claude`
  itself will reject an invalid value at spawn time; `spawn_cmd` does no
  validation of its own for any other env-driven value either.
- A CLI flag or role-JSON field for the same setting — env-var only, per
  Constraints.
- Per-role model overrides (e.g. different models for different roles) —
  `MUSTER_ROLE_MODEL` is a single global pin, not a per-role table.

## How we'll know it worked

- `spawn.py <role> "<task>" --dry-run` with `MUSTER_ROLE_MODEL=sonnet` set
  shows `--model sonnet` in the emitted command/settings (or, per
  `test_spawn.py`, a direct call to `spawn.spawn_cmd(...)` returns a `cmd`
  list containing `"--model", "sonnet"` when the env var is set that way).
- The same call with `MUSTER_ROLE_MODEL` unset produces a `cmd` with no
  `"--model"` token at all — output is byte-identical to today's
  `spawn_cmd` output modulo the (absent) flag.
- `spawn.py doctor` / the haiku probe's argv is unchanged — still hardcodes
  `"--model", "haiku"` regardless of `MUSTER_ROLE_MODEL`.
- `test_spawn.py`'s new case(s) pass, and all existing `SpawnCmd` tests
  (`test_flags`, `test_core_is_attached_by_path`,
  `test_core_dir_resolves_or_halts`, `test_env_stamps`,
  `test_unattended_is_separate`) continue to pass unchanged.
