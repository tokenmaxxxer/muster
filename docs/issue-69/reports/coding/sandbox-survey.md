# Coding phase-1 survey — issue #69

## Symptom recap

Role sessions binding an AF_UNIX socket at a path inside the workspace get
`bind: operation not permitted`, regardless of the chosen path. Issue #69
frames this as a third, independent gating layer next to the network
domain allowlist (issue #58) and the tool-permission layer (issue #65): a
syscall/filesystem-level restriction on socket binding.

## Where `spawn.py` composes sandbox settings

`role_settings()` (`spawn.py:299-413`) is the single place that builds the
`sandbox` block shipped to `claude --settings` for every role:

- `sandbox.filesystem.{allowWrite,denyWrite,denyRead}` — path lists,
  variable-substituted (`spawn.py:341-349`).
- `sandbox.network.allowedDomains` — merged additively from
  `PACKAGE_REGISTRY_HOSTS` (issue #38) and `WEB_ACCESS_DOMAINS` (issue #58)
  (`spawn.py:351-365`).
- `sandbox.filesystem.allowRead` — host package-cache mounts
  (`spawn.py:372-381`).
- `sandbox.credentials` / `sandbox.network.tlsTerminate` for masked env vars
  (`spawn.py:404-407`).
- `sandbox.allowUnsandboxedCommands = False`, forced, to close the
  boundary-fallback hole (`spawn.py:412`).

None of these touch anything socket- or bind-related today. There is no
existing merge block analogous to `PACKAGE_REGISTRY_HOSTS`/`WEB_ACCESS_DOMAINS`
for unix sockets — this would be new territory in `role_settings()`, not an
extension of one.

## Method reused from issue #58

Issue #58's coding survey (`docs/issue-58/reports/coding/survey.md`) resolved
its open question — "does the sandbox schema accept a literal wildcard for
`allowedDomains`?" — by locating the installed Claude Code extension's
settings JSON Schema on disk and reading the matcher behavior directly,
rather than guessing from `spawn.py` alone. Same method applied here:

```
/home/jwjung/.vscode-server/extensions/anthropic.claude-code-2.1.220-linux-x64/claude-code-settings.schema.json
```

Walking the schema for keys containing `sock`/`bind`/`unix`/`network`/`sandbox`
surfaces the full sandbox network property set at
`properties.sandbox.properties.network`:

```
allowedDomains        (array<string>)
deniedDomains          (array<string>)
strictAllowlist        (boolean)
allowManagedDomainsOnly(boolean)
allowUnixSockets       (array<string>)  -- "macOS only: Unix socket paths to
                                           allow. Ignored on Linux (seccomp
                                           cannot filter by path)."
allowAllUnixSockets    (boolean)        -- "If true, allow all Unix sockets
                                           (disables blocking on both
                                           platforms)."
allowLocalBinding      (boolean)        -- no description; distinct key,
                                           not documented as unix-socket-
                                           specific
allowMachLookup        (array<string>) -- macOS XPC/Mach lookup, unrelated
httpProxyPort / socksProxyPort / tlsTerminate
```

(Full `network` subschema captured in the proposal doc for exact wording.)

## Finding: is workspace-scoped AF_UNIX bind expressible?

**No, not on this platform (Linux).** The schema does distinguish a
path-scoped allow (`allowUnixSockets`) from a blanket allow
(`allowAllUnixSockets`) — so the schema author clearly considered scoping —
but the path-scoped key is explicitly documented as **macOS-only**, with the
stated reason "seccomp cannot filter by path" on Linux. This machine (and
presumably any Linux-hosted role session, per this repo's `env` block:
`Linux 6.8.0-110-generic`) cannot honor `allowUnixSockets` at all — the key
would be silently ignored.

The only Linux-effective lever is `allowAllUnixSockets: true`, which is
explicitly a blanket switch: "disables blocking on both platforms." It does
not distinguish `bind()` from `connect()`, does not accept a path list, and
is not scoped to the workspace directory — it is functionally identical in
shape to the network allowlist's rejected "wildcard everything" case, except
here there is no narrower alternative to fall back to on Linux, unlike
`allowedDomains` which at least accepts a curated host list.

So: the sandbox surface *can* express a workspace-scoped unix-socket
allowance in principle (`allowUnixSockets` exists as a concept), but only on
macOS. On Linux — the platform role sessions actually run on here — the
narrow form is a no-op, and the only working control is the wide-open one
the issue explicitly asked to avoid ("not a blanket network-allow, scoped
narrowly"). This is a platform (seccomp) limitation of the installed CLI's
sandbox runtime, not something `spawn.py` can work around by composing
settings differently.

## Conclusion

Option (b) applies: workspace-scoped AF_UNIX bind is not supported by the
current sandbox surface on Linux. A README limitation note is the correct
phase-1 deliverable, per the issue's acceptance criteria's second branch.
See `docs/issue-69/proposals/coding.md` for the exact wording proposed.
