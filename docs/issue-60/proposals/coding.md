# Issue #60 — Phase 1 Proposal: repo-level default role model

## files: (frozen write set)

- `spawn.py`:
  - New small helper function, e.g. `resolved_role_model() -> str`, placed
    near the existing `MUSTER_ROLE_MODEL` read sites (not inside
    `role_settings()`), that implements the full `env > config > none`
    precedence and returns the resolved, stripped model string (or `""`).
  - The `--model` composition block inside `spawn_cmd()` (spawn.py:1238-1243)
    — replaced to call the new helper instead of reading
    `os.environ.get("MUSTER_ROLE_MODEL")` directly.
  - The `--dry-run` branch inside `main()` (spawn.py:1382-1398) — replaced
    to call the same helper, so dry-run reflects the resolved value
    (env, config, or none) exactly as `spawn_cmd()` would compose it.
  - A new small config-file read function (e.g. `read_role_model_config()`),
    reading a repo-root file — exact filename/format decided in the coding
    session, constrained to: plain single-value text file preferred over a
    new structured format, at `ROOT`, with a name that cannot collide with
    `roles/*.json` (e.g. `role_model.txt`, not e.g. `roles/model.json`).
- `test_spawn.py`: new test cases alongside the existing
  `test_role_model_*` cases (test_spawn.py:91-141) and the `TestDryRun*`
  class, covering: config-only (no env) sets `--model`; env overrides
  config; whitespace-only config behaves like unset; no env + no config
  leaves `--model` absent (unchanged behavior); dry-run reflects all of
  the above.
- `README.md`: the `MUSTER_ROLE_MODEL` paragraph (README.md:47-50) —
  extended in place to document the config file and the full precedence
  chain (env > config > none), not a new section elsewhere.

**Explicitly excluded from this write set:** `role_settings()` (spawn.py:292
onward) and `roles/*.json`. Issue #58 (web-access allowlist) is
independently modifying `role_settings()`'s body in parallel; this
proposal's write set touches only the `--model` resolution call sites
(`spawn_cmd()`, the `--dry-run` branch in `main()`) and new
config-reading helper functions, so the two issues can land independently
without merge conflicts.

## Request (paraphrased)

Today, `MUSTER_ROLE_MODEL` is an opt-in env var read at two call sites in
`spawn.py`; if the orchestrator forgets to set it before a spawn, the
session silently falls back to the CLI's (expensive) default model.
Issue #60 asks for a durable, structural default: a repo-level config
value (e.g. `role_model`) that spawn.py reads when the env var is unset,
so "sonnet by default" no longer depends on per-command operator
discipline. The env var must still win when set (so ad hoc overrides
keep working), and the config value must fall back to "no --model flag"
(today's inherited-default behavior) when both are absent — with the same
whitespace-only-counts-as-unset handling that issue #35 established for
the env var.

## Constraints

- Precedence is strictly `env > config > none`: if `MUSTER_ROLE_MODEL` is
  set (post-strip, non-empty), it wins outright regardless of config.
  Otherwise, if the config value is set (post-strip, non-empty), it is
  used. Otherwise no `--model` flag is added (today's baseline behavior
  is preserved byte-for-byte when neither is set).
- `--dry-run` must reflect the fully resolved value through the same
  precedence chain, exactly as it does today for the env var alone
  (spawn.py:1382-1398) — a dry-run driven by config-only must show
  `--model <value>` and the JSON `"model"` key, matching what an actual
  spawn via `spawn_cmd()` would compose.
- Whitespace-only config value must behave exactly like unset — same
  `.strip()` + truthiness-check pattern used for `MUSTER_ROLE_MODEL`
  since issue #35 (commit `36d75c5`), applied consistently to the config
  value and to the final resolved value.
- Must not modify `role_settings()` (spawn.py:292-~430+) in any way, to
  avoid colliding with issue #58's in-flight changes to that same
  function. All new logic lives in new helper(s) plus edits to the two
  existing `--model` call sites.
- Config surface: prefer the existing repo surface if one exists; none
  does today (see survey — `roles/*.json` is per-role and wrong shape;
  `.claude/settings*.json` / `.mcp.json` are Claude Code's own surfaces,
  not muster's). A new minimal repo-root file is therefore justified;
  keep it a single plain value (not a new structured config format) to
  minimize scope, and keep it clearly separate from `roles/*.json`
  filenames so no accidental collision or ambiguity arises.
- `doctor()`'s haiku probe (spawn.py ~1191-1193) must remain unaffected —
  it hardcodes its own model and does not go through `spawn_cmd()`, per
  existing test `test_role_model_does_not_affect_haiku_probe`
  (test_spawn.py:129-141). No proposed change touches that probe.

## What will be done (phase 2, after approval)

1. Add a repo-root config file convention for `role_model` (exact
   filename decided in phase 2, e.g. `role_model.txt`, one line = the
   model string).
2. Add `read_role_model_config() -> str` to read that file if present,
   defaulting to `""` on missing file / read error, with the same
   `.strip()` semantics as the env var.
3. Add `resolved_role_model() -> str` implementing
   `env.strip() or config.strip() or ""` precedence — actually
   `(env_stripped if env_stripped else config_stripped)`, i.e. check env
   first with its own strip, fall through to config with its own strip.
4. Update `spawn_cmd()` (spawn.py:1238-1243) to call
   `resolved_role_model()` instead of reading `os.environ` directly.
5. Update the `--dry-run` branch in `main()` (spawn.py:1382-1398)
   identically, so both paths share one resolution function and cannot
   drift.
6. Add tests in `test_spawn.py` for: config-only, env-overrides-config,
   whitespace-only config as unset, neither set (baseline unchanged), and
   dry-run reflecting each case.
7. Extend the `MUSTER_ROLE_MODEL` paragraph in `README.md` with the
   config file and the full precedence chain.

## Out of scope

- Any change to `role_settings()` or `roles/*.json` (issue #58's
  territory).
- Any new general-purpose muster config file/format beyond the single
  `role_model` value (e.g. no attempt to introduce a broader
  `muster.toml`/`muster.json` config system in this issue).
- Per-role model overrides (issue #60 asks for one repo-wide default, not
  per-role granularity).
- Changes to `doctor()`'s haiku probe.

## How we'll know it worked (test plan)

- `test_spawn.py` (existing + new cases) passes, covering:
  - No env, no config → `spawn_cmd()` composes no `--model` flag (today's
    behavior, regression-guarded by existing
    `test_role_model_unset_is_unchanged`).
  - Env set, no config → `--model <env value>` (existing
    `test_role_model_set_appends_flag`, unchanged).
  - No env, config set to `sonnet` → `spawn_cmd()` composes
    `--model sonnet` (new test, matches issue's acceptance criterion 1).
  - Env set AND config set (different values) → env value wins (new
    test, matches acceptance criterion 2).
  - Config set to whitespace only, no env → behaves like unset, no
    `--model` flag (new test, matches acceptance criterion 2's second
    half, mirroring existing `test_role_model_whitespace_only_is_unchanged`
    for the env var).
  - `--dry-run` with config-only set shows `--model sonnet` in both the
    JSON `"model"` key and the printed `--model sonnet` line (new test,
    mirrors existing `TestDryRun*` class pattern).
  - `test_role_model_does_not_affect_haiku_probe` continues to pass
    unmodified (regression guard that the probe path is untouched).
- Manual smoke check (documented in phase-2 report, not required for
  automated tests): with the config file present and `MUSTER_ROLE_MODEL`
  unset, `python3 spawn.py <role> "<task>" --dry-run` prints
  `--model <configured value>`.
