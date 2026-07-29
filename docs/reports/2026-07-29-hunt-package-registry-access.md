---
proposal: docs/issue-38/proposals/coding.md
---

# Hunt record — package-registry-access

## after-proposal — stance 1: does the cache-dir probe's env-lookup ordering matter?

Verdict: FINDING — for `--issue N` sessions, `role_settings()` mounts the host's real GOMODCACHE/NPM_CONFIG_CACHE/PIP_CACHE_DIR read-only, but `_spawn_one` later overrides those same env vars to fresh, empty, per-workspace `.muster-cache/...` paths that were never mounted — so the mounted host cache is silently never used by the tools that read those env vars.

Kind: composition

Seed: git diff spawn.py — PACKAGE_CACHE_DIRS probe added in role_settings() (spawn.py ~L332-345); pre-existing wcache env override in spawn.py ~L1565-1573 (`extra_env.update({"GOMODCACHE": os.path.join(wcache, "gomod"), "npm_config_cache": ..., "PIP_CACHE_DIR": ...})`), applied to the child process only, computed and merged *after* `role_settings(role)` is already called at spawn.py:1550.

### Reproduce
```
python3 - <<'PYEOF'
import os, sys, tempfile
sys.path.insert(0, ".")

host_cache = tempfile.mkdtemp()
open(os.path.join(host_cache, "example.com@v1.0.0"), "w").close()
os.environ["GOMODCACHE"] = host_cache

import spawn
s = spawn.role_settings("coding")
mounted = s["sandbox"]["filesystem"].get("allowRead", [])
print("allowRead (host cache mounted read-only):", mounted)
assert host_cache in mounted

# what _spawn_one actually sets for the child process on `--issue N` runs
# (spawn.py L1565-1573), computed AFTER role_settings() already ran:
cwd = "/some/isolated/workspace"
wcache = os.path.join(cwd, ".muster-cache")
extra_env_gomodcache = os.path.join(wcache, "gomod")
print("actual child-process GOMODCACHE:", extra_env_gomodcache)
print("mounted host cache == child's real GOMODCACHE?", host_cache == extra_env_gomodcache)
PYEOF
```

### Observed
```
allowRead (host cache mounted read-only): ['/tmp/.../tmp1775zh2j', '/home/jwjung/.npm']
actual child-process GOMODCACHE: /some/isolated/workspace/.muster-cache/gomod
mounted host cache == child's real GOMODCACHE? False
```
The read-only allow-list grants access to the host's real package cache, but for every issue-based session (the primary spawn path — `spawn.py:1561-1573`) the child process's `GOMODCACHE`/`npm_config_cache`/`PIP_CACHE_DIR` are unconditionally rewritten to empty, workspace-local `.muster-cache/...` directories that are never added to `allowRead`. Go/npm/pip inside the sandbox therefore never see the mounted host cache at all — every module still gets refetched over the network allow-list the same PR added, silently defeating the entire point of PACKAGE_CACHE_DIRS for the one code path (`--issue`) that issue #38's own coding-record cites as the motivating failure ("go build 를 한 번도 못 돌림").

### Expected
Either the wcache override should not clobber `GOMODCACHE`/cache env vars when a matching host cache was already mounted read-only, or `role_settings()`'s cache probe/allowRead list should be computed using the same resolved env the child process will actually run with (post-wcache-override), so the mounted directory and the env var the tooling reads always agree.
