files:
- gates/gates.py
- test_gates.py
- docs/issue-333/reports/implementation.md

## Request

A number typed into a record (e.g. "107 detection items exist") starts
drifting from the artifact it counts the moment it is written, and
nothing catches the drift. Worse, a wrong denominator invalidates every
ratio built on it, so one hand-typed number corrupts every progress claim
derived from it. The fix: a record must show how a count was obtained —
reproduced command output, or an inline citation to the thing that
produced it — never a bare typed number standing for a fact. Per #310, a
prose rule doesn't discharge this; it needs a mechanical check that fails
when a record regresses to a bare assertion.

## Constraints

- Only *changed* records in a PR are checked — matches every existing
  `record_*` gate's scope (`record_wellformed`, `record_no_tool_residue`,
  `record_fulfils_diff`), and specifically avoids retroactively breaking
  the pre-existing, unenforced records the survey found (e.g.
  `docs/issue-170/reports/implementation.md:108`) unless they are touched
  again.
- Fail closed on ambiguity, matching every existing gate in
  `gates/gates.py`: an unreadable role file, an unparseable record, etc.
  are blocking reasons, not "nothing to check here."
- The check must not require inventing a new source-of-truth format for
  every possible count (detection items, test counts, file counts, ...)
  — it enforces *how a count is written in a record*, not what the count
  measures.
- Stay inside `gates/gates.py`'s existing `record_*` shape: a pure
  function of `(d: Path, cfg: dict) -> list[str]`, registered in `ALL`,
  reusable both from the router (`d/"work"`) and CI's direct repo path —
  same dual-entry shape `record_wellformed`/`record_wellformed_in` and
  `record_no_tool_residue`/`record_no_tool_residue_in` already use.

## Rationale

**Fenced-or-tagged requirement vs. NLP-style "does this read like a
measurement" detection.** Considered trying to detect derivation by
prose signal — e.g. requiring a nearby verb like "measured", "ran",
"counted" near a numeric ratio. Rejected: the survey's own reading of
existing hits shows genuine derivations are phrased in several
unpredictable ways ("re-ran `test_x`", "**what the measurement shows**",
a bare `ok 58 / 59` inside a shell transcript) — a keyword list would
either miss real derivations phrased differently tomorrow or accept fake
ones ("measured to be 107" is exactly as bare as "is 107"). A structural
signal — the number sits inside a fenced code block (reproduced tool
output) or is immediately followed by an inline citation tag — is
mechanically checkable without guessing at English/Korean phrasing, and
it's the two shapes the survey found the house already reaching for
independently (`ok 58 / 59` in a fence; `re-ran
test_spawn.WorkspaceSyncFailClosed` naming a runnable target). This
proposal formalizes the second shape as a lightweight required tag —
`` `derived: <command|path:line|test-name>` `` immediately after the
number — rather than accepting free-form prose next to it, so the gate
has one deterministic rule instead of trying to classify prose as
evidence-shaped or not.

**One shared gate for #333 and #303 vs. two separate gates.** The issue
text itself asks this to be checked. Rejected merging: per the survey,
#303's approved mechanism (declared capability envelopes) targets
producer-side config/allow-lists, and has no code path that touches
`docs/issue-*/reports/*.md` prose; #333's target is exactly that prose.
A single function trying to cover both would need two unrelated input
shapes (structured declarations vs. free-text records) and two unrelated
failure conditions (a list not growing to match reality vs. a number not
citing its source), which is exactly the "unrelated problems merged into
one issue" anti-pattern the operator named in item 7 of the same
2026-08-07 batch that filed #333. Kept as two independent gate functions
under the same principle, not one function.

**Blocking new bare counts vs. also flagging existing unenforced ones.**
Considered having the new check scan every record in the repo (not just
changed ones) so the `docs/issue-170` borderline case surfaces
immediately. Rejected: every existing `record_*` gate in this file scopes
to changed files only (`_changed_records()`), and a repo-wide scan would
make this the first gate to break that convention, plus it would fail
every future PR for a record nobody touched in this change — a
maintenance surprise with no relation to the PR under review. Consistent
scope with the rest of the file wins; the borderline case gets caught the
next time that record is edited, same as `record_no_tool_residue` would
only catch tool-tag residue in a record once the record is touched
again.

## What will be done

