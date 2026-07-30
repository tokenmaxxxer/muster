---
proposal: docs/issue-115/proposals/coding.md
---

# Hunt record — scope-approval-interface

## after-proposal — stance 1: silent-failure

Verdict: FINDING — a failed `git add`/`git commit` after a successful approval leaves the record file mutated to `loop_state: scope-approved` on disk; any later invocation hits the idempotency guard and returns 0 with a success message, even though no commit was ever made.
Kind: silent-failure
Seed: spawn.py `approve_scope()` (search `def approve_scope`) and its `approve-scope` CLI dispatch in `main()`.

### Reproduce
In `spawn.py` (lines ~846-879 of the version under review):

```python
record_path = root / BOARD / subject / "reports" / f"{front}.md"
fm = frontmatter(record_path)
state = fm.get("loop_state")
if state == "scope-approved":
    print(f"이미 scope-approved 다: {record_path}")
    return 0                      # <-- decided purely from the file, not git
...
new_text = re.sub(r"(?m)^loop_state:.*$", "loop_state: scope-approved", text, count=1)
record_path.write_text(new_text, encoding="utf-8")   # <-- disk write happens FIRST

rel = str(record_path.relative_to(root))
subprocess.run(["git", "-C", str(root), "add", rel], check=True)     # can raise
subprocess.run(["git", "-C", str(root), "commit", "-m", ...], check=True)  # can raise
print(f"...scope-approved 로 올리고 커밋했다 ...")
return 0
```

There is no try/except around the two `subprocess.run(..., check=True)` calls, and no
rollback of `record_path` if either raises. `git add`/`git commit` can fail for
mundane operational reasons after the write already landed: missing
`user.name`/`user.email`, a rejecting pre-commit hook, a held index lock, a full
disk, etc. — none of which are exotic.

Confirmed the idempotency branch is driven solely by on-disk frontmatter state
(not by git log/status) by running the repo's own test for it:

```
$ python3 -m unittest test_approve_scope.ApproveScope.test_already_approved_is_idempotent -v
test_already_approved_is_idempotent (test_approve_scope.ApproveScope) ... ok
----------------------------------------------------------------------
Ran 1 test in 0.003s
OK
이미 scope-approved 다: (a report record path under some subject's reports dir)
```
That test seeds a record with `loop_state: scope-approved` directly (no commit
involved) and `approve_scope()` still returns 0 — proving the check never
consults git.

I attempted to run the full combined scenario live (mock a matching approver
comment, force the `git commit` subprocess call to fail, then call
`approve_scope()` a second time to observe the idempotent 0-return) with a
scratch script under `$TMPDIR`, using the same monkeypatch technique as
`test_approve_scope.py` itself (patching `spawn._issue_comments`,
`spawn._pr_for_branch`, `spawn._repo_slug`, `spawn.subprocess.run`). Every
variant of that specific combined script was denied by the sandbox's
permission system before execution (`Permission to use Bash/Write has been
denied`), even though the individual pieces (writing scratch files, running
`git init`, importing and monkeypatching `spawn`, running the existing
idempotency test unmodified) each worked in isolation. I did not attempt to
bypass those denials. The finding stands on direct code reading (the
write-before-commit ordering and unguarded `check=True` calls are unambiguous
from the source) plus the live-verified fact that the idempotency check reads
only the file, established by the unmodified test run above.

### Observed
- The file write (`record_path.write_text`) happens unconditionally before the
  git operations that are supposed to persist it.
- The idempotency short-circuit (`state == "scope-approved"` -> `return 0`)
  consults only `frontmatter(record_path)`, never `git status`/`git log`.
- A `CalledProcessError` from either `git add` or `git commit` is unhandled,
  so it propagates as an uncaught exception on the *first* call (visibly
  non-zero) — but the file is already corrupted into "approved" state by
  then. The *next* call to `approve_scope` for the same subject will exit 0
  and print the "already approved" line, which is indistinguishable from a
  genuine, committed approval.

### Expected
`approve_scope()` should not treat "the file says scope-approved" as proof of
completion; it should verify the promotion actually landed in git (e.g. that
`record_path` is clean per `git status --porcelain` and/or that HEAD contains
a commit touching it) before short-circuiting with success, or it should wrap
the `git add`/`git commit` calls so that a failure reverts the file write
rather than leaving a dangling on-disk state that later reads as "already
approved."
