# Scout brief — issue-492

Mode: batched-sequential fallback (single WebSearch call; no parallel dispatch available in this session — falling back per protocol rather than serializing silently). 1 stage, well under the 5-stage/3min budget — saturation reached after one round: the exemplar's core claim (level-driven reconciliation) directly answers the one open design question (report-trust vs state-comparison) and no further round would change it.

## Exemplar: Kubernetes controller reconciliation loop
Must-bes the field converges on:
- separate the **desired state** (what was asked) from the **observed state** (what actually happened), never conflate them (spec vs status objects)
- the loop is **level-driven, not edge-driven**: it re-derives divergence from current state every tick, it does not trust a one-time "I'm done" event
- reconciliation is idempotent and non-terminating — re-running it when nothing diverged is a no-op, not an error

Performance axes exemplars compete on: (1) how fast observed state converges to desired after divergence, (2) whether the loop survives the controller process itself restarting mid-reconcile, (3) how legible the diff between desired/observed is to an operator.

Pattern to adopt: level-driven state comparison as the reconciliation primitive (desired = what a role/subject was dispatched to do; observed = board/roster/PR/log state read fresh each tick) — this is exactly the shape #492 asks for ("orchestrator's 'what next' input is observable state ... compared against what the session was asked to do").
Pattern to skip: full Kubernetes-style CRD/spec-status object model — overkill for a single-repo plugin; the repo already has an equivalent desired-state source (the issue's 실행 계획 checklist + role assignment) and an equivalent observed-state source (roster/board/ledger) that a reconcile step can read directly without inventing a new schema.

Gap line: the repo already has the *observed*-state derivation half (session_end_verdict's normal/crashed/stalled/in-progress 3-분법, spawn.py:1409; fail_closed_downgrade's outcome ledger, spawn.py:1457) — the field's "observed state must be freshly re-read, not trusted from a report" must-be is already met there. What's missing is the *comparison* half: nothing in spawn.py reads the **expected** side (what the dispatched role/subject was asked to deliver) and diffs it against the observed side to name a next action. That is the gap #492's step 1 needs to close.

Segment fit: internal orchestration tooling, not a user product — the exemplar's operator-legibility axis (axis 3) matters most here since the diff's consumer is spawn.py's own CLI operator/orchestrator, not an end user.

Sources:
- [Controllers | Kubernetes](https://kubernetes.io/docs/concepts/architecture/controller/)
- [The Reconciler Pattern | farishuskovic.dev](https://www.farishuskovic.dev/blog/k8s-reconciler-pattern/)
