# Coding phase-1 survey — issue #58

## How WebSearch/WebFetch are denied today

Checked all 9 role files (`roles/*.json`) and `spawn.py`. Finding: **denial is
domain-level, not tool-level.**

- No role file sets `disallowedTools`/`allowedTools` naming `WebSearch` or
  `WebFetch`. Grepping `spawn.py` and `roles/*.json` for those tool names
  finds nothing — the harness never blocks the tools by name.
- Every role's `sandbox.network.allowedDomains` is identical:
  `api.anthropic.com`, `*.github.com`, `github.com` (checked all 9 files).
  This is the issue-38 baseline plus `PACKAGE_REGISTRY_HOSTS` merged in at
  `role_settings()` (`spawn.py:344-352`) for sandboxed roles only.
- `WebFetch` needs to reach whatever host the fetched URL names — arbitrary,
  not knowable in advance. None of those hosts are in any role's allowlist,
  so every fetch outside the 3 allowed hosts hits the sandbox network
  boundary and is denied. `WebSearch`'s result-page fetches are similarly
  denied for the same reason. This matches the issue's cited symptom
  (issue #43: 3/6 survey targets unverified).
- The issue-38 mechanism this issue extends: `PACKAGE_REGISTRY_HOSTS` (a
  fixed short list) merged additively into every sandboxed role's
  `allowedDomains` inside `role_settings()` (`spawn.py:344-352`), never
  removing role-declared domains, never duplicating existing hosts. Same
  function, same merge shape — this issue needs the same location, a
  different domain set.

## Why a fixed host list does not fit this case

`PACKAGE_REGISTRY_HOSTS` works because package registries are a small,
enumerable set of official hostnames. Web search/fetch targets are not
enumerable — the whole point is reaching whatever page a search or an
in-context URL names. A fixed list would defeat the feature (issue #43's
exact failure). The minimal correct shape is an **open/wildcard domain
entry**, not a longer fixed list.

## Proposed minimal change

Add one new domain entry to the same merge block `role_settings()` already
runs for `PACKAGE_REGISTRY_HOSTS` (`spawn.py:344-352`), applied to **all**
sandboxed roles per the operator's option-B decision — no new role-level
flag, no per-role opt-in list, since every role gets it. Concretely: a
`WEB_ACCESS_DOMAINS = ["*"]`-shaped constant merged into
`sandbox.network.allowedDomains` the same additive/dedup way
`PACKAGE_REGISTRY_HOSTS` already is. Package-registry hosts and cache mounts
(`PACKAGE_CACHE_DIRS`, `go_proxy_layer()`) are untouched — different
constant, same merge call, no interaction between them.

Open question carried into phase 2: whether Claude Code's sandbox schema
accepts a literal wildcard `"*"` for `allowedDomains` (existing entries use
subdomain wildcards like `*.github.com`, not a bare `*`) — needs a quick
spawn-and-inspect check before landing, same as issue-38's qa did for its
merge behavior. If a bare `*` is not accepted, the fallback is whatever the
schema's documented "allow all" spelling is; this does not change the merge
site or the shape of the change, only the literal value.

Trade-off documentation lands in `README.md` immediately after the existing
"Package-registry access (issue #38)" section, following that section's own
structure (mechanism, then an explicit "Trade-off, explicit:" paragraph) —
per the issue's requirement to mirror it. Content: opening every role to
arbitrary web content widens the prompt-injection surface for
code-writing roles (a fetched page can contain instructions), and the
compensating control is muster's human gate chain (phase-1 proposal → human
Approve → PR diff review → human merge), not a technical filter on fetched
content.
