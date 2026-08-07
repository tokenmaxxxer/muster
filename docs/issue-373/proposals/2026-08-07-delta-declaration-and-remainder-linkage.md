---
status: proposed
files:
  - on-the-record/commands/run.md
  - on-the-record/hooks/proposal_delta_check.py
  - test_run_md_delta_shape.py
  - test_proposal_delta_check.py
  - gates/ci.py
  - gates/test_delta_gate_ci.py
  - .github/workflows/proposal-delta-gate.yml
---

## Request

#373: a proposal may deliver less than its issue asked for, and today
that reduction — if recorded at all — lives only inside the proposal's
own Rationale prose, which the operator has no requirement to open.
#373 asks for four things: (1) how a proposal states the delta in a
place a reader cannot miss; (2) whether accepting a reduced proposal
needs a distinct approval act, separate from the token a full-scope
proposal gets; (3) how the unmet remainder stays tracked instead of
evaporating; (4) whether the orchestrator's own relay to the operator
must state the delta. #373 states its own honesty requirement: a check
that only requires a Delta section to *exist*, without reading it, is a
presence check — the same trap #363 names for itself — and if that is
the ceiling, say so and say what it does not catch.

## Constraints

- Per #310: prose alone does not discharge this. Every mechanism below
  must be an executable artifact that fails on regression, or the record
  must say plainly it is unverifiable and why.
- Per #373's own boundary note: this is not #371 (status reports
  collapsing degrees of doneness) and not #363 (whether the generator
  survives) — it is specifically about the *requirement* shrinking
  before it is reported on.
- Reuse #310's shape for the remainder (generator gets/keeps its own
  issue; the reduced delivery does not close it) rather than invent a
  new tracking mechanism, per #373's explicit instruction.
