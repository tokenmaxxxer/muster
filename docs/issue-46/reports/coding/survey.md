# Issue #46 — Phase 1 Survey: cache-dir probe mounts a file as a cache dir

## Source

GitHub issue #46, filed by QA during review of issue #38 / PR #41 (edge case
4b, previously unfiled).

## Defect

`role_settings()` in `spawn.py` builds the host package-cache mount list for
sandboxed roles. The probe that decides whether a cache-dir env var (e.g.
`GOMODCACHE`) is eligible to be mounted read-only is at:

- `spawn.py:364` — `if os.path.exists(cache_path):`

`os.path.exists` returns `True` for both directories and regular files. If a
cache env var points at a *file* instead of a directory, that file passes the
check and gets appended to `sandbox.filesystem.allowRead`, mounting a file
into the sandbox as though it were a cache directory. This is the wrong trust
boundary: the intent (per the comment at spawn.py:355-356, "존재하는
디렉터리만 추가한다") is directory-only, but the code only checks existence.

## Fix shape

One-line change: replace `os.path.exists(cache_path)` with
`os.path.isdir(cache_path)` at spawn.py:364. `os.path.isdir` returns `False`
for both a missing path and an existing non-directory (file, symlink-to-file,
etc.), so it subsumes the existing "absent path is skipped silently" behavior
already covered by `test_absent_cache_dir_is_skipped_without_error` and adds
the missing "non-directory path is skipped" behavior.

No other call sites reference `cache_path` or this probe; the loop body
(lines 361-368) is otherwise unaffected.

## Test location

`test_spawn.py`, class `PackageRegistryAccess` (line 195), which already
holds the issue #38 cache-mount test cases:

- `test_present_cache_dir_added_to_allow_read` (line 204)
- `test_absent_cache_dir_is_skipped_without_error` (line 218)
- `test_go_proxy_layer_prefers_mounted_host_cache` (line 232)
- `test_go_proxy_layer_none_when_cache_not_mounted` (line 247)

Phase 2 will add a new case, e.g. `test_file_cache_dir_is_skipped_without_error`,
alongside these, following the same `GOMODCACHE` env-var save/restore pattern:
point `GOMODCACHE` at a regular file (via `tempfile.NamedTemporaryFile`) and
assert the file path is NOT present in `allowRead` after `spawn.role_settings("coding")`.

## Scope confirmation

This is confirmed to be a one-line source fix (`os.path.exists` →
`os.path.isdir`) plus one new test method in an existing test class. No other
files are implicated.
