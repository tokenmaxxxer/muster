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
could not. The session recorded the limitation honestly instead of
claiming success, and the issue asks that the gap be closed rather than
only logged.

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

The issue's own framing treats this as a network-access decision
(whether `github.com` should be allowlisted). survey.md's after-proposal
hunt correction found that framing is wrong: `WEB_ACCESS_DOMAINS =
["*"]` (spawn.py:142-147) is already merged into every sandboxed role's
`sandbox.network.allowedDomains` (spawn.py:477-499), and Claude Code's
own domain matcher treats a literal `"*"` entry as matching every host.
Network access to `github.com` — to any host — is already open for
every role. That measurement replaces the issue's stated premise; two
designs were weighed for what to do about the *actual* generator.

**(a) Add `github.com` to `PACKAGE_REGISTRY_HOSTS` anyway**, as
defense-in-depth for a hypothetical future role that both narrows its
own `allowedDomains` and somehow loses the wildcard merge. Rejected:
`WEB_ACCESS_DOMAINS` is unconditional in `role_settings()` — there is no
code path today where a sandboxed role gets `allowedDomains` without it
(spawn.py:489-491 runs inside the same `if sb0.get("enabled")` block as
the registry-host merge, with no branch that skips it). Defending
against a code path that does not exist is speculative, not a scoped
fix, and it would not have changed the outcome of #406's own reported
failure even if built.

**(b) Redirect `CARGO_HOME` into the workspace, the same way `GOCACHE`,
`GOMODCACHE`, `GOPATH`, `npm_config_cache`, and `PIP_CACHE_DIR` already
are** (spawn.py:3131-3140) — chosen. Reading that call site (added for
Go specifically, per its own comment: "실측: phase 2 가 go build 를 한
번도 못 돌림") shows the real generator: writes outside the workspace
fall outside the sandbox's write scope and stall on an unanswerable
approval prompt in a headless session. Cargo's default `CARGO_HOME`
(`~/.cargo`) is exactly such a path, and it is the one already-common
toolchain-cache key missing from that six-entry dict. This is the
smallest change that targets the actual failure (a write, not a
network, block) and reuses an established, already-tested pattern
rather than inventing a new one.

Per #363: the generator is "the workspace-cache write-redirection at
spawn.py:3131-3140 was built by observing go/npm/pip failures one at a
time and never extended to cargo, which fails the identical way but had
not yet been observed here." Adding `CARGO_HOME` removes that generator
for cargo; it does not remove it for any other unobserved toolchain
that might hit the same pattern later (e.g. Maven's local repo already
has read-only cache support via `PACKAGE_CACHE_DIRS`, but no workspace
write-redirect either) — noted as a like-for-like follow-up, not built
here, since it has not been measured as failing.

The read-only `~/.cargo/registry` sibling, `~/.cargo/git`, is still
added to `PACKAGE_CACHE_DIRS` alongside the `CARGO_HOME` redirect: it is
cheap, mirrors the existing entry exactly, and lets a host that has
already fetched git dependencies outside the sandbox serve them as a
fallback source — useful on its own, but (per the issue's own words)
insufficient alone on a clean host, which is why `CARGO_HOME` is the
change that actually closes the gap.

## What will be done

1. `spawn.py`: add `"CARGO_HOME": os.path.join(wcache, "cargo")` to the
   `extra_env` dict at spawn.py:3131-3140, in the same `if issue is not
   None:` block, alongside the six existing keys.
2. `spawn.py`: add `(None, "~/.cargo/git")` to `PACKAGE_CACHE_DIRS`
   (spawn.py:133-140) — same skip-if-absent mount rule every other entry
   already gets (spawn.py:506-515), no new code path.
3. `test_spawn.py`:
   - a test asserting `"CARGO_HOME"` is present in the `extra_env`
     returned for an `issue`-scoped spawn and points inside
     `<cwd>/.muster-cache` — the same shape an existing test (if any)
     uses for `GOMODCACHE`/`GOCACHE` at that call site; if no such test
     exists yet for the Go keys, add one for all of them together rather
     than leaving `CARGO_HOME` as the only tested key in that dict.
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
- Adding `github.com` to `PACKAGE_REGISTRY_HOSTS` (alternative (a)
  above) — confirmed no-op given the unconditional `"*"` wildcard merge,
  not built.
- Extending the same workspace-cache write-redirect pattern to any other
  toolchain besides cargo (e.g. Maven) — not measured as failing here.
- VCS-style git dependencies in other ecosystems (`npm install
  github:...`, `pip install git+...`) — same defect class, different
  instance, not measured or fixed here.

## How you'll know it worked

- `python3 -m pytest -q test_spawn.py -k "PackageRegistryAccess or cargo or CARGO_HOME"`
  passes, including the new `CARGO_HOME` extra_env assertion and the
  `~/.cargo/git` present/absent cache pair — each fails if the
  corresponding redirect or cache entry regresses.
- `python3 -m pytest -q --ignore=gates` (module-name collision with
  `gates/`, #398 in flight) passes with the new/changed tests included.
- Manual confirmation, recorded once in
  `docs/issue-406/reports/implementation.md`: a real cargo project with
  a `{ git = "https://github.com/..." }` dependency, built inside an
  actual spawned role session with `CARGO_HOME` redirected, either
  succeeds or is blocked by something this change does not claim to fix
  (recorded honestly either way, per #310/#358) — this is the part
  survey.md names as outside what the unit tests alone can discharge.