- Add `record_derived_counts(d: Path, cfg: dict) -> list[str]` to
  `gates/gates.py`, following the `record_wellformed`/
  `record_wellformed_in` split (a `_in(work: Path)` helper for the shared
  logic, and a thin `(d, cfg)` wrapper for the router entry point).
- The check walks each changed record's lines (via the same fence-tracking
  loop shape `record_no_tool_residue_in` already uses), skipping lines
  inside fenced code blocks entirely (a number inside a fence is
  reproduced tool output, not typed).
- Outside fences, a line matching either of two count shapes is a
  violation UNLESS that same line carries an inline derivation tag: a
  backtick-quoted `` `derived: <text>` `` immediately following the
  number (any non-empty `<text>` is accepted — this check enforces the
  *presence* of a derivation pointer, not the correctness of what it
  points to, which is outside what a text-only gate can verify):
  - a ratio: `\d+\s*(?:of|/)\s*\d+` (e.g. "107 of 122", "15/20"), and
  - a bare count noun-phrase: `\d+\s+(?:detection\s+)?items?\b` and the
    same shape for the other count nouns the issue's own example uses
    ("N work[s]", "N checks", "N cases") — the exact form is finalized in
    phase 2 against the real corpus of count nouns found across
    `docs/issue-*/reports/*.md`, but it must cover the issue's own
    motivating example, "107 detection items exist," which the ratio
    pattern alone does not match (caught by the after-proposal warrant
    hunt, `docs/reports/2026-08-07-hunt-derived-record-counts.md`: the
    ratio-only regex never fires on a bare single-number count, so this
    exact motivating case would have slipped through untagged).
- Add unit tests to `test_gates.py` mirroring
  `t_record_no_tool_residue_blocks_leaked_tag`/
  `t_record_no_tool_residue_allows_fenced_tag`/
  `t_record_no_tool_residue_passes_clean_record`: a bare ratio in prose
  blocks; a bare single-number count noun-phrase in prose blocks (the
  issue's own "107 detection items exist" shape); the same two shapes
  inside a fenced block pass; the same two shapes with a
  `` `derived: ...` `` tag pass; a record with no count claim at all
  passes untouched.
- Register `record_derived_counts` in `ALL` (`gates/gates.py`'s registry
  dict) so it is callable through `check()` the same way every other
  `record_*` gate is.

## Out of scope

- Wiring the new gate into the router's/CI's default `names` list for
  `check()` (i.e. making it actually run on every PR) — the survey did
  not find where that default list is configured (likely a `roles/*.json`
  or `gates/ci.py`/router config not yet inspected in depth); phase 2
  will locate and wire it only if it is a small, obvious addition inside
  the frozen write set, and will report as scope-exceeded and stop
  otherwise rather than widening the write set mid-build.
- Any attempt to verify a derivation tag's *content* is correct (e.g.
  running the cited command and checking its output matches the number)
  — a text gate can enforce that a citation exists, not that it's true;
  catching a false citation is a human-review/verify-role concern, not a
  mechanical one, and is not claimed as covered here.
- A shared mechanism with #303 (see Rationale) — the two stay separate
  issues with separate write sets.
- Any change to pre-existing, currently-unenforced records found during
  the survey (e.g. `docs/issue-170/reports/implementation.md:108`) — they
  are not touched by this PR and the gate only applies going forward, to
  files the PR itself changes.
- Retrofitting the six pre-existing records the survey found with ratio
  patterns — none of them are in this PR's write set.

## How you'll know it worked

- `test_gates.py`'s new tests (`t_record_derived_counts_*`, exact names
  chosen in phase 2 mirroring the existing `record_no_tool_residue`
  naming) exercise `gates.record_derived_counts_in()` directly: a bare
  "107 of 122" in prose returns a non-empty violation list; the same
  number inside a fenced block, or tagged `` `derived: ...` ``, returns
  `[]`. `pytest test_gates.py` passing (including the new cases) is the
  executable artifact that fails on regression, per #310's acceptance
  bar — reverting the derivation check, or a future record adding an
  untagged ratio into a changed record, fails this test/gate rather than
  passing silently.
- `docs/issue-333/reports/implementation.md` (phase 2) records the actual
  test run output and confirms the gate blocks the exact "107 of 122,
  no derivation" shape the operator's report describes.
