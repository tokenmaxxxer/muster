---
status: proposed
files:
  - gates/parallelism.py
  - test_parallelism.py
  - docs/issue-324/reports/implementation.md
---

## Request

The operator observes that on-the-record routinely runs independent work one
session at a time even though sessions are isolated (worktree-per-issue) and
could run concurrently. Nothing today computes what is actually independent,
reports available parallelism, or notices idle-able work sitting behind an
unrelated task. Per #310, this must land as an executable artifact that fails
on regression, not prose.

## Constraints

- Must not reopen or route around issue #120's decision: `spawn.py:drive()`
  deliberately does not choose which role/issue to spawn next — that judgment
  stays with the external orchestrator reading the board. This proposal adds a
  data surface, not an auto-scheduler.
- Must not attempt merge-conflict resolution or runtime coordination between
  live sessions — that is #323's boundary, filed alongside this issue and
  explicitly not a blocker for this one.
- Branches with no `spec.md` (not yet `scope-approved`) or no commits yet must
  be reported as "unknown," never silently omitted or treated as trivially
  disjoint — an omission or a wrong default would misrepresent coverage.

## Rationale

Two representations for a per-issue "write set" exist in the codebase today:
(a) the actual committed diff vs `origin/main` (`gates/gates.py:changed_files()`),
and (b) the declared `write:` globs an approved `spec.md` states up front.

Considered using only (a), the actual diff. Rejected: a diff only exists once
work has already started and files are already touched — by the time two
issues' diffs collide, both sessions may already be deep into conflicting
work, which is exactly the late-detection problem #323 describes ("at merge
time the context that would have made resolution easy is gone"). Diff-only
detection can't tell the orchestrator "these two are safe to start together"
*before* starting them, which is the actual ask (spawn independent work in
parallel, not merely notice conflicts after the fact).

Chosen: use the declared `spec.md` write-set (b) as the primary signal for
issues not yet started, falling back to the actual diff (a) for issues already
in progress (spec still governs, but work may have touched files outside a
stale/missing declaration). This lets the report answer "can I start N and M
together right now" before either has written a line, while still catching
overlap once work is underway — reusing `gates.gates.changed_files()` and the
`write:` glob parsing pattern already in `gates/gates.py:171-191` rather than
inventing a second parser.

## What will be done

- `gates/parallelism.py`: enumerate open issue branches (via existing
  `gates/flows.py` / `spawn.py` board-reading helpers, reused not
  reimplemented), determine each one's write-set signal (spec-declared globs,
  else actual diff vs `origin/main`, else `unknown`), and compute pairwise
  overlap across all open issues using `fnmatch`-based glob intersection (same
  matching primitive `writeset()` already uses). Expose a `parallelism_report(root)`
  function returning, per pair: `disjoint` (bool) or `unknown` (bool, with
  reason), plus a CLI entry point that prints the report so the orchestrator
  can consult it before spawning.
- `test_parallelism.py`: regression tests asserting (1) two issues with
  non-overlapping declared globs are reported disjoint/safe, (2) two issues
  with overlapping globs or overlapping actual diffs are reported unsafe, (3)
  an issue with no `spec.md` or no commits is reported `unknown`, never
  silently dropped from the report.
- `docs/issue-324/reports/implementation.md`: phase-2 record, written after
  approval per contract v3 s19.

## Out of scope

- Actually spawning multiple sessions concurrently — the mechanism
  (`spawn.py` roster/workspace isolation) already exists and is untouched here.
- Conflict resolution methodology for sessions that *do* overlap — #323.
- Enforcing that the orchestrator actually consults or acts on the report —
  adjacent to #298's "orchestrator is the only unenforced actor," not this
  issue's boundary.
- Any change to `spawn.py:drive()`'s role-selection behavior (#120 stands).

## How you'll know it worked

`python -m pytest test_parallelism.py` passes and fails on regression: it
constructs fixture issue directories with known overlapping and disjoint
write-sets and asserts `parallelism_report()` classifies each pair correctly,
including the `unknown` case for missing spec/no-commit branches. This is the
executable artifact #310 requires — a wrong overlap classification (a false
"safe" on an actual overlap, or silent omission of an unknown branch) fails
the suite.
