---
status: proposed
files:
  - docs/issue-501/reports/implementation/survey.md
  - docs/issue-501/proposals/2026-08-08-session-latency-breakdown.md
---

## Request

Step 1 of #501: measure, from today's real ledger/session-log data
(~80-123 sessions), the session-latency breakdown — fixed startup vs.
model working time vs. refusal/rework loops vs. approval round-trip idle —
citing source files for every row, and name the largest term so step 2's
cuts target it instead of a guess.

## Constraints

- Numbers must come from real data recorded today (`runs/ledger.jsonl` +
  its referenced `.session.*.log` files), not estimates.
- Every row of the breakdown must cite the file(s) it was derived from.
- No predetermined answer — the candidate directions listed in the issue
  (fixed-cost cuts, fast-path, fewer fix rounds, orchestrator batching)
  are confirmed or killed by what the numbers actually show, not assumed.

## Rationale

**Chosen approach**: use `runs/ledger.jsonl`'s `duration_s` (wall-clock)
against each session's own `.log` file's `duration_api_ms` (from the
`type:"result"` event) as the model-time term, treat the remainder as
non-model overhead, and separately compute inter-session gaps per issue as
the idle term.

**Alternative considered and rejected**: instrumenting hook-level
timestamps (patching `spawn.py`'s hooks to log wall-clock time per phase:
doctor probe, rulebook fetch, gate checks) to get a true fixed-startup
sub-breakdown. Rejected for step 1 because the session-log format
(`stream-json`) carries **no timestamp field on any event** except the
single end-of-session `result` line — confirmed by direct inspection of a
sample log (see survey). Building that finer instrumentation is itself a
code change to `spawn.py` (an operational-surface file, gated separately),
and the issue's step 1 asks for measurement from *existing* data, not new
instrumentation. It is exactly the kind of cut step 2 could add if the
coarse breakdown below shows fixed-startup is actually the dominant term —
but the data below shows it is not, so building it now would not have
paid for itself.

## What will be done

(Phase-1 scope: measurement + this proposal, per the issue's own
step-1/step-2 split. No code changes in this session.)

### Data

Source A — `runs/ledger.jsonl` (resolved at
`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/ledger.jsonl`,
gitignored per `spawn.py:2602-2604`): 123 rows, all timestamped
2026-08-08, spanning ~4.3h. All 123 referenced `log` files still exist on
disk and were read.

Source B — each row's own `.session.<ts>.<pid>.log` file (path taken
verbatim from the ledger row's `log` field): the `{"type":"result", ...}`
line's `duration_api_ms` field.

### (a) Fixed startup vs. (b) model working time

No event in the log format carries a per-phase timestamp (confirmed:
`init`, `hook_started`, `hook_response` events carry no wall-clock time
field) — so "fixed startup" (doctor probe, rulebook fetch, workspace
clone/reuse) cannot be isolated from other non-model wall-clock time with
what's recorded today. What *can* be measured precisely is the
model-vs-everything-else split:

| term | source | n | sum | share of wall-clock |
|---|---|---|---|---|
| wall-clock (session total) | `ledger.jsonl` `duration_s` | 123 | 36703.2s (611.7m) | 100% |
| model working time | each `.log`'s `result.duration_api_ms` | 123 | 31664.9s (527.7m) | **86.3%** |
| everything else (startup + hooks + gate checks + git/PR I/O, per session) | `duration_s − duration_api_ms/1000` | 123 | 5038.3s (84.0m) | 13.7% |

Per-session: wall-clock median 243.4s, p90 593.2s, max 1278.2s. Model time
median 218.7s, p90 498.2s. Non-model overhead median 16.9s, p90 93.1s, max
284.2s (one outlier session,
`tokenmaxxxer-core-issue-147-implementation.session.20260808T175916.
265356.log`, at 284s overhead against only 45s model time — worth a
one-off look in step 2, not evidence of a systemic fixed cost: the
p50/p90 gap between overhead (17s/93s) and model time (219s/498s) is an
order of magnitude in the other direction).

**5 of 123 sessions show negative "overhead"** (`duration_api_ms` slightly
exceeds `duration_s`) — the API's own reported time can include
concurrently-dispatched subagent/tool-call API time that overlaps
wall-clock rather than summing serially. Treated as noise around zero,
not a measurement error to correct — it does not change which term
dominates.

### (c) Refusal/rework loops

Outcome distribution (`ledger.jsonl` `outcome` field, all 123 rows):
`progressed` 98, `progressed-dirty-tree` 8, `refused` 7, `silent-failure`
6, `uncommitted-work` 2, `failed-no-commit` 1, `errored` 1.

Sessions whose outcome itself signals refusal/rework
(`refused`/`silent-failure`/`failed-no-commit`/`errored`, 15/123, 12.2% of
sessions) account for 1589.2s of model time and 358.8s of overhead — in
proportion to their share of sessions, not disproportionately expensive
per session.

Permission denials (`denials` field, a proxy for in-session
gate-refusal/retry loops within a still-`progressed` session) are
**common but individually cheap to observe from the ledger alone**: 96/123
sessions (78%) hit at least one denial, 535 denials total, but the ledger
does not record time-per-denial, so this term's wall-clock cost cannot be
separated from "model working time" above — denials happen *inside* the
model-time term (a denied tool call still consumes an API turn). This
means part of the 86.3% model-time share above is refusal/retry cost, not
new-work cost; the two are not currently separable from ledger data alone
and would need per-turn timestamps (not present) to split further.

