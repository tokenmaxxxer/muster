# QA phase-1 survey — issue #38

## Scope
QA the merged issue #38 change (PR #39, commit 8bda829): `role_settings()` in
`spawn.py` merges a shared official-registry allowlist into every sandboxed
role's `allowedDomains`, probes host package-cache dirs (Go/npm/pip/cargo/
Maven) and read-only-mounts present ones, and layers `GOPROXY` so a mounted
host `GOMODCACHE` is actually consulted on `--issue` spawns.

## App-up confirmation
```
$ python3 spawn.py
프로젝트: muster-issue-38-qa   경로: ...
subject: issue-38
  [qa] loop_state: (none yet)
...
보드가 누구를 깨우는지: spawn.py wake
```
Exit 0 — `spawn.py` is a CLI invoked directly, no server/daemon to boot.

## What landed (read, not yet executed as verdict)
- `spawn.py:39-50` — `PACKAGE_REGISTRY_HOSTS` (8 official registry hosts:
  npm, PyPI x2, Go proxy x2, crates.io x2, Maven Central) and
  `PACKAGE_CACHE_DIRS` (5 `(env_var, default_path)` pairs; cargo's entry has
  `env_var=None`, always uses the default path).
- `spawn.py:52-68` — `go_proxy_layer(s)`: reads the mounted `GOMODCACHE`
  host path from `s["sandbox"]["filesystem"]["allowRead"]`; if present,
  returns a `file://<host>/cache/download,https://proxy.golang.org,direct`
  GOPROXY string; else `None`.
- `spawn.py:344-352` — `role_settings()`: if `sandbox.enabled`, appends each
  `PACKAGE_REGISTRY_HOSTS` host to `sandbox.network.allowedDomains` that
  isn't already present (dedup, doesn't clear role-declared domains).
- `spawn.py:354-368` — for each `PACKAGE_CACHE_DIRS` entry, resolves the
  path (env var if set, else default, `expanduser`+`expandvars`), and if
  `os.path.exists()`, appends to `sandbox.filesystem.allowRead` (dedup).
  Absent dirs are skipped silently — no error, no stderr line.
- `spawn.py:1592-1598` (inside `_spawn_one`, `if issue is not None:` branch
  only) — after computing `extra_env` that redirects `GOMODCACHE`,
  `npm_config_cache`, `PIP_CACHE_DIR` etc. to workspace `.muster-cache/`,
  calls `go_proxy_layer(s)` and sets `extra_env["GOPROXY"]` if non-None.
  This only fires on `--issue` spawns; plain attended/unattended spawns
  never call `go_proxy_layer` or redirect `GOMODCACHE`.
- `roles/qa.json` (and other role files) still declare only
  `api.anthropic.com`, `*.github.com`, `github.com` in `allowedDomains` —
  the registry hosts are merged in-memory by `role_settings()`, not written
  back to the role JSON files.
- `test_spawn.py` — new `PackageRegistryAccess` class, 5 tests: registry
  hosts merged, present cache dir added to `allowRead`, absent cache dir
  skipped without error, `go_proxy_layer` prefers mounted host cache,
  `go_proxy_layer` is `None` when cache not mounted.
- `README.md` — new "Package-registry access (issue #38)" section:
  documents the two mechanisms and explicitly states the GOPROXY layering
  is wired for **Go only**; npm/pip/cargo/Maven caches are mounted
  read-only but their tools' cache env vars are unconditionally redirected
  to the empty workspace cache on `--issue` spawns, so for those
  ecosystems the registry allowlist — not the cache mount — is what
  actually avoids a network-denial failure today. States the trade-off:
  cache mount is read-only/low-risk, registry allowlist reopens outbound
  network to a fixed host set (package install = code execution).

## Existing test convention
`python3 -m unittest test_spawn.py` (stdlib unittest, no pytest).

## Acceptance criteria (from issue #38)
1. A spawned role session in a fresh workspace can build/test a project
   whose deps are present in host cache or fetchable from an allowed
   registry, without per-session improvisation.
2. The chosen mechanism and its security trade-off are documented
   (protocol.md or README) — landed as a README.md section.

## Edge cases not obviously covered by existing tests — targets for phase 2
- Cache dir that **exists but is empty**: `os.path.exists()` is true for an
  empty dir, so it should still be added to `allowRead` — confirm by
  execution, not just reading the `os.path.exists` call.
- Env var pointing to a **file, not a directory**: `os.path.exists()` is
  true for files too, so a misconfigured `GOMODCACHE=/path/to/a/file` would
  be added to `allowRead` as if it were a mountable directory — worth
  confirming whether this is silently accepted (a `sandbox.filesystem`
  mount of a file path may behave differently than a dir, or may just be
  inert) and whether `go_proxy_layer`'s `file://` URL construction breaks.
- **`allowedDomains` merge with pre-existing repo sandbox settings**: does
  a role JSON that already declares extra domains (or a future role with a
  differently-shaped `sandbox.network` block) keep those domains after the
  merge, and does merge order matter (dedup uses `if host not in domains`,
  so pre-existing duplicates of a registry host are not doubled)?
- **Real spawned session can actually read a mounted cache**: the unit
  tests only check that `role_settings()`'s returned dict contains the
  right `allowRead` entries — none of them actually launch a sandboxed
  Claude session and read a file from the mounted path. This is the gap
  between "settings say readable" and "sandbox enforces it" — needs an
  actual `--dry-run` or real spawn probe.
- Non-`--issue` spawn path: `go_proxy_layer` and the `GOMODCACHE`
  workspace-redirect are both gated on `if issue is not None:` — for a
  plain attended spawn, is the mounted host `GOMODCACHE` (added to
  `allowRead`) ever actually consulted, or is this cache-mount effectively
  dead for non-issue spawns?
