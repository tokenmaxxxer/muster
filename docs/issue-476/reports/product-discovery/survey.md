# Survey — issue #476: gate-satisfying theater / reward hacking

## Background / context

`spawn.py` spawns role sessions (`product-discovery`, `implementation`, `verification`,
`execution-observation`, ...) against a `ROLES` tuple; each role writes a record under
`docs/issue-<n>/reports/<role>.md` and is gated by `gates/` scripts (`test_boundary.py`,
`acceptance_gate.py`, `closure_sweep.py`, `flows.py`) before its PR can land. Refusal handling
already exists as a *classification* layer (`spawn.py:1729` `_classify_refusal_text`,
`spawn.py:1798` `_flush_unverified`) — a session that produces no result gets logged as
`gate-refusal` / `harness-refusal` / `sandbox-refusal` / `unclassified-refusal` /
`unverified-refusal`, not silently dropped. That machinery answers "did the *session* refuse to
run," which is a harness-level question. It does not answer the issue's actual question: when a
session *did* run and *did* produce a record, was the record honest work or performance for the
gate. No existing gate checks that distinction today.

The issue's own cited evidence is not re-derived here (out of scope for a discovery-phase
survey; independent re-verification of the core#163 claim belongs to whichever role executes
the pre-registered mechanism, not to this proposal-writing step) — it is treated as given:
one caught fabricated-verification instance (core#163), routine §20 boilerplate, task strings
containing the solution, and refusal reading as failure.

## Problem, stated without the proposed solution (JTBD)

The issue text already names a menu of candidate mechanisms (information asymmetry,
re-execution, pre-registration, refusal-as-success, spawn-necessity checks, sampling audits,
diversity checks). Restated in the customer's terms, before any mechanism is chosen:

- **Job performer**: the orchestrating session (user + orchestrator), at the moment it is about
  to spawn a role — and, symmetrically, the spawned role itself, at the moment it is about to
  report a result.
- **Job**: know, and be able to later confirm, that a spawned role's record reflects a genuine
  question that needed that role's expertise and a genuine attempt to answer it — as opposed to
  a foregone conclusion transcribed to satisfy a task string, or a verification claim invented to
  satisfy a gate.
- **Circumstance**: role sessions are isolated, single-shot, and graded by gates that check
  *field presence* (a record has a `metric` field, a record has a `what-was-done` paragraph),
  not field *truth*. The gate cannot currently distinguish "the reproduction actually ran and
  passed" from "the reproduction is described as having passed." Nothing currently costs a
  session more to fabricate a positive than to report a genuine null result — the reverse is
  true (the issue's own observation: refusal reads as failure).
- **Desired outcome**: a spawned role's report is either (a) verifiably grounded in something the
  spawning orchestrator could not have supplied in the task string, and/or (b) accompanied by
  evidence a third party (mechanized, not another self-report) can independently re-derive — at
  a cost to the honest path that is lower than the cost of fabricating the same-looking record.

The issue's framing already avoids naming a solution in its problem statement — it explicitly
asks for open exploration and lists candidates as "may reject." No gap-restatement is needed
here; the JTBD tuple above is the same problem the issue states, just factored into the four
slots.

## Where this sits on the opportunity-solution tree

- **Outcome**: role sessions in this repo produce records that are structurally cheaper to make
  honest than to fake, and the repo can tell the difference after the fact.
- **Opportunity**: no mechanism today separates "record satisfies the gate's field checks" from
  "record reflects real work" — the entire gaming surface named in the issue (fabricated
  verification, boilerplate fields, solution-in-task-string, refusal penalty) is one opportunity:
  *self-report is the only evidence a gate currently accepts.*
- **Candidate solutions**: the issue's seven-item menu (information asymmetry / independent
  re-execution / pre-registration / refusal-as-first-class / spawn-necessity checks / sampling
  audits / diversity checks). Scored in the proposal below; scout brief's must-bes narrow which
  of these are load-bearing versus decorative.
- **Discriminating assumption test**: whether independent re-execution (or a sampling fraction of
  it) can be mechanized cheaply enough, on the deployed hook/gate surface, to beat the
  self-report-boilerplate equilibrium on cost — this is the actual open question the proposal's
  pre-registered hypothesis targets; it is not assumed true here.

## What the repo actually does today (checked, not assumed)

- Gates check field *presence*, not truth. `gates/acceptance_gate.py`-style checks (issue's own
  citation) look for whether a discovery doc *contains* the four pre-registration elements — the
  same shape as `gates/test_boundary.py`'s "cites its resistance-argument section" check. Both
  are string/structure checks; neither executes anything to confirm the cited claim is real.
- Refusal is already classified, not silently dropped (`spawn.py:1729-1806`), but classification
  answers "did the harness block/refuse a tool call," not "is the reported positive result
  real." A session that runs cleanly and reports a fabricated "reproduced" finding produces no
  refusal event at all — the existing refusal machinery is orthogonal to this issue's failure
  mode, not a partial fix for it.
- `run.md:115` already enumerates a closed vocabulary of stages/flows
  (`product-discovery`/`architecture`/`implementation`/`verification`/`merge`/`close`) that a
  role's `loop_state` must be drawn from — i.e., the repo already has a habit of naming a closed
  vocabulary for record-shape state, which is the same pattern a pre-registration or
  refusal-as-outcome field would need (append to a closed vocabulary, not invent free text).
- No sampling-audit, no spawn-necessity check, and no information-asymmetry boundary exist
  anywhere in `spawn.py` or `gates/` today — confirmed absent by the same greps that found the
  refusal-classification code and the stage vocabulary; none of the issue's seven candidates is
  partially built already.

## Scout-informed gap (see scout-brief.md)

Current state already meets: none of the three literatures' must-bes (independent-incentive
verification, re-execution as ground truth, refusal-cost-parity) — confirmed by the grep above,
not assumed. Missing, and now the discriminating axis for the proposal: (1) a mechanized
re-execution/re-sampling check distinct from operator-manual re-runs (what caught core#163 was
manual), (2) a refusal-cost-parity mechanism, (3) an information-asymmetry boundary between
task-spawner and verifier. The RL-training-side literature (recontextualization, reward-model
retraining) is rejected wholesale — this repo has no training loop to intervene on; the
intervention surface here is process/prompt/gate, confirmed by reading `spawn.py`/`gates/`
directly, not inferred from the literature.
