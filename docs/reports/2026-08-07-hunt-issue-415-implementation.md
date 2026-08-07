---
proposal: docs/issue-415/proposals/implementation.md
---

# Hunt record — issue-415-implementation

## after-proposal — stance 1: assume the gate/checker this proposal describes is bypassable — find the bypass

Verdict: FINDING — the checker's fixed English/Korean phrase list ("does not exist", "is not implemented", "존재하지 않는다", etc.) is described as a closed set, so an absence claim phrased with a synonym/contraction outside that list evades detection entirely while remaining a genuine unscoped capability claim.
Kind: design-error
Seed: docs/issue-415/proposals/implementation.md, "## What will be done" item 1 ("a fixed English + Korean phrase list, reusing #358's own list where the shape overlaps")
cap_seconds: 60
tier: default
diff_stat_lines: docs-only (proposal file, no code diff)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:01:00Z

### Reproduce
No code exists yet (phase 1, proposal only), so this is a design-level reproduction against the proposal's own stated mechanism (fixed phrase-list matching, item 1 of "What will be done"):

Given the checker's documented trigger set is a *fixed* list of absence phrases (e.g. "does not exist", "is not implemented"), consider the sentence a role could actually write:

  "The audit-log capability isn't implemented, and there's no fallback for it."

This is a capability/contract-shaped absence claim with a bare noun-phrase subject ("the audit-log capability"), no file path, and no scope statement ("as of <sha> in <repo>") — exactly the shape item 2's fixture (a) says must be flagged. But it uses "isn't" (contraction) and "there's no X" instead of any string literally on the fixed list ("does not exist", "is not implemented", 존재하지 않는다, etc.).

### Observed
Per the proposal's own design (`check_repo_scope` scans for matches against "a fixed English + Korean phrase list"), a sentence using an unlisted synonym/contraction ("isn't implemented", "there's no X", "lacks X", "hasn't been built") produces zero matches against the phrase list and is never even considered for the scope-adjacency check — the sentence passes silently, indistinguishable from a properly-scoped claim or from prose that isn't an absence claim at all.

### Expected
An unscoped capability-absence claim of this shape should be flagged just like fixture (a) ("capability X not found" with no scope statement) is required to be flagged — the proposal's stated acceptance criterion (item 2a) is that *the shape* is what triggers the gate, but the actual mechanism (item 1) only triggers on literal fixed-list phrase matches, so any paraphrase of the same shape silently bypasses the gate. This is a silent failure mode baked into the design itself, not an implementation bug: a closed phrase list can never cover the open set of English/Korean ways to assert absence, and the proposal does not describe any fallback (e.g. a syntactic negation+capability-noun heuristic) for phrasing outside the list.
