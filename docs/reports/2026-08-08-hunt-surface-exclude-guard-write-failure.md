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

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `except OSError` around the exclude-write guard (spawn.py issue_workspace) does not catch `UnicodeDecodeError` raised by `ex.read_text()`, so a pre-existing non-UTF-8 `.git/info/exclude` crashes the spawn with an unhandled traceback instead of emitting the new "빠진 항목" stderr warning — the new warning path is silently bypassed by a raw exception escaping the try block entirely.
Kind: composition
Seed: spawn.py issue_workspace, lines ~2974-2987 (the newly-narrowed `except OSError as e:` block around the `.git/info/exclude` write)
cap_seconds: 120
tier: default
diff_stat_lines: spawn.py +28/-22, test file +20/-10
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:02:00Z

### Reproduce
```
python3 - <<'PY'
import tempfile
from pathlib import Path
d = Path(tempfile.mkdtemp())
git_dir = d / ".git" / "info"
git_dir.mkdir(parents=True)
ex = git_dir / "exclude"
ex.write_bytes(b"\xff\xfe garbage \x80\x81")  # non-UTF-8 pre-existing content
try:
    ex.read_text()  # this is exactly what spawn.py's issue_workspace() calls at line 2977
except Exception as e:
    print("EXCEPTION TYPE:", type(e).__name__, e)
    print("is OSError subclass:", isinstance(e, OSError))
PY
```

### Observed
```
EXCEPTION TYPE: UnicodeDecodeError 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte
is OSError subclass: False
```
`UnicodeDecodeError` is not caught by `except OSError as e:` at spawn.py:2984, so if `.git/info/exclude` in a workspace already contains non-UTF-8 bytes (e.g. leftover from a prior tool, another locale, or partial binary corruption), `ex.read_text()` at line 2977 raises `UnicodeDecodeError` which propagates out of `issue_workspace()` uncaught — no warning is printed, and the whole spawn crashes with a raw traceback instead of degrading gracefully with the intended stderr message.

### Expected
The write-failure guard's whole point (per the proposal) is to surface every credential-leak-guard write failure via a warning instead of failing silently/uncaught. A decode failure on the existing exclude file is exactly this class of failure — the except clause should catch it (or the read should be tolerant, e.g. `errors="replace"` as used elsewhere in spawn.py, e.g. line 1044/1156) so the same warning path fires instead of an unhandled `UnicodeDecodeError` escaping the function.
