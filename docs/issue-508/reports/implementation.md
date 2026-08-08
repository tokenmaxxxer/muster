---
code_under_review:
  - spawn.py
  - gates/test_hooks_parity.py
  - docs/handbooks/spawn.md
loop_state: landed
---

Subject: issue-508

## Summary of work

Delivered the spawn-time hooks.json injection for self-hosted sessions
approved in `docs/issue-508/proposals/2026-08-08-dogfood-hooks-for-self-hosted-sessions.md`:

- `spawn.py`: added `self_hosted_hooks(cwd)` — detects a self-hosted spawn
  target by `<cwd>/on-the-record/hooks/hooks.json` existing, loads it, and
  resolves `${CLAUDE_PLUGIN_ROOT}` to `<cwd>/on-the-record`. `role_settings()`
  now takes an optional `cwd` and merges the resolved hooks into the
  returned settings dict's `"hooks"` key only when the target is
  self-hosted — additive, no change for any other target repo. Both call
  sites (`main()`'s `--dry-run` path and `_spawn_one()`) now pass `cwd`.
- `gates/test_hooks_parity.py` (new): asserts every (event, matcher,
  script) entry in `on-the-record/hooks/hooks.json` has a matching entry
  in what `self_hosted_hooks()` actually returns (mechanical parity, read
  from the real file each run, not a hand-copied list) — plus a live-fire
  test that stages a spec-tracked file drifted from
  `docs/specs/reconciled-index.md` in a real temp git repo, runs the
  actual `spec-index-preflight.sh` (as registered via the self-hosted
  merge) the way the PreToolUse hook invokes it, and asserts the commit
  attempt is denied (exit 2) before it lands — then updates the index and
  asserts the same script allows it (exit 0) and the commit actually
  succeeds. Genuine red/green, not fixture-only.
- `docs/handbooks/spawn.md` (new): documents the self-hosted hook wiring
  mechanism, why spawn-time injection was chosen over a checked-in
  `.claude/settings.json` (the `require_no_repo_config` collision), and
  how to run the parity test.

## Why

Per the issue and the phase-1 proposal: this repo's own role sessions ran
with the plugin's shipped hooks (preflights, guards, stop-gate) inert,
because there is no `.claude/settings.json` here to wire them in, while
consumer installs get them via `--plugin-dir`. Checking in a settings
file here would collide with `require_no_repo_config`'s stop (this repo
is itself a spawn target on every self-hosted spawn), so the fix injects
the hooks into the generated `--settings` temp file instead, at the point
`role_settings()` already builds it.

## Upstream basis

docs/issue-508/proposals/2026-08-08-dogfood-hooks-for-self-hosted-sessions.md

## What did not work

- First live-fire test attempt passed `CG_PAYLOAD` via subprocess `env`.
  `spec-index-preflight.sh` overwrites `CG_PAYLOAD` from its own `cat`
  of stdin (`CG_PAYLOAD="$payload" python3 -c "$GUARD"`), so the env
  override was silently ignored and the guard always saw an empty
  payload (exit 0, no deny). Fixed by passing the JSON payload via
  `subprocess.run(..., input=payload)` (stdin) instead of `env`.

## Doctrine ladder placement

- [x] Spawn-mechanism behavior change (new `cwd` param on
  `role_settings()`, self-hosted hook injection) → `docs/handbooks/spawn.md`
  (new file, this commit).
- No new env var, dependency, or migration — no `.env.example` or
  manifest change needed.
- No library-or-format choice over a named alternative beyond what the
  phase-1 proposal's Rationale already recorded (checked-in settings vs.
  spawn-time injection) — nothing further for `docs/issue-508/decisions/`.

## Verification run (this session)

```
python3 -m py_compile spawn.py
python3 gates/test_hooks_parity.py
```
Output:
```
  ok  t_live_fire_deny_before_commit_lands
  ok  t_non_self_hosted_target_gets_no_injection
  ok  t_registered_hooks_match_hooksjson_entries
  ok  t_role_settings_merges_hooks_only_for_self_hosted_target

4 passed
```

## Open findings

None open at commit time.

## resolved_findings

- before-landing warrant-hunter (stance 0, bypass hunt), finding: silent
  fail-open — `self_hosted_hooks()` returned `None` with no log on a
  malformed/unreadable `hooks.json`, so a self-hosted spawn against a
  corrupted hooks.json ran with zero guard hooks and no visible signal.
  Repro: write invalid JSON to `<target>/on-the-record/hooks/hooks.json`,
  call `spawn.role_settings('implementation', target)` — `hooks` key
  absent, no error. Fix: both the read-failure and parse-failure paths in
  `self_hosted_hooks()` now print a stderr diagnostic before returning
  `None`, so the omission is visible instead of indistinguishable from a
  healthy self-hosted run. Re-ran `gates/test_hooks_parity.py` after the
  fix — still 4 passed.

## Closed checks

- closed_checks: `t_registered_hooks_match_hooksjson_entries` (parity
  pin) — passed against this record's code_under_review.
- closed_checks: `t_live_fire_deny_before_commit_lands` (live-fire
  red/green) — passed against this record's code_under_review.
