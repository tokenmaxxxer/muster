---
proposal: docs/issue-89/proposals/coding.md
---

# Hunt record — coding

## after-proposal — stance 1: fail-closed downgrade (progressed + no commit -> FAILED) vs. blocked-gate honesty

Verdict: FINDING — the proposed downgrade rule is gated on `outcome == "progressed"`, but `classify()` already discards a non-empty `blocked` signal whenever `delta` is non-empty (delta is checked before blocked at spawn.py:968-971), so a session that both touched the board and hit a human gate — but had not yet committed — will be classified "progressed" today and would be silently mislabeled FAILED under the proposed rule, exactly the "honest blocked report" case the proposal says it must not treat as failure.
Kind: composition
Seed: docs/issue-89/proposals/coding.md proposal (2): post-exit fail-closed verification at spawn.py ~1731-1748, downgrading self-reported "progressed" outcomes to FAILED when no new git commit landed, composed against classify() at spawn.py:951-974.

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-89-coding
python3 -c "import spawn; print(spawn.classify(0, {}, ['somefile.md'], ['blocked-line-1']))"
```

### Observed
```
progressed
```
`blocked` (a non-empty list representing an open human gate per `wakes.evaluate`) is passed but ignored because `delta` is checked first and returns immediately at spawn.py:968-969. The `blocked` branch at spawn.py:970-971 is unreachable whenever the board also changed.

### Expected
If a session left a board delta *and* a human gate is still open (`blocked` non-empty), and the proposal's new git-commit check finds no new commit, the outcome should resolve to "waiting-on-human" (or at least not silently collapse into "FAILED") — not be downgraded from "progressed" straight to "FAILED" with no visibility into the fact that a legitimate blocking gate was standing. As currently scoped, the downgrade only consults `outcome == "progressed"` and the commit check; it never re-examines `blocked`, so this case is invisible in the new code path exactly as it already is invisible in `classify()` today — the fix compounds an existing gap instead of closing it.
