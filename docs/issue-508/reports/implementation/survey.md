Subject: issue-508

## Current state

- `on-the-record/hooks/hooks.json` ships 9 hook commands across
  SessionStart, UserPromptSubmit, PreToolUse (Bash matcher: contract-guard,
  pr-preflight, spec-index-preflight; Write/Edit/MultiEdit/NotebookEdit
  matcher: deliverable-guard; Write/Edit/MultiEdit matcher:
  record-claim-guard), and Stop (stop-gate, role-test-claim-guard,
  decision-queue-stopgate, report-framing-check).
- This repo (`on-the-record`, the plugin's own home) has **no**
  `.claude/settings.json` or `.claude/settings.local.json` at all — `Read`
  on both returns "File does not exist."
- `spawn.py` is how this repo spawns role sessions (including this very
  session). `role_settings(role)` (spawn.py:427) builds a merged settings
  dict from `roles/<role>.json` — sandbox filesystem/network policy,
  `enabledPlugins` (all global plugins forced off), permission allow-list.
  It builds NO `hooks` key. The dict is dumped to a temp file and passed as
  `claude -p --settings <tmp>` (spawn.py:2886 `spawn_cmd`, used at
  spawn.py:3650). This session is running under exactly that path — the
  SessionStart/UserPromptSubmit reminders visible in this conversation come
  from *other* plugins loaded via `--plugin-dir` for the `implementation`
  role, not from on-the-record's own `hooks.json`, which is confirmed inert
  here.
- `spawn.py:require_no_repo_config` (spawn.py:857) is the reason a naive
  fix ("just check in `.claude/settings.json` here") is dangerous: when
  spawn.py spawns a role session **against an arbitrary target repo**, it
  refuses if that repo carries `.claude/settings.json`,
  `.claude/settings.local.json`, `.claude/hooks`, `.claude/agents`, or
  `.mcp.json` — because settings-file priority is `--settings` >
  `<repo>/.claude/settings.json` > `~/.claude/settings.json`, on-the-record
  only ever reads the two ends, and a checked-in repo hook is not bound by
  the sandbox's `filesystem` policy at all (documented incident,
  2026-07-27: a repo's own `SessionStart` hook wrote to a `denyWrite` path
  and read a `denyRead` path, full user privilege, no prompt). A repo can
  bypass trust via `--trust-repo-config`, which pins a content-hash of
  `.claude/` and re-triggers the stop when the hash changes.
  **on-the-record is itself such a target repo whenever spawn.py spawns a
  role session against it** (dogfooding = spawning role sessions with
  `cwd` = this repo). If this repo checks in `.claude/settings.json` to
  wire its own hooks.json, every future self-hosted spawn hits
  `require_no_repo_config`'s stop unless pre-trusted — a real interaction,
  not hypothetical, and it needs to be an explicit, working part of the
  fix (trust-pin it, or avoid the checked-in-file path entirely by having
  spawn.py inject the hooks key into the generated `--settings` temp file
  when `cwd` resolves to the on-the-record repo itself).
- No existing test asserts anything about hooks.json/registration parity.
  `gates/test_boundary.py` covers the trailer/board contract, not hooks.
  `gates/spawn_coverage.py` covers open-issue board coverage, unrelated.
- `roles/implementation.json` (the role spec this very session used) has
  no `hooks` key — confirms role specs don't currently carry hooks either.
- Deny-before-effect precedent already exists in this codebase: PreToolUse
  hooks that print to stderr and exit nonzero are how `spec-index-preflight.sh`
  etc. are meant to block a Bash commit attempt (per issue-508's body and
  #503's follow-up finding). A live-fire test needs a real `git commit`
  attempt in a temp clone with the registration active, and a
  denied-red/allowed-green pair.

## Write-set implications (what the eventual proposal must cover)

- `spawn.py` — most likely site for the fix: self-target detection +
  hooks-key injection into the generated settings, so the mechanism
  doesn't collide with `require_no_repo_config`'s trust gate on every
  future spawn against this repo.
- `gates/test_boundary.py` or a new `gates/test_*.py` — mechanical parity
  assertion: every `on-the-record/hooks/hooks.json` entry has a matching
  repo-side registration.
- A new test exercising the live-fire deny path (temp git clone, real
  commit attempt, hook active, expect nonzero exit / denial before the
  commit lands).

## Skip-condition check (scout-directive)

Scouting for "category best-in-class" does not apply: this is an
internal dev-tooling wiring fix for a single self-hosted repo, not a
product-shaped surface with external exemplars. The only real design
decision — checked-in `.claude/settings.json` vs. spawn-time injection —
is resolved by the `require_no_repo_config` interaction found above, which
is codebase-internal evidence, not something an external sweep would
improve on. Proceeding directly to the proposal's Rationale section with
that alternative recorded.
