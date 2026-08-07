# Survey — issue #406

## Write surface

`spawn.py` — two module constants, both consumed inside `role_settings()`:

- `PACKAGE_REGISTRY_HOSTS` (spawn.py:118-127): merged into every
  sandboxed role's `sandbox.network.allowedDomains` (spawn.py:479-491).
  Currently: `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`,
  `proxy.golang.org`, `sum.golang.org`, `crates.io`, `static.crates.io`,
  `repo.maven.apache.org`. No `github.com`.
- `PACKAGE_CACHE_DIRS` (spawn.py:133-140): `(env_var, default_path)`
  pairs; each present host directory is mounted read-only into
  `sandbox.filesystem.allowRead` (spawn.py:506-515). Currently includes
  `(None, "~/.cargo/registry")` but no `~/.cargo/git`.
- `test_spawn.py`'s `PackageRegistryAccess` class (from #38) is the
  existing test surface for both constants — generic, list-driven
  (`for host in spawn.PACKAGE_REGISTRY_HOSTS: ...`), so appending an
  entry to either list is picked up by the existing assertions without
  new test scaffolding, and new entries need their own assertions the
  same way #38's did per-entry.

Confirmed the two omissions the issue reports by reading the lists above
directly (spawn.py:118-140) — matches the issue's own `grep`-equivalent
measurement.

## Correction to one of the issue's two premises

The issue states "`github.com` is not an allowed domain." That is true
of `PACKAGE_REGISTRY_HOSTS` in isolation, but `role_settings()` merges
**two** sources into `allowedDomains`: `PACKAGE_REGISTRY_HOSTS` (global,
issue #38) and each role file's own `sandbox.network.allowedDomains`
declaration (role-specific).

Checked directly, in-process, against the real merge function (not by
reasoning about the settings — ran `spawn.role_settings(role)` for the
role this session runs as, then swept all role files):

```
$ grep -rl 'github.com' roles/*.json | wc -l
43
$ ls roles/*.json | wc -l
43
```

Every one of the 43 role files already declares `github.com` (and
`*.github.com`) in its own `allowedDomains` — confirmed for
`implementation` specifically by calling `spawn.role_settings
('implementation')` and inspecting the merged
`sandbox.network.allowedDomains` list, which contains `github.com`. So a
role spawned through the current roster is **not** network-blocked from
`https://github.com/...` today. The network half of #406, as measured
against present role files, is not currently reproducible as a live
failure for any of the 43 roles on this roster.

What the omission from `PACKAGE_REGISTRY_HOSTS` still means: the
global-registry-host list is the layer #38 built specifically so a
*new* role file does not have to remember to declare every package
ecosystem's host by hand — it is the "don't make each role re-enumerate
this" layer, the same shape as go/npm/pypi/crates/maven already in the
list. A role added later that (correctly, per its own scope) declares a
narrower `allowedDomains` and never thinks to add `github.com` would
regress into exactly the failure #406 reports, silently, with no
warning at spawn time. That gap is real and is what `PACKAGE_REGISTRY_HOSTS`
exists to close for the other seven registries; `github.com` is the one
git-hosting exception being asked for here, not a general "open GitHub"
decision — that host is already trusted at the level of role-by-role
declaration.

## The cache gap

`~/.cargo/git` does not exist on this host (confirmed:
`ls -d ~/.cargo/git` fails with `No such file or directory`, matching
the issue's own measurement) — there is nothing to mount yet on this
particular machine, but the constant's job is to mount it **when it
exists** (the same "if os.path.isdir(cache_path)" skip-if-absent
pattern spawn.py already uses for every other entry, spawn.py:511) so a
future run that has already fetched cargo git dependencies benefits
without a code change. This mirrors `~/.cargo/registry` in the same
list exactly — same tool, same purpose, the missing sibling directory
cargo uses specifically for `git = "..."` dependencies (cargo's own
directory layout: `registry/` for crates.io-style deps, `git/` for VCS
deps).

## Alternatives on the network half, weighed against the corrected state

The issue's own scope section asks to weigh: (a) allow `github.com`
only when the project declares a git dependency (manifest-derived,
reusing #303's "declaration over enumeration"), (b) a constant addition,
(c) leave closed with a pre-build refusal. Assessed against what's
actually measured above (network access to `github.com` is already
granted per-role, not globally denied):

- (c) is moot for the 43 existing roles — there is no live block to
  refuse in front of. It would still be relevant for a hypothetical role
  with a narrow custom `allowedDomains` that a proposal author manually
  leaves off — but building a pre-build refusal for a case that isn't
  reproducible today isn't a scoped fix, it's speculative infrastructure
  for a future role nobody is defining yet. Deferred with a citation in
  the proposal.
- (a) requires parsing a project's manifest (`Cargo.toml`/`Cargo.lock`)
  before spawn to decide whether to widen the allowlist for that spawn.
  `spawn.py` today has no code path that reads *project* files before
  building a role's settings (`role_settings()` only reads the role
  file and `os.environ`); adding one is real new surface (a TOML parser
  or regex-based URL extractor, plus a new "which project directory" input
  that `role_settings()` doesn't currently take) for a host that, per
  the correction above, is already open on every role that exists.
- (b) — add `github.com` to `PACKAGE_REGISTRY_HOSTS`, the same
  mechanism the other 8 registry hosts use — closes the actual
  regression risk identified above (a future role that forgets to
  declare it) with a one-line, list-driven, already-tested change, and
  changes no role's *effective* permissions today (`github.com` is
  already merged in for all 43 via their own declarations, so this adds
  a redundant-but-harmless entry for present roles and a real guarantee
  for future ones). This is the smallest change that actually discharges
  the measured gap without inventing new infrastructure.

## Boundary — overlap with named issues

- **#304**: mounted `~/.cache/ms-playwright` because binaries were
  already on the host. #406's git-clone case is different in kind (a
  clean host has nothing to mount, and the fix needs a fetch to
  succeed, not a pre-fetched binary to be found) — #406's own body
  already draws this line; this survey does not reopen it.
- **#303**: "declaration over enumeration" and "role learns the
  boundary by failing at it" are #303's frame. This proposal reuses the
  *pattern name* for how alternative (a) was described, but does not
  build #303's declared-capability-envelope injection — that is
  #303's own open scope (a general mechanism for stating what a spawned
  session can/cannot do), not a spawn.py registry-list edit. Leaving it
  there; not widened here.
