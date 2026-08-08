# Survey: class-A orchestrator-loop wiring (issue-464 step 2, implementation)

## Scope

ADR `docs/issue-464/decisions/2026-08-08-board-state-into-orchestrator-loop.md`
follow-up item 1: wire `gates/closure_sweep.classify()` and
`gates/spawn_coverage.find_uncovered()` into a `spawn.py:roster_watchdog()`
tick call; rewrite the #369/#383/#325 rows in
`on-the-record/UNENFORCED-CLAUSES.md` and `docs/specs/enforcement-boundary.md`
from "out of scope" to the new mechanism citation; tighten
`gates/test_boundary.py`'s `t_gate_porting_rows_are_ported_or_justified` per
the hunt finding recorded in the ADR's proposal. Class-B rows (#444 audit,
23 rows) are explicitly out of this session's scope per the operator's
step-2 instruction — separate follow-up issues.

## Scouting

Skipped: pure bugfix/wiring-shaped work inside this repo's own governance
tooling, no externally-comparable product surface — same reasoning the
architecture-role proposal already recorded for this issue.

## Current state

### `spawn.py:roster_watchdog()` (spawn.py:1634-1670)

- Runs once per orchestrator tick (10-15 min cadence, issue #90), scans the
  live roster, calls `watchdog_check_one()` per entry, prints anomalies,
  returns `anomaly_count` (issue #327) which `spawn.py watchdog` CLI
  (spawn.py:2445 area) turns into the process exit code.
- observe-only by contract: never fixes or kills anything (docstring,
  spawn.py:1636-1637).
- `_roster_load()` returning empty prints "돌고 있는 역할 세션 없음" and
  returns 0 immediately — a board-wide sweep must not depend on this early
  return, since closure/coverage checks are meaningful even with zero live
  sessions.
- No existing call into `gates/closure_sweep.py` or `gates/spawn_coverage.py`
  anywhere in `spawn.py`.

### `gates/closure_sweep.py`

- `classify(issue_state, pr_state, pr_body, issue, has_record_evidence=False) -> str | None`
  is a pure function (closure_sweep.py:38) — no network, easy to call from
  `roster_watchdog`.
- `find_violations(root, subjects=None, issue_states=None) -> (violations, skips)`
  (closure_sweep.py:83) does the actual `gh`-backed board sweep: reads
  `spawn.board(root)`, resolves each subject's issue state and PR
  state/body via `gh`, classifies, returns violations plus a `skips` list
  for subjects the `gh` calls could not resolve. This is the function
  `roster_watchdog` should call, not `classify` directly — `classify` is
  the unit the CLI's `main()` already builds on top of.
- CLI `main()` (closure_sweep.py:~180) exits 0 (no violations), 1
  (violations), or 2 (skips present — "확인 불가", distinct from "no
  violations").

### `gates/spawn_coverage.py`

- `find_uncovered(open_issues, board, now, grace_hours=3.0) -> list[int]`
  (spawn_coverage.py:26) is pure (no network) given `open_issues` and
  `board`.
- `_list_open_issues(root)` does the `gh issue list` call; `main()` wires
  `_list_open_issues` + `spawn.board(root)` + `find_uncovered` together and
  returns 1 on `gh` failure (explicit non-zero — comment in spawn_coverage.py
  notes this is itself the defect class the gate exists to avoid
  reproducing).

### `on-the-record/UNENFORCED-CLAUSES.md` rows to rewrite

- Line 48 (#369): cites `gates/ci.py`, says board-wide drift detection "out
  of scope per the operator's 2026-08-07 decision."
- Line 49 (#383): cites `gates/closure_sweep.py`, says `has_record_evidence`
  needs GitHub state "beyond one local session's tree" (no explicit
  out-of-scope phrase, but same reasoning family).
- Line 51 (#325): cites `gates/spawn_coverage.py`, explicit
  "out of scope by the same 2026-08-07 operator decision."
- All three need rewriting to cite the new `roster_watchdog` mechanism
  instead — this is also what makes the ADR's reversal real rather than
  documented-only.

### `docs/specs/enforcement-boundary.md` rows to rewrite

- Line 40 (`closure_sweep.py`): board-wide case marked
  "out of scope — operator decision, 2026-08-07."
- Line 43 (`spawn_coverage.py`): same marking, full row.
- Line 78 (`closure-sweep.yml`): board-wide case described as "existing
  `out of scope` drop, runnable locally as `python3 gates/closure_sweep.py`"
  — needs updating to describe the new orchestrator-tick call site instead
  of "runnable locally."
- Lines 25-26, 91, 104: general prose describing the 2026-08-07 ruling —
  these describe the ruling's *existence*, not the specific rows; the ADR's
  own text is that the reversal is narrow (#369/#383/#325 only, not
  #312/#388/#407), so this general prose stays but should gain a pointer to
  the ADR for the narrowed rows rather than being rewritten wholesale.

### `gates/test_boundary.py` mechanism-citation check (hunt finding)

- `t_gate_porting_rows_are_ported_or_justified` (test_boundary.py:146-166)
  checks only that `#{n}` appears as a `| #n |` table-row tag somewhere in
  `UNENFORCED-CLAUSES.md` (line 159: `re.search(rf"\|\s*{tag}\s*\|", ...)`).
  It does not inspect the row's verdict text at all — a placeholder or
  garbled row passes identically to a real mechanism citation. `#369,
  #383, #325` are all in `GATE_PORTING_ISSUES` (test_boundary.py:138-141),
  so this check already runs against the rows this session rewrites.
- Fix shape: after locating the row, assert its text matches one of a
  named vocabulary (`out of scope — operator decision`, a mechanism
  citation naming `roster_watchdog`, or another `UNENFORCED-CLAUSES.md`
  disposition keyword already in use) rather than accepting any non-empty
  row.

### Test coverage

- `test_spawn.py` exists at repo root (not `test/test_spawn.py` — the
  issue's acceptance text says `test/test_spawn.py` but the actual file
  lives at repo root, matching `gates/test_boundary.py`'s own
  `test_boundary_workflow_migration.py` sibling-file pattern and the
  general convention in this repo of gate/module tests living next to
  `spawn.py`). No existing test calls `roster_watchdog` with fixtures for
  closure/coverage violations — new tests are additive.

## Write set for phase 2

- `spawn.py` — add closure/coverage sweep call inside `roster_watchdog()`.
- `test_spawn.py` — tests for the new wiring (mock `find_violations`/
  `find_uncovered` to avoid real `gh` calls, matching `closure_sweep.py`'s
  own test patterns).
- `on-the-record/UNENFORCED-CLAUSES.md` — rewrite #369/#383/#325 rows.
- `docs/specs/enforcement-boundary.md` — rewrite `closure_sweep.py`/
  `spawn_coverage.py` board-wide-case rows and the `closure-sweep.yml` row.
- `gates/test_boundary.py` — tighten
  `t_gate_porting_rows_are_ported_or_justified` to check verdict text.
- `docs/issue-464/reports/implementation.md` — phase-2 record (written only
  after Approve, per contract v3 s19).

## Alternatives considered (feeds proposal Rationale)

- Call `closure_sweep.classify()` directly from `roster_watchdog` instead of
  `find_violations()`. Rejected: `classify` needs per-subject issue/PR
  state already resolved; `roster_watchdog` would have to reimplement
  `find_violations`'s `spawn.board()` walk and `gh` calls to feed it,
  duplicating logic `find_violations` already owns.
- Make the sweep call unconditional on every tick regardless of roster
  state. Considered: `roster_watchdog`'s early return on an empty roster
  (spawn.py:1652-1654, "돌고 있는 역할 세션 없음") would otherwise skip the
  board-wide sweep on a tick with zero live sessions, which is exactly a
  time a stale board is most likely to go unnoticed — the phase-2
  implementation should call the sweep before that early return, not after.
