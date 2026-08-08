# issue-464 phase-1 survey — architecture

## Scouting

Skipped. Neither product-shaped nor comparable to an external field: the
deliverable is a disposition table for this repo's own governance
mechanisms (orchestrator loop cadence, gate-vs-hook boundary). There is no
external exemplar to sweep for "how other systems classify their own
prose-only closures." The current-state survey below is the substitute
field pass — it inventories the actual write surfaces (`spawn.py`,
`gates/`, `on-the-record/hooks/**`) the disposition table must cite.

## Class A — board-state rows and the orchestrator loop

`on-the-record/UNENFORCED-CLAUSES.md` justifies #312, #325, #369, #383,
#388, #407 as "GitHub-board state unreachable from a local session" — a
`PreToolUse`/`Stop` hook runs inside one session tree with no board-wide
`gh` access. That premise holds for hooks. It does not hold for the
orchestrator: `spawn.py:roster_watchdog()` (spawn.py:1635) already runs on
a repeating board-read cadence — "오케스트레이터가 10-15분 간격으로 반복
호출한다" (spawn.py:1638) — and already calls `gh`-backed judgment
(`watchdog_check_one`, `_auto_respawn_check`) as part of that tick. It is
report-only by contract ("observe-only: 아무 것도 고치거나 죽이지
않는다", spawn.py:1637) and returns an anomaly count the CLI turns into an
exit code (spawn.py:1651-1654).

Two of the six rows already have gates built to this exact shape —
injectable pure function + thin CLI, report-only, board-wide, no daemon:

- `gates/closure_sweep.py` — `classify()` (closure_sweep.py:38) is pure
  (issue/PR state strings in, verdict out); the board-wide sweep drives it
  over `gh issue list`/`gh pr list`. Covers #369 (single-PR case already
  folded into `contract-guard.sh` per the spec; the board-wide remainder
  is this row) and #383 (`has_record_evidence`, needs the merged PR's
  record — the same "GitHub state beyond one session" gap).
- `gates/spawn_coverage.py` — `find_uncovered()` (spawn_coverage.py:26) is
  pure (open-issue list + `spawn.board(root)` in, uncovered issue numbers
  out). Covers #325 directly (its own UNENFORCED-CLAUSES row names this
  exact gate).

The other three rows in the six do not reduce to closure_sweep/
spawn_coverage board-wide logic and the issue's reversal instruction does
not reach them:

- #312 — phase-is-an-issue-property + `APPROVE issue-<n>/<role>` comment
  resolution. This is GitHub issue-comment history, not an
  absence-over-time board scan; it is a different shape of "board state"
  than closure_sweep/spawn_coverage generalize from. No existing gate
  computes it.
- #388 — `gh api` POST-vs-GET failure-mode distinction for CI's
  "no record" vs "API blocked" case. A live-call failure-mode
  discrimination, not a board-wide drift scan.
- #407 — `landing_readiness.py`'s advisory scope-overlap/checks judgment,
  already recorded as `contract, CI-supplement` (not an
  out-of-scope-operator-decision row) — a different verdict class than
  the 2026-08-07 reversal targets.

So the issue's "6 board-state rows" span two different UNENFORCED-CLAUSES
sections (the top-of-file table's `closure_sweep.py`/`spawn_coverage.py`
board-wide verdicts, and the "Justified — board-state unreachable"
gate-porting list) with overlapping but not identical membership. The
2026-08-07 reversal named in the issue applies specifically to the
closure_sweep/spawn_coverage board-wide verdicts (#369, #383, #325 sit on
that reasoning chain); #312/#388/#407 were never covered by that ruling
and stay as they are — read literally, the issue also asks to re-home
these three, but nothing in the operator's stated reasoning ("the
orchestrator... CAN call gh") extends to them, and no board-wide
absence/drift scan exists for their judgment shape. The proposal below
flags this as a scope note rather than silently either including or
dropping them.

## Class B — the 23 prose-only rows

Per the #444 audit (`docs/issue-444/reports/conformance-review.md`), all
23 rows (#318, #320, #321, #324, #329, #336, #362, #363, #371, #373, #374,
#376, #377, #379, #390, #391, #392, #412, #415, #416, #419, #424, #428)
are `Prose-only` — a proposal or report merged, no code artifact that
fails on regression. The audit's own follow-up column already sorts them
into two groups by its stated recommendation text:

**Group 1 — audit says "not a runtime contract, no consumer-facing
behavior to gate"** (internal dev-process/record-keeping, i.e. how role
sessions produce records, not what a consumer's plugin install enforces):
#321, #324, #329, #336, #371, #373, #391, #392. These are candidates for
`operator-drop` (recorded reasoning + operator confirmation) — the audit
already argues no gate is warranted, but issue-464 requires the *operator*
confirm the drop, not just the audit's argument stand alone.

**Group 2 — audit says "if still required, needs a `gates/` check first,
then delivery via #441's mechanism"**: #318, #320, #362, #363, #376,
#377, #379, #390, #412, #415, #416, #419, #424 (13 rows). These are
candidates for real enforcement — `shipped-hook` or
`deployed-contract+check` — since the audit found them consumer-facing in
principle but never built.

**#374, #428 — need actual runtime code, not just a gate:**
- #374 — "needs an actual Stop-hook implementation; currently only
  proposed." Belongs in Group 2's shape but the artifact is a hook, not a
  `gates/` check first.
- #428 — "needs an actual fix in `spawn.py` plus a consumer-facing
  equivalent under `on-the-record/hooks/**`." Same shape: `spawn.py` +
  hook, not a `gates/` check.

23 rows total: 8 (group 1) + 13 (group 2) + 2 (#374/#428) = 23. Matches
the issue's count.

## Sizing implication

23 class-B rows spanning up to three disposition types, plus the class-A
orchestrator-loop wiring, is not one session's work. The proposal below
sequences delivery into follow-up issues per group rather than doing all
25+ rows' code in this session — consistent with issue-464's own
"issue-sizing 준수" instruction.
