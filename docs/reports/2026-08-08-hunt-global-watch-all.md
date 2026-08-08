---
proposal: docs/issue-488/proposals/2026-08-08-global-watch-all.md
---

# Hunt record — global-watch-all

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `watch --all --follow` is still opt-in at the arming step, so the proposal does not close the acceptance gap it claims to close ("make an unmonitored session ending structurally impossible")
Kind: design-error
Seed: docs/issue-488/proposals/2026-08-08-global-watch-all.md
cap_seconds: 60
tier: default
diff_stat_lines: 2 files added (survey.md, proposal.md), docs-only
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:01:00Z

### Reproduce
Read the proposal's "What will be done" section: `_watch_all` is wired in
as an extra CLI verb (`spawn.py watch --all --follow`) that the
orchestrator must remember to invoke once per conversation. Then check
whether anything in `_spawn_one()` (spawn.py:3285) or `main()`'s spawn
path enforces or verifies that a `--all` watcher is actually running
before a spawn is allowed to proceed:

  grep -n "_spawn_one\|watcher\|require" spawn.py | grep -i watch

No hit ties spawning to watcher presence -- spawn.py has no mechanism (pid
file, lock, liveness check) that a spawn call consults to confirm a
`watch --all` process is live, and the proposal's own "What will be done"
list does not add one.

### Observed
The proposal's rationale explicitly rejects auto-arm-per-spawn (the only
option that would tie spawning to watching structurally) in favor of
"one existing CLI process" that the orchestrator arms "once per
conversation" by remembering to run `watch --all --follow`. The failure
mode the issue describes -- "orchestrator skipped re-arming watch" -- is
not eliminated, only changed shape: instead of forgetting to re-arm after
every respawn, the orchestrator can just as easily forget to arm `--all`
at the start of the conversation at all, or the arming process can exit
(crash, OOM, terminal closed) mid-conversation with nothing to detect or
report that the sole watcher died, silently returning the whole board to
the original unmonitored state the issue is trying to eliminate. No
supervision of the watcher process itself, and no gate that blocks or
flags a spawn made while no watcher is registered as running, is part of
the proposed design.

### Expected
Either the design should make watching structurally coupled to spawning
(the rejected auto-arm option, or some liveness check `_spawn_one` itself
consults before proceeding), or the proposal should not claim to make
"an unmonitored session ending structurally impossible" -- it only reduces
the frequency of the opt-in call from per-spawn to per-conversation,
which is a mitigation, not a structural fix, and the acceptance section
should be worded accordingly (or a companion check added) rather than
asserting the gap is closed.

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — watchdog_check_one signal 5 verifies only that watcher_pid is *some* live pid via _alive() (bare os.kill(pid, 0)), never that the pid actually belongs to a spawn.py watch --follow process, so any live-but-unrelated pid recorded under watcher_pid (e.g. via PID reuse after the auto-armed watcher crashes/exits) reads as a healthy watcher and the auto-arm gate silently fails to catch it.
Kind: silent-failure
Seed: spawn.py _spawn_one() bounded branch (wproc = subprocess.Popen([... "watch", "--follow" ...]); _workspace_index_put(..., watcher_pid=wproc.pid)) + watchdog_check_one() signal 5 (_workspace_index_load()[key]["watcher_pid"] liveness via _alive()) + _alive() at spawn.py:1500
cap_seconds: 180
tier: default
diff_stat_lines: proposal-scoped (spawn.py auto-arm + watchdog signal 5 + _watch_all, plus test_spawn.py WatcherAutoArm/WatchAll)
started_at: 2026-08-08T20:03:30+09:00
ended_at: 2026-08-08T20:06:30+09:00

### Reproduce
```
python3 /tmp/claude-1000/-home-jwjung--tokenmaxxxer-work-on-the-record-issue-488-implementation/bccd821c-9126-4e62-8c7a-2c1d19f4aef6/scratchpad/repro.py
```
repro.py contents:
```python
import sys, os, time
sys.path.insert(0, "/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-488-implementation")
import spawn

key = "issue-999999/impl"
entry = {"work": None, "ts": int(time.time())}

# workspace index says the watcher is this test process own pid --
# a real, live process, but never a spawn.py watch process.
spawn._workspace_index_put(999999, "impl", "/nonexistent", "/nonexistent.log", watcher_pid=os.getpid())

anomalies = spawn.watchdog_check_one(key, entry, now=time.time(), state={})
print("anomalies:", anomalies)
```

### Observed
```
anomalies: []
```
_alive(os.getpid()) returns True because the calling test process is itself alive -- signal 5 reports no problem even though watcher_pid never pointed at a spawn.py watch invocation. The same holds for any pid that gets reused by the OS after the real auto-armed watcher subprocess (wproc) exits (crash, stall-timeout expiry, OOM-kill, etc.) but before the next watchdog tick: _alive() has no cmdline/identity check, so the reused pid reads as watcher alive.

### Expected
Signal 5 (or _alive, when used for this purpose) should confirm pid identity -- e.g. compare /proc/<pid>/cmdline against the expected "spawn.py watch --issue <n> --role <r>" invocation, or record a pid/start-time pair at arm time -- before treating a live pid as evidence the auto-armed watcher is still the one running. As written, "a spawn cannot report success without its own watcher registered" degrades at watchdog-check time to "a spawn cannot report success without some pid number, alive or reused, sitting in watcher_pid."
