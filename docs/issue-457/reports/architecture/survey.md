# issue-457 phase-1 survey — 16 category-2 rows vs. shipped hook surface

## Scout: skipped
Skip condition: no design decision benefits from an external product exemplar. The
target shape is fixed by the operator's hook-first direction (PreToolUse/Stop under
`on-the-record/hooks/**`); the only open decision — porting order/grouping — is
answered from this repo's own coupling structure, not from a competitive field.

## Current state
Shipped hook surface (`on-the-record/hooks/`): `stop-gate.sh`, `contract-guard.sh`,
`deliverable-guard.sh`, `directive.sh`, `self-update.sh`, `hooks.json`. Two of the 16
rows already ride this surface per #444 (excluded here): #411, #441.

Row → current implementation (all CI-only, `gates/*.py` or `ledger/`):

| # | file | shape | GitHub-API dependent? |
|---|---|---|---|
| 310 | acceptance_gate.py | local text check (record body) | no |
| 312 | ci.py (closes-gate) | PR-closing decision | yes (`gh pr view`) |
| 319 | risk_report.py | non-blocking batch classifier | yes |
| 322 | ledger/decisions.py | mines role records for candidate rules | no (reads local git-durable text) |
| 325 | spawn_coverage.py | board-wide "issue got zero board activity" sweep | yes |
| 330 | gates.py + test_orphaned_references.py | invalidation-reach / orphaned-reference check | no |
| 331 | gates.py (checked-claims) | numeric-claim-derivation check on record body | no |
| 332 | gates.py + ci.py (landed, #332) | claim-evidence-at-write-time | no |
| 333 | gates.py (record_derived_counts) | "N of M" claim-derivation check on record body | no |
| 334 | skip_gate.py | wraps `pytest -ra` output, distinguishes skip from pass | no, but needs pytest output |
| 369 | ci.py | closes-gate discharge distinction | yes |
| 383 | closure_sweep.py | board-wide record-evidence sweep | yes |
| 388 | ci.py | closes-gate: "no record" vs "API blocked" | yes |
| 396 | (unimplemented — proposal still `status: proposed`, no `gates/consumer_boundary.py` on any branch) | would define what ships to consumers at all | n/a |
| 407 | landing_readiness.py | per-PR merge-readiness, GitHub checks+approvals+records | yes |
| 435 | gates.py/ci.py stub-detection + full-suite default | meta-check on gates.py's own integrity | no |

Notable: #396 (consumer-reach boundary) is itself one of the 16 rows, and it is the
row that would define *what* "consumer install" even contains. It has no code yet.
Treating it as an ordinary row risks building the other 15 against an undefined
boundary. Flagged as a sequencing dependency below, not absorbed into this role's
scope beyond that flag (implementation is phase-2/other-role territory).

## Coupling read
Rows split into two shapes:
- **Local-file-scoped** (session already holds everything needed: touched files,
  record text, git state) — 310, 322, 330, 331, 332(already landed, needs session-side
  mirror), 333, 334, 435. These can ride PreToolUse/Stop directly.
- **GitHub-API-scoped** (need `gh pr view`/board state no local session has) — 312,
  319, 325, 369, 383, 388, 407. A PreToolUse/Stop hook running inside one role's
  session cannot see PR statusCheckRollup or board-wide activity; these need either
  a justification row (b) or a differently-shaped enforcement point (orchestrator/CI
  step, not a session hook) — that shape call belongs to implementation, not this
  survey.

#319 (risk_report) is explicitly non-blocking (approval-fatigue tool, not a gate) —
strong justification-row candidate on its face, not a porting candidate.
