---
proposal: docs/issue-471/proposals/2026-08-08-batch-a-merge-state-integrity-gates.md
---

# Hunt record — issue-471-batch-a

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `t_gates_docstring_states_retroactivity_rule` (the proposed #362 check) is a pure docstring-string-presence assertion; it can be satisfied by pasting the rule sentence into `gates/gates.py`'s docstring while `gates.py`'s actual enforcement logic still violates the retroactivity rule, so the check passes with the underlying property still broken.
Kind: design-error
Seed: docs/issue-471/proposals/2026-08-08-batch-a-merge-state-integrity-gates.md (docs-only diff, new file, plus docs/issue-471/reports/implementation/survey.md)
cap_seconds: 60
tier: default (docs-only)
diff_stat_lines: 2 new files (docs-only)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:05:00Z

### Reproduce

The proposal's own text for this row (`## What will be done`) states the entire
mechanism: "Add `t_gates_docstring_states_retroactivity_rule`: asserts
`gates/gates.py`'s docstring contains the #362 rule text added above." No
runtime behavior of any gate is exercised — the check is over static prose.
Since the target files (`gates/gates.py` addition, `test_boundary.py`
function) don't exist yet, the bypass is demonstrated with a standalone
script implementing exactly the described check shape (string-containment
assertion) plus a stand-in for gates.py's actual retroactivity-relevant
logic, showing the two are independent:

```
python3 demo_check.py
```
(script contents: a docstring containing the rule sentence verbatim, a
`t_gates_docstring_states_retroactivity_rule`-equivalent function asserting
`RULE_TEXT in doc`, and a separate `gate_check_retroactivity(...)` function
representing what `gates.py` actually does when it evaluates an artifact —
which fails an artifact authored before the rule existed, i.e. violates the
rule itself.)

### Observed

```
t_gates_docstring_states_retroactivity_rule: PASS (docstring contains rule text)
artifact authored BEFORE rule existed, now fails the newly-added rule -> FAIL
```

The gate reports PASS while the artifact-level retroactivity guarantee it is
supposed to certify is simultaneously violated (`gate_check_retroactivity`
returns FAIL for an artifact that could not have known about the new rule
at authoring time). The check's own docstring-text edit and the underlying
enforcement code are two disconnected pieces of state; the proposal never
ties the assertion to any behavior of `gates.py`'s actual check functions
(e.g. a synthetic pre-rule artifact run through the real gate and asserted
to still pass). Only the sentence needs to exist somewhere in the module
docstring for the gate to go green.

### Expected

A gate meant to guarantee #362's property ("a check must not retroactively
invalidate an artifact that complied when authored") should exercise that
property against `gates.py`'s actual check behavior — e.g. construct or
reference a case where a rule changed after an artifact was authored and
assert the artifact still passes — not merely assert a sentence describing
the property is present in a docstring, which can be true independent of
whether any code obeys it.
