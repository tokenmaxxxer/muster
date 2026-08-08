# Unenforced contract clauses

Derived, gate-checked extract of `docs/specs/enforcement-boundary.md`'s
rows whose verdict is `contract, CI-supplement` or an `out of scope —
operator decision` variant — i.e. contract-bound clauses this plugin's
zero-install baseline (plugin hooks + `spawn.py`) does not mechanically
reach for a consumer project. Kept in sync by `gates/test_boundary.py`;
do not hand-edit the table below without updating the spec first.

A Claude Code session's `gh pr merge`/`git push` and opening a phase-2
session are reached with zero installation. What follows is not.

| mechanism | verdict | reason |
|---|---|---|
| `landing_readiness.py` | contract, CI-supplement | advisory scope-overlap/checks judgment; not folded into `contract-guard.sh` in this delivery, remains CI-only where installed |
| `claim_scan.py` | contract, CI-supplement | new (issue #476 H1): scans a record/PR body for claim-language ("reproduced"/"verified"/…) with no adjacent runnable evidence or no traceable target — CLI wrapper reads `gh pr diff`; not yet a `PreToolUse` hook, CI-only where installed |
| `reexecution_gate.py` | contract, CI-supplement | new (issue #476 H1): SHA-pinned worktree re-execution of a claim-adjacent command, gate-owned verdict written to `.reexecution/<issue>-<role>.json`, never role-writable; feeds `landing_readiness.reexecution_blocking_cause()`, folded into `landing_readiness.py`'s existing CI-supplement path — same boundary, no new install surface |
| `open_work.py` | contract, CI-supplement | query-construction only (#379); the actual open-issue/open-PR lookup runs manually per `run.md`'s instruction, not via a blocking hook in this delivery |

<!-- gate-porting-additions (issue #457) — the table above is the #452
     spec-verdict extract `gates/test_boundary.py` matches exactly against
     `docs/specs/enforcement-boundary.md`; everything below is issue #457's
     separate category-2 gate-porting justification list, scanned by a
     different check (`t_gate_porting_rows_are_ported_or_justified`), not
     the exact-match one. -->

## Gate porting (issue #457, #444 category-2 audit)

Every row of the #444 audit's category-2 list (16 `gates/*.py` checks with
no consumer-facing enforcement) ends up here as a justification, or has a
matching enforcement entry under `on-the-record/hooks/**` instead — see
`docs/issue-457/proposals/2026-08-08-gate-porting-order.md` for the full
porting-order rationale this list implements.

Ported (NOT listed as unenforced — see `on-the-record/hooks/**`):
`#310`, `#330`, `#331`, `#332`, `#333` (`record-claim-guard.sh`); `#334`,
`#435` (`role-test-claim-guard.sh`).

### Justified — GitHub-board state unreachable from a local session

A `PreToolUse`/`Stop` hook runs inside one session with no board-wide
GitHub API access; these checks need `gh pr view`/`statusCheckRollup` or
"did any session touch this issue" board state a local hook structurally
cannot compute.

| issue | source | reason |
|---|---|---|
| #312 | `gates/ci.py` | phase-is-an-issue-property + `APPROVE issue-<n>/<role>` comment resolution needs GitHub issue-comment history, not local diff state. |
| #369 | `gates/ci.py` | the consumer-facing single-PR portion is folded into `contract-guard.sh`; the board-wide drift-detection portion is now covered by `spawn.py:roster_watchdog()`'s per-tick `closure_sweep.find_violations()` call, running in the orchestrator (issue #464). |
| #383 | `gates/closure_sweep.py` | board-wide case now covered: `spawn.py:roster_watchdog()` calls `closure_sweep.find_violations()` each tick, reusing its `has_record_evidence`-aware classification and its `gh`-failure `skips` reporting (issue #464). |
| #388 | `gates/ci.py` | `gh api` POST-vs-GET distinction for "no record" vs "API blocked" needs a live `gh` call whose failure mode a static hook cannot reproduce faithfully; the read-only lookups this needs are already covered where reachable by `contract-guard.sh`. |
| #325 | `gates/spawn_coverage.py` | board-wide case now covered: `spawn.py:roster_watchdog()` calls `spawn_coverage.find_uncovered()` each tick, including on an empty live roster, reporting `gh`-list failures rather than treating them as clean (issue #464). |
| #407 | `gates/landing_readiness.py` | advisory scope-overlap/checks judgment already recorded as `contract, CI-supplement` in `docs/specs/enforcement-boundary.md` — not folded into a session-side hook in this delivery. |

### Justified — non-blocking by design, not a gate

| issue | source | reason |
|---|---|---|
| #319 | `gates/risk_report.py` | non-blocking approval-fatigue classifier feeding `gates.py`'s review surface; already recorded `n/a (infrastructure)` in `docs/specs/enforcement-boundary.md` — nothing to enforce. |
| #322 | `ledger/decisions.py` | mines role-record history for candidate rules the operator confirms by hand; a suggestion pipeline, not a blocking check. |

### Deferred — no implementation exists to port

| issue | source | reason |
|---|---|---|
| #396 | (none — `gates/consumer_boundary.py` does not exist) | `status: proposed`, no code anywhere in the repo. There is nothing to port; the architecture proposal flags this as a sequencing dependency for whichever role opens #396's own follow-up, not an architecture-boundary decision made here. |
