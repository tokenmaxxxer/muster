# Decision — add a Playwright browser-cache mount, not a sandbox change

## Context

Issue #304's architecture survey (PR #305) measured that the CDN-download
block on `playwright.azureedge.net` is caused by the Bash tool's own
approval gate, a layer independent of `sandbox.network.allowedDomains`.
Disabling the sandbox would not touch that gate. The one blocked-
verification class the survey could directly confirm — browser-binary
acquisition — has a fix that needs no network change at all:
`~/.cache/ms-playwright` exists and is readable on the host but was
missing from `PACKAGE_CACHE_DIRS` (spawn.py:119-125).

## Decision

Add `("PLAYWRIGHT_BROWSERS_PATH", "~/.cache/ms-playwright")` to
`PACKAGE_CACHE_DIRS`, and add `playwright_cache_layer()` (spawn.py, next to
`go_proxy_layer()`) that redirects `PLAYWRIGHT_BROWSERS_PATH` to the
mounted path when `role_settings()` has added it to
`sandbox.filesystem.allowRead`. Wired at the same call site as
`GOPROXY` (spawn.py, near `extra_env["GOPROXY"] = proxy`), for `issue is
not None` sessions only — i.e. role sessions, not ad-hoc spawns.

Two independent layers exist here, and this decision only touches one:

```
[layer 1] sandbox.filesystem.allowRead/denyRead   -- host filesystem reach
[layer 2] sandbox.network.allowedDomains + Bash approval gate -- outbound network
```

The Playwright cache mount is entirely layer 1: a read-only host-path
grant, same mechanism as the existing Go/npm/pip/cargo/Maven cache mounts.
It adds zero entries to `allowedDomains` and touches no network-layer
setting — it removes the *need* for the CDN fetch by making a local
binary source available first, rather than exempting the CDN host from
the approval gate.

## Alternative rejected

Add `playwright.azureedge.net` (and mirrors) to `PACKAGE_REGISTRY_HOSTS` so
the CDN fetch itself would be allowlisted. Rejected: survey Q1 measured
that allowlisting a host in `PACKAGE_REGISTRY_HOSTS` does not exempt it
from the Bash tool's approval gate (`proxy.golang.org` is allowlisted and
still blocked) — this alternative would not have fixed the failure it
targets, and it would have widened `allowedDomains`, the exact axis Q1
showed to be uncorrelated with the actual block.

## Scope note

This is a per-incident addition to a hardcoded list
(`PACKAGE_CACHE_DIRS`), the same shape as the four caches already there.
Issue #303 exists to replace that enumeration pattern with a consumer-side
declaration; this change follows the existing pattern because #303 has not
landed, and is not presented as a general fix for cache-mount
extensibility — only as the fix for the one blocked class #304 measured.

## Status

Landed, issue-304/implementation phase 2.
