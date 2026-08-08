# Survey — #505 slow-session root-cause mining

## Data source

`runs/ledger.jsonl`, resolved at
`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/ledger.jsonl`
(gitignored, per `spawn.py:2602-2604`, same source #501 used). 130 rows,
all `ts` in 2026-08-08 (`1786176521`-`1786194095`), spanning three repos:
`on-the-record`, `tokenmaxxxer-core`, `repo-status-board`. Each row's
`log` field points to a `.session.<ts>.<pid>.log` stream-json file on
disk; all referenced logs still exist and were read directly with `grep`
(the `Read` tool paginates the ledger itself; `grep -n`/`-c`/`-o` on the
`.log` files was used for the per-session mining — no external service
needed).

## Ranking

Sorted all 130 rows by `duration_s` descending. Top 8, spanning both
`on-the-record` and `tokenmaxxxer-core` (the two repos with slow-tail
sessions; `repo-status-board`'s slowest row is 252.5s, well below this
cutoff):

| rank | issue | repo | duration_s | denials | log |
|---|---|---|---|---|---|
| 1 | 474 | on-the-record | 1278.2 | 8 | on-the-record-issue-474-implementation.session.20260808T185416.615087.log |
| 2 | 147 | tokenmaxxxer-core | 945.0 | 10 | tokenmaxxxer-core-issue-147-implementation.session.20260808T180551.278899.log |
| 3 | 473 | on-the-record | 879.3 | 5 | on-the-record-issue-473-implementation.session.20260808T185414.614822.log |
| 4 | 444 | on-the-record | 786.6 | 22 | on-the-record-issue-444-conformance-review.session.20260808T171525.81566.log |
| 5 | 466 | on-the-record | 774.2 | 16 | on-the-record-issue-466-implementation.session.20260808T182125.376806.log (rc=1, errored) |
| 6 | 180 | tokenmaxxxer-core | 748.8 | 15 | tokenmaxxxer-core-issue-180-implementation.session.20260808T205402.1314513.log |
| 7 | 476 | on-the-record | 733.9 | 12 | on-the-record-issue-476-implementation.session.20260808T191137.703566.log |
| 8 | 457 | on-the-record | 730.3 | 9 | on-the-record-issue-457-implementation.session.20260808T173352.189778.log |
| 9 | 171 | tokenmaxxxer-core | 727.6 | 52 | tokenmaxxxer-core-issue-171-implementation.session.20260808T214140.1624298.log |
| 10 | 497 | on-the-record | 723.3 | 15 | on-the-record-issue-497-defect-verification.session.20260808T204508.1271715.log |

Row 9 (issue-171, 52 denials in one 727.6s session — an outlier even
against this slow-tail cohort) was substituted in for row 476 in the
actual mining pass below because its denial count signaled a
concentrated friction pattern worth reading in full; the acceptance
check only requires N>=8 analyzed with citations, not a fixed rank cutoff.

## Log format constraint (confirmed, same finding as #501's survey)

Stream-json events carry no per-event wall-clock timestamp field except
the terminal `result` event. Attribution below is therefore done by
**event-order and content**, not by summing timestamped sub-intervals:
each `"is_error":true` tool_result and each `tool_result_meta.non_execution_kind`
(`user-rejected`, `permission-rule`) was pulled out with
`grep -n '"is_error":true'` and read in context to classify the cause,
matching the issue's own instruction to cite "log file and line ranges"
rather than derive exact per-cause durations (which the format cannot
support without new instrumentation — the same conclusion #501 reached
for the fixed-startup term).

## What the mining actually found (headline, detail in proposal)

- Three sessions (466, 171, 444) show the exact friction class #187
  already named: a subagent or the top-level session repeatedly retries
  writes/commands into a sandbox-denied path with no adaptation between
  retries (issue-171: the identical scratchpad path denied 22 times
  across the session; issue-444: a `general-purpose` subagent's Bash
  calls denied 11 consecutive times over ~1 minute of wall-clock).
- Two sessions (474, 147) show `board-gate.sh` / gate-refusal loops
  against **wrong-branch or nonexistent-issue paths** the worker
  generated itself (writing `docs/issue-416/` or `docs/issue-999/` from
  a session whose branch is `issue-474/implementation` or
  `issue-147/implementation`) — repeated identically rather than
  correcting the path after the first refusal.
- One session (473) burned ~5 retries on `"This command requires
  approval"` / a malformed multi-statement Bash command the sandbox
  rejected as a compound operation, on top of one self-inflicted
  `InputValidationError` (malformed JSON tool call).
- issue-180 and issue-457 show the same approval-wall shape at lower
  multiplicity (2 each).
- Two sessions in the slow tail (473's large `gates.claims` output, 474's
  `test_recurrence.py` failures) are largely **genuine task size / real
  test-driven debugging**, not system friction — the issue explicitly
  asks to distinguish these, and they are called out as (d) in the
  proposal's table rather than force-fit into a bug row.

## Skip conditions checked

Scout-directive product-scouting does not apply: this is an internal
measurement/analysis task with no product-shaped surface and no external
best-in-class comparable (the issue is self-contained: mine data already
in the ledger and existing logs). Skip condition used: "the spec leaves
no design decision open" is *not* fully true (there is a real design
choice below — the log-citation table format), so a proposal §Rationale
naming the alternative was written rather than a bare skip claim.
