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
