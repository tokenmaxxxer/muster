# Coding phase-1 proposal — issue #69

files:
- README.md

## Request (paraphrased intent)

Role sessions on this platform cannot bind an AF_UNIX socket at a workspace
path — `bind: operation not permitted` regardless of path — so socket-based
tests (RPC seams, daemons) can't run inside role sessions; a human must run
them outside the sandbox and the session records them as unverified. Issue
#69 asks phase 1 to determine whether the sandbox surface can express
"allow AF_UNIX bind within the workspace, and only there" and, if yes,
enable it plus add a settings-composition test (option a); if no, add an
explicit README limitation note next to the existing sandbox notes
(option b).

## Constraints

- No code changes in phase 1 (this proposal only; `spawn.py`/tests are
  explicitly out of scope here).
- Any settings change must be narrowly scoped to the workspace, not a
  blanket allow — per the issue's own wording.
- If documenting a limitation, it must sit next to the existing sandbox
  notes in README (issue #38, #58/#65 sections), matching their structure
  (mechanism/reason, then explicit statement), per this repo's established
  pattern for sandbox trade-off notes.

## What will be done

**Option (b) is proposed — the workspace-scoped form is not supported by
the sandbox surface on Linux.**

### Why (a) is not available

The installed Claude Code CLI's sandbox settings schema
(`claude-code-settings.schema.json`, extension 2.1.220) exposes exactly two
unix-socket-related keys under `sandbox.network`:

- `allowUnixSockets: string[]` — "macOS only: Unix socket paths to allow.
  Ignored on Linux (seccomp cannot filter by path)."
- `allowAllUnixSockets: boolean` — "If true, allow all Unix sockets
  (disables blocking on both platforms)."

The schema does distinguish a path-scoped allow from a blanket allow, but
the path-scoped one (`allowUnixSockets`) only works on macOS; on Linux —
the platform role sessions run on in this environment — it is documented as
a silent no-op. The only Linux-effective control is `allowAllUnixSockets`,
which is explicitly blanket ("disables blocking on both platforms"): it does
not accept a path list, does not distinguish `bind()` from `connect()`, and
is not scoped to the workspace directory. Turning it on would satisfy the
literal symptom but violate the issue's own constraint ("not a blanket
network-allow, scoped narrowly") — it is a strictly wider grant than what
was asked for, with no narrower Linux-side alternative in the current
schema. No settings-composition change in `spawn.py`/`role_settings()` can
manufacture path-scoping that seccomp itself cannot enforce.

### README addition (exact wording)

Add a new subsection to `README.md` immediately after the existing "Web
access (issues #58, #65)" section (same file, same run of sandbox notes),
reading:

```markdown
### Unix-socket bind() in the workspace (issue #69)

Role sessions cannot bind an AF_UNIX socket at a path inside the sandboxed
workspace — `bind: operation not permitted`, regardless of the chosen path.
Tests that exercise a local socket boundary (RPC seams, daemons) cannot run
inside a role session and must be run outside the sandbox by a human.

**Why:** the installed Claude Code sandbox schema exposes two related
keys — `sandbox.network.allowUnixSockets` (a path list) and
`sandbox.network.allowAllUnixSockets` (a blanket switch). The path-scoped
key is documented as macOS-only ("Ignored on Linux (seccomp cannot filter
by path)"); on Linux, where role sessions in this environment run, only the
blanket switch has any effect, and it disables unix-socket blocking
entirely rather than scoping to the workspace. This is a seccomp limitation
of the sandbox runtime itself, not a `spawn.py` configuration gap — no
settings composition can add path-scoping that the underlying enforcement
mechanism does not support on this platform.

**Handling:** sessions must not work around this by disabling the sandbox
(`allowUnsandboxedCommands` stays forced `false`, see above) or by turning
on `allowAllUnixSockets` unilaterally — that trades a narrow, requested
scope for a blanket one, which is a materially different risk decision than
what was asked. Instead: report socket-bind tests as unverified (matching
the existing "honest reporting of unverified items" pattern from issue
#43/#58), and route them to a human to run outside the sandbox.
```

No other file changes. No settings-composition test is added, because there
is no settings composition to test — the negative result *is* the
deliverable, and it is a platform/schema fact, not a piece of merge logic
`role_settings()` could get wrong.

## Out of scope

- Any change to `spawn.py` or `role_settings()` — there is no merge logic to
  add for a control that has no narrowly-scoped Linux-side effect.
- Enabling `allowAllUnixSockets` for any role — rejected above as violating
  the issue's own narrow-scope requirement.
- macOS-specific behavior — `allowUnixSockets` would work there, but role
  sessions in this environment run on Linux; this proposal does not attempt
  platform-conditional settings.
- A settings-composition test file, since option (b) is being proposed (no
  new merge behavior exists to test).

## How it'll be known to work

A human approver can verify the schema claim independently: `grep -A3
'"allowUnixSockets"' <installed-extension-dir>/claude-code-settings.schema.json`
shows the "Ignored on Linux" text quoted above, and `"allowAllUnixSockets"`
shows the "disables blocking on both platforms" text. Once phase 2 lands the
README section verbatim (or with only wording polish approved by the human),
success is: the new "Unix-socket bind() in the workspace (issue #69)"
subsection exists in `README.md` immediately after the "Web access (issues
#58, #65)" section, and no `spawn.py`/test changes are made in the same
change (since none are proposed).
