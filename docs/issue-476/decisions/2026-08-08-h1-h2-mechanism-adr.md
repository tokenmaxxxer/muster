# ADR — issue #476: mechanized re-execution (H1) and refusal parity (H2)

Approved 2026-08-08 (`APPROVE issue-476/architecture`, issue comment) on top of
`docs/issue-476/proposals/architecture.md`. This is the canonical decision record;
the proposal document is its phase-1 draft.

## Context

`docs/issue-476/proposals/discovery.md` pre-registered H1 (primary) and H2
(secondary) with metrics, thresholds, and two named failure signatures for H1:
the re-run environment must be gate/hook-provisioned (never the audited
session), and the trigger must fire on claim-language pattern match (never a
self-reported opt-in field). The current-state survey
(`docs/issue-476/reports/architecture/survey.md`) found: no gate in this repo
executes anything today — every existing check (`acceptance_gate.py`,
`test_boundary.py`, ...) is a text/structure check over a record file,
aggregated by `gates/landing_readiness.py` before merge. H2's target pattern
(a closed vocabulary a field must be drawn from) already exists twice (`ROLES`
tuple, `run.md` `loop_state` stages) and needs only extension.

## Decision

### H1 — new required gate, `gates/reexecution_gate.py`

1. **Trigger — claim-language pattern match, not an opt-in field.**
   `gates/claim_scan.py` regex-matches claim vocabulary (`reproduced`,
   `verified`, `passed`, `confirmed`, `tests? pass`, `repro(duces)?` —
   case-insensitive, word-boundary) in each role record body staged in the PR
   diff. A claim-language hit with no adjacent machine-runnable command (a
   fenced code block or an explicit `Repro:`/`Verify:` line within N lines) is
   a hard fail on its own.
2. **Command-to-target traceability (closes the after-proposal hunt finding).**
   A cited command is accepted only if it names an identifiable target already
   present in the diff or repo (a test file path, function name, or module the
   claim's surrounding text also names). A command with no such target (a bare
   literal like `true`, `echo ok`, or anything untraceable to a concrete
   artifact) is a hard fail at `claim_scan.py` time, before execution — closes
   the vacuous-always-succeeding-command bypass the after-proposal warrant
   hunt found (`docs/reports/2026-08-08-hunt-architecture.md`).
3. **Provisioning — gate-owned, not session-owned.** Runs inside
   `gates/landing_readiness.py`'s aggregation (CI/merge-readiness, a process
   the audited role session has no write access to), in a fresh git worktree
   pinned to the PR's head commit SHA as reported by the triggering CI/PR
   event — never by re-reading the branch ref at execution time. SHA pinning
   closes a force-push race between trigger and re-run.
4. **Execution and ground truth.** Runs the cited command in the pinned
   worktree with a timeout; ground truth is the subprocess's own exit code
   (plus a diff against expected output where the record cites one) — never a
   re-read of the record's prose.
5. **Verdict storage — gate-owned artifact, session-unwritable.** The gate
   itself writes `.reexecution/<issue>-<role>.json` (exit code, command run,
   timestamp, worktree SHA) as part of the gate run — never a file the role
   session's own commits stage.
6. **Merge gating.** `landing_readiness.py` treats a `reexecution_gate`
   `fail` verdict identically to any other required-gate failure it already
   aggregates — no new merge ceremony.

### H2 — extend the existing closed vocabularies, no new gate shape

Add `refused` / `not-needed` / `cannot-verify` as valid `loop_state` values in
the closed enum `run.md` already defines, and extend `acceptance_gate.py`'s
field-presence check to require the same fields for a refusal-shaped record as
a positive one (a `reason:` field replacing the outcome-specific fields,
checked at the same strictness) — same pass/fail weight at
`landing_readiness.py`, no separate refusal gate.

## Gaming-resistance argument and failure signature, per mechanism

