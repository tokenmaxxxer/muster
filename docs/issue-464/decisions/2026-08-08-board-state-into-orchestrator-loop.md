# ADR: board-state disposition table (class A orchestrator-loop re-homing, class B #444 audit dispositions)

- Status: accepted
- Subject: issue-464
- Approved: 2026-08-08, `APPROVE issue-464/architecture` (single-account mode, JiwonJung94, approvers.md)

## Context

`on-the-record/UNENFORCED-CLAUSES.md` records 6 rows as "GitHub-board
state unreachable from a local session" (#312, #325, #369, #383, #388,
#407) and 23 rows from the #444 conformance audit as `Prose-only` with no
consumer-facing gate. issue-464 asked for a per-row disposition:
class A (the 6) needs mechanism-or-drop given the operator's 2026-08-08
reversal of the 2026-08-07 out-of-scope ruling ("the orchestrator ... CAN
call gh"); class B (the 23) needs one of `shipped-hook`,
`deployed-contract+check`, or `operator-drop` per row.

The 2026-08-07 ruling held that board-wide drift/absence scanning is a
retrospective GitHub-API operation a local `PreToolUse`/`Stop` hook
cannot perform (session-scoped, no board-wide `gh` access). The
2026-08-08 reversal narrows that: `spawn.py:roster_watchdog()`
(spawn.py:1635) is not hook-scoped — it already runs on the
orchestrator's repeating board-read tick (spawn.py:1638, "오케스트레이터가
10-15분 간격으로 반복 호출한다") and already makes `gh`-backed judgment
calls (`watchdog_check_one`, `_auto_respawn_check`) inside that tick,
report-only by contract (spawn.py:1637, "observe-only: 아무 것도 고치거나
죽이지 않는다"), non-zero exit on anomaly (spawn.py:1651-1654). Two of the
six rows already have gates built to that exact pure-function-plus-scan
shape: `gates/closure_sweep.py:classify()` (closure_sweep.py:38) and
`gates/spawn_coverage.py:find_uncovered()` (spawn_coverage.py:26).

Full survey: `docs/issue-464/reports/architecture/survey.md`.
Full disposition rationale: `docs/issue-464/proposals/2026-08-08-per-row-disposition-table.md`.

## Decision

### Class A — board-state rows (6)

| issue | disposition | mechanism / reason |
|---|---|---|
| #369 | re-homed: `spawn.py:roster_watchdog()` orchestrator-loop mechanism | board-wide remainder wired via `gates/closure_sweep.classify()` called from the watchdog tick; single-PR portion stays in `contract-guard.sh` as already recorded |
| #383 | re-homed: `spawn.py:roster_watchdog()` orchestrator-loop mechanism | `has_record_evidence`/`gates/closure_sweep.classify()` called from the watchdog tick, same board-wide read the tick already performs |
| #325 | re-homed: `spawn.py:roster_watchdog()` orchestrator-loop mechanism | `gates/spawn_coverage.find_uncovered()` called from the watchdog tick; row already names this exact gate |
| #312 | **not reversed** — re-confirmed drop | issue-comment-history resolution (`APPROVE issue-<n>/<role>` comment state), not an absence-over-time board scan; no existing gate computes it; operator's stated reasoning does not cover this shape |
| #388 | **not reversed** — re-confirmed drop | live `gh api` POST-vs-GET failure-mode discrimination, not a drift scan; a static/periodic tick cannot reproduce a live call's failure mode |
| #407 | **not reversed** — re-confirmed drop | already `contract, CI-supplement` verdict class (advisory scope-overlap judgment), a different verdict class than the reversal targets |

`UNENFORCED-CLAUSES.md`'s top table and gate-porting rows for #369/#383/#325
get their verdict changed from "out of scope" to a citation of the
`roster_watchdog` mechanism (follow-up issue, see below). #312/#388/#407's
existing rows stand unchanged, with a citation back to this ADR for why
the reversal does not reach them.

### Class B — #444 audit rows (23)

**`operator-drop`** (8): #321, #324, #329, #336, #371, #373, #391, #392.
Dev-process/record-keeping issues with no consumer-facing behavior to
gate, per the #444 audit's own recommendation; this ADR is the operator
confirmation the disposition table requires. Cited in
`UNENFORCED-CLAUSES.md` against this issue.

**`deployed-contract+check`** (13): #318, #320, #362, #363, #376, #377,
#379, #390, #412, #415, #416, #419, #424. Each needs a `gates/` check plus
`run.md` contract text with a named regression check, delivered via
#441's mechanism. Too large for one implementation session — sized as
follow-up issues per row or small batch (see below).

**`shipped-hook`** (2): #374, #428. Both need actual runtime code rather
than a `gates/` check — #374 a Stop-hook (currently only proposed), #428
a `spawn.py` fix plus an `on-the-record/hooks/**` equivalent.

23 rows: 8 + 13 + 2 = 23, matching the #444 audit's count.

## Consequences

- `UNENFORCED-CLAUSES.md` and `docs/specs/enforcement-boundary.md` need
  updates (implementation-role follow-up) reflecting the changed
  verdicts for #369/#383/#325 and the class-B dispositions; architecture
  does not make those edits (write scope is `docs/issue-464/decisions/**`
  plus its own report).
- `gates/test_boundary.py`'s `t_gate_porting_rows_are_ported_or_justified`
  currently only checks that an issue's `#N` tag appears somewhere in an
  `UNENFORCED-CLAUSES.md` row, not that the verdict text is a real
  mechanism citation (hunt finding, see proposal). The #369/#383/#325
  follow-up issue should tighten this check alongside the row rewrite.
- Follow-up implementation work is sized into separate issues (below),
  not built in this session, consistent with issue-464's own
  "issue-sizing 준수" instruction.

## Alternatives considered

- **Reverse all 6 class-A rows.** Rejected: the operator's stated
  reasoning ("the orchestrator ... CAN call gh") is scoped to the
  board-wide absence/drift-scan shape `closure_sweep.py`/
  `spawn_coverage.py` generalize; #312/#388/#407 are structurally
  different judgments (comment-history resolution, live-call
  failure-mode discrimination, already-recorded CI-supplement verdict)
  with no existing gate or board-wide-scan analog. Reversing them would
  assert a mechanism that does not exist.
- **New standalone watchdog mechanism per class-A row.** Rejected:
  `roster_watchdog()`'s existing tick, plus the already-built pure
  functions in `closure_sweep.py`/`spawn_coverage.py`, already provide
  the injection point; a new mechanism would duplicate it for no
  benefit.
- **One follow-up issue for all 13 `deployed-contract+check` rows.**
  Rejected per the survey's sizing note: 13 rows each needing a distinct
  `gates/` check plus contract text is not one implementation session's
  work; filed as multiple issues instead (see follow-up list).

## Follow-up implementation issues (to be filed by the operator)

1. **Class-A orchestrator-loop wiring** (#369, #383, #325): wire
   `gates/closure_sweep.classify()` and `gates/spawn_coverage.find_uncovered()`
   into a `roster_watchdog()` tick call, surfaced the same way watchdog
   anomalies are today (printed + non-zero exit, nothing auto-closed).
   Rewrite the #369/#383/#325 rows in `UNENFORCED-CLAUSES.md` (top table
   and gate-porting list) and `docs/specs/enforcement-boundary.md` to
   cite the new mechanism instead of "out of scope." Tighten
   `gates/test_boundary.py`'s `t_gate_porting_rows_are_ported_or_justified`
   to validate verdict text, not just tag presence (hunt finding).
2. **Class-A re-confirmed-drop citation** (#312, #388, #407): add a
   citation from their existing `UNENFORCED-CLAUSES.md` rows back to this
   ADR, recording that the 2026-08-08 reversal does not reach them and
   why.
3. **Class-B `operator-drop` recording** (#321, #324, #329, #336, #371,
   #373, #391, #392): add `UNENFORCED-CLAUSES.md` rows citing this ADR as
   the operator confirmation of the drop.
4. **Class-B `deployed-contract+check` delivery** — sized per row/small
   batch, not one issue (13 rows: #318, #320, #362, #363, #376, #377,
   #379, #390, #412, #415, #416, #419, #424). Each needs a `gates/` check
   plus `run.md` contract text with a named regression check, per #441's
   delivery mechanism.
5. **Class-B `shipped-hook` delivery — #374**: implement the Stop-hook
   currently only proposed.
6. **Class-B `shipped-hook` delivery — #428**: `spawn.py` fix plus an
   `on-the-record/hooks/**` consumer-facing equivalent.