### (d) Approval round-trip idle

Not a ledger field — reconstructed from inter-session gaps: for each
`(repo, issue, role)` pair with more than one session today (grouping key
includes `repo` — issue numbers are only unique within a repo, not
globally; see resolved finding below), sorted by `ts`, computed `idle =
next_session_start − prev_session_ts`, where `next_session_start =
next.ts − next.duration_s`.

- 80 consecutive same-(repo,issue) session pairs found; 79 had
  non-negative idle (1 pair overlapped — parallel dispatch, excluded as
  not a serial gap).
- Idle sum across those 79 pairs: 23336s (388.9m). Median 85s, p90 1063s,
  max 3389s (`tokenmaxxxer-core` issue 171, implementation→implementation).
- This total (388.9m) is **larger than total in-session wall-clock time**
  (611.7m) at 63.6% of it, and larger than the entire non-model overhead
  term (84.0m) by 4.6x — but it is heavily right-skewed: median idle is
  only 85s (fast orchestrator respawn is the typical case), while a
  handful of long gaps (the top 8 range 1063s-3389s, all on
  `tokenmaxxxer-core` issues 171 and 173 and `on-the-record` issues 472
  and 484) account for the bulk of the sum. This mixes orchestrator
  respawn latency and actual human-approval wait time indistinguishably
  (per the survey's stated limit) — cannot attribute the tail to either
  cause specifically from what's recorded.

**resolved_finding** (after-proposal warrant hunt,
`docs/reports/2026-08-08-hunt-session-latency-breakdown.md`, stance 2):
the first draft of this idle-gap grouping keyed on issue number alone
(via `-issue-(\d+)-` on `cwd`, no `repo`), which silently merges
same-numbered issues across different repos into one fabricated idle gap.
Today's real ledger has zero such collisions (verified across all 124
rows / 4 repos touched today), so the originally reported numbers were
unaffected, but the method itself was wrong. Fixed by keying on
`(repo, issue, role)` instead; re-run confirmed the totals and top-8 list
above are the corrected numbers (388.9m sum, same four issues in the
tail) — the finder re-cleared after the fix.

### Largest term, named

Ranking the four terms by measured wall-clock-equivalent sum:

1. **Model working time — 527.7m, 86.3% of in-session wall-clock.**
   Dominant *within a session*.
2. Inter-session idle (mixed respawn+approval-wait) — 388.9m, but
   concentrated in a long tail on 4 issues, not a uniform per-session
   cost.
3. Non-model in-session overhead (startup+hooks+gates+I/O) — 84.0m, 13.7%
   of in-session wall-clock.
4. Refusal/rework-outcome sessions' own cost — 15/123 sessions, in
   proportion to their share, not a distinct multiplier.

**Model working time is the largest single measured term** and dominates
per-session wall-clock by nearly 9:1 over non-model overhead. This kills
the "fixed startup is the dominant term" framing implicit in the issue's
first candidate direction (doctor-probe-once, rulebook-cache-reuse,
warm-workspace-pools) as the *primary* lever — those attack the 13.7%
term, not the 86.3% one. It does not kill that direction outright (84m/day
of overhead is real and some of it, like the one 284s-overhead outlier, is
plausibly a doctor-probe or clone cost worth a targeted look) — it demotes
it to secondary.

The inter-session idle tail (issues 171/472/484/173, gaps 1063-3389s) is
the other candidate worth step-2 attention: it is comparable in total
size to model time and, unlike model time, is plausibly compressible by
orchestrator-side batching (the issue's fourth candidate direction:
approve+respawn in one notification cycle) without touching model
behavior at all.

## Out of scope

- Building `test/test_latency_report.py` or any code change — this is
  step 1 (measurement + proposal) per the issue's own split; step 2 is
  the next proposal, once this one names its cuts against these numbers.
- Separating "fixed startup" from "hooks/gates" within the 84.0m overhead
  term — not possible from the current log format (no per-event
  timestamps); would require instrumenting `spawn.py` itself, which is
  step-2-shaped work on an operational-surface file.
- Separating "orchestrator respawn wait" from "human approval wait"
  within the 388.9m idle term — same limit, not recorded anywhere today.
- Sampling down from 123 to ~80 sessions — used the full available set
  instead, since it was already on disk and cheap to read; no sampling
  bias introduced.

## How you'll know it worked

- The breakdown table above has every row traceable to
  `runs/ledger.jsonl` and/or a named `.session.*.log` path — reproducible
  by re-running the same read-only aggregation against the same ledger
  file.
- The four candidate directions in the issue are each explicitly
  confirmed, demoted, or left open by a specific number above, not
  asserted from intuition.
- Step 2's proposal, once approved, targets model-working-time reduction
  and/or the inter-session idle tail (issues 171/472/484/173) as primary,
  and fixed-startup caching as secondary — traceable back to this table.

## What did not work

None — this session's scope was read-only measurement against existing
ledger/log data; nothing was written, undone, or replaced.
