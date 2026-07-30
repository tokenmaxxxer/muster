---
proposal: docs/issue-114/proposals/coding.md
---

# Hunt record — issue-114-event-exit-spawn

## after-proposal — stance: hunt composition regressions / silent-failure at the fork boundary

Verdict: FINDING — the bounded `claude` subprocess (Popen at spawn.py:2112-2115) never redirects `stderr`, so it inherits fd 2 straight through the `os.fork()`/`os.setsid()` chain from the original CLI invocation; any caller that captures spawn.py's own stdout/stderr via a pipe (the normal way an orchestrator wraps a CLI subprocess) will have that pipe's write end held open by the detached grandchild for the full session duration, so reading to EOF blocks for the whole run — defeating the entire point of bounded/`--stall-timeout` early return.
Kind: composition
Seed: `_spawn_one`'s fork-before-Popen restructuring (spawn.py `os.fork()` at line ~2106, `os.setsid()` at 2111, `subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, ...)` at 2112-2115 — no `stderr=` kwarg).

### Reproduce
Standalone repro isolating the exact fd-inheritance shape spawn.py uses (fork -> parent returns fast -> child setsid()s -> child Popen's a long-running subprocess without touching stderr):

```
# child.py (mimics spawn.py's bounded _spawn_one shape)
import os, subprocess, sys
child_pid = os.fork()
if child_pid > 0:
    print("parent: returning bounded", file=sys.stderr)
    sys.exit(0)
os.setsid()
proc = subprocess.Popen(["sleep", "5"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)  # no stderr= — same as spawn.py:2112-2115
proc.wait()
os._exit(0)

# orchestrator.py (mimics a caller invoking spawn.py as a subprocess, e.g. drive-from-outside or a wrapper)
import subprocess, time
t0 = time.time()
p = subprocess.Popen(['python3', 'child.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = p.communicate()
print('communicate() returned after %.2fs' % (time.time() - t0))
print('stdout:', out, 'stderr:', err)
```

Run: `python3 orchestrator.py`

### Observed
```
communicate() returned after 5.02s
stdout: b'' stderr: b'parent: returning bounded\n'
```
`communicate()` blocks for the full 5s of the detached grandchild's lifetime, even though the "parent" (bounded-return) branch exited in milliseconds. The grandchild (`sleep 5`, standing in for the `claude` role process) holds the caller's stderr pipe open because it was never redirected/closed across the fork+exec.

### Expected
Since the whole design intent of `bounded=True` (issue #114) is that the CLI call returns as soon as `_await_bounded()` sees an event or hits the stall timeout, a caller that pipes spawn.py's stdout/stderr (which is the ordinary way to invoke a CLI as a subprocess and capture its output) should get that return back promptly. Instead, because `subprocess.Popen` for the role's `claude` process at spawn.py:2112-2115 does not set `stderr=subprocess.PIPE` (or otherwise close/redirect inherited fds after fork), the detached grandchild keeps the caller's original stderr pipe open for the entire session, silently reintroducing the exact unbounded-block behavior the fork/watch split was built to remove — with no error or log line indicating why the caller's read never completes.
