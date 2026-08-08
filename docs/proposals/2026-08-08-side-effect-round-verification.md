---
status: landed
files:
  - docs/issue-497/reports/defect-verification.md
  - test/test_side_effect_round.py
---

## Intent

Verify, as a defect-verification pass, that today's ~25 on-the-record
merges do not interact badly as a set — independently attempting to
reproduce interaction defects across four named hunt areas, not
re-litigating any single PR's own review.

## Constraints

- Subject is issue #497; this role never files or fixes, only attempts
  reproduction and records outcomes (reproduced / not-reproduced /
  blocked: needs-repro-access).
- Every attempt below names its source verbatim (issue #497's own hunt-area
  text — there is no separate coding/qa/review record for issue #497
  itself, since #497 is a cross-cutting verification issue over other
  issues' already-closed work, not a built feature with its own pipeline).
- `code_under_review:` is the current tip of `main`, `5df67a4` (Merge PR
  #496), since #497's scope is the merged state of all listed PRs.
- Repro work (`test/test_side_effect_round.py`) is phase-2 only, gated on
  human approval per contract v3 s19; this proposal and the survey below
  are the only phase-1 writes.

## Current-state survey (what's actually wired, per area)

**Hook interactions** — `on-the-record/hooks/hooks.json` wires `PreToolUse`
for `Bash` as an ordered array: `contract-guard.sh` →
`pr-preflight.sh` → `spec-index-preflight.sh`, and separately for
`Write|Edit|MultiEdit` as `deliverable-guard.sh` then
`record-claim-guard.sh`. `Stop` runs `stop-gate.sh` →
`role-test-claim-guard.sh` → `decision-queue-stopgate.sh` →
`report-framing-check.sh`. Each hook was verified individually
(`docs/reports/2026-08-08-hunt-contract-guard-target-repo-resolution.md`,
`docs/reports/2026-08-08-hunt-issue-459-pr-and-spec-index-preflight-hooks.md`,
`docs/reports/2026-08-08-hunt-decision-queue-stophook-and-respawn-branch-fix.md`)
but never as a chain — no record traces one Bash call through all three
PreToolUse hooks together, or one Stop event through all four Stop hooks
together.

**Consumer-install smoke** — issue #444's
`docs/issue-444/proposals/2026-08-08-consumer-install-portability-audit.md`
and `docs/issue-444/reports/conformance-review.md` cover portability of
individual paths/gates in a consumer install, but predate #457's
claim-guards, #459's preflights, and #464/#466/#492's supervision wiring —
none of those newer hooks have been exercised from a fresh consumer clone.

**Retired-Actions edge** — `.github/workflows/` is confirmed absent from
this working tree; `gates/test_boundary_workflow_migration.py` (issue
#460) asserts the directory is absent/empty and checks deleted-workflow
migration mapping. `gates/acceptance_gate.py:22,52,65` and
`gates/gates.py:1125` still reference `.github/workflows/` in
strings/regexes — need to check whether any of those are now-dead
references to a retired mechanism (a leftover that could confuse an
operator reading gate output) rather than live enforcement.

**Supervision interplay** — `on-the-record/hooks/decision-queue-stopgate.sh`
(#466), `docs/issue-492/proposals/2026-08-08-implement-reconciliation-step.md`
and `docs/issue-492/decisions/2026-08-08-reconciliation-step-for-supervision.md`
(reconciliation), and watchdog work under `docs/issue-327/` and
`docs/issue-90/proposals/coding-watchdog.md` are each individually
covered, but no record exercises auto-arm + reconcile + watchdog firing
on the same tick together.

## What will be done (attempt list)

Each attempt names its source verbatim — issue #497's hunt-area text —
plus which current-state survey findings above it re-derives from (cite)
vs. exercises fresh (skip citing, since no PR-level record covers the
combination).

1. **[hook-interaction] PreToolUse Bash chain, same call.** Source:
   issue #497 — "multiple PreToolUse hooks (preflights, claim guards,
   contract-guard) firing on the same tool call — ordering, double-deny,
   one hook's output confusing another." Re-derives ordering from
   `hooks.json` (cited above, not re-read); fresh: drive one Bash tool
   call through `contract-guard.sh` → `pr-preflight.sh` →
   `spec-index-preflight.sh` in sequence and check for a case where one
   hook's exit/stderr causes the next to double-deny or misreport.
2. **[hook-interaction] PreToolUse Write/Edit chain, same call.** Source:
   issue #497, same hunt-area text, applied to the
   `deliverable-guard.sh` → `record-claim-guard.sh` pair on
   `Write|Edit|MultiEdit`. Fresh exercise.
3. **[hook-interaction] Stop hook chain, same event.** Source: issue
   #497, same hunt-area text, applied to `stop-gate.sh` →
   `role-test-claim-guard.sh` → `decision-queue-stopgate.sh` →
   `report-framing-check.sh`. Fresh exercise — no record traces all four
   together.
4. **[consumer-install] Fresh-clone minimal lifecycle.** Source: issue
   #497 — "fresh clone as a consumer project, run a minimal session
   lifecycle (spawn → record write → commit → pr-create shapes) and
   confirm each new hook fires or stays silent correctly." Re-derives
   older-path portability from #444's conformance-review (cited, not
   re-run); fresh: exercise spawn/record-write/commit/pr-create against
   #457's claim-guards, #459's preflights, and #464/#466/#492's
   supervision hooks specifically, since #444 predates them.
5. **[retired-actions] No live reference to `.github/workflows/`
   checks.** Source: issue #497 — "nothing still references workflow
   checks." Re-derives directory-absence from
   `gates/test_boundary_workflow_migration.py` (cited, already green in
   CI); fresh: check whether the `.github/workflows/` string references
   in `gates/acceptance_gate.py` and `gates/gates.py:1125` are dead
   references that could still fire against a hypothetical
   `.github/workflows/` path if one reappeared, or are correctly inert.
6. **[supervision] auto-arm + reconcile + watchdog, same tick.** Source:
   issue #497 — "auto-arm + reconcile + watchdog on the same tick — no
   duplicate respawns, no event storms." Re-derives each component's own
   correctness from #327/#466/#492's individual records (cited, not
   re-derived); fresh: drive a scenario where all three could fire in
   the same tick and check for duplicate respawn or event-storm
   behavior.

## Out of scope

- Fixing anything found — findings are filed `addressed_to: coding`.
- Re-litigating any individual PR's own review verdict.
- Any hunt area not named in issue #497's text.

## How you'll know it worked

`docs/issue-497/reports/defect-verification.md` (phase-2, post-approval)
has one exercised row per attempt above — either `reproduced` with a
finding block and evidence pointer, or `not-reproduced`/`blocked`
recorded plainly — and all four hunt areas are represented with no area
left as a silent omission. `test/test_side_effect_round.py` contains a
runnable repro for any `reproduced` outcome. `python3 -m pytest -q` is
green at the end.
