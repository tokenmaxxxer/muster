---
status: proposed
files:
  - docs/issue-457/proposals/2026-08-08-gate-porting-order.md
  - docs/issue-457/reports/architecture/survey.md
---

## Request
Issue #457 phase 1 asks for the porting order and grouping of the 16 repo-local
`gates/*.py` checks named in the #444 audit's category-2 list, into the shipped
`on-the-record/hooks/**` surface (PreToolUse/Stop), per the operator's hook-first
direction. Each row must end as either ported or justified — no silent gap.

## Constraints
- Target shape fixed by the operator: hooks ride PreToolUse/Stop, not a new gate
  runner.
- #457 is a programme index; deliveries split into follow-up issues per group
  (issue-sizing rule already stated in the issue body).
- Acceptance requires a parity-manifest test (`gates/test_boundary.py`) asserting
  each of the 16 numbers resolves to either a hook enforcement entry or a
  justification row in the #452 unenforced-clause artifact.
- Local-session hooks cannot reach GitHub API state (PR statusCheckRollup,
  board-wide activity) that some checks currently depend on — see survey.

## What will be done
Propose 5 groups, in porting order. Each group becomes one follow-up issue.

**Group A — record-claim integrity (port first; smallest, most local, and every
later record-writing hook composes with it)**
Rows: #310, #331, #333, #332(session-side mirror of the already-landed
write-time check).
Shape: all four inspect text written into `docs/issue-<n>/reports/**` /
`work/**` at write time — unverifiable-reason, numeric-claim-derivation, "N of M"
derivation, claim-evidence-at-write-time. One PreToolUse hook keyed on
Write/Edit under those paths, four independent check functions inside it.

**Group B — invalidation-reach / reference integrity**
Rows: #330.
Shape: local diff + doc-body check ("what does this change invalidate or reach
beyond its own acceptance criteria" + orphaned-reference detection). Pairs
naturally with Group A's PreToolUse hook (same trigger surface, second hook
module) but kept a separate issue since it is a distinct check family, not a
record-claim check.

**Group C — session-local test/build hygiene**
Rows: #334, #435.
Shape: #334 (skip-vs-pass) needs pytest `-ra` output; #435 needs gates.py's own
stub/full-suite integrity, whose hook-surface analogue is "did this hook module
actually get exercised, not stubbed." Both are Stop-hook shaped (checked once,
at session end / before a done-claim), not PreToolUse. Ported together because
they share the Stop-hook trigger point even though their subject matter differs.

**Group D — closes-gate / PR-closure family (justify, not port — flag for
implementation to confirm)**
Rows: #312, #369, #383, #388, #325, #407.
Shape: all six need `gh pr view` / board-wide GitHub state that a single local
session does not have. A PreToolUse/Stop hook inside one role's session
structurally cannot compute PR statusCheckRollup or "did any session touch this
issue." Recommend justification rows citing this reachability gap, UNLESS
implementation finds a local-state subset worth mirroring (e.g., a Stop-hook
warning when a session's own commits lack the evidence shape ci.py demands,
short of the full API-backed decision) — that subset call is implementation's,
not architecture's; this group is sequenced last among the "port" candidates so
that decision is made after A–C establish the hook-authoring pattern.

**Group E — non-blocking / out-of-scope-by-design (justify)**
Rows: #319 (risk_report — explicitly non-blocking, approval-fatigue tool, not a
gate; nothing to enforce), #322 (ledger/decisions.py — mines role-record
history for candidate rules the operator confirms; not a blocking check, a
suggestion pipeline).
These two are not gates in the block-or-pass sense at all; justification rows,
not follow-up issues.

**Sequencing dependency to flag, not to solve here**: #396 (consumer-reach
boundary) is itself one of the 16 rows and has no code anywhere yet
(`status: proposed`, no `gates/consumer_boundary.py`). It is the row that would
define what "consumer install" contains in the first place. Recommend it lands
before or alongside Group A, since the parity-manifest test this issue's
acceptance criteria requires is itself a consumer-boundary artifact. Hand-off:
this is a scope/sequencing flag for the operator and implementation, not an
architecture-boundary decision this role is deciding.

## Out of scope
- Writing the hooks themselves, the parity-manifest test, or the justification
  rows — phase-2/implementation.
- Deciding Group D's local-subset question — flagged for implementation to
  confirm against the operator, not decided here.
- #396's own design — belongs to whichever role opens that follow-up.

## How you will know it worked
Five follow-up issues opened (or the operator confirms a different split),
each carrying its group's row list and target hook file; `gates/test_boundary.py`
parity-manifest test (once written in phase 2 / #452) resolves all 16 numbers
with no silent gap.

## What did not work
(none yet — phase-1 planning only)
