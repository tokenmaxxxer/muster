---
proposal: docs/issue-450/proposals/2026-08-08-surface-exclude-guard-write-failure.md
---

# Hunt record — surface-exclude-guard-write-failure

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the planned warning only fires on the fresh-clone path; both early-return reuse paths in `issue_workspace()` skip the exclude-guard block entirely, so a workspace whose guard write failed once stays permanently unguarded and unwarned on every later reused spawn.
Kind: silent-failure
Seed: docs/issue-450/proposals/2026-08-08-surface-exclude-guard-write-failure.md (spawn.py's `issue_workspace()`, not yet built)
cap_seconds: 120
tier: default
diff_stat_lines: 0 (proposal doc only so far, no code diff yet)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:15:00Z

### Reproduce
Ran a script that:
1. Monkeypatches `Path.open` to raise `OSError` only for `.git/info/exclude` appends, then calls `spawn.issue_workspace(str(src), issue=99999, role="probe")` once -- the write fails (silently under current code; would print the planned warning under the proposed fix), and the returned workspace `work1` has `.git/info/exclude` missing the guard lines.
2. Restores `Path.open` (the underlying permission problem is now fixed) and calls `spawn.issue_workspace(str(src), issue=99999, role="probe")` a second time with the identical `(cwd, issue, role)`.

```
python3 repro_reuse.py
```

### Observed
```
work1 == work2: True
exclude text after reuse spawn: "# git ls-files --others --exclude-from=.git/info/exclude\n..."
.mcp.json present: False
```
The second call takes the `(work / ".git").exists()` reuse branch (spawn.py around line 2932), or the `src == work.resolve()` branch (spawn.py around line 2929) -- same effect -- which does `_fetch_or_halt` then `return` before ever reaching the exclude-guard try/write block (spawn.py around lines 2964-2983) that the proposal's fix targets. The guard entries (`.mcp.json`, `.gitconfig`, etc.) remain absent from `.git/info/exclude` on this and every subsequent reused spawn for the same issue/role, and -- because the fix as scoped only narrows the `except OSError` inside the fresh-clone branch -- no warning is ever printed for this state, indefinitely, even after the underlying write-permission problem that originally caused the miss is gone.

### Expected
Either the reuse branches should re-check/re-assert the guard entries (and warn if still missing) on every spawn, or the proposal should explicitly flag this gap so "surfaced once on the write that failed, then silent forever afterward on every reuse" isn't mistaken for closing issue #450's silent-failure complaint.
