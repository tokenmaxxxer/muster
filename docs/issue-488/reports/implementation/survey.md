# issue-488 current-state survey

## Write surfaces examined
- `spawn.py` (3732 lines, single file, no package split): CLI dispatch in
  `main()` (spawn.py:2645), `_watch()`/`_await_bounded()` (spawn.py:2151,
  2211), workspace index (`_workspace_index_load/_workspace_index_put`,
  spawn.py:2137), roster (`roster_register`/`roster_ps`, spawn.py:1508+),
  and `_spawn_one()` (spawn.py:3285) which does the actual `fork()` +
  bounded-wait-then-return-to-caller dance.
- `test/test_spawn.py` — exists, has prior watch/respawn coverage (search
  below); this is where issue-488's acceptance checks land.

## How watch currently works (opt-in, manual)
- `spawn.py watch --issue n [--role r] [--follow]` looks up one entry in
  the workspace index (`{issue}/{role} -> {work, log}`, spawn.py:2137-2150)
  written by `_spawn_one()` at spawn time, then either:
  - one-shot: `_await_bounded()` blocks for exactly one event or a stall
    timeout, then returns (spawn.py:2151-2202).
  - `--follow`: loops `_await_bounded()`, tracking cross-call stall time
    itself, until a `session-end` event appears or crash is detected via
    `wrapper_pid` death (spawn.py:2211-2295+).
- `_spawn_one()` itself already forks: the parent process (the CLI
  invocation caller made) does ONE bounded wait and returns
  (spawn.py:3373-3376); the child carries the session to completion. This
  is the "bounded" flow used whenever `--issue` is passed. So today, a
  bare `spawn.py <role> ... --issue n` call already returns quickly and
  does NOT itself follow to session-end — the caller (a human or
  orchestrator) must separately run `spawn.py watch --issue n --follow`
  to observe completion. That second call is the opt-in step issue-488
  says gets skipped.
- Nothing currently registers a background "watcher" process at spawn
  time. `roster_register()` (spawn.py:1508) records the session itself
  (pid, work, log) for `ps`/`kill`/`watchdog`, not a watcher.
- `roster_watchdog()` (spawn.py:1667) is a separate, also-manual sweep
  (`spawn.py watchdog [--auto-respawn]`) that polls the whole roster for
  silence/no-commit/denial signals — it is the closest existing thing to
  a "many sessions at once" mechanism, but it is a single poll-and-report
  invocation, not a long-lived `--follow`-style stream, and it is not
  wired to auto-arm either.

## Prior related work (read before proposing)
- issue-484 (referenced by 488): fixed a *race* in watch/respawn and
  labeling — did not touch the opt-in nature.
- issue-451 (referenced by 488): comment at spawn.py:2239-2242 says the
  `--follow` loop can spin forever if a workspace-index entry never
  appears, because neither session-end nor wrapper_pid death signals in
  that case — a related but distinct gap (the watcher exists but never
  progresses, vs. issue-488's watcher never gets armed at all).
- docs/issue-224/proposals/query-watch-reliability.md and
  docs/issue-224/decisions/watch-crash-exit-code.md: prior watch reliability
  work, established `WATCH_CRASH_RC = 2` semantics (spawn.py:2205) that
  any new watch surface should keep consistent with.
- docs/issue-327/*: idle-deadlock watchdog exit code work, another
  watch-adjacent surface (`roster_watchdog`), same "silent stall" theme.
- docs/issue-90/proposals/coding-watchdog.md: origin of `roster_watchdog`
  itself — a prior explicit choice to keep watchdog **manual, observation-
  only** ("기본 off, 관찰-전용 유지" at spawn.py:2669-2671), reflecting a
  standing project stance against auto-triggering respawns/side-effects
  from a background sweep without an explicit flag. Relevant precedent
  for judging whether "auto-arm a detached process on every spawn" fits
  this codebase's risk posture, or whether an opt-in-but-single-call
  `--all` sweep (still manual, but "manual once per conversation" instead
  of "manual once per spawn") is the better fit.

## Existing test coverage for watch/respawn
The issue text says `test/test_spawn.py`; the actual file is
`test_spawn.py` at repo root (no `test/` dir exists) — the write set below
uses the real path. Relevant existing classes: `WatchFollow` (line 4904,
covers `--follow` stop/stall/crash-detection semantics against a single
pre-known `{issue}/{role}` entry) and `Watchdog` (line 3091, covers
`roster_watchdog` sweep behavior). Neither covers "a session spawned
*after* a long-lived watcher started" — that is the acceptance gap
issue-488 names, and confirms no `watch --all` surface exists yet (no
`--all` flag defined in `main()`'s argparse block, spawn.py:2645-2676).

