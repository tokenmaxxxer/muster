# QA phase-2 proposal — issue #38

## Plan
1. Run the full `test_spawn.py` suite (not just `PackageRegistryAccess`) —
   confirm no regression elsewhere, evidence via command+output.
2. Verify acceptance criteria by execution:
   - AC1 (fresh workspace can build/test using cache-or-registry): probe via
     `role_settings("coding")` / `--dry-run` output showing merged
     `allowedDomains` and, when a cache dir is present on this host,
     `allowRead` containing it.
   - AC2 (documented): confirm README.md section exists and matches the
     shipped behavior (already read in survey; re-check for drift against
     current `spawn.py`).
3. Probe edge cases by direct execution, not reading:
   - Empty-but-existing cache dir → `role_settings()` output.
   - Env var pointing at a file, not a directory → `role_settings()` output,
     and `go_proxy_layer()` behavior with that path.
   - `allowedDomains` merge against a role/settings dict that already
     carries extra domains or duplicate registry hosts → confirm dedup and
     no loss of pre-existing entries.
   - A real spawned sandboxed session actually reading a file from a
     mounted cache path (vs. only settings-dict inspection) — via
     `--dry-run` composed command inspection and, if feasible within the
     timebox, an actual sandbox probe.
   - Non-`--issue` spawn path: confirm whether `GOPROXY` layering/GOMODCACHE
     handling applies or is silently absent.
4. Record every verdict (pass/fail/blocked) with command+output evidence in
   `docs/issue-38/reports/qa.md`.

## Timebox
~40 minutes of execution.

## Deliverable
`docs/issue-38/reports/qa.md` (session sheet: time breakdown, evidenced
findings, loop_state updates) + any `UNFILED(...)` bug reports if defects
are confirmed by reproduction.
