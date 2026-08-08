---
proposal: docs/issue-476/proposals/implementation.md
---

# Hunt record — implementation

## after-proposal — stance 0: assume the gate just proposed is bypassable — find the bypass

Verdict: FINDING — proposal's own literal scope choice for wiring reexecution_gate into blocking_causes (`{"reason": ..., "scope": {"gates/"}}`, step 3) makes a failed reexecution verdict invisible to `classify()` for any PR whose changed files do not start with `gates/` — i.e. exactly the normal case, since the PR being re-executed is a role's implementation/record PR, not a gates/ change.
Kind: design-error
Seed: docs/issue-476/proposals/implementation.md (H1 item 3: "Wire reexecution_gate's verdict into landing_readiness.py's blocking_causes construction ... a fail/error verdict ... becomes one {"reason": ..., "scope": {"gates/"}}-shaped (or PR-specific scope, decided at implementation time...) entry")
cap_seconds: 120
tier: default
diff_stat_lines: N/A (proposal doc, ~150 lines)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:02:00Z

### Reproduce
Using the existing `classify()` machinery the proposal explicitly says it will reuse unchanged (`gates/landing_readiness.py`), with the scope shape the proposal names literally for the reexecution_gate wiring:

```python
import sys
sys.path.insert(0, "gates")
from landing_readiness import classify

causes = [{"reason": "reexecution_gate: command exited 1", "scope": {"gates/"}}]
pr_files = frozenset(["src/feature.py", "roles/records/476-implementation.md"])
result = classify("OPEN", "pass", True, True, pr_files, tuple(causes))
print(result)
```

### Observed
```
('READY', None)
```
A PR whose role record contains an unreproduced/false claim, and for which `reexecution_gate` produced a `fail` verdict, is classified READY — the blocking cause never fires because `pr_files` (the PR's own record/source changes) don't match the `gates/` scope prefix. `classify()`'s scope semantics (any(f.startswith(tuple(scope)) for f in pr_files)) require the *offending PR itself* to touch `gates/` for the cause to apply to it — but the whole point of H1 is to catch false claims in ordinary role PRs that touch application code and records, not gates/.

### Expected
A `fail`/`error` reexecution verdict for a specific PR's claim should block that PR regardless of which files it touched — the proposal itself flags this as unresolved ("or PR-specific scope, decided at implementation time to match the existing scope semantics") but ships the literal `{"gates/"}` example as the illustrative wiring, and the existing `scope` mechanism has no PR-identity concept (only file-path prefixes) to express "this cause applies to PR #N specifically" without a hack such as adding every one of that PR's own file paths as scope entries (workable, but not what's specified, and not exercised by any test the proposal names).
