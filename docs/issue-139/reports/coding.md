# issue-139 — coding record

code_under_review: spawn.py (roster_register/roster_remove + `_roster_locked`)
loop_state: landed

## Why
`roster_register`/`roster_remove` did unlocked load-mutate-save on
`runs/active.json`; concurrent role sessions (the documented normal case)
could clobber each other's roster entry, and a measured incident showed `ps`
reporting "없음" for a session alive 16 minutes. `clean`/`kill` also trust the
roster, so a lost entry risks `clean` deleting a live workspace.

## Upstream basis
Issue #139 (author jjongkwann), which pre-scoped two acceptable fixes (lock
vs. delete-the-roster) and gave explicit acceptance criteria. Proposal at
`docs/issue-139/proposals/coding.md` (already committed on this branch)
adopted option 1 ("lock it") for smallest diff and no change to any reader.

## What was done
- Added `_roster_locked()` context manager in `spawn.py`: opens a sibling lock
  file (`<ROSTER>.lock`, derived from `spawn.ROSTER` at call time so tests that
  monkeypatch `spawn.ROSTER` stay isolated), takes `fcntl.flock(LOCK_EX)`,
  releases on exit.
- Wrapped `roster_register`'s and `roster_remove`'s load-mutate-save in
  `with _roster_locked():`. No other write site exists (`_roster_save` is
  called only from those two functions); read-only call sites are unaffected.
- Added `RosterConcurrency.test_concurrent_register_survives` in
  `test_spawn.py`: 20 threads call `roster_register` concurrently after a
  `threading.Barrier`; asserts all 20 entries survive in the final roster.

## Verification run (self-check, not a review pass)
Ran `python3 -m unittest test_spawn.py`: 103 tests, all pass (including the
new one). Ran the new test in isolation too (`python3 -m unittest
test_spawn.RosterConcurrency -v`): ok.

## What did not work
(nothing — first approach held)

## closed_checks
- roster-write-site-sweep (code_sha: this commit) — grepped `_roster_save`
  call sites; confirmed only `roster_register`/`roster_remove` call it, both
  now locked. No other unlocked writer exists.
- concurrent-register-race (code_sha: this commit) — 20-thread barrier test
  reproduces the race shape from the issue and passes under the lock (fails
  without it, verified manually by temporarily removing the `with` before
  committing).

## Hunt
Stance: none dispatched — single-turn headless session per invocation
instructions, no background dispatch survives turn end. Documented per hunt
cadence requirement as a deliberate skip, not an oversight.

## Out of scope (per proposal)
Option 2 (deriving `ps` from `/proc`/`pgrep`, dropping the roster file) not
attempted — left for a future issue if preferred.

## Open Findings
None outstanding.
