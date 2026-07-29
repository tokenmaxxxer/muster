# Issue #87 — Coding Record

loop_state: phase2-complete

code_under_review: 48b7ab4

## Upstream basis

- Issue #87 (`_muster_resolve` fallback still clones the old
  `tokenmaxxxer/muster` slug).
- Phase-1 proposal: `docs/issue-87/proposals/coding.md`.
- Approval: approved per task brief ("phase-1 proposal was approved").
- Phase-1 survey: `docs/issue-87/reports/survey.md`.

## Why

Execute the approved fix in both hooks: rename `_muster_resolve`/`MUSTER`
off the old naming, point the self-clone fallback at the
`tokenmaxxxer/on-the-record` repo and the `on-the-record` fallback path,
update comments, and add the migration probe (prefer the new path, fall
back to a still-present old-path checkout, else clone) per the proposal's
chosen option.

## What was done

In both `on-the-record/hooks/directive.sh` and
`on-the-record/hooks/self-update.sh`:

- Renamed `_muster_resolve` -> `_checkout_resolve` and the result variable
  `MUSTER` -> `CHECKOUT`, updating every call site and downstream
  interpolation (including the `spawn.py`/`wake` command lines and the
  orchestration-directive text in `directive.sh`).
- Renamed the env-var override `TOKENMAXXXER_MUSTER` ->
  `TOKENMAXXXER_CHECKOUT` (not spelled out verbatim in the proposal's numbered
  list, but required to satisfy the proposal's own success criterion that no
  `muster`-derived identifier remain, and it flows directly from the
  function/variable rename).
- Updated the self-clone fallback path from
  `$HOME/.claude/tokenmaxxxer/muster` to
  `$HOME/.claude/tokenmaxxxer/on-the-record`.
- Updated the clone URL from `https://github.com/tokenmaxxxer/muster.git`
  to `https://github.com/tokenmaxxxer/on-the-record.git`, including the
  fix-it hint in `directive.sh`'s "checkout not found" error message.
- Updated comments referring to "the muster checkout" to "the on-the-record
  checkout".
- Added the migration probe: before falling through to `git clone`, the
  resolver now checks `$HOME/.claude/tokenmaxxxer/muster` for a `spawn.py`
  and returns it if present, so an existing old-path checkout is preferred
  over a redundant clone (new path still wins if it already exists — old
  path is only a fallback). No move/delete of the old checkout is
  performed, per the proposal.
- Left the dev-override, plugin-root-ancestor, and marketplace-clone
  resolution branches behaviorally unchanged (only the renamed
  variable/function flow through them).

## What did not work

(none)

## Open findings

None raised against this work.

## Next steps

None — proposal scope executed. Any leftover "muster" string in
`docs/` (historical records) or in
`on-the-record/hooks/deliverable-guard.sh`'s comment ("the muster checkout
itself") is out of scope: the deliverable-guard.sh comment is not part of
the two-file write set frozen by the proposal, and historical docs are
dated records per the proposal's explicit out-of-scope note.

## Open-finding resolution path

No open findings currently block progress. Should a reviewer raise a
blocking finding, it will be addressed and logged here as
resolved_findings before further commits, per the coding-progress gate.

## resolved_findings

(none)

## closed_checks

closed_checks:
  - check: bash -n on-the-record/hooks/directive.sh
    code_sha: 48b7ab4
    result: pass (no syntax errors)
  - check: bash -n on-the-record/hooks/self-update.sh
    code_sha: 48b7ab4
    result: pass (no syntax errors)
  - check: grep -rn muster on-the-record/hooks/ (post-edit)
    code_sha: 48b7ab4
    result: only the intentional old-path fallback string
      (`$HOME/.claude/tokenmaxxxer/muster`) in both edited hooks, and one
      unrelated comment in the out-of-write-set `deliverable-guard.sh`; no
      `_muster_resolve`/`MUSTER` identifiers remain
  - check: grep -rn 'tokenmaxxxer/on-the-record' on-the-record/hooks/ (post-edit)
    code_sha: 48b7ab4
    result: clone URL and fallback path present in both hooks as expected
