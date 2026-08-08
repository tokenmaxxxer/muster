---
proposal: docs/issue-492/proposals/2026-08-08-implement-reconciliation-step.md
---

# Hunt record — implement-reconciliation-step

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the proposed `expects_pr` field is a static per-role table lookup (`role in ROLES_THAT_OPEN_PRS`), but the actual PR-opening code path (`ensure_pushed()`, called unconditionally at spawn.py:3799 for every role with `issue is not None`) has no role-based gate at all: it pushes and opens a PR purely based on whether the branch has unpushed commits (spawn.py:3283-3325, `ensure_pushed()`/the PR-open block at 3259+). Any role not in the proposed table can still legitimately open a PR; a session for such a role that crashes or vanishes before pushing would be recorded with `expects_pr=False`, so `reconcile()`'s only PR-divergence rule (`expects_pr true and pr_number is None and session_verdict != "in-progress" → respawn`) never fires and the divergence goes unreported — exactly the silent-failure the reconciliation step exists to close.
Kind: design-error
Seed: docs/issue-492/proposals/2026-08-08-implement-reconciliation-step.md (docs-only diff, 213 lines)
cap_seconds: 180
tier: size:>200
diff_stat_lines: 213
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:03:00Z

### Reproduce
```
grep -n "^ROLES\b" spawn.py            # closed 40-role enum, spawn.py:777
grep -n "def ensure_pushed" spawn.py    # spawn.py:3259
sed -n '3259,3325p' spawn.py            # role never checked to decide whether to push/open a PR
grep -n "ensure_pushed(" spawn.py       # spawn.py:3799 — called for every role when issue is not None
```

### Observed
`ensure_pushed(work, issue, role)` at spawn.py:3799 is invoked unconditionally whenever a spawned session has `issue is not None`, for any of the 40 roles in `ROLES` (spawn.py:777-789), including roles with no obvious PR-opening precedent (e.g. `market-analysis`, `pricing`, `legal-compliance`). Inside `ensure_pushed()`, the only decision is "does the branch have unpushed commits" (spawn.py:3283-3285, `nothing-to-push` vs proceeding to push+PR at 3298-3320) — `role` is passed through only for log/comment text, never for an eligibility check. The proposal's plan computes `expects_pr` once, at dispatch time, from a closed table (`role in ROLES_THAT_OPEN_PRS`), which the proposal itself hedges as possibly needing "an explicit per-role table if roles vary" — i.e. the author already suspects the mapping is not solid.

### Expected
`expects_pr` should reflect the actual runtime capability every role has to open a PR (any role that commits+pushes can trigger `ensure_pushed()`'s PR-open path), not a static subset of roles decided at dispatch time — otherwise a crashed/vanished session from any role outside the table is a `reconcile()` blind spot: `session_verdict` is "crashed"/"stalled" only catches it via rule 1 if the process itself is confirmed dead, but a session that writes a normal `session-end` event without ever pushing (e.g. died just after committing, before `ensure_pushed()`'s host-relay ran) yields `session_verdict="normal"`, `expects_pr=False`, `pr_number=None` — none of `reconcile()`'s stated rules fire, and the divergence is silently dropped exactly as issue-492 was raised to prevent.
