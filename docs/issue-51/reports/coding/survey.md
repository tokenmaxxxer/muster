# Survey — issue #51: clean deletes workspaces of still-running sessions

## Mechanism confirmed

`spawn.py clean` (spawn.py:1299-1326) iterates every git-checkout directory
under the work base (`MUSTER_WORK_DIR` or `~/.tokenmaxxxer/work`) and deletes
any whose git status is clean (`git status --porcelain` empty) and has no
commits ahead of its remote (`git log --branches --not --remotes` empty).
That is the *only* judgment it makes — it never looks at whether a session
is currently running against that workspace.

Separately, `spawn.py` already maintains a live-session roster (PR #28,
spawn.py:940-1014):

- `ROSTER = ROOT / "runs" / "active.json"`, a `{key: entry}` JSON map.
- `_spawn_one` registers an entry before starting the child process
  (spawn.py:1614-1623): key = `f"issue-{issue}/{role}"`, entry contains
  `pid`, `role`, `issue`, `ts`, `work` (the workspace path passed as `cwd`),
  `log`.
- The entry is removed via `roster_remove(roster_key)` right after the
  child process exits (spawn.py:1640), in the `try/finally` around the
  subprocess — so a live entry's `pid` is genuinely still running (barring
  a hard crash of spawn.py itself, which `_alive()` — spawn.py:956-961,
  `os.kill(pid, 0)` — already handles by treating unreachable pids as dead).
- `roster_ps()` (spawn.py:976-996) already contains the exact liveness
  check clean needs: load roster, for each entry check `_alive(pid)`,
  and prune dead entries.

`clean`'s workspace path (`w`, a `Path` under `wb`) is directly comparable
to a roster entry's `"work"` field — both are the same `cwd` string passed
into `issue_workspace()` / `_spawn_one`. No new bookkeeping is needed;
`clean` just never reads `ROSTER`.

## Confirmed cause

`clean` judges only preserved-work state (uncommitted/unpushed commits) and
never consults `runs/active.json`. A workspace with a clean git tree but an
actively running role session (mid-edit, about to commit) gets deleted out
from under it — matching the observed symptom (session dies mid-work, or
recreates a partial non-git dir that then blocks the next spawn with
"destination path already exists and is not an empty directory").

## Existing test coverage

`test_spawn.py` has no tests for `clean` or for the roster functions
(`roster_register`/`roster_remove`/`_alive`/`roster_ps`) at all — this is
net-new test surface, not a regression in an existing test.
