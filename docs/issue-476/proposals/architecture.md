---
status: proposed
files:
  - docs/issue-476/reports/architecture/survey.md
  - docs/issue-476/reports/architecture/scout-brief.md
  - docs/issue-476/proposals/architecture.md
---

# Proposal — issue #476: architecture for H1 (mechanized re-execution) and H2 (refusal parity)

Phase 1 only (contract v3 s19). Design only — no `gates/` or `spawn.py` code changes in this PR.
This document is the ADR for the mechanism; consequences and alternatives are stated inline per
the required record fields (context/decision/consequences/alternatives-considered).

## Context

`docs/issue-476/proposals/discovery.md` pre-registered H1 (primary) and H2 (secondary) with
metrics, thresholds, and two named failure signatures for H1: the re-run environment must be
gate/hook-provisioned (never the audited session), and the trigger must fire on claim-language
pattern match (never a self-reported opt-in field). The current-state survey
(`reports/architecture/survey.md`) confirms: no gate in this repo executes anything today — every
existing check (`acceptance_gate.py`, `test_boundary.py`, ...) is a text/structure check over a
record file, run through `gates/landing_readiness.py`'s aggregation before merge. H2's target
pattern (a closed vocabulary a field must be drawn from) already exists twice (`ROLES` tuple,
`run.md` `loop_state` stages) and needs only extension, not new machinery.

## Decision

### H1 — `reexecution_gate.py`, a new required gate under `gates/`

1. **Trigger — pattern match on claim vocabulary, not an opt-in field.** A new scanning step
   (`gates/claim_scan.py`) reads each role record body (`docs/issue-<n>/reports/<role>.md`) staged
   in the PR diff and regex-matches claim vocabulary (`reproduced`, `verified`, `passed`,
   `confirmed`, `tests? pass`, `repro(duces)?` — case-insensitive, word-boundary). This satisfies
   the discovery failure signature directly: a session cannot avoid re-execution by omitting a
   field, because the trigger is the language it uses to claim credit, not a checkbox it can leave
   unchecked. A claim-language hit with no adjacent machine-runnable command (a fenced code block
   or an explicit `Repro:`/`Verify:` line within N lines of the match) is a **hard fail on its
   own** — this closes the boilerplate-§20 loophole one level upstream of re-execution, since a
   record can no longer claim "verified" in prose with nothing to run.
2. **Provisioning — gate-owned, not session-owned.** When a claim has a citable command,
   `reexecution_gate.py` runs as part of the existing `gates/landing_readiness.py` aggregation
   (i.e. in CI/the merge-readiness check, a process the audited role session never has write
   access to — confirmed by the survey's read of `REPO_CONFIG`/hook packaging: hooks are additive
   to the session's harness, not something the session's own process controls). It creates a
   **fresh git worktree pinned to the PR's head commit SHA as reported by the triggering CI/PR
   event**, not by re-reading the branch ref at execution time — this closes a force-push race the
   discovery doc did not name but the survey's provisioning-boundary check surfaces: without SHA
   pinning, a session could force-push a different commit between trigger and re-run and the gate
   would re-execute the wrong code. Named here as an addition to the failure-signature list the
   implementation role inherits.
