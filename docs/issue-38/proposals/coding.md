---
kind: coding-record
loop_state: proposal-pending-approval
what-was-done: "Build proposal for issue #38: hybrid design combining a shared read-only host package-cache mount (default) with a per-role, centrally-defined registry allowlist (existing mechanism, normalized and extended). Frozen write set named below. No production code touched -- proposal only, awaiting human Approve before phase-2."
why: "Contract v3 s11 requires an approved proposal with a frozen write set before any spawn.py/roles/*.json edit lands."
upstream-basis: "docs/issue-38/reports/coding.md (this role's own phase-1 survey); gh issue view 38."
next-steps: "Await human Approve. On approval, phase-2 implements exactly the frozen write set below and lands via PR; nothing else changes."
open-findings: "The exact list of host cache-source env vars/paths to mount (GOMODCACHE, ~/.npm, ~/.cache/pip, ~/.cargo/registry, ~/.m2, ...) needs to be confirmed against what actually exists on the host running spawn.py at phase-2 time -- this proposal names the mechanism, phase-2 discovers and enumerates the concrete host paths present."
open-finding-resolution-path: "Phase-2 probes the host for each candidate ecosystem cache directory (os.path.exists) before adding it to allowWrite/allowRead mounts, so absent caches are silently skipped rather than causing a hard failure; the human reviewing the phase-2 diff can see exactly which paths were detected and mounted."
---

# Issue #38 — Build proposal: package-registry access for role workspaces

files:
- spawn.py
- roles/coding.json
- roles/qa.json
- roles/verify.json
- roles/feasibility.json
- roles/ops.json
- roles/product.json
- roles/reflect.json
- roles/review.json
- roles/ux-design.json
- README.md

## Request

Role sessions build/test real projects in sandboxed workspaces with
outbound network blocked by default. A fresh workspace has no package
cache, so any dependency fetch (Go modules, npm, PyPI, crates.io, Maven,
...) hits the sandbox network boundary and fails — this has already been
observed with Go (`proxy.golang.org ... Forbidden`) and is not
ecosystem-specific. Solve this at the spawn layer for all ecosystems, so a
role session in a fresh workspace can build/test without a human or the
session itself hand-copying caches in.

## Constraints

- Solution must be ecosystem-agnostic: no registry-specific special-casing
  beyond a data-driven list of hosts/paths (must cover at minimum Go, npm,
  PyPI, and ideally crates.io/Maven without new code per ecosystem).
- Must not weaken the sandbox's existing filesystem/network boundary model
  (`spawn.py:246-318`) — the fix is additive config, not a bypass.
- Must not break the existing `.muster-cache` write redirection
  (`spawn.py:1508-1522`), which exists specifically to keep sandboxed writes
  inside `cwd` and avoid approval-prompt stalls.
- `--settings` is a merge over user/repo settings (`spawn.py:8-13`,
  `spawn.py:595-609`) — the change must live where `role_settings()` already
  controls sandbox config, not rely on a layer that can be silently
  overridden.
- Per contract v3 s11, this phase does not touch `src/`/`test/` production
  code paths of the *target* repos being built by roles — only muster's own
  `spawn.py`/`roles/*.json`/`README.md`.

## What will be done

**Chosen design: hybrid — read-only host cache mount as the default path,
registry allowlist as the explicit fallback for cache misses, normalized
across all roles.**

1. **Read-only host cache mount (primary mechanism).** Extend
   `role_settings()` (`spawn.py:246-318`) so that, alongside the existing
   `.muster-cache` write redirection (`spawn.py:1508-1522`), each spawn also
   probes a fixed, ecosystem-agnostic list of well-known host cache
   directories (e.g. `$GOMODCACHE`/`~/go/pkg/mod`, `~/.npm`,
   `~/.cache/pip`, `~/.cargo/registry`, `~/.m2/repository` — the concrete
   set to be enumerated against the actual host at phase-2 time, see
   `open-findings`) and, for each one that exists, adds it to the sandbox's
   `sandbox.filesystem` read-allow list **read-only**, mounted at a path the
   ecosystem's own cache env var is pointed at (reusing the
   `string.Template(...).safe_substitute(resolved)` pattern at
   `spawn.py:288-296`). Package managers that find what they need in the
   mounted read-only cache never need network access.
