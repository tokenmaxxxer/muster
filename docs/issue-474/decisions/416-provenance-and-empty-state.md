# Provenance and empty-state fields — presence, not truth (#416, delivered in Batch D/#474)

`gates/acceptance_gate.py::check_issue_body` now requires, on any `##
Acceptance` section that references an executable artifact and is not
already exempted by `unverifiable:`:

- `empty state: <path or description>` (or `empty state: not applicable
  — <reason>`)
- `provenance: executed-live` | `provenance: executed-unit` | `provenance: read`

Both are **presence checks, not truth checks**. The gate cannot verify
that the named test file actually exercises the empty state, or that a
claim marked `executed-live` really was executed live rather than typed
in after the fact. It can only make the claim type visible and greppable
— per #310's own standard, prose does not discharge a requirement; a
mechanically-checkable field does more than prose, but not as much as
running the thing.

## Which of #416's four "what needs deciding" items this answers

1. **Whether a behavioral claim must state how it was verified, and
   whether reading may discharge it** — partially. The field is now
   required and mechanical (`executed-live`/`executed-unit`/`read`), so
   the claim type is no longer invisible. Whether `provenance: read`
   should be *banned* for behavioral claims is left open — this gate
   makes the read-vs-executed distinction visible, it does not resolve
   the policy question of whether reading is ever sufficient.
2. **Whether empty/initial state is a required, checkable member of an
   acceptance corpus** — yes, required and checkable at presence level.
   The gate does not check that the referenced fixture is *actually* an
   empty-state fixture.
3. **The setup-step-failure finding** — yes, checkable;
   `gates/test_setup_failure_propagates.py` builds a synthetic harness
   shaped like `tests/run-orchestrate-tests.sh`'s setup step and asserts
   a broken setup step makes the harness's own exit code nonzero.
4. **Orchestrator briefs requiring execution** — deferred, out of scope.
   No distinct "brief" artifact exists in this repo separate from the
   directives already governing a role session; attaching a second copy
   of the same field with no attachment point would be speculative.

## Placement note

The #416 proposal's own write set names
`docs/issue-416/decisions/provenance-and-empty-state.md` as this file's
path. `board-gate.sh` (contract v3 s10) mechanically refuses any
`docs/issue-416/**` write from the `issue-474/implementation` branch this
delivery runs on — a role writes another issue's docs tree only from that
issue's own branch. This file is the substitute, living under Batch D's
own issue-474 tree instead; see `docs/issue-474/reports/implementation.md`
"Rationale for deviations" for the mechanical reason.
