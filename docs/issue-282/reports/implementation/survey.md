SKIP CONDITION: pure bugfix. The issue names the exact defective code (spawn.py:2104-2114
`core_plugin_dirs()`), the exact drift cause (aa59f97 hardcoded a name tuple, 130cb13 later
promoted `warrant` into the marketplace without updating the tuple), and a concrete fix
direction with acceptance criteria. No design decision is open — scout's field-research
protocol is skipped per its own two-condition skip clause.

## Current state (verified by reading, not just the issue text)

- `spawn.py:2104-2114` `core_plugin_dirs()`: hardcodes `("core", "terse", "freelunch", "scout")`,
  filters silently with a bare `.is_file()` check, no reporting.
- `spawn.py:2035-2065` `core_root()`: resolves the `tokenmaxxxer-core` checkout root (local
  override env vars, then a managed clone under `runs/rulebooks/tokenmaxxxer-core`, halting via
  `sys.exit` if neither yields a `core/.claude-plugin/plugin.json`).
- The actual `tokenmaxxxer-core` checkout's marketplace file
  (`<core_root>/.claude-plugin/marketplace.json`) declares exactly five plugins, each with a
  local `"./name"` source: `core, terse, freelunch, scout, warrant`. Confirmed by reading the
  live checkout at `/home/jwjung/tokenmaxxxer/tokenmaxxxer-core/.claude-plugin/marketplace.json`.
- `spawn.py:229-250` `plugin_dirs()` (the role-rulebook sibling function) is the pattern to
  mirror: reads `plugins` from a marketplace.json, resolves each declared plugin's directory
  under the checkout root, and **prints a stderr line naming the plugin when its directory is
  missing** rather than silently dropping it — but it does not halt (its "no plugins resolved"
  case is a broader failure than a single missing plugin, so it only halts when the whole list
  comes back empty). The issue for `core_plugin_dirs()` explicitly asks for a *halt* (fail
  loudly) on a declared-but-missing plugin, which is stricter than `plugin_dirs()`'s current
  behavior — core plugins are load-bearing protocol machinery (contract enforcement, scope
  gates), unlike role-specific rulebook plugins where a missing one degrades a single role.
- `spawn.py:2881` calls `core_plugin_dirs()` and stores the result in `core_plugins`, passed to
  `spawn_cmd()` (`spawn.py:2891-2892`), which turns each path into a `--plugin-dir` flag
  (`spawn.py` `spawn_cmd`, confirmed via `test_spawn.py::test_core_is_attached_by_path`) and
  also derives `CLAUDE_PLUGIN_ROOT_CORE` from whichever entry is named `core`
  (`spawn.py:2294-2304`).
- The spawn banner is printed at `spawn.py:2887-2888`:
  `f"[{role}] 플러그인 {len(plugins)}개, 룰북 {checkout_version(role, spec)}, core {core_version()}, 작업 디렉터리 {cwd}"`
  — it reports a **count** of role plugins and a core rulebook version string, but never names
  which core plugins actually attached. The issue's acceptance criterion #3 ("스폰 배너가 붙은
  core 플러그인들을 이름으로 밝힌다") requires adding the names here.
- `test_spawn.py` already exercises `core_plugin_dirs` extensively via
  `mock.patch.object(spawn, "core_plugin_dirs", lambda: [])` in several call sites (lines
  ~3118, ~3202, ~3275) — those mocks are unaffected by changing the function's internals, since
  they replace the whole function. No test currently pins the *actual* returned name set against
  `marketplace.json`; that is the acceptance-criterion #3 gap ("마켓플레이스 대비 플러그인 셋을
  고정하는 테스트").

## Write set (frozen, projected honestly)

- `spawn.py` — rewrite `core_plugin_dirs()` to read `<core_root()>/.claude-plugin/marketplace.json`
  and resolve each declared plugin's local source directory, halting loudly (`sys.exit`) if any
  declared plugin's `plugin.json` is missing; update the banner at `spawn.py:2887-2888` to name
  the attached core plugins.
- `test_spawn.py` — one new test pinning the returned plugin-dir name set against a
  `marketplace.json`, built in a `tempfile.TemporaryDirectory()` the same way existing
  `core_root()` tests in this file already do (`tests/fixtures/rulebooks/tokenmaxxxer-core`
  only holds a bare `core/plugin.json`, no marketplace.json, so it is not reusable as-is), plus a
  test for the halt-on-missing-plugin case.

No new dependency, no new env var, no schema/migration change.
