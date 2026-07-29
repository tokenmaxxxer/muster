---
kind: coding-record
loop_state: proposal-pending-approval
what-was-done: "Phase-1 survey for issue #38 (package-registry access for role workspaces). Read the issue (two candidate designs: shared read-only host caches vs. sandbox registry allowlist, hybrid allowed). Surveyed spawn.py's workspace/cache setup and every roles/*.json sandbox.network.allowedDomains block. Found the allowlist mechanism from candidate design 2 already exists per-role but is hand-maintained and ecosystem-incomplete, and that cache redirection exists but points at an empty per-workspace dir with no host-cache mount (candidate design 1 is unimplemented). Wrote this survey and the companion proposal docs/issue-38/proposals/coding.md."
why: "Contract v3 s11: phase-1 (research/survey/proposal) must precede any spawn.py/roles/*.json edit. A grounded current-state survey with file:line evidence is required before a build proposal can freeze a write set for human Approve."
upstream-basis: "gh issue view 38 (issue body: problem statement, two candidate designs, acceptance criteria); spawn.py (role_settings, spawn_cmd, cache redirection); roles/coding.json, roles/qa.json, roles/verify.json (sandbox.network.allowedDomains)."
next-steps: "Await human Approve on docs/issue-38/proposals/coding.md. On approval, phase-2 implements the frozen write set named there."
open-findings: "None blocking. Only coding.json, qa.json, verify.json were read in full for this survey; feasibility.json, ops.json, product.json, reflect.json, review.json, ux-design.json were not individually audited and may have their own allowedDomains gaps -- phase-2 should sweep all role files, not just the three surveyed here."
open-finding-resolution-path: "Phase-2 sweeps all roles/*.json files (not just coding/qa/verify) when building the shared registry-host list, so any undiscovered allowedDomains gap in feasibility.json/ops.json/product.json/reflect.json/review.json/ux-design.json is caught and normalized during implementation, before the human Approve on that phase-2 diff."
---

# Issue #38 — Survey: package-registry access for role workspaces

Phase 1 (proposal-only). No production code touched. Evidence below is file
path + line references from the `issue-38/coding` checkout.

## What was done

Read issue #38 (`gh issue view 38`): role sessions run sandboxed with
outbound network blocked, so any project whose build/test fetches
dependencies fails at the fetch step (observed with Go/`proxy.golang.org`,
same wall for npm/PyPI/crates.io/Maven). Two candidate designs to evaluate:
(1) shared read-only host package caches mounted into the workspace, (2) a
sandbox registry allowlist; hybrid allowed. Surveyed `spawn.py`'s workspace
and cache setup and every `roles/*.json` file's `sandbox.network` block to
find the current-state baseline for both candidates. Wrote this survey and
the companion proposal `docs/issue-38/proposals/coding.md`.

## Why

Contract v3 s11: phase-1 (research/survey/proposal) precedes any
`spawn.py`/`roles/*.json` edit. A grounded current-state survey with
file:line evidence is required before a build proposal can freeze a write
set for human Approve.

## Upstream basis

`gh issue view 38` (problem statement, two candidate designs, acceptance
criteria); `spawn.py` (`role_settings`, `spawn_cmd`, the `.muster-cache`
redirection at `spawn.py:1508-1522`); `roles/coding.json`, `roles/qa.json`,
`roles/verify.json` (`sandbox.network.allowedDomains`).

## Open findings

None blocking. Only `coding.json`, `qa.json`, and `verify.json` were read
in full for this survey; `feasibility.json`, `ops.json`, `product.json`,
`reflect.json`, `review.json`, `ux-design.json` were not individually
audited and may have their own `allowedDomains` gaps — phase-2 should
sweep all role files, not just the three surveyed here.

## Open-finding resolution path

Phase-2 sweeps all `roles/*.json` files (not just coding/qa/verify) when
building the shared registry-host list, so any undiscovered
`allowedDomains` gap is caught and normalized during implementation, before
the human Approve on that phase-2 diff.

## Next steps

Await human Approve on `docs/issue-38/proposals/coding.md`. On approval,
phase-2 implements the frozen write set named there.

## 1. How role workspaces are created

- `spawn.py` is the single entry point that launches a role session. For a
  given `role` it loads `roles/<role>.json` (`role_settings()`,
  `spawn.py:246-318`) and merges it into a per-invocation `--settings`
  temp file (`spawn.py:1497-1500`).
- The workspace itself is `cwd` (a git worktree/checkout for the issue
  branch — see the commit-before-exit instructions built at
  `spawn.py:1490-1495`); each `spawn` invocation gets its own `cwd`.
