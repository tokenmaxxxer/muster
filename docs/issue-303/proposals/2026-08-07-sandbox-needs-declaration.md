---
status: proposed
files:
  - spawn.py
  - docs/specs/sandbox-needs.example.json
  - docs/handbooks/sandbox-needs.md
  - test_spawn.py
---

## Request

A consumer repo has no way to declare its own verification-environment needs (registry hosts, package caches, read paths) — `spawn.py` hardcodes them, and one of the three (`allowRead`) has no hardcoded list to even patch. Build a declaration channel: a consumer repo states its needs in a file it owns; `spawn.py` reads and merges it, current narrow lists as floor not ceiling; an unsatisfiable declaration fails loudly at spawn.

## Constraints

- Three lists named in the issue; state explicitly which convert now: `core_plugin_dirs()` is **already converted** (issue #282, reads `marketplace.json`) — nothing to do. `RECORD_FIELDS_TERMINAL_STATES` (#147) lives in each rulebook plugin's own `hooks/record-fields-gate.sh`, not in this repo — **follow-up**, out of this write set. `PACKAGE_REGISTRY_HOSTS`/`PACKAGE_CACHE_DIRS`/`allowRead` (spawn.py:104-125, 433, 472-479) — **converted now**.
- Current narrow defaults (8 registry hosts, 5 cache dirs, empty allowRead) stay as the floor: a declaration only adds, never removes.
- `allowRead` is additive-to-default-allow, not a whitelist (measured against the installed CLI binary — see survey.md measurement 1); the new channel must not accidentally introduce a `denyRead`-by-default posture that isn't there today.
- A symlink from inside the workspace to an outside path already resolves past `denyRead` (measured — see survey.md measurement 2); this fix is not a new leak, but the declaration doc should say so, since it changes what "no channel" means for affected projects today (a stopgap exists).
- An unsatisfiable declaration (references a path/host the declaration schema doesn't support, or malformed JSON) must `sys.exit` with a named error at spawn — never a silent skip that surfaces mid-session as an absent file.

## Rationale

Considered keeping the per-incident pattern (add `~/.cache/ms-playwright` to `PACKAGE_CACHE_DIRS`, add the model directory to a new hardcoded list) and rejected it: it's what created #282 (the marketplace list drifted from `PACKAGE_CACHE_DIRS`'s hardcoded twin) and #147 (7 repos' overrides landing nowhere) in the first place — this issue's own history is the evidence against it. It also can't ever cover `allowRead`, since no list exists there to extend.

Considered making the declaration a Python file consumers import (mirrors `roles/*.json` structurally less, but would let a repo declare computed logic) and rejected it: `docs/specs/approvers.md` is the established precedent for "orchestrator reads a plain file the consumer owns" and it's a flat, auditable diff in the consumer's PR — a Python file invites arbitrary code running during spawn resolution, which is a bigger blast-radius change than this issue asks for.

Considered folding the declaration into `roles/<role>.json` in this repo instead of a file in the consumer repo, and rejected it: that keeps ownership here, which is exactly the property being removed ("onboarding a project needs no on-the-record code change").

## What will be done

- Add `docs/specs/sandbox-needs.json` as an **optional**, consumer-owned declaration file, read from the target repo's root (the `-C <dir>` argument's tree, same place `docs/specs/approvers.md` is read from today). Schema:
  ```json
  {
    "registryHosts": ["example.registry.internal"],
    "cacheDirs": [{"env": "SOME_CACHE", "default": "~/.cache/some-tool"}],
    "readPaths": ["~/large-artifact-dir"]
  }
  ```
  Missing file = empty declaration (no behavior change from today).
- `role_settings(role: str)` (spawn.py:390) currently takes no target-repo path, so it has no way to locate a consumer repo's `docs/specs/sandbox-needs.json` — confirmed against its two call sites: the `--dry-run` path (spawn.py:2575, has `a.cwd` in scope but never passes it) and `_spawn_one()` (spawn.py:2991, has `cwd` in scope but never passes it). Change the signature to `role_settings(role: str, cwd: str)` and thread `a.cwd` / `cwd` through both call sites (and the ~20 direct calls in `test_spawn.py`, updated alongside the new tests).
- Inside `role_settings()`: after resolving the role file, read `<cwd>/docs/specs/sandbox-needs.json` if present; merge `registryHosts` into the existing `PACKAGE_REGISTRY_HOSTS`-derived domain list (same dedupe-on-append as today), `cacheDirs` into the existing `PACKAGE_CACHE_DIRS` walk (same exists-on-host skip), and **new**: `readPaths` appended to `sandbox.filesystem.allowRead` the same way cache dirs already are — this is the fix for the allowRead gap, since today only `PACKAGE_CACHE_DIRS` writes that key.
- Malformed JSON, or a declared `readPaths`/`cacheDirs` entry pointing to something that isn't resolvable as a path string → `sys.exit` naming the file and the bad entry, at spawn, before the session starts — never a silent skip.
- `docs/handbooks/sandbox-needs.md`: what the file is for, its schema, the additive-floor guarantee, and the symlink-stopgap note from the constraints section (so a project blocked today has an immediate workaround while it adds the declaration).
- Extend `test_spawn.py` alongside the existing `test_registry_hosts_merged_into_allowed_domains` / `test_present_cache_dir_added_to_allow_read` tests: declared host merges, declared cache dir merges, declared read path lands in `allowRead`, absent file is a no-op, malformed file exits loudly.
- The proposal body itself states the #147/#282 split (this section + Constraints) so the issue's "state explicitly which lists convert now" requirement is satisfied in the record, not left implicit.

## Out of scope

- `RECORD_FIELDS_TERMINAL_STATES` / #147 — different repo's gate code, not in this repo's write set.
- Any change to the installed Claude Code CLI's sandbox semantics (`allowManagedReadPathsOnly`, symlink resolution) — those are platform behavior, observed and documented, not modified.
- Retrofitting existing `roles/*.json` files to declare anything — the declaration lives in the *consumer* repo, not `roles/`.
- A schema-validation library dependency — plain `json.loads` + manual key checks, matching this file's existing dependency-free style.

## How you'll know it worked

- `test_spawn.py -k sandbox_needs` (new tests) pass, covering: host merge, cache-dir merge, `allowRead` populated from a declared `readPaths` entry with no `PACKAGE_CACHE_DIRS` involvement, absent-file no-op, malformed-file loud exit.
- Full existing `test_spawn.py` suite still passes unchanged (floor behavior preserved).
- Manually constructing a `docs/specs/sandbox-needs.json` with a `readPaths` entry and running `role_settings()` against it shows the path in the resulting `sandbox.filesystem.allowRead` — the concrete case from the issue's third comment (the 3.4 GB `onnx_models/` directory) becomes declarable without any `spawn.py` edit.
