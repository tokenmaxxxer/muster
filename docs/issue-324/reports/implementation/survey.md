# Survey — issue #324: independent work is serialized

## Write surfaces examined

- `spawn.py` (3382 lines): launches one role session per invocation, isolates each
  in a per-issue clone/branch, and already supports many concurrent live sessions
  (`roster_register`/`roster_ps`, `spawn.py:1414-1460`; per-issue workspace claim,
  `spawn.py:2863`). Mechanically parallel-safe already.
- `spawn.py:drive()` (`spawn.py:2208-2220`) deliberately does **not** pick which
  role/issue to spawn next — issue #120 removed that routing table on purpose:
  "누구를 다음에 띄울지" is a judgment call the external orchestrator makes by
  reading the board, not something `spawn.py` computes. This is a design decision
  I must not reopen or route around.
- `gates/gates.py:changed_files()` (`gates/gates.py:162-168`) and `writeset()`
  (`:171-191`) already compute a single issue's write-set: committed diff vs
  `origin/main` unioned with working-tree changes, checked against `spec.md`'s
  declared `write:` globs. This is the per-issue primitive; nothing today runs it
  *across* issues to find overlap. **Correction (post PR #339 review):** the
  original survey generalized this code path into "an approved `spec.md`
  declares an issue's write-set" without checking whether any flow produces a
  `spec.md`. Repo-wide measurement (2026-08-07, on-the-record main): 0 of 87
  `docs/issue-*/` trees contain a `spec.md`, and no writer exists in
  `spawn.py` or `commands/*.md`. `writeset()`'s `spec.md` read is dead code
  for the current flow — it fail-closes every time. This is a separate
  finding, not fixed here (out of #324's scope). The primary write-set signal
  used by this proposal's design is instead the proposal frontmatter `files:`
  list (67% coverage: 72 of 107 `docs/issue-*/proposals/implementation.md`
  files declare one), coordinated with #323 which independently chose the
  same ledger.
- `gates/flows.py:flows_payload()` (`:257`) is the existing read-only board/status
  aggregator (per-issue stage, open PRs, roster liveness) — the closest existing
  "report" surface and the natural place data-wise, but it has no file-overlap
  computation.
- `runs/ledger.jsonl` (`ledger_write()`, `spawn.py:2085`) records `board_delta`
  (which `docs/issue-*/**` files changed), not full working-tree write-sets, so it
  cannot answer "which two issues touch the same code."
- No design/decision doc, ADR, or code anywhere proposes or implements
  cross-issue write-set overlap detection. `README.md` mentions parallelism only
  as aspirational narrative. Confirmed via full-repo grep for
  parallel/serial/concurrent (see prompt-level research notes); no prior art to
  build on beyond the per-issue primitives above.

## What is unknown / thin

- Proposals with no `files:` frontmatter (33%, 35 of 107 measured) have no
  declared write-set to read. A cross-issue report needs to decide how to
  treat those: report them as "unknown, cannot judge safe" rather than
  silently omitting them (an omission would misrepresent coverage). Given a
  third of proposals fall into this bucket, the report's `unknown` handling
  is not an edge case — it is load-bearing for whether the report is useful
  at all, and is called out explicitly in the proposal's test plan.
- Branches that exist but have no commits yet (freshly opened, no diff vs
  `origin/main`) have an empty committed write-set — same "unknown" treatment
  needed, not "trivially disjoint."

## Sibling-issue boundary (overlap check)

- **#323** ("no methodology for gracefully resolving conflicts between parallel
  role sessions") is the *resolution* half — what to do when two sessions do
  overlap. #324 explicitly says it is not blocked by #323: "the dependency graph
  and the parallelism report are useful before conflict handling is solved."
  This proposal stays on the *detection/reporting* side only — it does not touch
  merge-conflict handling, locking, or any runtime coordination between live
  sessions. That is #323's boundary, not this one's.
- **#310** (acceptance must name an executable artifact) governs the acceptance
  criterion below: the deliverable must be a script/test that fails on
  regression, not documentation of intent.
- **#298** (orchestrator is the only unenforced actor) is adjacent but distinct:
  it is about enforcement surfaces for the orchestrator's *procedural*
  obligations generally. This proposal adds one new *data* surface (a
  parallelism report) the orchestrator can consult; it does not attempt to
  enforce that the orchestrator actually acts on it — that would be #298's
  concern, not #324's, and is out of scope here.
- No skip condition applies (this is not a pure bugfix, and there was a real
  design choice among representations of "write set" — see proposal Rationale).

## Expected write set

- `gates/parallelism.py` (new) — computes per-issue write-sets across all open
  issue branches and reports pairwise overlap/independence.
- `test_parallelism.py` (new) — executable regression check: overlapping
  write-sets must be flagged unsafe, disjoint ones flagged safe, unknown
  (no spec / no commits) branches flagged unknown rather than silently skipped.
- `docs/issue-324/reports/implementation.md` — phase-2 implementation record
  (written only after approval, per contract v3 s19).
