---
code_under_review:
  - gates/gates.py
  - test_gates.py
  - docs/decisions/2026-08-07-measured-claim-line.md
loop_state: landed
---

# Implementation record — issue #332

Phase 2, executing the approved proposal
(`docs/issue-332/proposals/2026-08-07-claim-evidence-at-write-time.md`,
approved via issue-level comment `APPROVE issue-332/implementation`,
single-account mode, role-handoff contract v3). No follow-up comment after
the APPROVE token — nothing conditional to bind to beyond the proposal
itself.

## What was done

1. `docs/decisions/2026-08-07-measured-claim-line.md`: recorded the
   `fulfils: count <derivation> <N>` grammar as a decision — what
   `<derivation>` may be (glob/path match-count, or a `shlex`-tokenized
   shell command run with `shell=False` whose stdout must be a bare
   integer), how it's re-run (against the current work tree, not the
   diff — a count is a property of state, not of a change), and why
   `count` extends `fulfils:` rather than becoming a new marker.
2. `gates/gates.py`: added `_COUNT_CLAIM` (splits a `count` claim's
   trailing integer from its derivation) and `_count_derivation()`
   (re-runs the derivation, returns `None` when unresolvable). Added a
   `count` branch to `record_fulfils_diff` alongside the existing
   `delete`/`create`/`move` branches, following their exact
   fail-closed shape (unparseable claim → blocked, mismatch → blocked,
   match → silent pass). No sibling function created — extends the
   existing one per the proposal's Rationale.
3. `gates/ci.py`: **not modified.** `record_fulfils_diff` was already
   the function `ci.check()` calls (unconditionally, whenever
   `closes_only=False`); extending that function's `count` handling
   automatically reaches the same call site the proposal's item 3 asked
   for. No new wiring needed.
4. `test_gates.py`: six new tests next to the existing `t_fulfils_*`
   tests — command-derivation match/mismatch, glob-derivation
   match/mismatch, malformed claim (missing `<N>`), and an unresolvable
   command (non-integer stdout) — mirroring the shape of the existing
   `delete`/`create`/`move` test pairs (correct passes, wrong fails,
   malformed fails closed).

## Why (upstream basis)

Proposal `docs/issue-332/proposals/2026-08-07-claim-evidence-at-write-time.md`,
approved. The proposal's own Rationale (extend `fulfils:` rather than a
new marker or a free-text linter) and "What will be done" items 1-4 map
1:1 onto the four items above.

## Confirmation run

```
$ python3 -m pytest test_gates.py -k fulfils -q
...............                                                          [100%]
15 passed, 66 deselected in 0.55s
```
`fulfils: count python3 -m pytest test_gates.py -k fulfils -q 15` would
not itself parse (pytest's quiet-mode dot output isn't a bare integer) —
the count claimed here is stated in prose, not as a `fulfils:` line,
since this record's own claim is about a test *run*, not a re-runnable
derivation matching a static count.

Full-suite run (`python3 test_gates.py`) was also executed once: every
other test passed; `t_repo_local_claude_config_stops_the_spawn` fails in
this sandbox with `OSError: [Errno 30] Read-only file system:
'/home/jwjung/.tokenmaxxxer/trusted-repo-config.json'` — a pre-existing
sandbox filesystem restriction unrelated to this change (its traceback
points at `spawn.py::require_no_repo_config`, a file this change never
touches, attempting a write outside the repo tree). Not counted as a
regression from this work.

## What did not work

None.

## Doc-placement ladder

- Library/format decision (the `count` claim grammar) →
  `docs/decisions/2026-08-07-measured-claim-line.md` (item 1 above).
- No new env var, config key, dependency, or migration introduced —
  nothing else on the ladder applies.

## Post-proposal hunt finding, addressed (per #330/#358)

The phase-1 hunt (`docs/reports/2026-08-07-hunt-claim-evidence-at-write-time.md`)
found that the only required-status-check workflow
(`.github/workflows/plan-aware-closes-gate.yml`) invokes `gates/ci.py`
with `--closes-only`, which returns before ever reaching
`record_fulfils_diff` — so the pre-existing `fulfils:` gate (#155)
already wasn't enforced on real PRs, only in local/pytest runs. Per the
proposal's own instruction ("Phase 2 must either widen ... or explicitly
scope this proposal's 'how you'll know it worked' down to pytest-only
enforcement and say so"), this record scopes down explicitly: the `count`
kind is enforced by `pytest test_gates.py -k fulfils` (see the run above)
and by any local/manual `gates/ci.py` invocation without `--closes-only`
— **not** by the required PR check today. Widening
`.github/workflows/plan-aware-closes-gate.yml` was not in this issue's
frozen write set (`gates/gates.py`, `gates/ci.py`, `test_gates.py`,
`docs/decisions/2026-08-07-measured-claim-line.md`,
`docs/issue-332/proposals/2026-08-07-claim-evidence-at-write-time.md`)
and is not silently added here; it is a distinct gap in an already-shared
CI-wiring surface, left as a follow-up rather than folded into this
issue's scope.

## What this reaches beyond its own acceptance (per #330)

- Does not retroactively invalidate any already-merged record's
  unevidenced claims.
- Extends `_FULFILS_LINE`-adjacent parsing / `record_fulfils_diff`, used
  by every role writing a phase-2 record today; a malformed `count` line
  now fails-closed the same way a malformed `delete`/`create`/`move` line
  already did.
- No `gates/ci.py` change was needed, so this change specifically leaves
  the CI check-list wiring surface untouched — the pre-existing
  `--closes-only` gap (above) still affects every PR touching a phase-2
  record, unchanged by this issue.

## Hunt

This session is headless/single-shot (contract v3 s22): a background
hunter dispatch whose result isn't consumed before the turn ends is
prohibited, and there is no further turn in this session to consume one.
No hunter dispatched at this transition for that reason. The phase-1
hunt already ran and surfaced one finding; that finding is resolved
above under "Post-proposal hunt finding, addressed," so nothing was left
unexamined by skipping a second dispatch.

## Open findings

None outstanding. The one finding raised against this work (the
phase-1 hunt's `--closes-only` CI-wiring gap) is addressed above under
"Post-proposal hunt finding, addressed" — scoped down explicitly rather
than left implicit, per the proposal's own instruction.

closed_checks:
- name: fulfils-count-red-green (correct count passes — command and
  glob derivations both; wrong count blocks; malformed claim
  fails closed; unresolvable/non-integer derivation fails closed)
  code_sha: gates/gates.py (record_fulfils_diff + _count_derivation,
  this commit)
