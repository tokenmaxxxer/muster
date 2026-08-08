---
status: proposed
files:
  - docs/issue-476/reports/product-discovery/survey.md
  - docs/issue-476/reports/product-discovery/scout-brief.md
  - docs/issue-476/proposals/product-discovery.md
---

# Proposal — issue #476: making honest work cheaper than gate theater

Phase 1 only. This document pre-registers hypotheses, a metric, a threshold, and a decision rule
per the issue's Acceptance — it does not build a mechanism. The timestamp of this proposal's
commit is the pre-registration point; nothing below may be edited after data collection starts
(role-handoff contract's own no-moved-finish-line rule, applied here as this issue's own
constraint too).

## Candidates scored (RICE), against the JTBD in survey.md

Reach and Impact are scored 1-5 against "role sessions in this repo, per week" (≈1-3 subjects/
week per `docs/issue-*` cadence observed). Effort is in relative days. Confidence reflects
whether the mechanism's gaming-resistance argument survived the scout brief's must-be check.

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Mechanized independent re-execution (re-run the claimed repro/check in a clean checkout, compare verdicts) | 5 | 5 | 0.8 | 3 | 6.7 | **Keep — primary hypothesis** |
| 2 | Refusal-as-first-class (null/refusal result priced equal to a positive at the gate) | 5 | 4 | 0.7 | 1 | 14.0 | **Keep — secondary hypothesis** |
| 3 | Pre-registration (orchestrator states the question + what-would-change-its-mind before spawn) | 4 | 3 | 0.6 | 2 | 3.6 | Keep, but downstream of #1/#2 — see rejection notes |
| 4 | Sampling audit (random fraction independently re-verified, consequence recorded) | 3 | 4 | 0.6 | 2 | 3.6 | Keep as #1's scaling strategy, not a separate mechanism |
| 5 | Information asymmetry (verifier sees only the artifact, never builder's record/intent) | 3 | 3 | 0.4 | 3 | 1.2 | **Reject** |
| 6 | Spawn-necessity checks (falsifiable "why does this need THIS expertise") | 2 | 2 | 0.3 | 3 | 0.4 | **Reject** |
| 7 | Diversity checks against answer-copying (deliverable contains something not derivable from the task string) | 3 | 2 | 0.3 | 2 | 0.9 | **Reject for now — insufficient evidence to score higher** |

### Why each rejection, stated plainly (the issue asked for reasons, not a silent drop)

- **#5 Information asymmetry — reject.** The scout brief's must-be #1 (verification sharing no
  incentive with the thing verified) is about *incentive* independence, not *information*
  independence. Hiding the builder's record from the verifier does not change who benefits from
  a lenient verdict — an operator-controlled orchestrator can still read both records after the
  fact and would need a second, separate incentive-independence mechanism anyway. This
  repo's actual failure mode (per the issue's own evidence: fabricated "reproduced" claims) was
  not caused by the verifier seeing too much context — it was caused by nobody re-running
  anything. Blinding the verifier to intent does not fix a verifier that never executes. Lower
  reach because it only helps the subset of roles that are verification-shaped, not the
  boilerplate-§20 or task-string-transcription failure modes.
- **#6 Spawn-necessity checks — reject.** Falsifiability of "why does this need THIS expertise"
  is judged by the same orchestrator that decided to spawn the role, or by a downstream gate that
  can only check for the *presence* of a justification field — exactly the field-presence-not-
  truth gap the survey found in `acceptance_gate.py`/`test_boundary.py` today. This candidate
  would add a new gate of the same shape already shown to be gameable (issue's own §20-boilerplate
  evidence: sessions already fill required fields to pass, not to inform). It fails the issue's
  own constraint ("must not be a new gate that can itself be satisfied by performance") on its
  face — no gaming-resistance argument survives contact with the repo's own evidence.
- **#7 Diversity checks — reject for now, not permanently.** No literature (RL, audit, or spec-
  gaming) surfaced this as a load-bearing must-be independently of re-execution; it functions as
  a secondary signal on top of #1 (a record whose content is fully derivable from the task string
  is exactly the shape re-execution would also flag once #1 exists, because there'd be nothing to
  re-run). Building it before #1 would add detection surface with no independent evidence it
  catches anything #1 doesn't. Revisit after #1's measurement window if #1's false-negative rate
  (records that pass re-execution but still read as transcription) is non-trivial.
