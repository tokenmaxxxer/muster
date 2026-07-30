---
kind: coding-record
subject: issue-103
loop_state: landed
code_under_review: (see PR)
---

# coding record — issue #103

## why

Two live incidents (write-time free-text verdict, #100; the
`scope-proposed`/`decided` vocabulary gap, controller #93) came from
`wakes.py`/`wake-routing.md` consuming state/field values no rulebook
actually produces. Issue #103 requires a test that catches this class
of gap at design time.

## upstream basis

PR #108 (proposal `docs/issue-103/proposals/coding.md`) merged;
phase 2 opened by that approval.

## what was done

Built the frozen write set exactly per the approved proposal:
- `docs/specs/loop-state-vocab.md` (new): declared `loop_state`/`verdict`
  vocab per role (feasibility/qa/ux-design/verify/review/coding) for
  the 6 values `wakes.py` consumes by exact-match comparison, plus a
  `## Human-only allowlist` section for `scope-approved` (producer:
  "a human, via the pre-approval gate — no role").
- `test_vocab_coherence.py` (new, repo root): an explicit `CONSUMED`
  list of (role, field, value, wakes.py line) tuples mirroring the 6
  literal comparisons + the `scope-approved` gate check, parses the
  vocab doc, asserts each consumed value is declared for its role or
  present in the allowlist; failure message names the value, role,
  and call-site line. No network, no `spawn.rulebook_dir()`.
- `wakes.py`: 7 comment-only additions pointing each comparison at
  `docs/specs/loop-state-vocab.md` as source of truth. `git diff
  --stat` confirms 7 insertions, 0 deletions — no logic change.

## what did not work

Nothing abandoned or replaced during the build.

## open findings

None.

## next-steps

None — build complete, PR opened.

## open-finding-resolution-path

N/A — no open findings.

## closed_checks

- `test_vocab_coherence.py` self-run: 3/3 passed (`code_under_review`
  = the commit on this branch containing this record).
- `test_gates.py` regression run: same pre-existing failure
  (`t_repo_local_claude_config_stops_the_spawn`, read-only-fs sandbox
  restriction writing outside the repo) reproduced identically on
  unmodified `wakes.py` via `git stash` — confirmed not a regression
  from this change; all other `test_gates.py` cases pass.
- Deliberate-mismatch check: temporarily changed one `wakes.py`
  comparison value to a value absent from both the doc and the
  allowlist (with the test's `CONSUMED` list updated to match, since
  it's an explicit maintained list, not `ast`-derived) — rerun failed
  with the expected message naming that exact value and call-site;
  reverted, rerun passed clean again.
