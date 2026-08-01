# Survey — issue #182: inject CLAUDE_PLUGIN_ROOT_CORE into role sessions

## Confirmed gap
`grep -rn CLAUDE_PLUGIN_ROOT spawn.py` returns zero hits. Rulebook gates
resolve the core shared library via
`${CLAUDE_PLUGIN_ROOT_CORE:-<plugin-relative-path>/core}` (per issue text);
spawn.py never sets that variable, so gates fall through to the relative
fallback, which resolves inside the rulebook clone, not the real deploy
path — matching the issue's fail-open report.

## Where the env dict for role sessions is built
`spawn_cmd()` (spawn.py:1919-1975) is the single place that builds the
session argv + env additions; `_spawn_one()` (spawn.py:2290+) is the only
caller (both `main()` and `drive()` funnel through it — see the docstring
at spawn.py:2295-2296 on why a second spawn path would silently drop a
gate). `spawn_cmd()` currently sets only `CLAUDE_ROLE`,
`TOKENMAXXXER_SPAWNED`, optionally `GH_TOKEN`/`GIT_TERMINAL_PROMPT`, and
`TOKENMAXXXER_UNATTENDED` (spawn.py:1953-1974). `_spawn_one()` merges this
`extra_env` onto `os.environ` at the `subprocess.Popen(...,
env={**os.environ, **extra_env}, ...)` call (spawn.py:2401).

## Where the core checkout path is known
`core_root()` (spawn.py:1746-1783) resolves and — if absent — clones the
`tokenmaxxxer-core` checkout, returning its root `Path`. Every source of
core content already keys off this: `core_plugin_dirs()` (spawn.py:1786-
1796) builds `[root / n for n in ("core", "terse", "freelunch", "scout")]`
and passed as `--plugin-dir` args in `spawn_cmd()`. The `core` plugin's
own directory — `core_root() / "core"` — is exactly the path
`CLAUDE_PLUGIN_ROOT_CORE` needs to name: it is the directory the gate
scripts run from, and rulebook gates reference `core/` as
`${CLAUDE_PLUGIN_ROOT_CORE:-...}`, i.e. the plugin's own root when core is
loaded via `--plugin-dir`.

`core_plugin_dirs()` is called once in `_spawn_one()` at spawn.py:2332 and
its return value is *not* otherwise retained — `core_root()` would need a
second call inside `spawn_cmd()`, or the resolved list threaded in, to
name the `core` member without re-deriving it.

`core_plugin_dirs()` filters candidates that pass
`(root / n / ".claude-plugin" / "plugin.json").is_file()` — so under the
list, `core` may legitimately be absent if that specific plugin subdir
lacks a `plugin.json` (degraded checkout). The injected env var needs to
handle that case — an env var pointing at a nonexistent path is exactly
the fail-open surface issue #182 exists to close if left unguarded.

## doctor() probe (spawn.py:1852-1893)
`doctor()` spins up a throwaway probe plugin and checks that
`UserPromptSubmit`/`PreToolUse` fire in headless mode at all — it never
loads the real core plugin, never invokes a real gate script, and does
not touch `CLAUDE_PLUGIN_ROOT_CORE`/`spawn_cmd()` in any way (confirmed:
no `core_root`, no `spawn_cmd`, no `CLAUDE_PLUGIN_ROOT` reference in the
function body). It answers "do hooks fire" — not "can a gate actually
resolve gate-lib and deny." Issue #182's ask #2 ("검토") is exactly this
gap: today doctor-ok can be recorded even though a real role session's
gates fail open on gate-lib resolution.

## Existing regression-test pattern
`test_spawn.py` already has a `TestSpawnCmd`-shaped suite exercising
`spawn_cmd()`'s env dict directly, e.g.:
```
_, env = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
self.assertEqual(env["CLAUDE_ROLE"], "execution-observation")
```
(test_spawn.py:82-83, similarly :90 for `TOKENMAXXXER_UNATTENDED`). This
is the natural home for a `CLAUDE_PLUGIN_ROOT_CORE` assertion — same
function, same call shape, no new test scaffolding needed. `doctor()`'s
own probe is exercised separately (test_spawn.py:241 comment confirms
`doctor()`'s haiku probe intentionally bypasses `spawn_cmd()`), so a
doctor-probe regression test (if ask #2 is adopted) is a second,
independent test addition, not a variant of the existing one.

## Alternatives visible from the code as it stands
- Set the var unconditionally to `str(core_root() / "core")` inside
  `spawn_cmd()` — but `spawn_cmd()` presently takes `core_plugins` as an
  already-resolved `list[Path]` parameter and does not call `core_root()`
  itself; it would need a new import-free reliance on the passed
  `core_plugins` list instead, since `core_root()` triggers a network
  clone if missing (spawn.py:1770-1775) — calling it a second time from
  inside `spawn_cmd()` risks a second clone attempt if a caller ever
  passes `core_plugins` from a different source than `core_plugin_dirs()`.
- Derive the path from the already-resolved `core_plugins` list passed
  into `spawn_cmd()` (the list `_spawn_one()` builds via
  `core_plugin_dirs()` and hands in at spawn.py:2332) by locating the
  entry whose `.name == "core"`. This avoids a second `core_root()` call
  and stays consistent with "whatever plugins were actually resolved and
  passed to `--plugin-dir`" rather than re-deriving from scratch — see
  proposal Rationale for the tradeoff against the first alternative.
