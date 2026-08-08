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

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: NO FINDING
Seed: staged diff — gates/approval_request_shape.py (missing_approval_clauses, has_generator_section), gates/open_work.py (build_open_work_query), gates/test_boundary.py citation rows, docs/specs/enforcement-boundary.md, on-the-record/UNENFORCED-CLAUSES.md, on-the-record/commands/run.md new section
cap_seconds: 180
tier: default
diff_stat_lines: 304 insertions(+), 3 deletions(-) across 9 files
started_at: 2026-08-08T18:57:52+09:00
ended_at: 2026-08-08T19:00:30+09:00

Checked candidate pairs for cancellation:
- `gates/approval_request_shape.py::missing_approval_clauses` vs the live `on-the-record/hooks/stop-gate.sh` heredoc it was ported from — the docstring itself flags future-drift risk between the two copies, but as staged the three regexes (`ISSUE_RE`/`CHANGE_RE`/`RISK_RE`) are byte-identical between the two files, confirmed by direct diff read. No divergence exists yet, so no cancellation to reproduce today.
- `gates/open_work.py::build_open_work_query` vs `gates/landing_readiness.py`'s existing `gh issue/pr list` usage — different concerns (open-work lookup vs per-PR landing classification), no overlapping verdict space.
- New gates are not wired into `gates/gates.py`'s dispatcher (grep confirms zero references outside their own modules/tests), and are explicitly documented as `contract, CI-supplement`/non-blocking in both `docs/specs/enforcement-boundary.md` and `on-the-record/UNENFORCED-CLAUSES.md` — same disposition already used for `landing_readiness.py`, not a new contradiction.
- `on-the-record/hooks/deliverable-guard.sh`'s `docs/` write-tree deny vs this delivery's own writes to `docs/specs/enforcement-boundary.md` — guard exits 0 immediately whenever `CLAUDE_ROLE` is set (role/subagent session), which is the session type that would actually author these files, so no live cancellation reproduced.
- Ran `missing_approval_clauses` directly against a realistic approval message ("requesting approval for issue-472: added new gates. Risk considered: none.") — it under-matches (misses issue ref and change statement) because of the narrow regexes, but this is the same behavior `stop-gate.sh` already has (identical regex, pre-existing), not something this change newly cancels.

No pair of already-shipped rule and this change's new gate/rule was found to structurally cancel or contradict each other with a runnable repro.
