# Survey — issue #373

## Issue in situ

Read #373, and the two proposals it names in instance:

- #318 → PR #338 (revised): adds a six-item shape check on `run.md`'s text
  (`test_run_md_shape.py`) plus a standalone pure-function checker,
  `on-the-record/hooks/approval_request_check.py`, that scans a *given
  message string* for the six required items. Wiring that checker to a
  live `Stop` hook is explicitly deferred to #298 ("declaring the `Stop`
  hook itself and wiring it to call that function is left to #298").
- #320 → PR #342 (revised): same shape — a `run.md`-text test plus a
  `report-framing-check.sh` handler meant to run under `Stop`, again
  deferred/conditioned on #298's hook-declaration ownership rule
  ("whichever of #318/#320 lands on `main` first declares `hooks.json`'s
  `Stop` entry").

Both proposals already moved *past* the pure "checks the spec, not the
message" state #373 describes — the revision (triggered by #298's
2026-08-07 comment correcting the "no such hook exists" premise) added
message-level pure functions. What #373 is actually about is not "redo
#318/#320" — it is the *general* mechanism: how a proposal declares that
it delivers less than its issue asked, in a place the operator cannot
miss, and how the unmet remainder stays tracked. #318/#320's revision
notes are a *sample instance* of this general defect (the delta from
"inspect the orchestrator's real output" to "check run.md's text" was
recorded only inside a Rationalize prose paragraph, in both cases), not
the target of the fix itself.

## Prior-art shapes read (per #373's own pointers)

- **#310** — "a stated requirement must end up in code or contract with
  something that fails when it regresses." Establishes: (1) a promise,
  memory note, hardcoded-list edit, or doc sentence never discharges a
  requirement; (2) an interim mitigation lands *with* the issue for the
  generator and does not close the issue; (3) issue closure must gate on
  the record naming an executable check. #373 explicitly says #310's
  shape is "the obvious candidate" for scope item 3 (remainder tracking)
  — reuse, don't invent.
- **#298** (2026-08-07 Korean-language comment) — corrects the "no hook
  observes the orchestrator's own text" premise: Claude Code's `Stop`
  hook fires at turn end, receives `last_assistant_message`, and can
  return `decision: "block"` or inject `additionalContext`. This is the
  only currently-known mechanism that can see the orchestrator's actual
  relay text (scope item 4). `on-the-record/hooks/hooks.json` today
  declares only `SessionStart`, `UserPromptSubmit`, `PreToolUse` — no
  `Stop` key exists yet on `main`.
- **#363** — "nothing requires a proposal to address the generator." Sets
  its own trap explicitly: a required `## Generator` heading whose
  *presence* is checked but whose *content* is never read is a symptom
  fix for the symptom-fix problem. #373 names the identical trap for
  itself: "a check that merely requires a Delta section to be present,
  without reading it, is a presence check."

## Current-state survey of the write surfaces #373's scope implies

- `on-the-record/commands/run.md` (orchestrator's own instructions,
  read live by the session that plays "당신은 조율 세션이다"). Step 5
  ("PR 을 설명한다") already requires four items on every approval/merge
  relay (무엇을/왜/실제로 무엇이 바뀌었는가/어떻게 검증됐는가) plus
  flow/stage/next (#54) and link obligation (#236). It has **no**
  instruction today that the relay must state a delta when the
  underlying proposal delivers less than its issue asked — this is the
  literal gap #373 names ("the orchestrator relaying a proposal to the
  operator must state the delta").
- `on-the-record/hooks/hooks.json` — three declared events, no `Stop`
  key. #318/#320 both plan to add one, each conditioned on landing
  order (first declares, second appends a handler to the same array).
  A third checker for #373 would need to follow the same
  first-declares/second-appends protocol rather than invent a second
  declaration.
- `on-the-record/hooks/approval_request_check.py` (from #318, not yet on
  `main` — lives on `issue-318/implementation`) is the closest existing
  precedent for a pure, hook-free, string-in/struct-out checker over the
  orchestrator's own relay text. #373 scope item 4 fits this exact shape:
  a pure function, checker only, hook wiring deferred to #298.
- `gates/` (CI-level, deterministic, zero-LLM gates that block PR merges
  — `gates/gates.py`, `gates/ci.py`, wired via
  `.github/workflows/plan-aware-closes-gate.yml`). This is the *only*
  currently-existing mechanism in the repo that mechanically blocks a
  merge on PR/issue metadata (e.g. the plan-aware Closes gate). It is
  the natural home for scope item 3 (linkage between a reduced delivery
  and the issue tracking the remainder) — #310's shape landed as a
  regression test on `run.md` text there, but nothing today checks a
  *proposal file's own content* for a Delta declaration or a remainder
  issue reference. `gates/` sits inside `gates.py`'s own
  `PROTECTED_ROOT_DIRS`, so any change there is a protected-path change
  requiring human review regardless of gate outcome — expected, not a
  defect to route around.
- Proposal-document *shape* (the seven sections: `files:`, `## Request`,
  `## Constraints`, `## Rationale`, `## What will be done`,
  `## Out of scope`, `## How you'll know it worked`) is enforced on this
  session by an external harness directive
  (`proposal-shape-directive`/`proposal-shape-gate.sh`) that lives
  outside this git repository, in the implementation-role plugin
  configuration. **on-the-record's own repo does not define or enforce
  proposal-file shape at authoring time** — it can only inspect a
  proposal file's *committed content*, after the fact, at PR-check time
  (via `gates/`) or when the orchestrator relays it (via `run.md` +
  `Stop`). This is a real ceiling on scope item 1: nothing in this repo
  can force a role session to write a `## Delta` section the moment it
  authors the proposal — the earliest in-repo enforcement point is the
  PR-merge gate.

## Skip-condition check (scout-directive)

This issue asks for a design decision — how a delta is stated, whether a
distinct approval act is required, how the remainder stays linked, and
whether the orchestrator's relay must state it — none of which is a pure
bugfix or a spec with no design freedom. Scouting (external prior-art
survey) was evaluated and skipped: #373 itself names the precedent to
reuse (#310's shape) and the mechanism to build on (#298's `Stop` hook
correction) inside the issue text; this is an internal-consistency
design problem (how this repo's own contract composes with its own prior
decisions), not a category where an external product's best-in-class
practice would change the shape. Recorded per the mandatory skip line.
