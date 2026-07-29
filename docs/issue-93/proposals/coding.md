---
title: issue-93 build proposal
---

files: `spawn.py`, `README.md`, `test_spawn.py`

## Request

Make `sonnet` the built-in default role model so a fresh machine with no
`MUSTER_ROLE_MODEL` and no `role_model.txt` still spawns role sessions on a
cheap, known model instead of silently inheriting the caller's (possibly
expensive) session model.

## Constraints

- Precedence order unchanged: env > config > built-in default — only the
  terminal value changes (`""` → `"sonnet"`).
- Issue #35 strip semantics unchanged: whitespace-only env or config values
  still behave as unset and fall through to the next layer.
- `--dry-run` must reflect the resolved model through the same chain,
  including the new built-in default.
- No new env var, dependency, or config schema change.

## What will be done

1. `spawn.py`: `resolved_role_model()`'s final `return read_role_model_config()`
   path returns `"sonnet"` when that read yields `""` — i.e. `return
   read_role_model_config() or "sonnet"`. Update the function's docstring and
   the two call-site comments (`spawn_cmd`, dry-run branch) that currently
   describe the terminal case as "no `--model` attached."
2. `README.md:88-100`: update the precedence sentence to
   `MUSTER_ROLE_MODEL (env) > role_model.txt (config) > sonnet (built-in
   default)` and rewrite the "missing/whitespace-only ... same as unset (no
   `--model` flag, today's baseline)" sentence to state that the built-in
   default is what attaches in that case.
3. `test_spawn.py`: flip the seven tests that currently assert
   `assertNotIn("--model", cmd)` / `assertNotIn("model", out)` in the
   double-unset case (env absent/whitespace AND config absent/whitespace/
   missing/non-UTF8) to assert `--model sonnet` / `out["model"] == "sonnet"`
   instead — removing the "no --model attached" case per the issue. Add one
   new test asserting `spawn.resolved_role_model() == "sonnet"` with both env
   and config absent, as the explicit built-in-default assertion the issue
   requests. Tests that already assert override behavior (env-set,
   config-only, env-overrides-config) are left as is.

## Out of scope

- `doctor()`'s hardcoded haiku probe (unaffected, doesn't call
  `resolved_role_model()`).
- Any change to `role_model.txt`'s file location, format, or tracked/
  untracked status.
- Warrant-hunter probes closed under this record land in
  `docs/issue-93/reports/coding.md` in phase 2, not here.

## How it'll know it worked

`python -m unittest test_spawn.py -v` passes, including the new
built-in-default test; manual check that `spawn.py --dry-run` (or the
`spawn_cmd`/`role_settings` acceptance path) shows `--model sonnet` /
`"model": "sonnet"` with `MUSTER_ROLE_MODEL` unset and no `role_model.txt`
present.
