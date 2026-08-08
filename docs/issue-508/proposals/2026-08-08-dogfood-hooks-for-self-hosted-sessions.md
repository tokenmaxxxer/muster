---
status: proposed
files:
  - spawn.py
  - gates/test_hooks_parity.py
  - docs/handbooks/spawn.md
---

## Request

#508: on-the-record's own repo sessions run with the plugin's shipped
hooks (`on-the-record/hooks/hooks.json`) inert, because this repo carries
no `.claude/settings.json` wiring them in — so preflights, claim guards,
and contract-guard never fire on sessions working ON on-the-record
itself, even though consumers get them via the marketplace install path.
Make every shipped hook live for this repo's own sessions, with a
live-fire deny test and a mechanical parity pin between `hooks.json` and
the registration.

## Constraints

- Must not reopen the `require_no_repo_config` hole: on-the-record
  already refuses to spawn against a target repo carrying a checked-in
  `.claude/settings.json`/`.claude/hooks`/etc. (spawn.py:857), because a
  repo-declared hook is not bound by the spawned session's
  `sandbox.filesystem` policy and runs with full ambient privilege
  (2026-07-27 incident, documented in spawn.py). on-the-record is itself
  such a target repo on every self-hosted spawn, so a fix that checks in
  `.claude/settings.json` here would trip that same stop on every future
  spawn against this repo unless separately trust-pinned.
- Registration must be mechanically kept in sync with
  `on-the-record/hooks/hooks.json` — a hand-copied second list drifts.
- `${CLAUDE_PLUGIN_ROOT}` in the shipped hooks.json must resolve
  correctly when the hooks run against on-the-record's own tree (not a
  consumer's plugin-cache path).

## Rationale

Two mechanisms were viable, per the issue body's own wording ("spawn
workspace/session wiring (spawn.py) or checked-in .claude/settings.json"):

- **Checked-in `.claude/settings.json`** — alternative considered,
  rejected. Simplest on paper, but per the survey it collides with
  `require_no_repo_config`: on-the-record spawning a role session against
  itself is exactly the "target repo carries its own
  `.claude/settings.json`" case that function exists to stop. Using it
  would require every self-hosted spawn to carry `--trust-repo-config`
  (or a pre-seeded trust pin), which either reintroduces a manual opt-out
  step on every clone/CI run or requires special-casing "this repo trusts
  itself" — at which point the special-casing has to live in spawn.py
  anyway, so the checked-in file buys nothing spawn.py-side logic doesn't
  already have to do. Rejected instead of accepted in favor of the
  spawn-time approach below.
- **Spawn-time injection in `spawn.py`** (chosen instead) —
  `role_settings()` already builds the merged `--settings` temp file
  spawn.py hands to `claude -p` (spawn.py:427, spawn_cmd at
  spawn.py:2886). Detecting that the spawn target `cwd` resolves to the
  on-the-record repo itself and merging
  `on-the-record/hooks/hooks.json`'s hooks into that generated dict's
  `"hooks"` key never touches `require_no_repo_config` at all — there is
  no checked-in `.claude/settings.json` for it to trip on. The same code
  path this repo already uses to spawn its own role sessions (including
  this one) becomes the place the hooks turn on.

## What will be done

- Add a helper in `spawn.py` (near `role_settings`) that loads
  `on-the-record/hooks/hooks.json`, resolves `${CLAUDE_PLUGIN_ROOT}` to
  the on-the-record repo root, and returns the resulting `hooks` dict.
- In `role_settings()`, when the spawn target `cwd` resolves to the
  on-the-record repo root (self-hosted dogfooding), merge that dict into
  the returned settings under `"hooks"` — additive, no change for spawns
  against any other target repo.
- Add `gates/test_hooks_parity.py`: asserts every command entry present
  in `on-the-record/hooks/hooks.json` has a matching entry in the
  spawn.py-side registration output (same event, same matcher, same
  script name) — mechanical parity pin per the issue's acceptance
  criterion.
- Add a live-fire deny test in the same file (or a sibling test module):
  spins up a temp git clone of a minimal repo shaped like on-the-record's
  spec-tracked layout, runs the self-hosted `role_settings()` output
  through an actual `claude`-hook-shaped invocation (or, if driving the
  real CLI is impractical in test, directly invokes
  `spec-index-preflight.sh` as the PreToolUse hook would, with the merged
  settings' env) attempting to stage a spec-tracked file without index
  regen, and asserts the attempt is denied (nonzero exit / blocking
  output) before a commit lands — red without the registration, green
  with it.
- Document the self-hosted hook wiring (new spawn behavior) in
  `docs/handbooks/spawn.md` per the doctrine ladder (this is a
  spawn-mechanism behavior change, not a new env var/dep, so it goes to
  the handbook rather than `decisions/`).

## Out of scope

- Changing what the individual hook scripts (`spec-index-preflight.sh`
  etc.) check — this is wiring only, not hook logic.
- Extending self-hosted hook wiring to any repo other than on-the-record
  itself (no general "any target repo can opt in to its own hooks"
  mechanism).
- Touching `require_no_repo_config`'s behavior for actual consumer target
  repos.

## How you'll know it worked

- `gates/test_hooks_parity.py` fails red on a `hooks.json` entry with no
  matching spawn.py-side registration, and passes on current state after
  the change.
- The live-fire test denies a real `git commit` attempt (spec-tracked
  file staged without index regen) in a temp clone with the registration
  active, and the same attempt succeeds when the registration is stubbed
  out — a genuine red/green pair, not fixture-only.
