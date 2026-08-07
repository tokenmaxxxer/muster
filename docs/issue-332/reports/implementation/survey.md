## Current-state survey — issue #332

### Scope boundary check against sibling issues

Issue #332 is filed as "the generator" — the operator's report names six distinct
unevidenced-claim defects, each already spun into its own issue:

- denominator maintained by hand → #333
- tests that skip and count as passing → #334
- fakes diverging from the real interface → #335
- registration points listed by hand / success declared without completing the
  instruction → #331 ("Success is declared without completing the instruction,
  and the operator cannot tell")
- spec contradiction across repos → #336

That leaves #332 itself with no undelegated specific mechanism to fix — its own
acceptance criterion is the generator claim: "a claim be recorded without
evidence at the moment it is made." The only thing left in #332's own scope is
the general policy/mechanism, not any one instance already owned by a sibling.

### Existing mechanism precedent: `fulfils:` (issue #155)

`gates/gates.py::record_fulfils_diff` (lines 408-462) is the only existing gate
that checks a *claim* in a phase-2 record against *evidence* derived
mechanically from the commit diff, at write time:

- A record may write `fulfils: delete|create|move <path>` lines.
- The gate reads `_committed_changes_with_status()` (git status letters) and
  fails the record if the claimed delete/create/move isn't actually present in
  the diff.
- Unparseable `fulfils:` lines are a block, not a skip (fail-closed — same
  principle as `dep_names()`).
- Records with zero `fulfils:` lines are untouched — it's an opt-in marker,
  not a mandatory field.

This is the shape #332 needs to generalize: a claim-line convention paired
with a gate that derives the actual state and rejects a mismatch, wired into
`gates/gates.py::ALL` and `gates/ci.py` the same way `record_fulfils_diff`
already is.

### What's NOT yet covered by this precedent

`fulfils:` only covers file-existence claims (delete/create/move). It does not
cover the general pattern in the operator's report: a *quantitative* or
*completion* claim ("25 of 107", "다 됨", "통과") written in prose with no
adjacent evidence pointer, where nothing forces the writer to name what was
run to derive the number.

Grep across `gates/gates.py`, `roles/*.json`, and `docs/decisions/` turned up
no other claim-evidence gate and no existing convention for a generic
"evidence:" or "measured-by:" companion field. `roles/*.json` declares
`record_fields` (enum-checked frontmatter fields, see `record_enums()`), but
enums constrain a value to a fixed set — they don't verify a number against a
derivation.

### Write surfaces this touches

- `gates/gates.py` — new check function + `ALL` registration (mirrors
  `record_fulfils_diff`'s shape).
- `gates/ci.py` — wire the new check into the CI-facing check list the same
  way existing `record_*` checks are wired (needs confirming which list adds
  it — `ci.py` imports `gates` and calls `gates.check(...)`; the exact call
  site needs reading before build).
- `test_gates.py` — new gate needs unit tests (existing file already covers
  `record_fulfils_diff`; same test shape applies).
- `docs/decisions/` — the convention itself (a new claim-line syntax, e.g.
  `measured: <derivation>`) is a public-signature/format decision per the
  doctrine ladder, and belongs there, not just in code.
- `docs/issue-332/proposals/` — this proposal.

### Alternatives considered while surveying

1. **A free-text linter that flags any number in prose without an adjacent
   citation.** Rejected before proposing: unbounded false-positive surface
   (issue numbers, port numbers, dates all contain digits), and no clear
   "evidence" format to validate against — this would either fail-open
   (useless) or fail-closed on nearly everything (unusable, gets disabled,
   which is exactly the failure mode `gates/ci.py`'s own docstring warns
   against).
2. **Extend `fulfils:` itself to accept a `count` kind** (e.g. `fulfils: count
   <path-or-command> <N>`), reusing the existing marker line and gate function
   rather than inventing a parallel one. This is the leading candidate — see
   proposal Rationale.
