files:
- gates/gates.py
- test_gates.py
- docs/issue-333/reports/implementation.md

# Survey — issue #333 (hand-asserted counts in records drift from the artifact they count)

## Write set

- `gates/gates.py` — phase 2 adds one new mechanical check function,
  registered in `ALL`, following the existing `record_*` check shape
  (`record_wellformed`, `record_no_tool_residue`, `record_fulfils_diff`).
- `test_gates.py` — phase 2 adds unit tests for the new check (positive:
  fenced/tagged count passes; negative: bare count in prose fails).
- `docs/issue-333/reports/implementation.md` — phase 2 writes this; not
  touched in phase 1.

No other files were found to reference count/ratio assertions inside
records — the existing `record_*` gates never inspect record *prose*
content for numeric claims, only frontmatter, structural well-formedness,
tool-tag residue, and `fulfils:` diff-matching.

## What "detection items" in the operator's report actually refers to

`gh issue view 333` was checked directly. The "107 detection items / 15
more found by cross-check" is the operator's illustrative anecdote from
*another* project's session ("Reported from another session running
on-the-record"), quoted inside this issue's body — it is not a literal
artifact inside this repo (`on-the-record` itself). Grepped `docs/`,
`gates/`, `roles/` for `107` and `"detection item"`: no matches beyond an
unrelated `gates/flows.py:107` line-number citation. This repo (the
orchestrator) is the correct place to fix the pattern generically, because
every board repo's records are produced by roles spawned through it, and
the mechanism has to apply across boards, not to one project's detection
list.

## Confirmed: the pattern already occurs in this repo's own records

Grepped every `docs/issue-*/reports/*.md` for the ratio shape
`\d+ (of|/) \d+` (six files hit: `docs/issue-167/reports/implementation.md`,
`docs/issue-170/reports/implementation.md`, `docs/issue-221/reports/implementation.md`,
`docs/issue-241/reports/technical-writing.md`, `docs/issue-64/reports/feasibility.md`,
`docs/issue-227/reports/execution-observation.md`). Read each hit in
context:

- `docs/issue-167/reports/implementation.md:118,122` — `ok 58 / 59` sits
  inside a fenced shell-transcript block (pytest output), directly
  reproducing a command's stdout. This is the good case: the number is
  shown, not asserted.
- `docs/issue-227/reports/execution-observation.md:133` — `5 of 5` is
  immediately preceded on the same line by prose describing what a
  measurement showed ("**The gate-relevant invariant holds, without
  exception.** 5 of 5"), under a section titled "What the measurement
  shows, stated plainly" — the derivation is narrated right there, not a
  bare assertion.
- `docs/issue-221/reports/implementation.md:236` — `3 of 4 error/...`
  follows "re-ran `test_spawn.WorkspaceSyncFailClosed`" in the same
  sentence — the test name that produced the number is named inline.
- `docs/issue-241/reports/technical-writing.md:87-100` — a manual mapping
  table (source doc section -> destination) with row-count claims baked
  into column headers (e.g. "1-3 / 1-3"); each row's own "found?" column
  cites a concrete grep or file check. Not a plain ratio-of-unknowns case.
- `docs/issue-170/reports/implementation.md:108` — `43 of 44
  t_-prefixed checks pass` — no fenced block and no inline command name on
  that line; the surrounding paragraph needs to be read to know whether a
  derivation is nearby (not fully confirmed — flagged as a possible
  borderline case for phase 2 to re-check against the gate once built,
  since this record predates the gate and won't be re-scanned unless
  touched again).

Net: the house habit already leans toward citing how a number was
produced (fenced output, or "re-ran <test>" naming the source), it is
just never enforced — exactly the defect the issue names ("a number with
no derivation should be readable as an estimate and never as a fact").
The new gate's job is to make the existing good habit mandatory going
forward, not to invent a new writing style.

## Existing conventions to extend

- `gates/gates.py`'s `record_*` family (`record_wellformed`,
  `record_no_tool_residue`, `record_fulfils_diff`) all: (1) operate only
  on the PR's *changed* records via `_changed_records()`/`changed_files()`
  — never rescan the whole repo, so pre-existing unenforced records (like
  the `docs/issue-170` borderline case above) are not retroactively
  broken; (2) fail closed on anything unparseable rather than treating it
  as "nothing to check"; (3) are opt-in by shape — e.g.
  `record_fulfils_diff` only fires on lines matching a specific marker
  (`fulfils:`), so a record that doesn't use the marker isn't touched by
  that gate at all. The new check should follow the same three
  properties.
- `docs/decisions/2026-07-29-headless-cli-measured-facts.md` establishes
  the house's existing "measured fact, cited to `path:line`" convention
  for decision docs (a `Source: path:line` line after each claim) — the
  same idea this issue wants generalized into records, just not
  mechanically enforced there either. Not directly reusable as a decision
  doc (records and decisions are different doc kinds with different
  frontmatter/gates), but it's evidence the citation habit is already the
  house style, independently arrived at.
- `_TOOL_TAG`/fence-tracking loop inside `record_no_tool_residue_in`
  (`gates/gates.py:387-398`) is the existing, already-tested pattern for
  "track fenced-code-block state while walking a record line by line and
  skip lines inside fences" — the new check reuses this exact loop shape
  (a fence gives structural evidence a number was reproduced output, not
  typed).

## Issue #303 relationship (checked per the issue's own hint)

Read `gh issue view 303` in full: #303 is about a *producer*-side pattern
— a role discovering a missing capability (e.g. a cache path, a sandbox
permission) and closing it by hand-adding one line to a hardcoded
allow-list, which only fixes the one instance and leaves the generator
that keeps producing new instances untouched. #333 is a *consumer*-side
(reporting) pattern — a record stating a count about an artifact that
already exists elsewhere, with no link back to how the count was
produced. Different artifacts (config/allow-list vs. record prose),
different failure shape (list never grows to cover the true set vs.
denominator silently drifts from the true set), and no shared code path
today (`gates/gates.py` has no allow-list-growth check and #303's
approved mechanism — declared capability envelopes — doesn't touch
`docs/issue-*/reports/*.md`). One general principle ("derive, don't hand
assert") covers both, but the enforcement mechanisms don't overlap enough
to be one gate function; scoping #333 to records only, as filed, keeps
the two issues' write sets from colliding.

## Test coverage found

- `test_gates.py` already tests the `record_*` family (`record_enums`,
  `record_wellformed`, `record_no_tool_residue`, `record_fulfils_diff`)
  with the same fixture shape: build a temp git repo, commit a record
  file with/without the pattern under test, assert `ALL["<name>"](d, cfg)`
  returns the expected violation list. Phase 2's tests copy this fixture
  pattern directly — no new test scaffolding needed.
