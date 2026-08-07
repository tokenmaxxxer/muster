---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - docs/issue-406/reports/implementation.md
---

## Request

#406: a role hit a build it could not run — a sandboxed session tried to
fetch a cargo git dependency (`{ git = "https://github.com/..." }`) and
could not, because `~/.cargo/git` (the cache cargo uses for VCS
dependencies, distinct from `~/.cargo/registry`) is never mounted. The
session recorded the limitation honestly instead of claiming success,
and the issue asks that the gap be closed rather than only logged.

## Constraints

- Per #310: acceptance needs an executable artifact that fails on
  regression, not a doc sentence.
- Per #363: state what generated the defect and whether the fix removes
  the generator, not just this one instance.
- Per #358: absence claims must record what was searched.
- Per #390: state the base state was verified against.
- Do not fold in #303 (declared capability envelope, a general
  mechanism) or #304 (already-solved, different-kind case) — survey.md's
  Boundary section draws both lines.

## Rationale

Two designs were weighed for the network half (the cache half has one
obvious shape, covered under "What will be done").

**(a) Manifest-derived, per-spawn host allowlisting** — parse the
project's `Cargo.toml`/`Cargo.lock` before building a role's settings,
extract git-dependency hosts, and merge only those into that spawn's
`allowedDomains`, reusing #303's declaration-over-enumeration framing.
Rejected for now: `role_settings()` has no existing input for "which
project directory is this spawn for" (it only reads the role file and
`os.environ`), so this needs new plumbing through the caller as well as
a manifest parser, for a host — `github.com` — that survey.md's direct
measurement shows is **already** present in all 43 roster roles' own
`allowedDomains` declarations. Building manifest-derived scoping now
would add real surface (parser, new function parameter, new failure
modes when a manifest is malformed) to solve a problem that, on the
present roster, does not reproduce. It is the right shape if a future
role narrows its own declared domains and needs cargo git deps scoped
tightly — noted as a follow-up, not built here.

**(b) Add `github.com` to `PACKAGE_REGISTRY_HOSTS`** — chosen. This is
the exact mechanism the other eight registry hosts already use
(spawn.py:118-127), merged the same way, tested the same generic,
list-driven way `PackageRegistryAccess` already tests the other eight.
It closes the actual regression survey.md identified: a role file added
later that does not itself declare `github.com` would silently hit
#406's failure again, and `PACKAGE_REGISTRY_HOSTS` is precisely the
layer #38 built so a role does not have to remember every package
ecosystem's host by hand. Effective permissions for the 43 existing
roles do not change (the host is already merged in via their own
declarations); the guarantee is for the roster's next role, which is
the actual generator #406's own failure traces back to — a global list
missing one git-hosting entry the other seven ecosystems' equivalents
already have.

Per #363: the generator was `PACKAGE_REGISTRY_HOSTS`/`PACKAGE_CACHE_DIRS`
being built for registry-style (single-host, versioned-artifact)
package fetches and never extended to cover a VCS-style dependency,
which cargo (uniquely among the six ecosystems already covered) supports
natively. Adding both entries removes the generator for cargo git
dependencies specifically; it does not remove the generator for VCS-style
dependencies in other ecosystems (e.g. `npm install github:user/repo`,
`pip install git+https://...`) — those are a different instance of the
same class and are out of scope below, not silently swept in.

## What will be done

1. `spawn.py`: add `(None, "~/.cargo/git")` to `PACKAGE_CACHE_DIRS`
   (spawn.py:133-140) — same skip-if-absent mount rule every other entry
   already gets (spawn.py:506-515), no new code path.
2. `spawn.py`: add `"github.com"` to `PACKAGE_REGISTRY_HOSTS`
   (spawn.py:118-127) — merged into every sandboxed role's
   `allowedDomains` the same way the existing eight are (spawn.py:479-491).
3. `test_spawn.py`, `PackageRegistryAccess` class:
   - extend `test_registry_hosts_merged_into_allowed_domains` (or add a
     sibling assertion) to include `github.com`.
   - a new test using a role **fixture** with a narrow, hand-written
     `allowedDomains` (not a real roster role, so the assertion is not
     vacuously satisfied by every role already declaring `github.com`
     itself) asserting `github.com` still lands in the merged output —
     this is the regression test for the actual gap identified in
     survey.md (a future narrowly-scoped role).
   - a cache-dir test for `~/.cargo/git` parametrized the same way
     `test_present_cache_dir_added_to_allow_read` /
     `test_absent_cache_dir_is_skipped_without_error` already cover
     `GOMODCACHE` (present → mounted; absent → skipped, no error).
4. `docs/issue-406/reports/implementation.md` — phase-2 record. States
   plainly (per survey.md's ceiling) that a live `cargo build` against a
   real git dependency inside a spawned sandbox session is not something
   `pytest` can exercise, and records that confirmation as a manual,
   logged step run once during phase 2 rather than implied by the unit
   tests passing.

## Out of scope

- #303's general declared-capability-envelope mechanism.
- #304 (already solved, different failure kind).
- Manifest-derived, per-project host scoping (alternative (a) above) —
  left as a named follow-up, not built.
- VCS-style git dependencies in other ecosystems (`npm install
  github:...`, `pip install git+...`) — same defect class, different
  instance, not measured or fixed here.
- Any pre-build refusal/warning UI for the (currently unreproducible)
  case of a role that narrows its own `allowedDomains` below
  `github.com` — noted in survey.md as moot for the present roster.

## How you'll know it worked

- `python3 -m pytest -q test_spawn.py -k PackageRegistryAccess` passes,
  including the two new assertions (narrow-role-fixture merge, and the
  `~/.cargo/git` present/absent cache pair) — each fails if the
  corresponding constant entry regresses or the merge/mount logic
  changes shape.
- `python3 -m pytest -q --ignore=gates` (module-name collision with
  `gates/`, #398 in flight) passes with the new/changed tests included.
- Manual confirmation, recorded once in
  `docs/issue-406/reports/implementation.md`: a real cargo project with
  a `{ git = "https://github.com/..." }` dependency, built inside an
  actual spawned role session, either succeeds or is blocked by
  something this change does not claim to fix (recorded honestly either
  way, per #310/#358) — this is the part survey.md names as outside
  what the unit tests alone can discharge.
