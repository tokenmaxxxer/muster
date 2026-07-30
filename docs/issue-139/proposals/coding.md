# issue-139 — build proposal (coding)

references #139

## Request (paraphrased)
`runs/active.json` roster writes (`roster_register`/`roster_remove` in `spawn.py`)
are unlocked read-modify-write; concurrent sessions can clobber each other's
entries, so `ps`/`kill`/`clean` can go blind on a live session. Fix so `ps` never
reports "none running" while a spawned process is alive.

## Constraints
- `runs/` is gitignored working state — no schema/migration concern.
- Fix must not change `roster_ps`/kill/clean's read path or the roster's data
  shape (pid, workspace, issue, role, start time).
- Single-host coordination only (no cross-host locking need, per current usage).

## What will be done
files: `spawn.py`, one new test file under `test/`.

Adopt option 1 from the issue ("lock it"): wrap the load-mutate-save section of
`roster_register` and `roster_remove` in an `fcntl.flock(LOCK_EX)` critical section
using a sibling lock file (`runs/active.json.lock`), released on exit via a context
manager. This directly satisfies the acceptance criteria (two concurrent
registrations both survive) with the smallest diff and no change to any reader.

Add a test exercising two concurrent `roster_register` calls (subprocess or
thread-based) asserting both entries survive in the final roster.

## Out of scope
- Option 2 (deleting the roster in favor of deriving `ps` from `/proc`/`pgrep` plus
  per-workspace files) — larger rewrite of `roster_ps`/kill/clean's data source,
  left as a possible future issue if the maintainer prefers it later.
- Any change to `roster_ps`, `kill`, or `clean`'s read logic — they already read
  correctly; only the writers race.

## How it'll be known to work
- Manual: start two role sessions on different issues, kill one, confirm `spawn.py
  ps` still lists the other with correct pid/elapsed time.
- Automated: new test in `test/` asserting two concurrent registrations both
  survive under the lock.