- `on-the-record`'s own repo does not own proposal-document *shape* at
  authoring time (survey: that convention is enforced by an external
  harness directive, not by anything in this repository) — so nothing
  proposed here can be a write-time gate on the proposal file itself.
  The earliest in-repo enforcement point is PR-merge time (`gates/`) and
  the orchestrator-relay moment (`run.md` + `Stop`, per #298).
- `gates/` is a protected root directory (`gates.py`'s own
  `PROTECTED_ROOT_DIRS`) — any change there always requires human
  review regardless of what the new check finds, which is the existing,
  correct behavior for pipeline-logic changes, not something to route
  around.
- `hooks.json`'s `Stop` key: #318 and #320 already agreed a
  first-declares/second-appends protocol for it (`docs/issue-320/…`
  Constraints). Any `Stop`-observing checker this proposal adds is a
  pure function only (mirrors #318's `approval_request_check.py`); it
  does **not** declare or wire `hooks.json`'s `Stop` key — that
  remains #298's, per the same reasoning #318/#320 already gave (folding
  #298's subject in through a sibling issue defeats the operator's own
  item-7 parallelism principle).

## Rationale

**Scope item 2 (distinct approval act) — considered and deliberately
left undecided here, not silently dropped.** #373 states this itself:
"whether to accept a smaller version of their own requirement is [the
operator's] decision and one of the few decisions in this system that
genuinely cannot be delegated." A role proposal choosing the shape of
its own approval token would be exactly the kind of self-authorized
discharge #310 exists to block. This proposal makes the delta
*mechanically visible* (items 1, 3, 4 below); whether visibility must
also force a distinct token, versus the operator simply reading a
now-unmissable Delta line before typing the same `APPROVE` string, is
listed under Out of scope for the operator to decide separately — not
because it's hard to build, but because building it here would be this
proposal deciding a question #373 says only the operator can decide.

**Alternative considered for item 1 (delta declaration): a
write-time hook that blocks a role session from committing a proposal
file missing a `## Delta` section.** Rejected — per the survey, this
repo does not own proposal-file shape at authoring time; that convention
lives in an external harness config outside this repository's write
set. Building a write-time gate here would require editing files outside
the frozen set (survey-order violation) or duplicating a convention this
repo cannot see change. Chosen instead: a **PR-merge-time gate**
(`gates/ci.py`, new `_delta_remainder_mismatch`) that reads the
merged-in proposal file's content directly from the PR diff/HEAD and
blocks the merge if a `## Delta` section is absent, or present but names
no remainder issue. This is later than authoring time but it is the
earliest point this repo can actually check, and unlike a Rationale
paragraph, it is a required, blocking CI check the same way
`plan-aware-closes-gate.yml` already is for `Closes` — not something the
operator has to remember to look for.

**Alternative considered for item 1's content bar: LLM-graded semantic
check that the stated delta accurately reflects the issue's actual
requirement.** Rejected for this proposal — #373's own acceptance
section pre-empts exactly this over-claim risk ("state honestly where
the ceiling is"). What's built here is a **presence-and-pattern** check:
does `## Delta` exist, and if its content isn't the literal string
`없음`/`none`, does it contain an `#<n>` reference. It cannot verify the
delta is an *honest* or *complete* description of the gap between issue
and proposal — that remains a human judgment at approval time, same as
#363's own stated ceiling for its Generator heading. Named explicitly in
"How you'll know it worked" rather than left implicit.

**Alternative considered for item 3 (remainder linkage): a fresh
tracking mechanism (e.g. a `docs/issue-<n>/remainder` marker file).**
Rejected per #373's explicit instruction to reuse #310's shape rather
than invent one: the remainder is just another issue, the same as any
interim-mitigation generator issue #310 already requires. The gate's job
is only to check that *a* reference exists in the Delta section, not to
create new bookkeeping.

**Alternative considered for item 4 (orchestrator relay): wire the
checker straight into a newly-declared `Stop` hook in this proposal.**
Rejected — mirrors the exact reasoning #318/#320 already recorded for
their own checkers: hook *declaration* is general orchestrator-output
enforcement, which is #298's stated subject, and two more issues
independently reasoning their way to the same conclusion (checker now,
wiring deferred) is the correct shape to keep, not diverge from. Chosen:
add the run.md instruction (so an orchestrator reading its own spec is
told to state the delta — the exact mechanism #373's instance shows is
*necessary but not sufficient*) plus a pure function
`proposal_delta_check.py` that #298's eventual `Stop` wiring can call
against `last_assistant_message`, the same dependency-handoff shape
`approval_request_check.py` already established for #318.

## What will be done

1. **`on-the-record/commands/run.md`, step 5** — add one new bullet
   under "1단계 승인 요청 시": if the proposal file being relayed
   contains a `## Delta` section whose content is not `없음`, the
   approval-request message must state the delta explicitly (what the
   issue asked, what this proposal delivers, which issue tracks the
   remainder) and must not use the same bare "승인할까요?" framing a
   full-scope proposal gets. Placed alongside the existing four-item
   requirement, not folded into it — a delta is an additional axis, the
   same way flow/stage/next (#54) sits alongside rather than inside the
   four items.
2. **`on-the-record/hooks/proposal_delta_check.py`** — two pure
   functions, no I/O, no hook registration (mirrors
   `approval_request_check.py`'s shape exactly):
   - `check_proposal_delta(proposal_text: str) -> DeltaResult`: detects
     a `## Delta` heading; if present and not `없음`/`none`, extracts
     whether an `#<n>` issue reference exists in that section.
   - `check_relay_states_delta(proposal_text: str, relay_text: str) ->
     RelayResult`: given a proposal with a non-`없음` Delta and a
     candidate orchestrator relay message, flags whether the relay text
     itself names the delta (marker-phrase match, same technique
     `approval_request_check.py` uses for its six items). Consumable by
     #298's future `Stop` handler the same way #318's checker is.
3. **`gates/ci.py`** — add `_delta_remainder_mismatch(repo, pr, issue)`:
   reads the phase-1 proposal file(s) touched by the PR
   (`docs/issue-<n>/proposals/*.md` in the PR's diff), and for any with
   a `## Delta` section not equal to `없음`, requires an `#<n>` issue
   reference inside that section. Wired into `check()` under a new
   `--delta-only` mode (mirrors the existing `--closes-only` mode's
   narrow-scope reasoning documented in `check()`'s own docstring) so it
   runs independently of the Closes gate and doesn't inherit its
   unrelated write-scope checks.
4. **`.github/workflows/proposal-delta-gate.yml`** — new required-status
   workflow, structurally identical to
   `.github/workflows/plan-aware-closes-gate.yml` (checkout `main`,
   `python3 gates/ci.py . --pr "$PR_NUMBER" --autodetect --delta-only`),
   with the same branch-protection caveat stated explicitly in the
   workflow's own comment (registering it as a required check is a
   separate Settings action, not something this PR can do).
5. **`test_run_md_delta_shape.py`** — asserts the new run.md bullet's
   marker phrases are present; fails the moment a future edit drops
   them (same pattern as `test_run_md_shape.py`).
6. **`test_proposal_delta_check.py`** — fixtures: a proposal with no
   Delta section, one with `## Delta\n없음`, one with a Delta and a
   remainder `#N`, one with a Delta and no `#N` (must flag); a relay
   message that states the delta and one that doesn't (for
   `check_relay_states_delta`).
7. **`gates/test_delta_gate_ci.py`** — mirrors
   `gates/test_closes_gate_ci.py`'s shape: a synthetic proposal file
   with no Delta section passes (nothing to check when the section is
   absent — see Out of scope), one with `## Delta` and no remainder
   `#N` fails, one with `## Delta` and a remainder reference passes.

## Out of scope

- **Whether a reduced proposal requires a distinct approval token from a
  full-scope one (#373 scope item 2).** Left to the operator, per
  Rationale — this proposal only makes the delta visible before any
  approval, distinct token or not.
- **Requiring `## Delta` to exist on every proposal, including ones with
  no reduction.** The gate in step 3 only fires when a `## Delta`
  section is *present*; it does not require every proposal to carry one.
  A proposal with no `## Delta` section at all is not flagged by this
  gate — stated explicitly because the honest ceiling here is real: this
  proposal does not build a mechanism that forces every future proposal
  author to declare "no delta" the way `record-shape-directive`'s
  "`## What did not work`, present even when empty" pattern does for
  records. That stronger, always-required shape is exactly what an
  authoring-time hook could enforce, and per Constraints this repo does
  not own that surface. Recorded as the honest gap, not silently
  narrowed into "the same thing."
- **Semantic verification that a stated delta accurately reflects the
  issue's real requirement**, or that a linked remainder issue actually
  covers the missing part. Presence-and-pattern only; see Rationale.
- Declaring or wiring `hooks.json`'s `Stop` key — #298, per the
  first-declares/second-appends protocol #318/#320 already set.
- Retroactively adding `## Delta` sections to any already-merged or
  currently-open proposal (including #318's/#320's own).

## How you'll know it worked

`python3 -m pytest test_run_md_delta_shape.py test_proposal_delta_check.py gates/test_delta_gate_ci.py -q`
passes. `test_run_md_delta_shape.py` fails the moment `run.md` loses the
new delta-relay marker phrases. `test_proposal_delta_check.py` fails if
either pure function stops correctly classifying its fixtures, including
the no-remainder-reference case. `gates/test_delta_gate_ci.py` fails if
`_delta_remainder_mismatch` stops blocking a PR whose touched proposal
has a non-`없음` `## Delta` section with no `#<n>` remainder reference.

**Ceiling, stated per #373's own requirement:** none of these check that
a stated delta is *true* to the issue, that a linked remainder issue is
a *good* description of the gap, or that a proposal without any
`## Delta` section genuinely has no reduction rather than an
undeclared one. What is checked, mechanically, on every PR touching a
phase-1 proposal: if a delta is declared, a remainder issue must be
named (item 3, reusing #310's shape); if `run.md`'s instruction text
that the orchestrator must state a declared delta is edited away, a test
fails (item 4's necessary-but-not-sufficient half — it checks the
*instruction* survives, the same limitation #373's own instance names
for the six-item check, not the live relay). The live-relay check
(`check_relay_states_delta`) exists and is tested as a pure function but
is not wired to run automatically on every orchestrator turn until #298
declares `Stop` — stated here rather than implied as closed.
