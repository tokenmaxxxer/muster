# Proposal — issue-304: keep the sandbox, adjust two settings, add one cache

## Intent

Answer #304's three questions by measurement (survey.md) and turn the result
into a keep/narrow/remove call, plus the settings changes the measurements
justify.

## Constraints

- Do not fold in #292 (compound Bash refusals) or #301 (workflow token
  scope) — out of scope per the issue.
- The recommendation must be argued from survey.md's measured results, not
  from posture.
- If keeping: name settings that cost verifications and protect nothing.
- If removing: name what replaces `a663b6a`'s protection.

## Recommendation: keep-with-adjusted-settings

**Keep** `sandbox.enabled` and `allowUnsandboxedCommands=False`. Q1 showed
the actual blocker for the CDN download and the `proxy.golang.org` fetch is
the Bash tool's own approval gate, which fires independent of
`sandbox.network.allowedDomains` — turning the sandbox off does not touch
that gate at all, so it buys none of the relief #48 wants. It only removes
the one measured protection this repo has direct evidence for: `a663b6a`'s
`~/.claude`-credential read, reachable the moment an agent works around a
blocked command by disabling the sandbox — which is exactly what
`allowUnsandboxedCommands=False` exists to prevent (survey.md Q1, Q2).
Removing the sandbox trades a real, demonstrated credential-exposure path
for zero measured reduction in blocked verifications.

**Adjust:** add `~/.cache/ms-playwright` to `PACKAGE_CACHE_DIRS`
(spawn.py:119-125) plus a `PLAYWRIGHT_BROWSERS_PATH` redirect mirroring
`go_proxy_layer()` (spawn.py:151-168), so a mounted Playwright cache is
actually used instead of silently ignored. Q3 measured the cache present
and readable on this host; without the env redirect, mounting alone does
not stop a Playwright launch from still trying its default browsers path.
This removes the one blocked-verification class (browser-binary
acquisition) this survey could directly confirm, at zero network-surface
cost — `PACKAGE_CACHE_DIRS` mounts are read-only and add no host to
`allowedDomains`.

**Name what buys nothing:** none of the currently-open switches
(`SANDBOX_OPEN_NETWORK`, `SANDBOX_OPEN_TOP_LEVEL`, spawn.py:139-148) are
implicated by any Q1–Q3 measurement — they are already open, so they are
not candidates for removal by this issue. Nothing in this survey's
measurements identifies a setting that is closed today and costs
verifications while protecting nothing; the one setting that looked like a
candidate (`allowedDomains` scoping) turned out, on measurement, not to be
the actual gate for the failures #48 attributed to it. No settings are
recommended for removal.

## What will be done (phase 2, on approval)

1. Add `("PLAYWRIGHT_BROWSERS_PATH", "~/.cache/ms-playwright")` to
   `PACKAGE_CACHE_DIRS` in spawn.py.
2. Add a `playwright_cache_layer()` function mirroring `go_proxy_layer()`
   that sets `PLAYWRIGHT_BROWSERS_PATH` to the mounted path when present,
   called from wherever `go_proxy_layer()`'s result is currently wired into
   the spawned environment.
3. Record this decision as an ADR under `docs/issue-304/decisions/` with a
   C4 note on where the approval gate sits relative to
   `sandbox.network.allowedDomains` (two independent layers, not one).

## Out of scope

- #292, #301 (per issue).
- Re-running the other four verifications from thaki issue-48 / PR #50 —
  not present in this checkout; Q3's extrapolation is stated as an
  extrapolation, not re-measured.
- Any change to the Bash-tool approval-gate's own pre-approval patterns —
  that lives in Claude Code's permission engine, not in this repo's
  `spawn.py`, and is not this issue's write surface.

## How this will be verified

- Phase 2 diff is small (~10-15 lines) and mechanical against the frozen
  `go_proxy_layer()` pattern; verification is: mount appears in
  `sandbox.filesystem.allowRead`, `PLAYWRIGHT_BROWSERS_PATH` resolves to
  it, and a Playwright-driven check in a role session no longer attempts a
  CDN fetch (observable via absence of an approval-gate prompt for that
  host, the same signal Q1 used).
