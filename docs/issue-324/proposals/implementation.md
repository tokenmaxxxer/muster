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

Two representations for a per-issue "write set" were considered as the
primary (pre-start) signal:

(a) The actual committed diff vs `origin/main`
(`gates/gates.py:changed_files()`). Rejected as *primary*: a diff only exists
once work has already started and files are already touched — by the time two
issues' diffs collide, both sessions may already be deep into conflicting
work, which is exactly the late-detection problem #323 describes ("at merge
time the context that would have made resolution easy is gone"). Diff-only
detection can't tell the orchestrator "these two are safe to start together"
*before* starting them, which is the actual ask.

(b) The `spec.md`-declared `write:` globs that `gates/gates.py:writeset()`
(`:171-191`) reads (`gates/gates.py:183`, `spec = d / "spec.md"`). This was
this proposal's original choice, and PR #339 review rejected it: measured
2026-08-07 against on-the-record main, 0 of the 87 `docs/issue-*/` trees
contain a `spec.md`, and no code path in the current flow (`spawn.py`,
`commands/*.md`) writes one. `writeset()`'s `spec.md` read is dead code for
today's flow — it fails closed to "spec 가 없어 write-set 을 검사할 수 없다" every
time. Building the primary signal on an artifact that is always absent means
the report would *always* fall through to the diff fallback this proposal
itself rejects as too late; the design argument collapses. See the Revision
note below for why this was written down as confirmed without checking.

Chosen instead: the proposal frontmatter `files:` list under
`docs/issue-<n>/proposals/implementation.md` (the block this very file opens
with) as the primary, pre-start signal, falling back to the actual diff (a)
for issues already in progress, and `unknown` when neither is available.
Coverage measured 2026-08-07 against on-the-record main: 72 of 107 proposal
files (67%) declare a `files:` list; the remaining 33% fall into `unknown`
per the existing "never silently dropped" constraint. This is materially
better than `spec.md`'s 0% and is a value phase-1 proposals already freeze
before phase-2 starts, so reading it doesn't require inventing any new
write-up step. It reuses the `write:`-glob-style `fnmatch` matching primitive
`writeset()` already uses, applied to the `files:` list instead of a
nonexistent `spec.md`.

**Ledger ownership, coordinated with #323**: #323 (parallel-conflict
methodology) has independently landed on the same `files:` frontmatter list
as its write-set ledger. Two issues choosing different ledgers here would
fork the registry exactly the way #318 collapsed `run.md`'s duplicate lists
into one — the opposite of what #318 did. To avoid that fork: whichever of
#323 or #324 lands first implements the single frontmatter-`files:` parsing
helper (proposed name: `parse_declared_files(proposal_path) -> list[str] |
None`, returning `None` when no `files:` key is present so callers can map
that to `unknown`); the other issue imports it rather than reimplementing.
This proposal implements the helper inside `gates/parallelism.py` if it lands
first; if #323 lands first, this proposal imports #323's helper instead of
duplicating it. The owning module and the exact function are recorded here so
either side can check on merge which one actually shipped first.

## What will be done

- `gates/parallelism.py`: enumerate open issue branches (via existing
  `gates/flows.py` / `spawn.py` board-reading helpers, reused not
  reimplemented), determine each one's write-set signal — proposal
  frontmatter `files:` list (primary, pre-start), else actual diff vs
  `origin/main` (issue already in progress), else `unknown` (neither
  available) — and compute pairwise overlap across all open issues using
  `fnmatch`-based glob/path intersection (same matching primitive
  `writeset()` already uses). Includes `parse_declared_files()` per the
  ledger-ownership note above, written so #323 can import it instead of
  duplicating the parser if #324 lands first. Expose a `parallelism_report(root)`
  function returning, per pair: `disjoint` (bool) or `unknown` (bool, with
  reason — "no files: declared and no commits yet", "signal is diff-only",
  etc.), plus a CLI entry point that prints the report so the orchestrator
  can consult it before spawning.
- `test_parallelism.py`: regression tests asserting (1) two issues with
  non-overlapping declared `files:` lists are reported disjoint/safe, (2) two
  issues with overlapping declared `files:` lists or overlapping actual diffs
  are reported unsafe, (3) an issue with no `files:` frontmatter and no
  commits is reported `unknown`, never silently dropped from the report, (4)
  the ~33% `unknown` proposals do not silently drop out of the pairwise report
  — each still appears with an explicit reason.
- `docs/issue-324/reports/implementation.md`: phase-2 record, written after
  approval per contract v3 s19.
- Separately reported, not fixed here (out of scope for this PR): file a
  finding that `gates/gates.py:writeset()`'s `spec.md` read is dead code for
  the current flow (0/87 issue trees have one; no writer exists). That's a
  distinct defect from this proposal's design choice and belongs to whoever
  owns `gates/gates.py`, not to #324.

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
`files:`-declared write-sets and asserts `parallelism_report()` classifies
each pair correctly, including the `unknown` case for proposals with no
`files:` frontmatter and branches with no commits. This is the executable
artifact #310 requires — a wrong overlap classification (a false "safe" on an
actual overlap, or silent omission of an unknown branch) fails the suite.

## Revision note

PR #339 review rejected the first version of this proposal: its primary
signal was `spec.md`'s declared `write:` globs, and `spec.md` does not exist
anywhere in the repository (0 of 87 `docs/issue-*/` trees, no writer in the
current flow). That made the primary signal permanently absent, collapsing
the design to the diff-only fallback the proposal itself argued was too late
— the whole rationale for choosing (b) over (a) fell apart. This revision
replaces the primary signal with the proposal frontmatter `files:` list
(67% coverage, measured, vs. `spec.md`'s 0%), coordinates the ledger
definition with #323 so the two issues don't fork the write-set registry, and
files the `spec.md` dead-code observation as a separate, out-of-scope finding
instead of building on it.

**Root cause of the original error**: the survey observed a true, narrow fact
— `gates/gates.py:writeset()` reads `d / "spec.md"` and fail-closes when it's
missing — and the proposal silently generalized that single code-read into
"an approved `spec.md` is the declared write-set for an issue," without ever
grepping the repository for whether any `spec.md` actually gets produced by
today's flow. The narrow fact (this function has a `spec.md` code path) got
written down as though it were the broader claim (this repo produces
`spec.md` files), and the broader claim was never checked against the primary
source (a repo-wide grep, which the review then ran and got zero hits). This
is the same failure class named in #287: an inference or an absence-of-
verification gets recorded as a confirmed fact instead of being checked
against the primary source before it's relied on. The fix here is not just
picking a different artifact — it's that this revision's coverage numbers
(87 trees / 0 `spec.md`; 107 proposals / 72 with `files:`) come from an
actual measurement cited in the review, not from re-generalizing another
narrow code-read.
