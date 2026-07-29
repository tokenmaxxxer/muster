# Issue #60 — Phase 1 Survey: repo-level default role model

## Issue text (verbatim, via `gh issue view 60`)

> ## Problem
>
> Issue #31 added MUSTER_ROLE_MODEL as an opt-in env var. In practice the
> orchestrator must remember to prefix every spawn with
> MUSTER_ROLE_MODEL=sonnet; a spawn without it silently inherits the user's
> (expensive) default model. The operator wants sonnet to be the durable
> default for all role sessions, guaranteed structurally rather than by
> per-command discipline.
>
> ## Requirement
>
> - A repo-level (or muster-level) config value, e.g. `role_model`, read by
>   spawn.py when MUSTER_ROLE_MODEL is unset. Precedence: explicit env var >
>   config value > no --model (inherit).
> - Where the config lives is the implementer's phase-1 survey question
>   (existing muster/repo config surface preferred over a new file; if a new
>   file is unavoidable, justify it).
> - --dry-run must reflect the resolved model the same way it does for the
>   env var (issue #35's strip semantics apply to the config value too).
> - Tests alongside the existing SpawnCmd/model cases; README documents the
>   precedence chain next to MUSTER_ROLE_MODEL.
>
> ## Acceptance
>
> - With config set to sonnet and no env var, a spawn's composed command
>   contains --model sonnet.
> - Env var still overrides config; whitespace-only config value behaves
>   like unset.

## Where spawn.py lives and its shape

`spawn.py` (1725 lines) is the top-level orchestrator script at the repo
root of *this* repo (muster itself): `ROOT = Path(__file__).resolve().parent`
(line 24). It is not per-target-repo config — it drives spawns of role
sessions for whichever repo the orchestrator points it at via `-C`. So
"repo-level" for issue #60 means **muster's own repo**, not the target
repo being worked on.

## Current `--model` resolution logic (issue #31 / #35)

Two independent read sites for `MUSTER_ROLE_MODEL`, both already using the
issue #35 strip semantics:

1. **`spawn_cmd()`** (function starts at spawn.py:1211), the path that
   actually launches a session:

   ```python
   # spawn.py:1241-1243
   role_model = (os.environ.get("MUSTER_ROLE_MODEL") or "").strip()
   if role_model:
       cmd += ["--model", role_model]
   ```

2. **`main()`'s `--dry-run` branch** (spawn.py:1382-1398), which does not
   call `spawn_cmd()` (no session is launched, so `spawn_cmd()`'s
   `--model` composition never runs) and therefore duplicates the same
   resolution independently, by design (see the comment at 1384-1388,
   citing `docs/reports/2026-07-29-hunt-muster-role-model-build.md`):

   ```python
   # spawn.py:1389-1397
   role_model = (os.environ.get("MUSTER_ROLE_MODEL") or "").strip()
   if role_model:
       out["model"] = role_model
   print(json.dumps(out, indent=2, ensure_ascii=False))
   if role_model:
       print(f"--model {role_model}")
   ```

   `out` here is `role_settings(a.role)` (spawn.py:1383) — the dry-run
   branch *reads* `role_settings()`'s dict and *mutates a local copy* of it
   to append `"model"`; it does not touch `role_settings()`'s own code.

## `role_settings()` — why it is off-limits for this issue's write set

`role_settings()` (spawn.py:292-~430+) computes a role's **sandbox
boundary and global-plugin suppression** from `roles/<role>.json`: merged
env defaults, `$VAR`/`~` expansion, `allowWrite`/`denyWrite`/`denyRead`
substitution, and (per issue #38) package-registry host allowlisting. It
has nothing to do with `--model` resolution today — the `--dry-run` branch
only borrows its output dict as a base to print. **Issue #58 (web-access
allowlist) is independently modifying this same function** (adding to the
`allowedDomains`/host-allowlist logic that already lives here per the
issue #38 comment at spawn.py:39-41). To keep #58 and #60 mergeable
independently, this proposal's write set must never touch the body of
`role_settings()` — only the two `--model` resolution call sites
(`spawn_cmd()` and the `--dry-run` branch in `main()`) and a helper
function for reading the new config value.

## Existing config surfaces in this repo

Surveyed for a "repo-level config" home that could carry `role_model`
before inventing a new file:

- **`roles/<role>.json`** (`roles/coding.json`, `roles/qa.json`, etc.) —
  per-role sandbox/env specs consumed by `role_settings()`. Wrong shape:
  these are per-role, not a single repo-wide default, and touching their
  loader risks brushing `role_settings()`.
- **`.claude-plugin/marketplace.json`** — plugin marketplace manifest,
  unrelated to spawn behavior.
- **`.mcp.json`**, **`.claude/settings.json`**, **`.claude/settings.local.json`**
  — Claude Code's own settings surfaces (merged into spawned sessions'
  `--settings`, and explicitly the *user's* global config that
  `role_settings()` suppresses for isolation — not an appropriate place to
  add a muster-specific default, and structurally owned by Claude Code /
  the user, not muster).
- No existing `muster.toml` / `muster.yaml` / `muster.json` / `.musterrc`
  or any dedicated muster-level config file exists in the repo (confirmed
  by search).

**Conclusion: no existing single-value repo config surface fits.** The
closest fit and simplest addition consistent with "prefer existing
surface over new file" is **a small dedicated `role_model` config file at
repo root**, e.g. `ROOT / "role_model.txt"` (or a minimal
`muster.json` with a `role_model` key, if a container format is
preferred for future extensibility) — read only by a new small helper
next to the existing `MUSTER_ROLE_MODEL` read sites, never by
`role_settings()`. Phase 2 will decide the exact filename/format
(`role_model.txt` as one line of plain text is the minimal option, since
today's config need is a single string value); the proposal below records
this as an open implementation choice, constrained to *not* colliding
with `roles/*.json` naming or `role_settings()`.

## Issue #35 strip semantics precedent

Fix commit `36d75c5` ("fix(issue-35): strip MUSTER_ROLE_MODEL before
truthiness check") establishes the pattern used at both current read
sites: `(os.environ.get("MUSTER_ROLE_MODEL") or "").strip()`, then
`if role_model:`. A whitespace-only env value strips to `""`, which is
falsy, so it behaves exactly like unset. Issue #60 must apply the same
`.strip()` + truthiness-check pattern to the new config value (both when
read standalone, and again after the config value is folded into the
`env-then-config` precedence chain), so a whitespace-only config value
also behaves like unset.

## Relevant functions/lines summary

| Item | Location |
|---|---|
| `spawn_cmd()` — `--model` composition | spawn.py:1211, model logic at 1238-1243 |
| `main()` `--dry-run` branch — `--model` reflection | spawn.py:1382-1398 |
| `role_settings()` (off-limits, issue #58 territory) | spawn.py:292-~430+ |
| Issue #35 strip fix (precedent to reuse) | commit `36d75c5`, spawn.py:1241, 1389 |
| README precedence doc for `MUSTER_ROLE_MODEL` | README.md:47-50 |
| Existing model-related tests | test_spawn.py:30-141 (`test_role_model_*`, `TestDryRun*`) |
| No existing muster-level config file | confirmed via repo-wide search |