- **#3 and #4 kept but subordinated**, not independently scored as separate builds: pre-
  registration (#3) is the *precondition* that makes #1's re-execution meaningful (re-running
  against an undeclared, post-hoc question can't be judged pass/fail); sampling (#4) is *how #1
  scales* when full re-execution is too expensive for every record. Both are folded into the #1
  hypothesis's design space rather than competing against it.

## Pre-registered hypothesis package

**H1 (primary).** If a mechanized, non-operator independent re-execution check is added to the
gate path for any record claiming a "reproduced"/"verified"/"passed" outcome, the rate of
undetected fabricated-positive records (a claimed-passing verification whose own cited
repro/test actually fails on independent re-run) will fall, because fabrication currently
survives exactly because nothing re-runs it.

- **Metric**: `fabrication_survival_rate` = (fabricated-positive records that were merged without
  independent-re-run catching them) / (total records claiming a reproduced/verified/passed
  outcome), measured over a rolling window of the next 30 such records after the mechanism ships.
- **Threshold**: baseline is unmeasured-but-nonzero (issue cites exactly one caught instance,
  core#163, caught by *operator* manual re-run, not by any mechanism — meaning the mechanized
  rate today is effectively 100% survival, since no mechanism exists to catch anything). Decision
  threshold: **fabrication_survival_rate ≤ 10%** after the mechanism ships (i.e., mechanized
  re-execution alone, or mechanized re-execution + sampling, catches ≥90% of the fabrication
  instances an equivalent-effort human audit would have caught over the same window).
  **Guardrail metric**: `false_reject_rate` (honest records the mechanism blocks or flags as
  fabricated) must stay **≤ 5%** over the same window — a mechanism that suppresses the
  fabrication rate by also rejecting honest null/negative results is a reduced-trust result, not
  a win, per this repo's own guardrail-metrics obligation.
- **Decision rule**: if `fabrication_survival_rate` ≤ 10% AND `false_reject_rate` ≤ 5% after 30
  qualifying records → **go**, keep the mechanism as-is. If `fabrication_survival_rate` > 10% →
  **pivot**: the re-execution check exists but isn't catching enough — widen its trigger
  condition (more claim-types re-run) before declaring it insufficient. If `false_reject_rate` >
  5% regardless of the primary metric → **kill-and-redesign**: the mechanism is punishing honest
  work, which directly reproduces the issue's own "refusal reads as failure" failure mode at one
  level removed — this is the guardrail this hypothesis cannot be allowed to trade away.
- **Gaming-resistance argument**: re-execution's ground truth is the re-run's own exit
  code/output diff, not a self-report — the mechanism being verified (the claim) and the thing
  producing the verdict (an independent process run in a clean checkout) share no state and no
  authorship. A session cannot inflate its own re-execution result the way it can inflate a
  prose record, by the same logic the scout brief's must-be #1 names (auditor-paid-by-client
  fails when the auditor's incentive and the audited party's incentive are the same; here the
  fix is making them structurally different processes, not just different prompts).
- **Failure signature**: the mechanism fails quietly if the re-execution step itself becomes
  gameable — e.g., if the "clean checkout" it runs in is reachable/writable by the session under
  audit, or if the trigger condition for "this claim needs re-execution" is itself a
  self-reported field a session can omit. Both are named here so the implementation role is on
  notice: the re-run environment must be provisioned by the gate/hook layer, never by the audited
  session, and the trigger must fire on pattern-match against claim language (e.g. "reproduced",
  "verified", "tests pass"), not on a field the session opts into.

**H2 (secondary).** If a gate accepts a well-formed "not-needed" / "cannot-verify-with-reason"
outcome at the same structural cost (same required fields, same pass-through to merge) as a
positive finding, the rate of manufactured deliverables on subjects with no real work to do will
fall, because the issue's own evidence names refusal-penalization as a direct cause of
manufactured positives.

- **Metric**: `manufactured_deliverable_rate` = (records on subjects independently judged, post
  hoc by the human approver, to have had no genuine task) / (total records), measured over the
  next 20 records after H2 ships, using the human approver's existing PR-review Approve/no-Approve
  signal as the independent judgment (no new judgment mechanism invented for this metric).
- **Threshold**: **manufactured_deliverable_rate ≤ 15%** (no clean baseline exists — the issue's
  evidence is qualitative here, "routinely" — so 15% is set as a conservative first-cut ceiling,
  to be revisited once one measurement window exists).
- **Guardrail metric**: `refusal_rate` (fraction of records that take the null/refusal path) must
  not exceed **40%** — a mechanism that makes refusal *cheaper* than work, rather than merely
  *equally priced*, would invert the problem into under-work instead of over-performance; this
  guardrail catches that inversion.
- **Decision rule**: manufactured_deliverable_rate ≤ 15% AND refusal_rate ≤ 40% → **go**. Above
  15% → **pivot**: the null path exists but isn't actually equal-cost yet (check whether gates
  still implicitly reward field-count/length). Above 40% refusal → **kill-and-redesign**: sessions
  are now over-refusing, which the guardrail catches before it's mistaken for success.
- **Gaming-resistance argument**: this mechanism doesn't stop fabrication directly — it removes
  the *incentive* the issue names as the root driver of fabrication in one class of cases (no
  real task existed). Its own gaming risk is symmetric abuse (claiming "not-needed" to avoid real
  work); the guardrail above is the stated countermeasure, not an afterthought.
- **Failure signature**: fails quietly if "not-needed with reason" becomes a boilerplate string
  itself (the exact §20-boilerplate failure mode this issue already documents, one level up) —
  the reason field would need the same non-boilerplate scrutiny H1's re-execution gives positive
  claims, which is why H1 is primary and H2 is explicitly secondary, not a substitute.

## ITWWS (if this works we should ...)

If H1's mechanized re-execution proves out (go verdict), extend its trigger-language pattern set
to cover other self-report claim types this repo makes beyond "reproduced/verified/passed" (e.g.
"measured", "confirmed") — deferred to the architecture/implementation phase, not actioned here,
because the trigger vocabulary is an implementation decision that needs the actual hook/gate
surface in hand, not a phase-1 guess.

If H2's refusal-cost-parity proves out, extend the same-cost principle to partial results
("found 2 of an expected N, ran out of budget") — currently ungoverned by either hypothesis and
left as an explicitly deferred follow-up, not silently dropped.

## Deployment-surface constraint carried forward

Both hypotheses are scoped to land on the deployed plugin surface (hooks / `spawn.py` / `run.md`
contract), per the issue's own constraint — neither proposes a new out-of-band service. The
architecture role inherits H1 as primary build target and H2 as secondary; this proposal does not
specify hook names or gate file edits, which are architecture/implementation decisions.