- Toolchain caches are redirected **into the workspace**, not shared across
  spawns (`spawn.py:1508-1522`):
  ```
  wcache = os.path.join(cwd, ".muster-cache")
  GOCACHE, GOMODCACHE, GOENV, GOPATH, XDG_CACHE_HOME,
  npm_config_cache, PIP_CACHE_DIR  →  all under wcache
  ```
  The comment at `spawn.py:1509-1512` explains why: writes to `~/...` caches
  hit the sandbox filesystem boundary and stall the session on an approval
  prompt, so caches are moved under `cwd` where sandboxed writes are already
  allowed. `.muster-cache/` is added to the workspace `.gitignore`
  (`spawn.py:1380-1382`), confirming it is workspace-local, throwaway state
  — **every fresh spawn starts with an empty cache**, matching the issue's
  observed symptom (fresh workspace → cold cache → fetch → sandbox network
  denial).
- There is no code path anywhere in `spawn.py` (or elsewhere in the repo)
  that mounts, copies, or otherwise exposes a host-level package cache
  (`GOMODCACHE`, `~/.npm`, pip cache, cargo registry, `~/.m2`, etc.) into the
  workspace. The only cache-related logic is the redirection above.

## 2. How the sandbox currently blocks/allows outbound network

- The sandbox boundary is declared per role in `roles/<role>.json` under
  `sandbox.network.allowedDomains`, merged unchanged into the `--settings`
  passed to `claude -p` (`role_settings()`, `spawn.py:246-318`; no field in
  that function rewrites `sandbox.network` — only `sandbox.filesystem` paths
  are template-substituted, and `sandbox.allowUnsandboxedCommands` is forced
  to `false` at `spawn.py:316`).
- This **is already the "registry allowlist" design from the issue**, but
  applied inconsistently and by hand, per role:
  - `roles/coding.json`:
    ```json
    "sandbox": { "enabled": true, "network": { "allowedDomains": [
      "api.anthropic.com", "*.github.com", "registry.npmjs.org",
      "pypi.org", "files.pythonhosted.org", "github.com" ] } }
    ```
    npm and PyPI are allowed. **crates.io, Maven Central, and
    `proxy.golang.org` are absent** — which reproduces exactly the failure
    reported in the issue (`go build`/`go test` → `proxy.golang.org ...
    Forbidden`), because coding is the role that runs builds/tests and its
    allowlist has no Go entry at all.
  - `roles/qa.json` and `roles/verify.json`: allowlist is
    `api.anthropic.com`, `*.github.com`, `github.com` only — **no package
    registry is reachable**, even though both roles may need to build/run
    what coding produced.
  - Other role files (`feasibility.json`, `ops.json`, `product.json`,
    `reflect.json`, `review.json`, `ux-design.json`) were not individually
    audited for this survey (see `Open findings` above) but appear to follow
    the same per-role, hand-maintained `allowedDomains` shape.
- Consequence: the allowlist mechanism exists today, but it is (a)
  ecosystem-incomplete (only npm/PyPI show up anywhere in the files read; no
  crates.io/Maven/Go-proxy entries found), (b) duplicated by hand across
  every role file with no shared source of truth, and (c) silently divergent
  between roles that may all need to build the same repo.
- `role_settings()` also sets `sandbox.allowUnsandboxedCommands = False`
  unconditionally (`spawn.py:313-317`) specifically to stop a session from
  routing around a filesystem/network denial by disabling the sandbox and
  re-running the command — so a registry-allowlist gap cannot be
  "self-healed" by the session; it just fails, and the issue reports that
  sessions instead hand-copy the host's module cache in, which the issue
  calls the wrong layer, and which this survey confirms is not automated
  anywhere in this repo.

## 3. Design-relevant constraints found

- `--settings` is a **merge**, not a replacement, over user/global settings
  (module docstring, `spawn.py:8-13`) and over repo-level
  `.claude/settings.json` / `.claude/settings.local.json`
  (`spawn.py:595-609`) — any registry-allowlist or cache-mount change must
  be expressed at the layer `role_settings()` controls, or it risks being
  silently overridden by a higher-priority settings file.
- Env var resolution already has an established pattern for cross-platform,
  variable-substituted paths (`spawn.py:267-296`): role files declare
  defaults with `~`/`$VAR`, the environment can override, and
  `sandbox.filesystem` paths are substituted from the *resolved* env. Any
  read-only cache-mount design should reuse this substitution mechanism
  rather than inventing a second one.
- No `docs/decisions/` or `docs/handbooks/` directory exists in this
  checkout (only `docs/reports`, `docs/superpowers`, `docs/issue-34`,
  `docs/issue-31`, `docs/specs`, `docs/proposals`) — there is currently no
  existing ADR or handbook entry documenting the sandbox network/filesystem
  policy; the issue's acceptance criterion ("documented in protocol.md or
  README") has no existing home to extend other than `README.md` itself.