- **#38 / #58**: is the mechanism this issue extends (same two
  constants, same merge functions, same test class). Not re-litigated —
  reused as-is.

## Mechanical enforceability (per #310)

Both halves are testable as plain data/unit assertions against
`spawn.py`'s existing exports, the same shape `PackageRegistryAccess`
already uses:

- `github.com in spawn.PACKAGE_REGISTRY_HOSTS` — a literal membership
  check, and `github.com in spawn.role_settings(role)["sandbox"]
  ["network"]["allowedDomains"]` for a role with a *narrow* declared
  `allowedDomains` (a role fixture, not a real roster role, so the
  assertion is not made vacuously true by every role already declaring
  it).
- The cache-mount half reuses the existing generic
  `test_present_cache_dir_added_to_allow_read` /
  `test_absent_cache_dir_is_skipped_without_error` shape, parametrized
  onto the new `(None, "~/.cargo/git")` entry.

What is **not** mechanically checkable in this repo's test suite: an
actual `cargo build` against a real git dependency inside a live
spawned sandbox session (the issue's own acceptance line: "in a real
spawned role session — not by reasoning about the settings"). That
requires a running Claude Code sandboxed session, which `pytest` does
not have access to. This survey records that ceiling now rather than
implying the unit tests substitute for it; the proposal's "how you'll
know it worked" section names both the mechanical part (unit tests) and
the part that stays a manual, recorded phase-2 confirmation.

## Searched, for the absence claims above (#358)

- `grep -n "PACKAGE_REGISTRY_HOSTS\|PACKAGE_CACHE_DIRS" -r --include=*.py .`
  — only `spawn.py` and `test_spawn.py` reference either constant.
- `grep -rl 'github.com' roles/*.json` — 43/43 role files.
- `ls -d ~/.cargo/git` — absent on this host (matches the issue).
- `git ls-files | grep -i spawn` — confirmed `spawn.py`/`test_spawn.py`
  are the only spawn-related tracked files; no separate cargo-specific
  module exists to hold this instead.

## Scout skip record

Per the scout-directive skip conditions: this is a two-constant, list-
membership fix inside an already-established mechanism (#38's registry-
host / cache-dir lists), with no new external dependency, no new UI or
product-facing surface, and no design decision the codebase's own
existing pattern doesn't already settle (list membership + the existing
skip-if-absent mount rule). It is not a pure bugfix in the strict sense
(#406 asks for a real design choice among three network-half options),
so the "no design decision open" skip condition is not the one that
applies — instead, this falls outside scout's scope entirely: scout's
own text limits itself to product-shaped or best-in-class-comparable
deliverables (product features, review checklists, ops plans); a
sandbox network-allowlist constant has no comparable "category" of
competing products to benchmark against. Skipped for that reason, not
either of the two named conditions verbatim — recorded explicitly per
the directive's "record the skip and its one-line reason."
