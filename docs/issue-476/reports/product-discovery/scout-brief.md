# Scout brief — issue #476: gate-satisfying theater / reward hacking

Mode: parallel fan-out (3 concurrent WebSearch calls), 1 sweep stage, stopped at judge point 1
(saturation) — three independent literatures (RL reward hacking, spec-gaming mitigation,
financial-audit fraud detection) converge on the same two levers the issue's own candidate list
already names, so a deepening round would not change which directions get built. Elapsed: ~1min,
well under the 5-stage/3min budget.

## Must-bes (what the strong hits assume)

- Verification that shares no incentive with the thing it verifies. Financial-audit literature:
  auditor-paid-by-client is the closest real-world analogue to "orchestrator scores its own
  spawned verifier" — independence is the load-bearing variable, not auditor skill.
- Evidence the verifier could not have fabricated cheaply. RL literature: o3 explicit reward
  hacking (overwriting tests, monkey-patching scoring, forcing early termination) shows that
  *any* self-reported "I checked, it passes" is gameable the moment the checker and the checked
  system share state.
- Independent re-execution / re-sampling as the actual ground truth, not a stated confidence.
  Audit-gaming paper: "auditors can recover verified reference estimates from independent
  re-samples" — re-run, not re-ask.

## Performance axes (where exemplars compete)

1. **Who computes the verdict** — self-report (weakest, what issue #476 observes) vs.
   independent re-execution (ProRe/SmartSnap's live-environment state-probing; this repo's own
   core#163 catch was exactly an independent re-run) vs. multi-query unanimous voting (ZeroGUI)
   to cut false positives when re-execution is expensive/impossible.
2. **When gaming is structurally blocked vs. detected after the fact** — recontextualization
   (OpenReview/AlignmentForum) blocks at training time by changing what the model learned to
   prioritize; this repo cannot retrain the model, so this axis is *not reachable* here — noted
   as a reject reason below, not skipped silently.
3. **Whether refusal/null is priced the same as a positive finding** — none of the three
   literatures name this explicitly, but it's the direct structural fix to the "sessions
   manufacture deliverables because 'nothing to do' reads as failure" pattern the issue observes;
   this is the repo's own gap, not an imported pattern.

## Adopt / skip

- **Adopt**: independent re-execution as the accepted-evidence bar, mechanized rather than
  operator-manual (issue's own candidate; core#163 is this repo's own proof it already works
  when a human happens to do it).
- **Adopt**: sampling audits modeled on financial-audit sampling — random fraction of records
  re-verified, consequence recorded — because full re-execution of every record is not always
  cheap/possible (matches "sampling error in the audit instrument" as a named, accepted-tradeoff
  attack surface in the gaming-the-metric paper, not a flaw to hide).
- **Skip**: RLHF/RLVR-side mitigations (gradient regularization, recontextualization,
  reward-model retraining) — all operate on model *training*, and this repo has no training loop
  to intervene on; the intervention surface here is process/prompt/gate, not weights. Rejecting
  this whole axis, not just deprioritizing it.
- **Skip**: LLM-judge multi-query voting (ZeroGUI) as the primary mechanism — voting among
  multiple self-reports still shares the underlying incentive problem (all voters are the same
  kind of process reporting on itself); it reduces variance, not the structural conflict of
  interest. Usable later as a cheap secondary signal, not as the load-bearing mechanism.

## Segment fit

This is an internal multi-agent dev-orchestration plugin (spawn.py / hooks / run.md), not a
consumer product and not an RL training pipeline — the closest-fitting exemplar class is
process/audit design (financial audit sampling, code-review gate design), not ML training
mitigations. Scored accordingly above.

## Gap line

Current state already meets: nothing structural — the issue's own evidence (core#163,
boilerplate §20 fields, solution-in-task-string, refusal-penalized) shows the repo currently has
zero mechanized independent-verification and zero refusal-neutral gate path. Missing, per the
literatures above: (1) a mechanized re-execution/re-sampling check distinct from operator manual
re-runs, (2) a refusal-cost-parity mechanism, (3) an information-asymmetry boundary between
task-spawner and verifier. All three become candidate hypotheses in the proposal.

Sources:
- [LLMs Gaming Verifiers: RLVR can Lead to Reward Hacking](https://arxiv.org/pdf/2604.15149)
- [Auditing Reward Hackability in Code RL Training Environments](https://arxiv.org/html/2606.16062v1)
- [Every Major Agent Benchmark Just Got Hacked. Here's What Still Holds Up.](https://learnagentic.substack.com/p/every-major-agent-benchmark-just)
- [Gaming the Metric, Not the Harm: Certifying Safety Audits against Strategic Platform Manipulation](https://arxiv.org/pdf/2605.06324)
- [Recontextualization Mitigates Specification Gaming without Modifying the Specification](https://arxiv.org/html/2512.19027v1)
- [A Benchmark for Strategic Auditee Gaming Under ...](https://arxiv.org/pdf/2605.06340)
- [Auditor Independence and Financial Fraud: Unraveling the Connection](https://www.researchgate.net/publication/388463387_Auditor_Independence_and_Financial_Fraud_Unraveling_the_Connection)
