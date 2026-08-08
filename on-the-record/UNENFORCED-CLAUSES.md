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
