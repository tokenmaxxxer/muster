
## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: NO FINDING
Seed: docs/issue-327/proposals/2026-08-07-idle-deadlock-watchdog-exit-code.md (frozen write set: spawn.py, test_spawn.py, docs/issue-327/decisions/watchdog-exit-code.md)
cap_seconds: 120
tier: default
diff_stat_lines: 21-200 (docs-only proposal+survey)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:05:00Z

Searched for any caller/test/doc that invokes `roster_watchdog()` or the `spawn.py watchdog` CLI subcommand and depends on its exit code being 0: grepped every `.py` file for `roster_watchdog(` (only definition + CLI dispatch at spawn.py:2438 + a docstring mention at spawn.py:1884), grepped all other `test_*.py` files (`test_flows.py`, `test_gates.py`, `test_approve_scope.py`, `test_vocab_coherence_roles.py`, `gates/test_closes_gate_ci.py`) for "watchdog" (no matches), searched for `.yml`/`.yaml` CI/workflow files referencing watchdog (none exist in the repo), and searched for cron/systemd unit files (none). The only prose reference outside the write set, `on-the-record/commands/run.md`, instructs an agent to run `spawn.py watchdog` manually and read its printed output/report anomalies to the user — it never branches on `$?`, so a nonzero exit there doesn't silently break anything. `docs/handbooks/operations.md`'s "exit 0" mentions are about a *role session's own* exit code (a different code path, `session_end_verdict`), not `roster_watchdog()`'s return value. `drive()` also never calls into watchdog. No `subprocess.run(...check=True...)` chains to `spawn.py watchdog` exist anywhere in the tree. The frozen write set (spawn.py, test_spawn.py, decision doc) appears to cover every place `roster_watchdog()`'s return value is produced or consumed in this repo.
