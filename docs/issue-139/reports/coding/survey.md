# issue-139 — phase-1 current-state survey

`runs/active.json` (the roster) is read/written only inside `spawn.py`, via
`_roster_load`/`_roster_save` and mutated by `roster_register` (~line 1267) and
`roster_remove` (~line 1273): both do an unlocked load-whole-dict → mutate-one-key →
write-whole-dict. `fcntl`/`flock` do not appear anywhere in `spawn.py` before any
change (grep: 0 hits). `roster_ps` (backs `spawn.py ps`) and the kill/clean code
paths only read the roster; they do not race each other, only the two writers do.

Two sessions calling `roster_register`/`roster_remove` near each other can
interleave: the second writer's in-memory snapshot was taken before the first
writer's save, so its write clobbers the first writer's entry. This matches the
measured incident: a killed session's `roster_remove` raced a live session's
`roster_register`, and the surviving roster lost the live entry — `ps` then
reported "없음" for a session that had been running 16 minutes.

Write surface for a fix is `spawn.py` only (`ROSTER` path, `_roster_load`,
`_roster_save`, `roster_register`, `roster_remove`). No other file reads or writes
`runs/active.json`; `runs/` is gitignored working state, so no migration/schema
concern. Test surface: `test/` has no existing file exercising the roster
functions (grepped, none found) — a new test file is in scope, asserting two
concurrent registrations both survive.

## Scout: skipped

Skip condition applied: pure bugfix. The issue is a concrete race-condition report
with two fully-specified acceptable shapes (lock vs. delete-the-roster) and
explicit acceptance criteria already given by the issue author; there is no
product-shaped or exemplar-comparable design surface — this is an internal
single-host process-coordination primitive, not a user-facing product, so no
category best-in-class applies beyond the two shapes the issue itself names.
