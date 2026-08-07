# Issue #341 — Phase 1 Proposal (implementation)

files:
- `test_gates.py` (or `test_spawn_constraints.py`, a new small module —
  final name settled in phase 2 by whichever fits the existing test
  layout better): one regression test asserting `spawn.py` carries no
  concurrency-limiting construct (no `Semaphore`/`Lock`/queue/counter
  capping simultaneous spawns).
- `docs/issue-341/reports/implementation.md` (phase 2 record; states
  the mechanical-enforceability verdict this proposal reaches).
- No changes to `on-the-record/commands/run.md`, `spawn.py`,
  `gates/gates.py`, or `roles/*.json`.

## Request (paraphrased)

A live orchestrator invented a "슬롯" (slot) capacity limit that does
not exist anywhere in `spawn.py`, throttled 11 real, ready tasks
against it, and reported the resulting idleness as normal — undetected
until the operator asked. The general defect: the orchestrator can
state any constraint (a limit, a dependency, an ordering requirement)
in conversational prose, nothing requires it to name what enforces the
constraint, and nothing downstream checks the claim against reality.
Acceptance requires either an executable artifact that fails when this
regresses, or an explicit, reasoned record that the requirement is not
mechanically checkable — never a prose-only fix, which is the exact
non-discharge #310 already named and which four prior attempts already
failed at in this same repository.

## Constraints

- Per the invoking instructions and #310: this proposal must not
  resolve to a sentence added to `on-the-record/commands/run.md`
  telling the orchestrator to be more careful about claiming limits.
  Any change to run.md that isn't backed by something that fails on
  regression is out of scope for this proposal, full stop.
- Per the issue's own Acceptance: the hard part — that orchestrator
  constraints are stated in conversational prose with no structured
  field — must be confronted directly. If no code change closes it,
  the record must say so and say why, not stay silent or paper over
  it with an unenforced convention.
- The boundary against #324, #327, #298 (drawn in the issue) is not
  re-litigated; the survey confirmed it holds and is not redrawn here.
- No new dependency, no new environment variable, no schema/migration.

## Rationale

**Chosen approach:** ship the one piece that genuinely is mechanically
checkable today — a regression test pinned to the issue's own
falsifiable fact, that `spawn.py` has no concurrency limit — and pair
it with an explicit, reasoned non-enforceability verdict for the
general claim ("any orchestrator-stated constraint names its
enforcer"), recorded in this issue's phase-2 record rather than
smuggled into run.md as prose.

**Alternative considered and rejected — keyword/regex gate scanning
orchestrator chat output for constraint-shaped language** (e.g. "대기",
"제한", "슬롯", "limit", "must wait") and requiring an enforcer
citation nearby: rejected because there is no committed artifact to
scan. Surveyed every place an orchestrator turn's content lands in
git: the Mission Board is explicitly recomputed fresh every render and
never stored (run.md's own text says so); the Execution Plan block in
the GitHub issue body has no field for ad hoc capacity claims (only
step ordering); `runs/ledger.jsonl` is a spawn/exit accounting log,
not a claims log, and doesn't exist in this checkout. `gates/gates.py`
is diff-based by design (`git diff --name-status` against
`origin/main...HEAD`, fail-closed when unreadable) — it has nothing to
diff when the content in question was never a commit. A gate built to
scan text that doesn't exist as a git object is decoration, not
enforcement — worse, per gates.py's own stated principle
("불확실하면 막는다" — a gate that must guess is refused, not
approximated), a keyword gate would have to guess at natural-language
intent, which the project's own gate-design doctrine already treats as
disqualifying.

**Alternative considered and rejected — a new spawn.py flag that logs
stated constraints + their enforcer to `runs/ledger.jsonl`, gated by a
script that verifies the named enforcer resolves to real code:**
rejected as the proposal's mechanism (though noted as the real
structural prerequisite, below) because routing through it stays
voluntary. The orchestrator can still state "waiting for a slot" in
plain chat without ever calling the flag — which is exactly what
happened in the incident. Building the flag doesn't close the gap;
it only gives a well-behaved orchestrator a nicer way to do something
it was already free to do (or skip) with no consequence either way.

## What will be done

1. Add a regression test that imports/greps `spawn.py`'s spawn path
   and fails if a concurrency-limiting construct (semaphore, lock,
   bounded queue, or a counter compared against a `MAX_CONCURRENT`-
   shaped constant) is present around simultaneous session spawning.
   This does not stop the orchestrator from *claiming* a limit in
   chat, but it means the one artifact a true claim would have to
   point at is itself continuously verified — a future PR that adds a
   real slot limit to `spawn.py` will visibly break/update this test
   in the diff, rather than the limit being invented and never
   written down anywhere. This is the "executable artifact that fails
   when this regresses" the issue's Acceptance calls for, scoped to
   the one part of the problem that has a code-shaped ground truth.
2. Write the phase-2 record (`docs/issue-341/reports/implementation.md`)
   stating plainly, per the issue's own permitted escape hatch: the
   general rule ("every orchestrator-stated constraint names its
   enforcer") is **not mechanically enforceable today**, because
   orchestrator conversational turns are not a git-tracked artifact
   and every existing gate in this repository (`gates/gates.py`) is
   diff-based. Enforcing the general rule would first require making
   orchestrator claims a committed artifact (the rejected ledger-flag
   alternative above sketches the shape) — and even then, routing
   through it stays voluntary unless something *forces* every
   constraint-shaped utterance through that channel, which is an
   open design question about the orchestrator's own protocol, not a
   gate this issue can unilaterally build. That decision — whether to
   redesign the orchestrator/board interface so constraint claims
   become a required structured emission — is left to the user as a
   follow-on issue, not decided here.
3. State the #330 reach-beyond-acceptance note directly in the record:
   the regression test's actual guarantee is narrower than the
   issue's title suggests — it guards `spawn.py` against ever
   silently *acquiring* the exact invented constraint from this
   incident, not against the orchestrator saying something false
   about it. Anyone reading the test in isolation should not conclude
   the general problem is solved.

## Out of scope

- Any change to `on-the-record/commands/run.md`.
- Building the ledger-flag / claims-log infrastructure sketched in
  the rejected alternative — that is a real, larger design decision
  (does the orchestrator's protocol require routing every stated
  constraint through a structured, committed channel?) that belongs
  in its own proposal with its own user sign-off, not folded into this
  one under the banner of "closing #341 for good."
- #324's parallelism computation and #327's idle-time defect
  treatment — confirmed out of boundary by the survey, not
  re-litigated.
- Re-scoping or redrawing the #324/#327/#298 boundary — the survey
  found it correctly drawn.

## How you'll know it worked

- `pytest test_gates.py` (or the new module) passes on a clean
  checkout and fails if a concurrency-limiting construct is
  introduced into `spawn.py`'s spawn path — run once as part of
  phase-2 delivery and its output quoted in the record.
- The phase-2 record contains an explicit, reasoned
  mechanical-enforceability verdict for the general claim, with the
  `## What did not work`/reasoning trail showing the two rejected
  alternatives above, so a future reader (or the user) can see this
  was confronted, not routed around.
- No sentence resembling "orchestrator should be more careful about
  claiming limits" appears anywhere in `on-the-record/commands/run.md`
  as a result of this change — checkable by `git diff` on that file
  showing no touch at all.
