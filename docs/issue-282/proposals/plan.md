files: spawn.py, test_spawn.py

## Request

`core_plugin_dirs()` in `spawn.py` hardcodes a 4-name tuple (`core, terse, freelunch, scout`)
instead of reading `tokenmaxxxer-core`'s marketplace.json, which now declares five plugins
(adds `warrant`). Because of this, `warrant` — the scope-gate/hunt-guard/approval-freeze
protocol — never attaches to any role session, and a plugin dropped from the tuple in the
future would fail the same way, silently. Fix: read the plugin list from marketplace.json, halt
loudly on a declared-but-missing plugin dir, name the attached plugins in the spawn banner, and
pin the plugin set with a test against marketplace.json.

## Constraints

- No new dependency, no new env var, no schema/migration.
- Must not change `core_plugin_dirs()`'s return type (`list[Path]`) or call sites
  (`spawn.py:2881`, consumed by `spawn_cmd()` and the banner) — only its internals and the
  banner's format string.
- Must halt (`sys.exit`), not warn, on a declared-but-missing core plugin dir — core plugins are
  load-bearing protocol/gate machinery, not an optional role extra.
- Skip condition per scout's own clause: pure bugfix, fix direction and acceptance criteria
  already fully specified in the issue — no design decision is open, so the scout sweep does
  not run.

## Rationale

Considered mirroring `plugin_dirs()`'s existing behavior exactly (print-and-skip a missing
plugin, matching its role-rulebook counterpart) — rejected. `plugin_dirs()` skips a missing
role-plugin because a role rulebook's own scope failing is a degraded-but-survivable session;
a missing *core* plugin silently drops shared enforcement machinery (scope gates, contract
checks) that every role session is supposed to be running under, which is exactly the failure
mode this issue reports (`warrant` dropped for weeks with no visible signal). The issue's own
acceptance criteria confirm this: "A declared-but-missing plugin dir halts the spawn with a
named error." So `core_plugin_dirs()` gets stricter behavior than `plugin_dirs()`, not the same
behavior — the two functions' write sets differ (core-wide gate machinery vs. one role's
extras), so keeping their loudness policies different is intentional, not an inconsistency to
later reconcile.

## What will be done

- Rewrite `core_plugin_dirs()` (`spawn.py:2104-2114`) to:
  - Load `<core_root()>/.claude-plugin/marketplace.json`, iterate its `plugins` list.
  - For each declared plugin, resolve its local source dir (mirroring `plugin_dirs()`'s
    `source` handling, restricted to the `"./name"` string form that all five core plugins
    currently use — a non-string/remote `source` in the core marketplace is out of scope, see
    below).
  - If the plugin's `.claude-plugin/plugin.json` is missing, `sys.exit` with a message naming
    the plugin and the expected path (loud failure, not a filtered/silent drop).
  - Return the resolved `list[Path]`, same shape as today.
- Update the spawn banner (`spawn.py:2887-2888`) to name the attached core plugins (e.g. append
  `core 플러그인 {', '.join(p.name for p in core_plugins)}`), passing `core_plugins` into the
  banner's format call — `core_plugin_dirs()` is already invoked before the banner line
  (`spawn.py:2881`), so the resolved list is in scope with no reordering needed.
- Add to `test_spawn.py`:
  - A test building a temp `tokenmaxxxer-core`-shaped checkout (marketplace.json + 5 plugin
    dirs, mirroring the real one) and asserting `core_plugin_dirs()` returns exactly those five
    names — this is the "pin the set against marketplace.json" acceptance criterion.
  - A test where marketplace.json declares a plugin whose directory is absent, asserting
    `core_plugin_dirs()` raises `SystemExit` naming that plugin.

## Out of scope

- Non-string/remote `source` entries (e.g. `{"source": "github", ...}`) in the core
  marketplace — none of the five current core plugins use this form; `plugin_dirs()`'s handling
  of that case (skip, since it's a genuine remote-source concept) is not being ported here
  because core plugins are always local. If a future core plugin declares a remote source,
  that's a follow-up, not this fix.
- Changing `plugin_dirs()`'s (the role-rulebook function) missing-plugin behavior — it stays a
  warn-and-skip, per the Rationale above.
- Any change to `warrant`'s own hooks/content — this fix only makes the existing plugin load.

## How you'll know it worked

- `python -m pytest test_spawn.py -k core_plugin_dirs -v` passes, covering both the pinned-set
  test and the halt-on-missing test.
- Manually invoking `spawn.core_plugin_dirs()` against the real
  `tokenmaxxxer-core` checkout returns 5 paths (`core, terse, freelunch, scout, warrant`), run
  once and the actual output shown in the phase-2 record.
- The spawn banner line, inspected by reading the updated format string, names all attached core
  plugins rather than only a role-plugin count.