2. **Registry allowlist (fallback for cache misses).** The
   `sandbox.network.allowedDomains` mechanism already exists per role
   (`roles/coding.json` etc.) but today is hand-curated and inconsistent
   (survey: coding has npm+PyPI but no Go/crates.io/Maven; qa/verify have
   none at all). Normalize this into one shared, versioned list of official
   registry hosts (`registry.npmjs.org`, `pypi.org`,
   `files.pythonhosted.org`, `proxy.golang.org`, `sum.golang.org`,
   `crates.io`, `static.crates.io`, `repo.maven.apache.org`, ...) defined
   once (e.g. a `PACKAGE_REGISTRY_HOSTS` constant in `spawn.py`) and merged
   into every role's `allowedDomains` inside `role_settings()`, rather than
   copy-pasted per role file. This is the fallback that handles dependencies
   the host cache doesn't already have — new/updated packages, or
   ecosystems with no local cache on the host at all.
3. **Ecosystem-agnosticism**: neither mechanism special-cases a package
   manager's behavior — the cache mount is a filesystem policy keyed off a
   directory's existence, and the allowlist is a static list of known
   registry hostnames. Adding a new ecosystem later means adding one cache
   path and a few hostnames to two data tables, not new code.
4. **Documentation**: since no `docs/decisions/` or `docs/handbooks/`
   directory exists yet (survey finding), the mechanism and its trade-off
   (below) will be documented directly in `README.md`, next to the existing
   sandbox/hardening notes (`README.md:43-46` area), per the issue's
   acceptance criterion.

### Security trade-off (explicit)

- **Cache mount (default, low risk):** read-only, so a compromised
  build/install step in the sandbox cannot write back into the host cache
  or use it as an exfiltration/persistence channel. Blast radius is bounded
  to "stale or missing dependency" — worse case is a build failure, not a
  new attack surface. Staleness is real: a role session can only build with
  what the host already fetched, so first-time/updated dependencies still
  need network.
- **Registry allowlist (fallback, higher but bounded risk):** this
  reopens outbound network to a fixed set of hosts. Package install is a
  code-execution path — anything reachable through the allowlist can pull
  and run arbitrary published code from that registry (supply-chain
  exposure is real and not eliminated by allowlisting the *registry*
  domain, only by *not* reaching arbitrary hosts). This proposal accepts
  that risk deliberately, scoped narrowly to official registry hosts only
  (no wildcards, no mirrors, no CDNs beyond the registry's own asset host),
  and keeps it as the fallback rather than the default — most builds should
  be satisfiable from the read-only cache alone, so the allowlist's actual
  exposure window (sessions that hit a genuine cache miss) is expected to
  be the minority case, not the common path. This is a widening of the
  sandbox's isolation boundary relative to today's default-deny-most-hosts
  posture, and is the one part of this proposal a human reviewer should
  weigh most carefully before Approve.

## Out of scope

- Per-repo opt-in/opt-out toggles for the allowlist (issue mentions this as
  acceptable but not required; not included in this phase's write set —
  can be a follow-up issue).
- Actually enumerating/verifying which host cache directories exist on the
  spawn-running machine (deferred to phase-2 implementation, see
  `open-findings`).
- Any change to target-repo `src/`/`test/` code, or to non-muster
  repositories.
- Write access to host caches from inside the sandbox (mount is read-only
  only; no cache-population-from-sandbox mechanism is proposed).
- Private/internal package registries (only official public registries are
  proposed for the allowlist; private registry support would need
  credential handling out of scope here).

## How we'll know it worked

- A spawned `coding` (or `qa`/`verify`) role session, in a fresh workspace,
  can run `go build`/`go test`, `npm install`, and `pip install` for a
  project whose dependencies are either present in the mounted host cache
  or fetchable from the allowlisted registries, without a network-denial
  failure and without any manual cache-copying step.
- `roles/*.json` no longer show divergent, hand-maintained
  `allowedDomains` lists for the same registries — the shared host list is
  defined once and merged in by `role_settings()`.
- `README.md` documents the mechanism and states the security trade-off
  above in plain language, satisfying the issue's acceptance criterion.
- Existing tests in `test_spawn.py` continue to pass, plus new cases
  covering: (a) `role_settings()` merges the shared registry-host list into
  `allowedDomains`, (b) a present host cache directory is added to the
  read-only filesystem allow-list, (c) an absent host cache directory is
  skipped without error.
