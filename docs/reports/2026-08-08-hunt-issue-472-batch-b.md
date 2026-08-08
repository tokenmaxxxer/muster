---
proposal: docs/issue-472/proposals/2026-08-08-batch-b-proposal-content-shape-gates.md
---

# Hunt record — issue-472-batch-b

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — "must not touch Batch A's {362, 390, 412} entries" constraint has zero mechanical enforcement: `t_class_b_disposition_rows_cited` iterates `_ISSUE_467_BATCH_A_CITATIONS` as it exists at run time, so silently deleting a Batch A key (or repointing it to any other existing file) still passes.
Kind: silent-failure
Seed: docs/issue-472/proposals/2026-08-08-batch-b-proposal-content-shape-gates.md (proposal, docs-only), citing gates/test_boundary.py's `_ISSUE_467_BATCH_A_CITATIONS` dict and `t_class_b_disposition_rows_cited` (state added by Batch A, commit 9554c53)
cap_seconds: 120
tier: default
diff_stat_lines: 2 files changed, ~242 lines (docs-only proposal diff vs origin/main)
started_at: 2026-08-08T09:44:36Z
ended_at: 2026-08-08T09:59:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-472-implementation
python3 - <<PYEOF
src = open("gates/test_boundary.py", encoding="utf-8").read()
old = '_ISSUE_467_BATCH_A_CITATIONS = {\n    362: ROOT / "gates" / "test_boundary.py",\n    390: ROOT / "gates" / "test_merge_state_gate.py",\n    412: ROOT / "on-the-record" / "hooks" / "test_self_update_shallow.py",\n}'
new = '_ISSUE_467_BATCH_A_CITATIONS = {\n    390: ROOT / "gates" / "gates.py",\n    412: ROOT / "on-the-record" / "hooks" / "test_self_update_shallow.py",\n}'
open("gates/test_boundary.py", "w", encoding="utf-8").write(src.replace(old, new))
PYEOF
python3 gates/test_boundary.py
# entry for #362 is now gone entirely, and #390's citation has been
# repointed from test_merge_state_gate.py to gates.py
```
(then restore with `git checkout -- gates/test_boundary.py`)

### Observed
```
ok - t_class_b_disposition_rows_cited
...
11/11 passed
```
The test suite is fully green even though #362's citation was deleted and #390's was repointed away from its real test file — exactly the edit the proposal's own constraint text says a Batch B diff "must not" make.

### Expected
`t_class_b_disposition_rows_cited` (or a companion assertion the Batch B proposal should add alongside its own {318, 363, 379} additions) would need to pin the Batch A keys/paths as a fixed baseline — e.g. assert `_ISSUE_467_BATCH_A_CITATIONS[362] == ROOT / "gates" / "test_boundary.py"` etc. — so that removing or repointing a prior batch's citation actually fails the gate. As written (and as the proposal plans to leave it, since its "What will be done" section only describes adding three new keys, not adding any such pin), the "additions only, don't touch Batch A's entries" rule is enforced by nothing but implementer discipline; the test that is supposed to be the mechanical backstop for the disposition table cannot detect this exact regression class.
