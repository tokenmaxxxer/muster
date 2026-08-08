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
| `closure_sweep.py` | contract (single-PR case) / **out of scope — operator decision, 2026-08-07** (board-wide case) | single-PR closing-keyword act folds into `contract-guard.sh`; board-wide drift detection over already-merged PRs is a retrospective scan the operator ruled out of scope for issue #441 |
| `landing_readiness.py` | contract, CI-supplement | advisory scope-overlap/checks judgment; not folded into `contract-guard.sh` in this delivery, remains CI-only where installed |
| `spawn_coverage.py` | **out of scope — operator decision, 2026-08-07** | "an issue was filed but no session ever started" is an absence-over-time signal, structurally identical to `closure_sweep.py` board-wide; ruled out of scope by the same decision |

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
| #369 | `gates/ci.py` | the gate workflow always checks out `main`; the consumer-facing single-PR portion of this concern is already folded into `contract-guard.sh` per `docs/specs/enforcement-boundary.md`'s `closure_sweep.py` row — the remaining board-wide drift detection is out of scope per the operator's 2026-08-07 decision recorded there. |
| #383 | `gates/closure_sweep.py` | `has_record_evidence` needs the closing PR's merged record, i.e. GitHub PR/issue state beyond one local session's tree. |
| #388 | `gates/ci.py` | `gh api` POST-vs-GET distinction for "no record" vs "API blocked" needs a live `gh` call whose failure mode a static hook cannot reproduce faithfully; the read-only lookups this needs are already covered where reachable by `contract-guard.sh`. |
| #325 | `gates/spawn_coverage.py` | "an issue was filed but no session ever started" is a board-wide absence-over-time signal — structurally the same as `closure_sweep.py`'s board-wide case, ruled out of scope by the same 2026-08-07 operator decision (`docs/specs/enforcement-boundary.md`). |
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
