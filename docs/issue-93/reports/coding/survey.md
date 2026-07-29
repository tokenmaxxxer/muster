---
title: issue-93 current-state survey
---

## Field

`resolved_role_model()` in `spawn.py:1313-1320` implements the #60 precedence
chain: `MUSTER_ROLE_MODEL` (env, stripped) > `role_model.txt` (config,
stripped) > `""` (unset). Two callers consume it: `spawn_cmd()`
(`spawn.py:1354-1356`, appends `--model <value>` to argv only when non-empty)
and the `--dry-run` branch (`spawn.py:~1504-1512`, sets `out["model"]` only
when non-empty).

Issue #93 asks for exactly one change: the terminal case returns `"sonnet"`
instead of `""`. Both callers already branch on truthiness, so once the
terminal value is never falsy, `--model sonnet` and `out["model"] = "sonnet"`
attach unconditionally when both env and config are unset/whitespace-only.
No caller logic needs to change — only the fallback return value.

## Write set

- `spawn.py` — `resolved_role_model()` body (1 line changed: `return ""` →
  `return "sonnet"`), plus its docstring and the two inline comments at the
  call sites that currently say "둘 다 비어있으면(기본) ... --model 을 붙이지
  않는다" (now false).
- `README.md:88-100` — precedence paragraph: "> none" becomes "> sonnet
  (built-in default)"; the "missing/whitespace-only ... same as unset (no
  `--model` flag, today's baseline)" sentence needs to state the new
  terminal value.
- `test_spawn.py` — the #60 test classes assert the "no `--model`" outcome
  in the double-unset case; those need to flip to asserting `--model sonnet`
  (and `out["model"] == "sonnet"` for dry-run). This is the "no-model-attached
  case disappears" instruction from the issue body. Affected tests:
  `test_role_model_unset_is_unchanged`,
  `test_role_model_whitespace_only_is_unchanged`,
  `test_role_model_whitespace_only_config_is_unchanged`,
  `test_role_model_non_utf8_config_is_unchanged`,
  `test_role_model_no_config_file_is_unchanged`,
  `test_unset_output_has_no_model_key`,
  `test_whitespace_only_output_has_no_model_key`. Env-set and config-only
  cases (`test_role_model_set_appends_flag`,
  `test_role_model_config_only_appends_flag`,
  `test_role_model_env_overrides_config`,
  `test_config_only_output_reflects_model`) already assert override values
  and are unaffected. One new test asserts the built-in default explicitly
  (both env and config absent → `resolved_role_model() == "sonnet"`).

No new dependency, no new env var, no schema/migration. `role_model.txt`
stays untracked and per-machine as before; only its absence stops meaning
"no model."

## Scouting

Skipped per scout-directive: this is a fully-specified implementation (the
issue body states the exact terminal-case change, the acceptance test, and
which existing tests must flip) — not a product surface with a category
bar to discover.
