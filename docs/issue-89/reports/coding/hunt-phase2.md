---
proposal: docs/issue-89/proposals/coding.md
---

# Hunt record — issue-89 phase 2 (fail_closed_downgrade)

## after-proposal — stance: fail_closed_downgrade's "new_commit" signal is HEAD-comparison, not commit-creation

Verdict: FINDING — `new_commit` in `_spawn_one` is computed as `after_head != before_head`
(spawn.py:1773), which is true for *any* HEAD movement, including a plain
`git checkout <other-existing-branch>` that lands on a pre-existing commit. A
session that self-reports "progressed", creates zero new commits, but ends
the turn checked out on a different branch/commit than it started on (e.g. by
switching to an unrelated pre-existing branch, or resetting to an older
ancestor commit that differs from `before_head`) passes the `new_commit`
check and slips through `fail_closed_downgrade()` untouched — exactly the
false "progressed" claim the fail-closed guard exists to catch.
Kind: design-error
Seed: commit 351007c, spawn.py fail_closed_downgrade() / _git_head() / the
`new_commit = issue is not None and after_head is not None and after_head != before_head`
line wired into _spawn_one before wakes.consume()/ledger_write().

### Reproduce
```python
import subprocess, tempfile, os, importlib.util
spec = importlib.util.spec_from_file_location("spawn", "spawn.py")
spawn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(spawn)

td = tempfile.mkdtemp()
def git(*a):
    return subprocess.run(["git", "-C", td, *a], capture_output=True, text=True, check=True)

git("init", "-q")
git("config", "user.email", "t@t.t")
git("config", "user.name", "t")
open(os.path.join(td, "a.txt"), "w").write("x")
git("add", "a.txt"); git("commit", "-q", "-m", "init")
init_branch = subprocess.run(["git", "-C", td, "symbolic-ref", "--short", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
git("checkout", "-q", "-b", "other")
open(os.path.join(td, "b.txt"), "w").write("y")
git("add", "b.txt"); git("commit", "-q", "-m", "pre-existing unrelated commit")
git("checkout", "-q", init_branch)

before_head = spawn._git_head(td)          # captured as before_head in _spawn_one
git("checkout", "-q", "other")             # the "session" makes NO new commit —
                                            # it only switches to a pre-existing branch
after_head = spawn._git_head(td)           # captured as after_head in _spawn_one

new_commit = after_head is not None and after_head != before_head
print("new_commit:", new_commit)
print(spawn.fail_closed_downgrade("progressed", 3, [], new_commit, []))
```

### Observed
```
new_commit: True
progressed
```
`fail_closed_downgrade` leaves the self-reported "progressed" outcome
untouched even though the session's workspace committed nothing new this
turn — `wakes.consume()` and `ledger_write()` then record the false
"progressed" claim, which is precisely the failure mode the phase-2 guard
was added to close.

### Expected
`new_commit` should reflect "this session created a commit that did not
exist in the workspace before the session started," e.g. by checking that
`after_head` is a descendant of `before_head` (`git merge-base --is-ancestor
before_head after_head`) rather than merely `!=`. A checkout to an unrelated
pre-existing commit/branch is not evidence of new work and should still be
demoted to `failed-no-commit`.
