---
code_under_review: spawn.py
loop_state: complete
---

# Phase 2 — Playwright cache mount (issue #304)

Implements the phase-2 half of `docs/issue-304/proposals/architecture.md`
("What will be done (phase 2, on approval)" items 1-3), approved via
`APPROVE issue-304/architecture` on the issue (single-account mode). That
proposal's recommendation was keep-with-adjusted-settings: keep
`sandbox.enabled` and `allowUnsandboxedCommands=False` unchanged, add the
one cache mount the architecture survey's Q3 measured as removing a
blocked-verification class at zero network-surface cost.

## Why

The architecture survey (PR #305) measured three things: Q1, the Bash
tool's own approval gate — not `sandbox.network.allowedDomains` — blocks
the CDN download and even an allowlisted `proxy.golang.org` curl; Q2, what
`denyRead` protects (`~/.ssh`, `~/.claude` credentials, sibling checkouts,
`runs/` state) against a role session holding a live `gh` token and
reading untrusted issue/PR input; Q3, `~/.cache/ms-playwright` exists and
is readable on this host but was absent from `PACKAGE_CACHE_DIRS`. The
recommendation drawn from those three measurements was to change nothing
about the sandbox's network/read-protection settings and add the missing
cache mount.

## What was done

- **spawn.py `PACKAGE_CACHE_DIRS`**: added
  `("PLAYWRIGHT_BROWSERS_PATH", "~/.cache/ms-playwright")`, the same
  `(env_var, default_path)` shape as the four existing entries
  (GOMODCACHE, NPM_CONFIG_CACHE, PIP_CACHE_DIR, cargo, Maven). No other
  change to that list or to how `role_settings()` mounts it — the existing
  loop (spawn.py, `role_settings()`, "호스트 패키지 캐시를 읽기 전용으로
  마운트한다") already adds any present cache dir to
  `sandbox.filesystem.allowRead`; the new entry rides that unchanged path.
- **spawn.py `playwright_cache_layer(s)`**: new function next to
  `go_proxy_layer()`, same shape — looks up the same `PACKAGE_CACHE_DIRS`
  entry, checks the host path is in the resolved `allowRead` list, returns
  the path (or `None` if not mounted). Unlike `go_proxy_layer()`'s
  multi-source `GOPROXY` fallback chain, this is a single-path redirect:
  Playwright reads exactly one `PLAYWRIGHT_BROWSERS_PATH`, no fallback
  syntax needed.
- **Wiring**: in the `issue is not None` branch of the spawn call site
  (same block that sets `GOCACHE`/`GOMODCACHE`/etc. under `.muster-cache`
  and calls `go_proxy_layer(s)`), added
  `extra_env["PLAYWRIGHT_BROWSERS_PATH"] = playwright_cache` when
  `playwright_cache_layer(s)` returns non-`None`. Role sessions only — ad
  hoc spawns (`issue is None`) get no `.muster-cache` write redirection
  either, so this follows the same boundary as `GOPROXY`.
- **ADR**: `docs/issue-304/decisions/playwright-cache-mount.md` — records
  the two-layer model (filesystem-read vs. network-approval), the rejected
  alternative (allowlisting the CDN host, which Q1 showed would not have
  worked since allowlist membership didn't correlate with the actual
  block), and the scope note below.

## What did not work

None. The change is a mechanical mirror of the existing `go_proxy_layer()`
pattern; no dead end encountered.

## Effect verification

Ran against this host directly (no network/CDN access needed for this
check — it verifies the mount and env wiring, the two things `spawn.py`
controls):

1. `python3 -c "import ast; ast.parse(open('spawn.py').read())"` — syntax
   check passes after the edit.
2. Loaded `spawn.py` and called `role_settings("release-engineering")` (a
   sandbox-enabled role): confirmed
   `/home/<user>/.cache/ms-playwright` appears in the resulting
   `sandbox.filesystem.allowRead` (the existing `PACKAGE_CACHE_DIRS` mount
   loop picked up the new entry with no code change needed there), and
   `playwright_cache_layer(s)` on that same settings dict returns that
   same path.
3. Confirmed the mount touches only `sandbox.filesystem.allowRead` — the
   `PACKAGE_CACHE_DIRS` mount loop (spawn.py, `role_settings()`) never
   writes to `sandbox.network.allowedDomains`, and neither does
   `playwright_cache_layer()`; no host was added to
   `PACKAGE_REGISTRY_HOSTS` or `WEB_ACCESS_DOMAINS`. This confirms the
   stated Q3 property (cache mounts widen no network surface) still holds
   for the new entry — checked by inspection of the two code paths, since
   they are disjoint by construction (one function only ever appends to
   `filesystem.allowRead`, the other only ever reads it).
4. Did not run an actual Playwright browser launch inside a live
   sandboxed role session (would need a role invocation with a Playwright
   dependency present and network instrumentation to observe an
   approval-gate prompt) — verified instead, per item 2-3, that the
   mechanism a Playwright launch would depend on
   (`PLAYWRIGHT_BROWSERS_PATH` resolving to the mounted, readable host
   path before any browser download is attempted) is correctly wired.
   This is the same class of evidence the architecture survey's own "How
   this will be verified" section named as sufficient: mount appears in
   `allowRead`, `PLAYWRIGHT_BROWSERS_PATH` resolves to it.

## Open findings

None outstanding. Item 4 under "Effect verification" above is a known
limit, not a finding: a live Playwright CDN-approval-gate observation
inside a sandboxed role session was not run this session (no Playwright
dependency staged in this checkout to trigger a real launch), so the claim
is scoped to "the wiring the launch depends on is correct," not "a launch
was observed to skip the approval prompt."

## Scope note (per issue #303)

This is a per-incident addition to a hardcoded list
(`PACKAGE_CACHE_DIRS`), not a general fix. Issue #303 exists to replace
the cache-enumeration pattern with a consumer-side declaration; this
change follows the existing pattern precisely because #303 has not landed
yet. Do not read this as "the general fix for cache-mount extensibility"
— it addresses only the one blocked-verification class #304's Q3
measured.

## Doc placement

- `docs/issue-304/decisions/playwright-cache-mount.md` — library/pattern
  choice (cache-mount + env-redirect vs. CDN-host allowlisting), same
  commit.

## Hunt cadence

Headless single-shot session (contract v3 s22): no background
warrant-hunter dispatch this turn — a dispatch whose result is not
consumed before the turn ends is prohibited, and there is no further turn
in this session to consume it. No closed_checks entries beyond the
effect-verification steps above.
