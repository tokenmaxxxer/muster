---
loop_state: landed
---

# Coding record — issue #155

upstream: docs/issue-155/proposals/2026-07-31-coding-fulfils-marker-gate.md
(approved via issue comment `APPROVE issue-155/coding`)

code_under_review: 1d296ea3128abac8f94a458b775fd4779c109011

## What was done

- `gates/gates.py`: new `_committed_changes_with_status(work)` — a sibling
  of `_committed_changes` that preserves the `--name-status` letter
  (A/M/D/R/C) instead of discarding it, returning
  `(status, path, old_path_or_None)` tuples. Existing callers
  (`changed_files`, `_worktree_changes` consumers) are unchanged.
- `gates/gates.py`: new gate `record_fulfils_diff(d, cfg)`, registered in
  `ALL`. Parses `fulfils: delete|create|move <path>[...]` lines out of
  changed phase-2 records (`_changed_records`) with a shallow per-line
  regex (`_FULFILS_LINE`, same style as `_write_scope_overrides`'s
  `- write:` parsing) and checks each claim against the commit diff's
  status letters: `delete` needs a `D` (or the old side of an `R`/`C`);
  `create` needs an `A` (or the new side of an `R`/`C`); `move <old> ->
  <new>` needs an exact `R`/`C` pair. An unparseable claim-type keyword
  or a malformed `move` (no `->`) blocks — fail closed, same stance as
  `dep_names()`. Records with zero `fulfils:` lines are untouched.
- `test_gates.py`: new `_fulfils_repo` fixture (two-commit repo — init,
  then ops + record together, mirroring `_record_repo` but with real
  file mutations so the diff has something to check) and 8
  `t_fulfils_*` cases: delete/create/move true-positive and false-claim
  pairs, an unparseable claim line, and a claim-free record passing
  untouched. The delete false-claim case reproduces issue #145's actual
  incident shape.

## Why

The approved proposal closes the gap the issue's incident exposed: a
record could claim a file mutation ("deleted X") that its own commit
diff didn't contain, and nothing caught the mismatch. `fulfils:` is an
opt-in, line-level marker checked deterministically against
`--name-status`; unmarked prose claims stay exactly as unverified as
before (documented in the proposal's side-effect analysis — the gate's
guarantee is "every `fulfils:` line matches the diff," not "every claim
in this record is true").

## What did not work

`_fulfils_repo`'s rename op initially called `git mv old/a.py new/a.py`
without creating `new/`'s parent directory first — `git mv` doesn't
auto-create target directories the way a plain filesystem move might,
so the first run failed with exit 128. Fixed by `mkdir(parents=True)` on
the target's parent before the `git mv` call.

## Confirmation run

`python3 -c "... run all 8 t_fulfils_* cases ..."` — all pass.
`python3 test_gates.py` (full suite) — every test passes except the
pre-existing sandbox-only failure in
`t_repo_local_claude_config_stops_the_spawn`
(`OSError: Read-only file system: /home/jwjung/.tokenmaxxxer/trusted-repo-config.json`),
already flagged this way in prior coding records (e.g. issue-149's) and
unrelated to this change's write set.

## Hunt

warrant-hunter dispatch was not run this phase — the new surface reuses
already-reviewed shapes end-to-end (`_committed_changes`'s `-z`
name-status parsing for the status-preserving sibling, `dep_names()`'s
fail-closed-on-unparseable stance, `_changed_records`'s record
discovery) and is covered by 8 new test cases spanning both fail-closed
paths (unparseable claim, false claim) and the pass paths (all three
claim kinds, claim-free record).

closed_checks: none (no findings addressed to this record).

## Open findings

None outstanding for this record.

## Out of scope (unchanged from proposal)

Documenting the `fulfils:` syntax in a handbook page; `closed_checks:`/
`code_sha:` cross-checking; test-execution claim verification.
