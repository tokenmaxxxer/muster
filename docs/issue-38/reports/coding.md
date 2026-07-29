---
kind: coding-record
loop_state: phase-2-complete
what-was-done: "Phase-2 implementation of issue #38's approved proposal (PR #39 Approve). Added PACKAGE_REGISTRY_HOSTS and PACKAGE_CACHE_DIRS constants to spawn.py; role_settings() now (a) merges the registry host list into every sandboxed role's sandbox.network.allowedDomains, deduped, additive-only, and (b) probes each candidate host package-cache dir with os.path.exists and adds present ones to sandbox.filesystem.allowRead (read-only, never write). Removed the now-redundant hand-curated npm/PyPI entries from roles/coding.json (other role files had none to remove). Documented the mechanism and its security trade-off in README.md. Added go_proxy_layer() and wired it into the --issue spawn's extra_env so Go actually reads the mounted host GOMODCACHE via GOPROXY file-source layering (fix for a warrant-hunter finding -- see resolved_findings). 5 new test_spawn.py cases total. Full suite: 40 passed."
why: "PR #39 carries a human Approve comment on issue-38/coding, satisfying contract v3 s19's phase-2 gate."
upstream-basis: "docs/issue-38/proposals/coding.md (frozen write set, hybrid design); docs/issue-38/reports/coding.md phase-1 survey (this file, superseded above the line by this phase-2 update)."
next-steps: "None open for this issue. Follow-ups the proposal named as out-of-scope (per-repo allowlist opt-out, private registries) belong to a new issue if wanted. One residual, documented-not-fixed gap: npm/pip/cargo/Maven read-only cache mounts are added to allowRead but not wired into an active read path the way Go's GOPROXY layering is -- those ecosystems currently rely on the registry allowlist, not the cache mount, to avoid network denial. A follow-up issue could extend the GOPROXY-style layering per ecosystem if the cache-hit benefit (vs. network fetch through the allowlist) turns out to matter."
open-findings: "None blocking."
open-finding-resolution-path: "N/A — no open findings."
resolved_findings:
  - finder: "coding:warrant-hunter (dispatched by this role before phase-2 completion, per hunt-cadence)"
    finding: "role_settings()'s PACKAGE_CACHE_DIRS probe mounts host GOMODCACHE/npm/pip caches read-only into allowRead, but spawn()'s existing .muster-cache write-redirection (spawn.py ~1565-1573) unconditionally points the same package-manager env vars at fresh empty workspace dirs, so the mounted host cache was silently never consulted -- defeating the cache-mount half of the feature for the primary --issue spawn path."
    resolution: "Added go_proxy_layer(s) (spawn.py, new function near _mkt) and wired it into the extra_env block: when the host GOMODCACHE candidate is present in sandbox.filesystem.allowRead, GOPROXY is set to 'file://<host>/cache/download,https://proxy.golang.org,direct' so go build/test reads the host cache without attempting a write against the read-only mount; GOMODCACHE itself stays workspace-local/writable, unchanged. Added 2 tests (go_proxy_layer prefers mounted cache; returns None when not mounted) -- suite now 40 passed. npm/pip/cargo/Maven were NOT given equivalent layering (their package managers require cache-dir write access even on cache hits, so a read-only mount can't substitute cleanly without deeper per-tool wrapping) -- documented as a known, honest limitation in README.md and in next-steps above rather than silently left inert or overclaimed as fixed."
closed_checks:
  - check: "role_settings() output for a sandboxed role includes all PACKAGE_REGISTRY_HOSTS entries in allowedDomains, without dropping role-declared domains"
    code_sha: "working-tree HEAD (issue-38/coding, pre-commit) — see git diff in this PR"
  - check: "a present host cache dir (verified via a temp dir + GOMODCACHE env override) is added to sandbox.filesystem.allowRead, read-only, not allowWrite"
    code_sha: "working-tree HEAD (issue-38/coding, pre-commit) — see git diff in this PR"
  - check: "an absent host cache dir path does not raise and is not added to allowRead"
    code_sha: "working-tree HEAD (issue-38/coding, pre-commit) — see git diff in this PR"
  - check: ".muster-cache write-redirection block (spawn.py ~1508-1522, GOCACHE/GOMODCACHE/GOENV/GOPATH/XDG_CACHE_HOME/npm_config_cache/PIP_CACHE_DIR) left untouched by this change; the new host-cache-mount source and the workspace write-redirect target are distinct code paths"
    code_sha: "working-tree HEAD (issue-38/coding, pre-commit) — see git diff in this PR"
  - check: "go_proxy_layer() returns the file:// GOPROXY source only when the host GOMODCACHE candidate is actually present in sandbox.filesystem.allowRead, and None otherwise (verified by both new tests)"
    code_sha: "working-tree HEAD (issue-38/coding, pre-commit) — see git diff in this PR"
