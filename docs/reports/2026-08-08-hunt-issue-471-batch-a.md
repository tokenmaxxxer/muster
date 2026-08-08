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

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: FINDING — `gates.role_scope()` (the pre-existing role/write_scope governance rule) and this Batch A delivery cancel each other: every file this diff needs to touch (`gates/gates.py`, `gates/test_boundary.py`, `gates/test_merge_state_gate.py`, `on-the-record/commands/run.md`, `on-the-record/hooks/self-update.sh`, `on-the-record/hooks/test_self_update_shallow.py`) falls outside `roles/implementation.json`'s `write_scope` (`["src/**", "test/**"]`), and this repo has no `docs/specs/write_scope.md` override to widen it. `gates/ci.py::check()` calls `gates.role_scope(repo, branch)` for any PR check that isn't `--closes-only` (i.e. the normal review path, not just the required-status-check path) — so the very PR that delivers this Batch A work, opened from `issue-471/implementation`, is flagged as scope-violating by its own repo's role gate for every file it ships.
Kind: composition
Seed: gates/gates.py (+4 lines docstring), gates/test_boundary.py (+43), on-the-record/commands/run.md (+22), on-the-record/hooks/self-update.sh (+17), plus new gates/test_merge_state_gate.py, on-the-record/hooks/test_self_update_shallow.py
cap_seconds: 180
tier: size:large
diff_stat_lines: 87 tracked + 2 new files
started_at: 2026-08-08T00:06:00Z
ended_at: 2026-08-08T00:09:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-471-implementation
python3 -c "import sys; sys.path.insert(0,'gates'); import gates; from pathlib import Path; print(gates.role_scope(Path('.'), 'issue-471/implementation'))"
```

### Observed
```
['write_scope 이탈: gates/gates.py (역할 implementation, 허용: src/**, test/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**)',
 'write_scope 이탈: gates/test_boundary.py ...',
 'write_scope 이탈: on-the-record/commands/run.md ...',
 'write_scope 이탈: on-the-record/hooks/self-update.sh ...',
 'write_scope 이탈: gates/test_merge_state_gate.py ...',
 'write_scope 이탈: on-the-record/hooks/test_self_update_shallow.py ...']
```
Confirmed the enforcement path is live (not just the narrow `--closes-only` mode): `gates/ci.py::check()`, when called with `pr is not None` and `closes_only=False` (the default review-time invocation, distinct from the `--closes-only` required-status-check mode carved out for issue #245), unconditionally appends `gates.role_scope(repo, branch)` to the blocking-reason list (`gates/ci.py` around line 460).

### Expected
Either `roles/implementation.json`'s `write_scope` should include the paths this Batch A work is required to touch (`gates/**`, `on-the-record/**`), or a write-scope override should exist widening it for this issue/role — otherwise the role-scope gate and the Batch A deliverable cancel each other: the deliverable cannot land as an `issue-471/implementation` PR without also being flagged as a scope violation by the same repo's own governance rule.
