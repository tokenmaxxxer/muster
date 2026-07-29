# Role-session runtime distribution (for issue-90 watchdog interval)

## Data source

`spawn.py` writes one JSON line per role session to `runs/ledger.jsonl`
(`ledger_write`, `spawn.py:1107-1114`, called at `spawn.py:1811-1820`). The
recorded fields per session include exactly the runtime signal the watchdog
needs directly:

```
ts, role, cwd, session_id, cost_usd, turns, rc, outcome,
board_delta, denials, duration_s, rulebook, gates
```

`duration_s` (`spawn.py:1817`, `round(time.monotonic() - t0, 1)`) is the
session's own wall-clock length — no derivation needed if this file has
entries.

**But it doesn't, here.** `runs/` is gitignored by design ("측정 데이터는
소스가 아니다" — measurement data is not source, `spawn.py:1108-1109`), so
it is empty in this checkout: `runs/ledger.jsonl` does not exist in
`/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-90-coding`. A populated
copy exists on this host at
`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/ledger.jsonl`,
but reading it was denied by the sandbox permission layer for this task
(Read and Bash `cat`/`python3` against that path both errored with
"Permission to use ... has been denied"). So the one place the actual
`duration_s` numbers live was not accessible in this run.

**Fallback used: git commit-timestamp clustering per role branch**, as
directed when no runtime data is reachable. Role output in this repo lands
as commits on `issue-<n>/<role>` branches (e.g. `issue-69/coding`,
`issue-73/coding`, `issue-90/coding`). Consecutive commit timestamps on a
branch mark points where the running agent produced visible output; a large
gap between two commits marks the boundary between one spawn/session and
the next (respawns, waits, human review turnaround). This is a runtime
*proxy*, not `duration_s` — it bounds session length from below (only
covers time between the first and last commit of a burst) and says nothing
about sessions that produced zero commits.

## Distribution

Source: `git log --format='%cI' remotes/origin/issue-69/coding` (42 commit
timestamps, 2026-07-24 22:35 -> 2026-07-29 13:18, this being the branch with
the deepest history available locally). Clustering rule: a gap of >60
minutes between consecutive commits starts a new session-cluster (60 min
chosen because the empirical gap list has a clear break — gaps cluster below
~51 min or jump to 80+ min, see below).

Per-cluster span (oldest -> newest, minutes), n=15 clusters:
`0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 36.5, 41.8, 48.8, 142.6, 222.3`

(the ten 0-minute entries are single-commit clusters: the agent's whole
visible output for that spawn was one commit, so the *measurable* span is
zero even though the session itself took nontrivial wall-clock time before
that commit — this is exactly the "short-lived vs long-lived" split the
issue asks about.)

- min: 0 min (single-commit sessions — majority, 10/15 clusters)
- median: 0 min (n=15, so median is the 8th value = 0)
- p90: ~142.6 min (the 90th-percentile index in this n=15 sample)
- max: ~222.3 min (the largest multi-commit burst, 16 commits)

Short vs long: sessions split into two regimes — commit-sparse sessions
(1-2 commits, spanning 0-2 min, the large majority) and commit-dense
sessions (7-16 commits over 37-222 min, a handful of long working
sessions). There is no smooth middle; the distribution is bimodal.

Raw inter-commit gaps across the same 41 gaps (sorted, minutes) — this is
the "normal inter-output gap" baseline used below:
`1.1, 1.2, 2.7, 5.0, 5.7, 7.9, 8.1, 9.4, 13.2, 13.7, 14.8, 15.4, 16.3, 16.6,
17.3, 17.5, 17.6, 19.2, 19.4, 21.4, 22.5, 23.7, 24.4, 36.5, 41.8, 48.8, 50.8,
80.6, 150.5, 160.3, 207.6, 249.6, 256.0, 264.4, 299.6, 314.4, 385.2, 804.4,
982.2, 995.2, 1000.6` — median gap ≈ 22.5 min. The break at 51 -> 80.6 min is
why 60 min was chosen as the cluster-boundary threshold above; gaps above
that are cross-session idle time (waiting on review, re-spawn latency),
not in-session silence.

## Interval implications

Because the true `duration_s` ledger was unreachable, treat the numbers
above as an order-of-magnitude floor, not a precise SLA input.

- **Check interval**: should be a small fraction of the *shortest* regime we
  care about catching stuck, i.e. the commit-dense/long-session regime
  (median-of-long-sessions ≈ 48.8 min in this sample), and no larger than
  roughly a third of the p90 completion time (142.6 min):
  `interval ≈ min(48.8, 142.6) / 3 ≈ 16 min`.
  Round down for safety margin -> **interval on the order of 10-15 minutes.**
  This also sits comfortably below the observed median inter-output gap
  during active sessions (22.5 min), so a watchdog polling at 10-15 min will
  typically see at least one commit/output between checks during a healthy
  long session, without polling so tightly that normal short silent stretches
  (a few minutes of tool calls between commits) trip it.

- **Silence threshold** (how long with *no* observed output before flagging
  the role as stuck): must sit above the normal in-session gap ceiling but
  below the p90 full-session completion time, so it doesn't fire on a
  slow-but-alive session yet does fire before the tail:
  - normal gap ceiling observed within-session: ~51 min (the last gap
    before the cross-session break)
  - p90 completion: ~142.6 min
  - silence threshold ≈ midpoint-ish, biased toward the gap ceiling since
    false negatives (missing a truly stuck session) are cheaper to recover
    from than false positives interrupting a live one:
    `threshold ≈ 51 + (142.6 - 51) * 0.4 ≈ 51 + 36.6 ≈ 88 min`.
  Round to **~90 minutes of silence** before the watchdog escalates
  (nudge/ping), with the outer bound of the observed max session (~222 min,
  or the >4-hour cross-session gaps seen in the raw list) reserved as the
  hard kill/timeout tier, since anything past that is indistinguishable
  from an abandoned/crashed session in this data.

- **Caveat to carry forward**: these thresholds are derived from a commit-
  visibility proxy on one branch's history, not the ledger's actual
  `duration_s`. Once `runs/ledger.jsonl` is readable (either by relaxing the
  sandbox for that path or by re-running this analysis with direct file
  access), re-derive min/median/p90/max directly per role from `duration_s`
  and prefer those numbers — they measure session wall-clock time directly
  instead of inferring it from when commits happened to land.