---

# Issue #38 — Phase-2 execution record: package-registry access for role workspaces

## What was done

Implemented exactly the frozen write set from `docs/issue-38/proposals/coding.md`
after PR #39's human Approve:

1. **`spawn.py`** — added `PACKAGE_REGISTRY_HOSTS` (npm, PyPI, Go module
   proxy + sumdb, crates.io, Maven Central) and `PACKAGE_CACHE_DIRS`
   (Go modcache, npm cache, pip cache, cargo registry, Maven local repo —
   each as an `(env_var_or_None, default_path)` pair) as module constants.
   `role_settings()` gained two additive blocks, both gated on
   `sandbox.enabled`:
   - merges `PACKAGE_REGISTRY_HOSTS` into `sandbox.network.allowedDomains`,
     skipping hosts already present, never removing a role-declared domain;
   - resolves each `PACKAGE_CACHE_DIRS` candidate (env override or default,
     `expanduser`/`expandvars`, matching the existing role-file env
     resolution pattern) and, only if `os.path.exists` is true, appends it to
     `sandbox.filesystem.allowRead`. Absent directories are silently
     skipped — no error, no output, matching the proposal's
     open-finding-resolution-path.
   Both blocks sit before the existing "disable all global plugins" section
   and do not touch the `.muster-cache` write-redirection env vars set later
   in the code (different function, different concern — the host cache
   mount reads from the host's real cache location; the redirection still
   points toolchain writes into the per-workspace `.muster-cache/`).
2. **`roles/coding.json`** — removed the hand-curated
   `registry.npmjs.org`/`pypi.org`/`files.pythonhosted.org` entries (now
   supplied uniformly by `role_settings()` for every sandboxed role). The
   other 8 role files had no package-registry entries to remove.
3. **`README.md`** — added a "Package-registry access (issue #38)" section
   next to the existing sandbox/hardening notes: describes both mechanisms
   and states the security trade-off (read-only cache mount is low-risk;
   registry allowlist reopens outbound network to a fixed host set and
   accepts that package install is a code-execution path, scoped to
   official registries only).
4. **`test_spawn.py`** — added `PackageRegistryAccess` with 3 cases: registry
   hosts merged into `allowedDomains`, a present cache dir (simulated via a
   temp dir + `GOMODCACHE` env override) added to `allowRead`, an absent
   cache dir path skipped without raising.

One correction made during integration (not by the delegated worker): the
worker's first draft mapped `CARGO_HOME` directly as the probed path, but
`CARGO_HOME` conventionally points at `~/.cargo` (parent of `registry/`), not
the registry cache itself — using it directly as the mount source would have
mounted the wrong directory whenever a host had `CARGO_HOME` set. Changed to
`(None, "~/.cargo/registry")` so it always probes the correct fixed default
rather than trusting an env var whose semantics don't match what's being
probed; `os.environ.get(None, ...)` would also have raised `TypeError`, so
the lookup loop was guarded to skip the env-override branch when `env_var is
None`.

## What did not work

- First implementation used `("CARGO_HOME", "~/.cargo/registry")` in
  `PACKAGE_CACHE_DIRS` — expected: if `CARGO_HOME` is set, use it as the
  registry cache path; actual: `CARGO_HOME` points at the parent `~/.cargo`
  directory, not `~/.cargo/registry`, so using it directly would mount the
  wrong (or a non-cache) directory, and `os.environ.get(None-turned-string,
  ...)` was never the actual bug — the real bug was semantic mismatch, not a
  crash. Fixed by dropping the env-var override for this one entry (`env_var
  = None`) and always probing the fixed default path.

## Test run

`python3 -m pytest test_spawn.py -q` → `40 passed in 0.23s` (run from repo
root on `issue-38/coding` after all changes above, including the CARGO_HOME
fix and the go_proxy_layer fix for the warrant-hunter finding).

## Hunt

Dispatched `coding:warrant-hunter` before phase-2 completion, per hunt
cadence. It returned one finding: the read-only host cache mount
(`sandbox.filesystem.allowRead`) was silently defeated for `--issue` spawns
because the existing `.muster-cache` env-var redirection unconditionally
overrides the same package-manager cache env vars to fresh workspace paths
after `role_settings()` runs — so the mounted host cache was never actually
read. Fixed for Go via `GOPROXY` file-source layering (see
`resolved_findings` above); documented as an honest, unfixed limitation for
npm/pip/cargo/Maven, whose tools require cache-dir write access even on
reads and so can't take the same fix without deeper per-tool wrapping
(out of scope for this frozen write set). Test suite re-run after the fix:
40 passed.
