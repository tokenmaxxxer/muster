# Survey — issue #503 (streaming per-unit landing as the structural norm)

## What exists today

### Contract text (`on-the-record/commands/run.md`, 501 lines)

- The parallel-step syntax (`‖`, "실행 계획" block, ~line 296-344) already
  defines *concurrent dispatch* of roles within a step, and "병렬 스텝의
  부분 반려" (~line 345-352) already says a rejected role in a parallel
  step is respawned alone while already-merged siblings in the same line
  are **not** redone. That is half of streaming (don't undo what landed),
  but it does not say the coordinator must *act* (verify/merge/re-scan)
  on each completion as it arrives rather than waiting for the whole
  step's roster to finish before doing anything. Nothing in run.md
  currently forbids or discourages "wait for all N, then process."
- Landing-is-per-PR precedent already exists at issue #407 (~line
  279-289): "랜딩은 기본적으로 PR 단위다... 여러 PR에 걸친 원인으로
  머지를 멈출 때는... `landing_readiness.py`를 돌려... `BLOCKED_ON_SCOPE`로
  분류하는 PR만 지목한다 — 나머지는 그대로 이 스텝이 요구하는 형태가
  아니다." This is the exact mirror pattern the issue asks for (§Scope
  bullet 1: "mirror of the landing-is-per-PR rule #407"), but it is
  phrased for the *merge* decision only, not for fan-out dispatch/watch
  in general — the issue asks the same "don't block on the slowest" norm
  to apply structurally to the whole fan-out lifecycle (verify → merge →
  re-scan), not just to the close-out merge step.
- No section currently states a default streaming norm with a
  named-cross-unit-dependency exception as a first-class rule roles are
  expected to follow when *they themselves* fan out sub-work (dispatch
  guidance to roles, §Scope bullet 2). The only fan-out guidance role
  sessions currently inherit is the freelunch directive (injected at
  session start, not part of run.md), which already governs execution
  style (worker dispatch, hedging) but says nothing about *landing*
  order once workers return.

### Orchestrator loop mechanics (`spawn.py`)

- `reconcile(expected, observed)` (spawn.py:1510) is a **pure per-entry
  comparison function** — one roster entry in, zero-or-one divergence
  dict out. It has no batching built in.
- `roster_reconcile(issue=None)` (spawn.py:1913-1935) is the CLI
  entrypoint (`spawn.py reconcile`). It loads the roster, and for each
  entry **prints and acts (records divergence + next_action) in the same
  loop iteration** — already per-entry, not "collect all divergences,
  then decide." This is already the right shape at the *reporting*
  layer; nothing currently makes "act on it" (respawn / merge / re-scan)
  mandatory per-event rather than left as a batched follow-up decision
  by the coordinating session reading the printed lines.
- `roster_watchdog()` (spawn.py:1854-1911) is explicitly observe-only
  (mirrors run.md's own "observe-only" framing at ~line 486-496) — it
  reports anomalies per entry but never merges or kills. It's a
  different lifecycle stage (liveness, not completion) from what #503
  is about, but it's the closest existing "loop over roster, act
  per-entry" precedent for the orchestrator loop behavior the issue
  wants.
- There is no fan-out **fixture** today that models "N simulated workers
  completing at different times" and asserts each is processed
  (verify/merge equivalent) on its own completion rather than at a
  collected barrier. `test_spawn.py`'s `Reconcile` class (line 3584) and
  `RosterConcurrency` class (line 4594) test `reconcile()`/roster
  mechanics per-entry already, but none of the existing tests assert the
  *temporal* streaming property (unit A's action fires before unit C
  even finishes) — they test correctness of a single reconcile call, not
  ordering across a batch.

### Enforcement / spec-index scaffolding

- `gates/test_boundary.py` (299 lines) enforces that
  `docs/specs/enforcement-boundary.md` covers every `gates/*.py` /
  `on-the-record/hooks/*.sh` / `spawn.py` mechanism with a recorded
  verdict — it does not currently touch run.md section presence at all;
  it is the wrong gate to extend for "does run.md carry a norm section."
  A spec-index / run.md section-presence check (if warranted) would be
  a **new** small check, not an extension of an existing assertion in
  that file — this narrows what "check: gates/test_boundary.py (or
  spec-index-tracked run.md)" in the issue's acceptance criteria plausibly
  means: the issue names it as one *candidate* location, not a
  guaranteed existing hook to extend.
- No file named anything like "spec index" was found under `docs/specs/`
  beyond `enforcement-boundary.md`; `grep -r spec-index` only hits the
  unrelated issue-459 preflight-hook docs. There is no existing
  machine-checked "run.md must contain section X" gate to model the new
  check after 1:1 — closest analog is `t_run_md_references_unenforced_clauses`
  (gates/test_boundary.py:131), which asserts a specific reference line
  exists in run.md via simple substring/regex search. That is the
  pattern a new streaming-norm-section check would most plausibly copy.

## Write set this points to (for the proposal)

- `on-the-record/commands/run.md` — add the streaming-per-unit-landing
  norm section (contract text + named-dependency exception), placed near
  the existing #407 per-PR-landing text and the "병렬 스텝의 부분 반려"
  section so the three related rules sit together.
- `gates/test_boundary.py` — add one assertion that the new run.md
  section exists (mirroring `t_run_md_references_unenforced_clauses`'s
  regex-presence style), so the norm is mechanically checked like the
  issue's acceptance criterion asks.
- `test_spawn.py` — add a fan-out fixture (red-green pair) demonstrating
  that 3 simulated roster entries completing at different times are each
  reconciled/actioned on their own completion, not held for a barrier.
  Lands in (or near) the existing `Reconcile`/`RosterConcurrency` classes
  since those already own the roster/reconcile fixtures this needs to
  build on.
- `spawn.py` — only if the fixture proves the *current* reconcile-loop
  call site genuinely batches (it does not appear to, per the reading
  above — `roster_reconcile` already loops-and-acts per entry). Kept in
  the write set as a contingency, not a committed change — see proposal
  Rationale.

## Alternatives visible from this survey (for the proposal's Rationale)

- Extending `t_run_md_references_unenforced_clauses`-style regex check
  in `gates/test_boundary.py` vs. inventing a new standalone
  spec-index/run.md-section gate module. Both are plausible given what
  exists; the survey above is what makes this a real choice rather than
  a decorated one.
- Writing the fan-out streaming fixture as new tests in the existing
  `Reconcile`/`RosterConcurrency` classes vs. a new dedicated test class.
  Both plausible: existing classes already own the relevant fixtures
  (`_roster_load`/`_build_expected`/`_build_observed` helpers), but the
  issue frames this as its own acceptance item, arguing for visibility
  as a named class.

## Skip conditions checked (scout-directive)

Scouting (external/product-shaped sweep) was skipped: this is a
contract-text + internal-orchestrator-loop change with no external
product or category to benchmark against — the "spec leaves no design
decision open" condition does not literally apply (there are two small
internal design choices, listed as alternatives above), but there is no
external field to scout since the deliverable is this repo's own
governance text and Python fixtures, not a product surface. One-line
reason: internal contract/tooling change, no product-shaped or
external-prior-art surface to sweep.
