---
proposal: docs/proposals/2026-07-30-issue-120-remove-wake-routing.md
---

# Hunt record — issue-120-remove-wake-routing

## after-proposal — stance 1: stale references to deleted `wakes`/`spawn.py wake` outside the changed files

Verdict: FINDING — on-the-record/hooks/directive.sh still instructs agents to run the now-deleted `spawn.py wake` subcommand, which fails silently as a bogus role name instead of a clear error.
Kind: silent-failure
Seed: removal of the `wake` CLI subcommand from spawn.py per issue #120; on-the-record/hooks/directive.sh was not part of the changed fileset.

### Reproduce
grep -n "spawn.py wake" on-the-record/hooks/directive.sh
python3 spawn.py wake -C .

### Observed
directive.sh line 62: `read the board first with \`python3 ${CHECKOUT}/spawn.py wake -C <repo>\`.` (and lines 63-65 build an entire "WAKES-ON" workflow instruction around re-running `wake` after every merge).

Running the command itself:
```
$ python3 spawn.py wake -C .
맡길 일이 없다. 사용법: spawn.py <역할> "<맡길 일>" [-C <경로>]
```
`wake` is silently parsed as a role/task argument and rejected with the generic "no task to hand off" usage message — there is no indication the `wake` subcommand was removed. An agent following directive.sh's instructions gets a confusing, unrelated error and no signal that the wake system is gone.

### Expected
Either directive.sh's WAKES-ON instructions should have been removed/updated as part of this change, or `spawn.py` should fail with an explicit "unknown command: wake (removed)" message so the stale instruction fails loudly instead of masquerading as a normal usage error.

### Resolution
Fixed in the same build: on-the-record/hooks/directive.sh rewritten to describe reading the board directly and orchestrator judgment, with no `spawn.py wake` reference left. This consumer was missed by the phase-1 survey (docs/issue-120/reports/coding/survey.md did not enumerate hook scripts) — noted in docs/issue-120/reports/coding.md's "What did not work".
