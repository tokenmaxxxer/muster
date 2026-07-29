# Coding phase-1 proposal — issue #58

files:
- spawn.py
- README.md
- test/test_spawn.py (if a test file for spawn.py already exists — verify path in phase 2 before writing)

## Request (paraphrased intent)

Every spawned role session is currently sandboxed to 3 network hosts
(`api.anthropic.com`, `*.github.com`, `github.com`), which silently denies
WebSearch/WebFetch for all roles. The operator picked option B: give every
role — not just research roles — real web search/fetch access, extending
the issue-38 `allowedDomains` merge mechanism in `role_settings()`. The
accepted prompt-injection trade-off must be documented next to the issue-38
note.

## Constraints

- Extend the existing merge mechanism (`spawn.py:344-352`), do not invent a
  parallel path.
- Package-registry allowlist and cache-mount behavior (`PACKAGE_REGISTRY_HOSTS`,
  `PACKAGE_CACHE_DIRS`, `go_proxy_layer()`) must be unchanged.
- Applies to every sandboxed role uniformly (option B) — no per-role opt-in.
- Trade-off note placed next to the issue-38 note in README, mirroring its
  structure.

## What will be done

1. Add a new module-level constant in `spawn.py` (name TBD at implementation
   time, e.g. `WEB_ACCESS_DOMAINS`) holding whatever the sandbox schema's
   documented "allow all outbound domains" value is (candidate: `["*"]`;
   confirmed against the schema during phase-2 execution, per the open
   question in the phase-1 survey).
2. In `role_settings()`, merge this constant into every sandboxed role's
   `sandbox.network.allowedDomains` the same additive, dedup-safe way
   `PACKAGE_REGISTRY_HOSTS` is merged today (same code block,
   `spawn.py:344-352`, extended rather than duplicated).
3. Add a README section immediately after "Package-registry access (issue
   #38)" documenting the mechanism and, explicitly, the prompt-injection
   trade-off: arbitrary fetched web content can carry instructions aimed at
   the agent; the compensating control is muster's existing human gate
   chain (phase-1 proposal → human Approve → PR diff review → human merge),
   which stays the final defense — no technical content filter is added.
4. Extend `test/test_spawn.py` (or wherever issue-38's `allowedDomains`
   merge tests live — confirmed by grep in phase 2) with a case asserting
   the web-access domain entry is present in a sandboxed role's merged
   `allowedDomains` alongside the registry hosts, and that role-declared
   domains and `PACKAGE_REGISTRY_HOSTS` are unaffected.

## Out of scope

- Any change to `PACKAGE_REGISTRY_HOSTS`, `PACKAGE_CACHE_DIRS`, or
  `go_proxy_layer()`.
- Per-role opt-out or narrower-than-all-roles gating (issue explicitly
  chose option B).
- A content filter, sanitizer, or injection-detection layer on fetched web
  content — the issue names the human gate chain as the compensating
  control, not a technical filter.
- Non-sandboxed roles (none currently exist — all 9 role files have
  `sandbox.enabled: true`; if that ever changes, out of scope here).

## How it'll be known to work

A spawned role's resolved settings (`role_settings()` output, same way
issue-38's qa verified its merge — direct function call, inspect the
returned dict) show the web-access domain entry present in
`sandbox.network.allowedDomains` for every role, with
`PACKAGE_REGISTRY_HOSTS` and role-declared domains still present and
undeduped-away. A live spawned session (any role) can execute a WebSearch
and a WebFetch against an arbitrary URL without a sandbox network denial.
`test_spawn.py` passes, full suite, alongside the existing issue-38 cases.
