# Coding build proposal — issue #72

## Request (paraphrased intent)

Flip the sandbox posture from default-deny (opened one switch at a time,
whack-a-mole style: #38, #58, #65, #69) to default-open. Keep the sandbox
itself on and keep the two things it must still enforce — workspace write
scoping and the rulebook/gate hooks. Open every other restriction switch the
schema exposes, starting with `allowAllUnixSockets`. Replace README's
per-restriction trade-off note pattern with one posture statement.

## Constraints

- Sandbox stays `enabled: true` for every role — reason 1 (headless Bash
  auto-allow) depends on the sandbox existing, not on any of its internal
  restriction switches.
- `sandbox.filesystem.allowWrite`/`denyWrite` (workspace write scoping,
  reason 2) is untouched.
- `sandbox.allowUnsandboxedCommands` stays `false` (`spawn.py:412`,
  unrelated to this issue — it is what keeps the sandbox mandatory).
- board-gate/gh-guard hooks (reason 3) are untouched — they live outside
  the sandbox schema entirely.
- Same merge site and shape as #38/#58: additive, applied uniformly to all
  sandboxed roles, no per-role opt-in.

## What will be done (pending approval)

1. Add a new constant near `PACKAGE_REGISTRY_HOSTS`/`WEB_ACCESS_DOMAINS`
   (`spawn.py`, ~line 42-53) holding the open-everything-else settings
   surveyed in `docs/issue-72/reports/coding/survey.md`:
   - `sandbox.network.allowAllUnixSockets = True`
   - `sandbox.network.allowLocalBinding = True`
   - `sandbox.network.allowMachLookup = ["*"]` (macOS only; no-op on Linux
     per the schema's own doc string)
   - `sandbox.enableWeakerNetworkIsolation = True`
   - `sandbox.allowAppleEvents = True` (macOS only)
   - `sandbox.enableWeakerNestedSandbox = True`
   - `sandbox.allowPty = True`
2. Merge these into `role_settings()` alongside the existing
   `sb0.get("enabled")` block (`spawn.py:353-365`) — same
   additive/no-clobber pattern, applied to every sandboxed role.
3. Rewrite README's `## Isolation — a sandbox, not a container` section:
   remove the per-restriction "Trade-off, explicit:" pattern under
   "Package-registry access" and "Web access" (keep those sections'
   mechanism description, drop the repeated trade-off paragraphs), and add
   one posture statement: default-open within the sandbox, the three
   reasons it stays on, and the two things that remain restricted
   (workspace write scope, hook gates). This directly answers the issue's
   README acceptance criterion.
4. No new role-level flags, no per-role settings changes — `roles/*.json`
   files are untouched, exactly like #38/#58.

## Out of scope

- `filesystem.allowGitConfig` — dropped from the open set (not the write-scoping
  exception from before, a correction): warrant-hunter verified against the
  installed binary's zod schema that no `allowGitConfig:v.boolean()...`
  declaration exists under `filesystem` — only an internal function-parameter
  destructure defaulting to `false`. Setting it via `roles/*.json`/
  `role_settings()` would be a silent no-op; the survey's inventory table
  now flags this.
- `filesystem.denyRead`/`allowRead` — not one of the three keep-reasons'
  concerns (write only), and not named in the acceptance criteria; left
  as-is.
- `ignoreViolations`, `mandatoryDenySearchDepth`, `tlsTerminate` — not
  default-deny restriction switches (observability/internal-default/
  opt-in-only mechanism respectively); no change proposed.
- Verifying the exact bwrap/Seatbelt runtime effect of each opened switch
  on both platforms — phase 2 will do a spawn-and-inspect check (same as
  #58 did for the `"*"` domain literal) before landing, not during this
  proposal.

## How you'll know it worked

- A role session can bind an AF_UNIX socket in its workspace on both Linux
  and macOS (issue's acceptance criterion) — verified in phase 2 by
  spawning a role and exercising a Unix-socket bind inside it.
- README states the default-open posture, the three reasons the sandbox
  stays on, and what remains restricted.
