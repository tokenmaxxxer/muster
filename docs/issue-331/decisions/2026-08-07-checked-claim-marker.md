# `checked:` / `## Acceptance verification` marker convention

Subject: issue-331

## Decision

A phase-2 record that sets its role's terminal `loop_state` (the last
value in `roles/<role>.json`'s `record_fields.loop_state` list) must
carry a `## Acceptance verification` section, one line per criterion:

```
- <criterion excerpt> — checked: <target> — result: pass|fail|unverifiable[: <reason>]
```

`<target>` is one of:
- `path::test_name` — a test node ID. `gates/gates.py:record_checked_claims`
  verifies the named `def test_name` exists in `path` by parsing, not
  executing, the file.
- any other string — read as a CI check name. `gates/ci.py` cross-checks
  it against `gh pr view --json statusCheckRollup` for a successful
  entry (`conclusion`/`state` == `SUCCESS`).

`result: unverifiable` requires a non-empty `<reason>` after the colon
(per #310: an unverifiable criterion must say so and say why, and that
declaration satisfies the check for that one item).

Absence of the section entirely, on a record that declares the
terminal `loop_state`, is a denial — this is mandatory, not opt-in
(unlike `fulfils:`, issue #155), because reaching the terminal state is
exactly the unchecked claim #331 exists to close.

## Rationale

Considered re-running the named test/command inside the gate so the
gate's own execution is the evidence. Rejected: `gates/gates.py` is
pure and diff-only by design, and executing an arbitrary string pulled
from record prose inside a PreToolUse hook or CI job is a
command-injection surface — see
`docs/issue-331/proposals/checked-claims-gate.md`'s Rationale section
for the full argument. Existence-checking a test node ID (falsifiable
without execution) and cross-checking an independently-already-run CI
result give mechanical falsifiability without adding an execution
surface.

## Terminal value derivation

`roles/<role>.json` does not mark which `loop_state` value is terminal
explicitly. Surveyed role definitions consistently order the list as a
progression (`implementation`: scope-proposed → scope-approved →
in-progress → landed; `technical-feasibility`: measuring → verdict;
`defect-verification`: a single-element list, `cleared`), so the last
element of the declared list is read as the terminal value. A role
definition with no `record_fields.loop_state` declared at all is left
untouched by this gate (no terminal value to check against).