- **H1 trigger.** Gaming requires avoiding claim vocabulary entirely (forfeits
  the credit claimed) or finding synonyms outside the regex. Failure
  signature: a claim made in a form the regex misses — living risk, not
  eliminated; the vocabulary is expected to need iteration.
- **H1 provisioning + verdict storage.** The verdict-producing process shares
  no state or authorship with the audited session: it runs after the session
  exits, against a SHA-pinned commit the session cannot retroactively change,
  writing a verdict file the session never has write access to. Gaming it
  requires making the actually-committed code pass the actually-cited
  command — the honest-work path, not a cheaper one. Failure signature: a
  CI/hook environment that cannot create git worktrees and silently skips the
  gate instead of failing closed (see Consequences).
- **H2 vocabulary extension.** Gaming risk is symmetric abuse (claiming
  refusal to dodge real work), not asymmetric — countered by the
  pre-registered `refusal_rate ≤ 40%` guardrail (discovery doc), measured in
  step 4 (execution-observation), not architecturally preventable at design
  time. Failure signature: refusal rate exceeds the guardrail with no
  corresponding drop in fabricated-verification incidents, meaning refusal
  became the new cheap performance.

## Consequences

- New runtime capability enters the gate suite: subprocess execution in an
  isolated checkout. This is new surface area (execution risk,
  timeout/resource handling) the existing text-only gates did not carry — the
  implementation role must scope command execution (timeout, network access
  policy inside the worktree, resource limits) as part of building
  `reexecution_gate.py`.
- `landing_readiness.py` gains a dependency on git worktree creation being
  available in whatever CI/hook environment runs the gate suite. If a
  consumer's environment cannot create worktrees, `reexecution_gate.py` must
  fail closed (block merge), not silently skip — otherwise H1's own
  gaming-resistance argument breaks. This repo's established habit is
  fail-loud on malformed state, not silent skip (survey finding).
- H2 adds no new runtime dependency, only enum/field-check extension —
  lowest-risk half of this decision, matches discovery's RICE Effort=1 score.
- Per the operator's iterative-decision-rule addition (issue #476 comment,
  2026-08-08): step 4's observation record measures the pre-registered metric
  against threshold and triggers either close (effect shown) or a new
  discovery round (effect absent) — this ADR's mechanisms are not
  declared done on delivery.

## Alternatives considered (rejected)

1. **LLM-based verifier subagent reads the record and judges it.** Rejected —
   still self-report shaped from the ground-truth side; an LLM judgment adds
   another self-report layer rather than removing incentive dependence.
2. **Standalone external CI service outside the plugin.** Rejected on the
   issue's explicit constraint: must ship on the deployed plugin surface
   (hooks/`spawn.py`/`gates/`/`run.md`), zero-install for consumers
   (#441/#460 line).
3. **Session runs its own re-check before submitting the record.** Rejected —
   this is exactly the named failure signature (the audited session
   provisions its own verification), which discovery's failure-signature line
   rules out.
4. **A new dedicated `refusal_gate.py` for H2, separate from
   `acceptance_gate.py`.** Rejected in favor of extending the existing closed
   vocabulary and gate — a new gate shape for H2 would itself be "a new gate
   that can be satisfied by performance," whereas extending an
   already-checked enum reuses a check the repo already runs at equal
   strictness.

## Deployment-surface constraint carried forward to implementation

`reexecution_gate.py` and `claim_scan.py` land under `gates/`; the
`loop_state`/`ROLES`-style vocabulary extension lands in `run.md` and whatever
`spawn.py` code reads those enums today — no new out-of-band service. Exact
function signatures, timeout values, and the full claim-vocabulary regex are
implementation-phase (step 3) decisions this ADR does not fix.

## Hand-off

Interface shape detail (exact `claim_scan.py` regex, `reexecution_gate.py`
function signatures, `.reexecution/<issue>-<role>.json` schema) → step 3
implementation. Timeout/resource-limit values for subprocess execution inside
the worktree, if they become a performance budget question → performance
engineering; not decided here.
