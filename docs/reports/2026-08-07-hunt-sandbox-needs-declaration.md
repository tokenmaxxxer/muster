---
proposal: docs/issue-303/proposals/2026-08-07-sandbox-needs-declaration.md
---

# Hunt record — sandbox-needs-declaration

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: FINDING — `role_settings(role: str)` has no `cwd`/target-repo-root parameter, and neither do any of its call sites, so the proposal's plan to read `<target repo>/docs/specs/sandbox-needs.json` from inside `role_settings()` cannot be implemented without changing `role_settings()`'s signature and updating every call site (spawn.py `main()` at line 2575, `_spawn_one` at line 2991, and ~20 call sites in test_spawn.py) — a change the proposal's "What will be done" section never mentions, describing only edits to the body of `role_settings()`.
Kind: design-error
Seed: docs/issue-303/proposals/2026-08-07-sandbox-needs-declaration.md — "In `role_settings()` (spawn.py:390-520): after resolving the role file, read the target repo's `docs/specs/sandbox-needs.json` if present..."
cap_seconds: 120
tier: default
diff_stat_lines: n/a (proposal not yet implemented)
started_at: 2026-08-07T13:20:23+09:00
ended_at: 2026-08-07T13:24:00+09:00

### Reproduce
```
grep -n "def role_settings" spawn.py
# -> spawn.py:390:def role_settings(role: str) -> dict:
grep -n "role_settings(" spawn.py test_spawn.py
# every call site passes only a role string, e.g.:
# spawn.py:2575:        out = role_settings(a.role)
# spawn.py:2991:    s = role_settings(role)          # inside _spawn_one(cwd, role, ...) — cwd in scope but not passed
```

### Observed
`role_settings()` is a pure function of `role` only — it has no parameter carrying the `-C <dir>` target repo path, and none of its ~20+ call sites (production or test) pass one. The `-C` value (`a.cwd` / `_spawn_one`'s `cwd` param) is available at the call sites but never threaded into `role_settings()`.

### Expected
The proposal should list the signature change to `role_settings(role, cwd)` (or equivalent) and the resulting edits to every call site as part of the frozen write set / "What will be done", since without it there is no way for the function to locate the consumer repo's `docs/specs/sandbox-needs.json` — it can only ever see this repo's own tree (or none at all).
