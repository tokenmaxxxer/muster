# Proposal: fix cache-dir probe to require a directory (issue #46)

files:
- spawn.py
- test_spawn.py

## Request

Fix the cache-dir eligibility probe in `role_settings()` (`spawn.py:364`),
which currently uses `os.path.exists` and therefore treats a cache env var
(e.g. `GOMODCACHE`) pointing at a regular file the same as one pointing at a
real cache directory — mounting that file read-only into the sandbox
(`sandbox.filesystem.allowRead`). Use `os.path.isdir` instead so a
non-directory path is skipped exactly like an absent path already is. Add a
regression test next to the existing `PackageRegistryAccess` cache-mount
cases in `test_spawn.py`.

No secrets involved; this is a pure logic/trust-boundary fix reported by QA
against issue #38 / PR #41.

## Constraints

- Minimal, single-purpose change: only the probe condition at spawn.py:364
  changes. No refactor of the surrounding loop, no behavior change for
  directories or absent paths.
- New test lives inside the existing `PackageRegistryAccess` test class in
  `test_spawn.py`, following the same env-var save/restore pattern already
  used by its sibling tests (`test_present_cache_dir_added_to_allow_read`,
  `test_absent_cache_dir_is_skipped_without_error`).
- Work-in-English policy: code/comments/commit/PR in English.
- Phase 2 (actual code change) only proceeds after this proposal is reviewed
  and approved by a human.

## What will be done

1. In `spawn.py`, change the condition at line 364 from
   `if os.path.exists(cache_path):` to `if os.path.isdir(cache_path):`.
2. In `test_spawn.py`, add a new test method to `PackageRegistryAccess`
   (e.g. `test_file_cache_dir_is_skipped_without_error`) that:
   - creates a temporary regular file (`tempfile.NamedTemporaryFile`),
   - sets `GOMODCACHE` to that file's path,
   - calls `spawn.role_settings("coding")`,
   - asserts the file path is NOT present in
     `out["sandbox"]["filesystem"].get("allowRead", [])`,
   - restores the prior `GOMODCACHE` value in a `finally` block, matching the
     existing tests' cleanup pattern.

## Out of scope

- Any other cache-dir-related logic (e.g. `.muster-cache` write redirection,
  `go_proxy_layer`) — unaffected and untouched.
- Symlink edge cases beyond what `os.path.isdir` already resolves.
- Any change to `PACKAGE_CACHE_DIRS`, `PACKAGE_REGISTRY_HOSTS`, or other
  issue #38 mount/allowlist behavior.

## How we'll know it worked

- The new test in `PackageRegistryAccess` passes: pointing `GOMODCACHE` at a
  file results in that file path being absent from
  `sandbox.filesystem.allowRead`, mirroring the existing absent-path test.
- All pre-existing `PackageRegistryAccess` tests (directory-mount,
  absent-path-skip, go-proxy-layer cases) continue to pass unchanged, showing
  the fix does not regress the directory-mount or absent-path behavior.
