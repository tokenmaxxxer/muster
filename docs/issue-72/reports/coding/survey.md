# Coding phase-1 survey — issue #72

## Method

Same as #58/#69: grep the installed CLI binary (`claude` 2.1.220,
`~/.local/share/claude/versions/2.1.220`) for its zod sandbox schema —
`strings -a <binary>` piped to grep for `v.boolean()`/`v.array()` schema
declarations and their accessor functions (`Hl?.<path>`), which reveal both
the setting name and its nesting (`sandbox.network.*`,
`sandbox.filesystem.*`, or top-level `sandbox.*`).

## Full restriction-switch inventory found

| switch | nesting | default (per schema) | what it restricts |
|---|---|---|---|
| `allowUnixSockets` | `network` | none allowed | macOS-only list of specific Unix socket paths to allow |
| `allowAllUnixSockets` | `network` | `false` | if true, disables Unix-socket blocking entirely on both platforms — **the issue's named starting point** |
| `allowLocalBinding` | `network` | restricted | binding to local network addresses/ports |
| `allowMachLookup` | `network` | none allowed | macOS-only list of mach service names reachable (trailing-`*` wildcard supported) |
| `allowPty` | top-level `sandbox` | restricted | pty allocation inside the sandboxed process |
| `allowGitConfig` | `filesystem` | `false` | read access to the host's global git config |
| `enableWeakerNetworkIsolation` | top-level `sandbox` | `false` | macOS-only: access to `com.apple.trustd.agent`, needed for Go-based CLI tools (gh, gcloud, terraform) to verify TLS certs through the sandbox's proxy |
| `allowAppleEvents` | top-level `sandbox` | `false` | macOS-only: sandboxed Apple Events — CLI's own doc string flags this as "a demonstration vector through the trustd service" |
| `enableWeakerNestedSandbox` | top-level `sandbox` | `false` | relaxes confinement when a sandboxed process itself spawns a nested sandbox |
| `allowUnsandboxedCommands` | top-level `sandbox` | permissive by default | whether `dangerouslyDisableSandbox` is honored at all — `spawn.py:412` already forces this to `false` (issue predates #72, trap ③ in README) |
| `ignoreViolations` | top-level `sandbox` | none | per-command list of violation types to log-but-not-block; observability knob, not a restriction to open |
| `mandatoryDenySearchDepth` | (internal, ripgrep-search-depth default) | `3` | search-tool internal default, not a settings.json-exposed restriction |
| `tlsTerminate` | `network` | unset | in-process TLS termination for request-body inspection; already conditionally set by `spawn.py:405-407` only when `credentials.envVars` masking is active — unrelated to this issue's restriction set |
| `filesystem.allowWrite` / `denyWrite` | `filesystem` | workspace-scoped | the write boundary — this is reason 2, not a candidate to open |
| `filesystem.denyRead` / `allowRead` | `filesystem` | mostly open, selectively deny | read boundary; role files here set none directly (`role_settings()` only appends cache dirs to `allowRead`); out of scope — the issue's 3 keep-reasons name **write** isolation, not read, and the acceptance criteria only test AF_UNIX bind |
| `network.allowedDomains` / `allowedHosts` / `deniedHosts` | `network` | role-declared + merges (#38, #58) | already fully open (`WEB_ACCESS_DOMAINS = ["*"]`, #58) — not a remaining restriction |

## Classification against the three keep-reasons

Reasons (from the issue): (1) headless Bash auto-allow — sandboxed Bash
skips human approval prompts; (2) workspace write scoping; (3) rulebook/gate
separation (board-gate, gh-guard hooks).

None of the switches above serve any of the three:

- Reason 1 is about the **permission-prompt layer** (`permissions.allow`,
  `--permission-mode acceptEdits`), already handled separately (#65) — none
  of the sandbox-schema network/process switches touch that layer.
- Reason 2 is `filesystem.allowWrite`/`denyWrite` only — every switch in the
  table above is either `network`, `filesystem.allowGitConfig` (read-only
  git config access, not the write boundary), or top-level process
  confinement (pty, mach lookup, Apple Events, nested-sandbox strength).
  None touch the write boundary.
- Reason 3 (board-gate, gh-guard) is enforced entirely by PreToolUse hooks
  external to the sandbox schema (`.claude/hooks/*`) — no sandbox-schema
  switch implements or overlaps with it.

**Conclusion: every restriction switch found is a candidate to open**,
except the three already correctly kept for other reasons noted in the
table (`allowUnsandboxedCommands: false` — keeps the sandbox itself
mandatory, i.e. the precondition for reason 1; `filesystem.allowWrite`/
`denyWrite` — reason 2; `tlsTerminate` — orthogonal credential-masking
mechanism, unset unless needed, not a default-deny switch).

## Where the merge belongs

Same site pattern as #38/#58: a new constant merged inside `role_settings()`
(`spawn.py`), additive alongside the existing `PACKAGE_REGISTRY_HOSTS` /
`WEB_ACCESS_DOMAINS` merges at `spawn.py:351-365`, applied to every
sandboxed role uniformly (no per-role opt-in, consistent with the prior
two operator decisions on this same function).
