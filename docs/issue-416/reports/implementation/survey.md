# Survey — issue-416

Scope: this repo (`on-the-record`) is the gates/orchestrator project itself,
not the sibling gitstore project the incident happened in. #416's two
findings are about mechanisms this repo can build: a gate that checks issue
text/records, not the sibling's Go code.

## Existing acceptance/provenance machinery

- `gates/acceptance_gate.py` (issue-310): requires an issue's `## Acceptance`
  section to name an executable artifact (backticked `test/`, `gates/`,
  `.github/workflows/` path, or a `gate:`/`check:` line) or an explicit
  `unverifiable: <reason>` escape. Pure `check_issue_body(issue, body)`,
  network-free, unit-tested in `gates/test_acceptance_gate.py`. This is the
  natural extension point for #416 finding 2 — it already parses the
  Acceptance section and already has an escape-hatch pattern
  (`unverifiable:`) to model a new `empty state:` / `provenance:` field on.
- `gates/skip_gate.py` (issue-334): distinguishes "ran and skipped" from
  "ran clean" by parsing pytest's `-ra` skip summary — adjacent to #416
  finding 1 (distinguishing claim types) but a different axis (skip vs pass,
  not read vs executed).
- `docs/issue-390/proposals/2026-08-07-merge-state-gate.md` (issue-390): the
  most recent proposal of this shape — re-verification against landing
  state. Its "How you'll know it worked" section is the house style to match:
  build a synthetic failing case (here, a synthetic arity mismatch), assert
  the check fails before the fix and passes after. Also models the required
  honesty move #416 asks for: it states its own gap (mocked-boundary,
  #388-shape) as "not caught, and not mechanically reachable by this
  mechanism" rather than implying full coverage.
- No existing gate anywhere in `gates/` inspects referenced test files'
  *content* for what states they cover — every existing gate reads issue
  prose or pytest's own output, never a target repo's test fixtures. This
  matters for scoping finding 2: this repo cannot mechanically prove a
  sibling repo's test corpus exercises the empty state (it has no access to
  that repo). What it *can* do is require the corpus's own acceptance record
  to declare, as a checkable presence field, that the empty/initial state is
  a named member of the corpus — the same shape `unverifiable:` already
  uses for a different gap.

## Provenance (finding 1) — what's structurally reachable

No field anywhere in this repo's gates or record shapes distinguishes
"read the code" from "ran it." `record-shape-gate.sh` (referenced by the
`record-shape-directive` this session runs under) checks `code_under_review:`
and `loop_state:` frontmatter and a `## What did not work` heading, but
nothing about how a behavioral claim inside the record was produced.
Grepping this repo for any existing `provenance:`-shaped field or gate
inspecting one: none found. This is a genuine gap, not a rename of
something existing.

The issue itself is explicit that a prose record cannot mechanically prove
"I ran it" vs "I read it" — only a structured field's *presence* is
checkable, not its truth. Confirmed by reading `gates/acceptance_gate.py`'s
own docstring, which states the same limit for `unverifiable:`: the gate
checks that the escape hatch is used, not that the claim behind it is
correct. This repo has no mechanism anywhere (gate, hook, CI job) that
verifies a *claim's truth* rather than a *field's presence* — that ceiling
is structural to a text-based gate, not specific to #416.

## Setup-failure-fails-the-run (finding 3)

`tests/run-orchestrate-tests.sh` is the one shell harness in this repo with
a "setup step" shape (the `hooks.json` parse via a `python3 - <<PY` heredoc
before the real assertions run). It already checks `$?` after that step and
increments `fail` on nonzero — not silently swallowed today. But there is
no test *of that property itself*: nothing asserts that if the setup step
were broken, the harness's own exit code would go nonzero. That is exactly
the "deliberately break a setup step and assert the suite goes red" check
#416 asks for, and it is checkable without touching the sibling project:
mutate a throwaway copy of the harness (or a synthetic harness built the
same way) so its setup step fails, run it, assert nonzero exit.

## Orchestrator briefs (finding 4)

`no-mock-directive` and `freelunch-directive`, both active in this very
session (see system reminders), already carry "say runs/works only about
what you actually ran" and "single confirmation run" language — this
matches the issue's own description of "manual compensation... written by
hand into every brief today." Making that durable (moving it from a
per-session directive into a mechanically-enforced field) is the same
provenance-field mechanism as finding 1, applied to briefs specifically.
No separate code surface exists for "briefs" in this repo distinct from the
directives already governing this session — building a second copy of the
same field for briefs specifically, with no distinct enforcement point (no
central place a brief round-trips through), is deferred as speculative
scope, not because it's undesirable.

## Skip condition check

Not applicable — scouting/skip record: this is not a product-shaped
deliverable (it's a repo-internal gate), so per scout-directive it scouts
"the best of the deliverable's own kind" rather than a product category.
That scouting is the existing-mechanism survey above (acceptance_gate,
skip_gate, the #390 proposal as the house exemplar) rather than an external
web sweep — the relevant field is this repo's own established gate
patterns, which is where the strongest prior art for "how do we check this
kind of thing" already lives.