3. **Execution and ground truth.** Runs the cited command in the pinned worktree with a timeout;
   ground truth is the subprocess's own exit code (and, where the record cites specific expected
   output, a diff against that), never a re-read of the record's prose. The cited command is
   accepted only if it names an identifiable target already present in the diff or repo (a test
   file path, function name, or module the claim's surrounding text also names) — a command with
   no such target (a bare literal like `true`, `echo ok`, or any command not traceable to a
   concrete artifact) is a **hard fail at `claim_scan.py` time**, before execution, on the same
   footing as a claim with no adjacent command at all. Without this, exit-code-only ground truth
   is gameable by citing a vacuous always-succeeding command next to the claim — named here as a
   failure signature the after-proposal hunt surfaced (warrant-hunt, 2026-08-08): a record could
   satisfy both the trigger's "has an adjacent runnable command" check and the gate's "exit 0"
   check without exercising anything real. Command-to-target traceability closes that gap; it does
   not fully eliminate gaming a target-naming heuristic, and is itself a living risk the
   implementation role inherits (e.g. citing a real test path but running an unrelated command
   against it) — the vocabulary/heuristic will need iteration, per discovery's own ITWWS note.
4. **Verdict storage — gate-owned artifact, session-unwritable.** The gate writes
   `.reexecution/<issue>-<role>.json` (exit code, command run, timestamp, worktree SHA) itself,
   as part of the gate run, not as a file the role session edits — the verdict is never staged by
   the audited session's own commits, so it cannot be silently overwritten after the fact the way
   a self-authored record field could be.
5. **Merge gating.** `landing_readiness.py` treats a `reexecution_gate` verdict of `fail` (claim
   asserted, re-run exit nonzero) identically to any other required-gate failure it already
   aggregates — no new merge ceremony, same structural cost as the existing gate suite.

### H2 — extend the existing closed vocabularies, no new gate shape

Add `refused` / `not-needed` / `cannot-verify` as valid `loop_state` values in the same closed
enum `run.md` already defines (survey: `run.md` stage vocabulary), and extend
`acceptance_gate.py`'s field-presence check to require the *same* fields for a refusal-shaped
record as a positive one (a `reason:` field replacing the outcome-specific fields, checked for
presence exactly as strictly as today's positive-path fields) — same pass/fail weight at
`landing_readiness.py`, no separate refusal gate. This is deliberately a vocabulary extension, not
new code, per the survey's finding that this pattern is already used twice in this codebase.

## Deployed-surface / gaming-resistance argument, per mechanism

- **H1 trigger (pattern match).** Gaming this requires either avoiding the claim vocabulary
  entirely (which forfeits the credit the claim was for) or finding synonyms outside the regex —
  a living risk, not eliminated; named explicitly below as a failure signature, not hidden.
- **H1 provisioning (gate-owned worktree, SHA-pinned).** The verdict-producing process shares no
  state or authorship with the audited session: it runs after the session has exited, against a
  commit SHA the session cannot retroactively change, in a worktree the session's own tool calls
  never touched. To game it, a session would have to make the actual committed code pass the
  actual cited command — which is the honest-work path, not a cheaper one. This is the same
  incentive-independence argument discovery's scout brief cites (auditor/audited-party incentive
  separation), applied here as a *process*-separation instantiation rather than a prompt-level one.
- **H1 verdict storage (gate-owned artifact).** A session cannot inflate a re-execution verdict
  the way it can inflate prose, because it never has write access to the verdict file — the file
  is produced by the gate run itself, analogous to a CI check's own status output.
- **H2 vocabulary extension.** Gaming risk is symmetric abuse (claiming refusal to dodge real
  work), not asymmetric — countered by the pre-registered `refusal_rate ≤ 40%` guardrail
  (discovery doc), measured in step 4 (execution-observation), not architecturally preventable at
  design time. Stated here as a carried-forward, not resolved, risk.

## Consequences

- New runtime capability enters the gate suite: subprocess execution in an isolated checkout. This
  is new surface area (execution risk, timeout/resource handling) the existing text-only gates did
  not carry — the implementation role must scope command execution (timeout, no network access
  inside the worktree unless the cited command needs it, resource limits) as part of building
  `reexecution_gate.py`, not as an afterthought.
- `landing_readiness.py` gains a dependency on git worktree creation being available in whatever
  CI/hook environment runs the gate suite — a deployment-environment assumption that did not exist
  before; if a consumer's environment cannot create worktrees, `reexecution_gate.py` must fail
  closed (block merge) rather than silently skip, or H1's own gaming-resistance argument breaks
  (survey's own note: this repo's habit is fail-loud on malformed state, not silent skip).
- H2 adds no new runtime dependency, only enum/field-check extension — lowest-risk half of this
  proposal, matches its discovery-stage RICE Effort=1 score.

## Alternatives considered (rejected)

1. **LLM-based verifier subagent reads the record and judges it.** Rejected — still self-report
   shaped from the ground-truth side (an LLM's judgment, not an exit code); discovery's own
   candidate #5 (information asymmetry) was rejected on the identical incentive-independence
   argument: blinding or adding a second LLM judge does not change who benefits from a lenient
   verdict, it only adds another self-report layer.
2. **Standalone external CI service outside the plugin.** Rejected on the issue's explicit
   constraint: must ship on the deployed plugin surface (hooks/`spawn.py`/`gates/`/`run.md`),
   zero-install for consumers (#441/#460 line) — an external service fails that constraint on its
   face.
3. **Session runs its own re-check before submitting the record ("self-check before you claim").**
   Rejected — this is exactly the named failure signature (the audited session provisions its own
   verification), which discovery's failure-signature line explicitly rules out.
4. **A new dedicated `refusal_gate.py` for H2, separate from `acceptance_gate.py`.** Rejected in
   favor of extending the existing closed vocabulary and the existing gate — a new gate shape for
   H2 would itself be "a new gate that can be satisfied by performance" (the issue's own
   constraint) at the field-presence level, whereas extending an already-checked enum reuses a
   check the repo already runs at equal strictness.

## Deployment-surface constraint carried forward to implementation

`reexecution_gate.py` and `claim_scan.py` land under `gates/`; the `loop_state`/`ROLES`-style
vocabulary extension lands in `run.md` and whatever `spawn.py` code reads those enums today — no
new out-of-band service, consistent with discovery's carried-forward constraint. Exact function
signatures, timeout values, and the full claim-vocabulary regex are implementation-phase decisions
this proposal does not fix.
