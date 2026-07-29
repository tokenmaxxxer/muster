---
kind: coding-record
subject: issue-95
loop_state: landed
upstream:
  - path: docs/issue-95/proposals/coding.md
    sha: 293bdb7
---

# issue-95 — phase 2: execute approved wake-routing relocation

Approval: PR #96 comment "APPROVE issue-95/coding" (single-account mode,
exact string match), 2026-07-29T21:59:59Z.

## Why

Phase 1 found `wakes.py` already implements the WAKES-ON routing table
correctly, but its comments and README attribute that table to the
external contract's §3/§5/§14/§15/§18/§19 — so a future routing change
(new role, rerouted edge) would misleadingly read as a contract
amendment. This phase moves ownership: the table now lives as this
repo's own doc, with zero change to actual routing behavior.

## What was done

Executed the approved proposal exactly: added
`docs/specs/wake-routing.md`, reworded `wakes.py` and README.md
attribution comments only, added one structural equivalence test to
`test_gates.py`. See clause-by-clause mapping below.

## Clause -> fulfilling change

- Proposal clause 1 (write `docs/specs/wake-routing.md`): fulfilled by
  new file `docs/specs/wake-routing.md` — nine-row table (7 mechanical,
  2 judgment), the two human-only edges, the first-build approval guard,
  the finding-return edge, phrased in board vocabulary
  (`loop_state`/`verdict`/`addressed_to`/`upstream`), no contract
  section numbers.
- Proposal clause 2 (reword `wakes.py`): fulfilled by comment/docstring
  edits only. Every `§3`/`§5`/`§14`/`§15`/`§18`/`§19` attribution now
  points at `docs/specs/wake-routing.md`; `§1`/`§2`/`§6`/`§9`/`§12`
  references left untouched (those describe consumption/staleness/board
  mechanics outside the routing table's scope, per the proposal's exact
  clause). `_rows()`, `JUDGEMENT`, `HUMAN_ONLY`, `Row`, and every branch
  condition are byte-identical — `git diff` on `wakes.py` touches only
  string/comment lines.
- Proposal clause 3 (reword README.md): fulfilled — the four spots
  (file-purpose table line 63, wake walkthrough lines 281/316, §3/§5
  disagreement note lines 508-510) now cite
  `docs/specs/wake-routing.md`.
- Proposal clause 4 (add equivalence test): fulfilled by
  `t_wake_routing_doc_matches_rows` in `test_gates.py` — parses the
  markdown tables in `docs/specs/wake-routing.md`, extracts the role
  column, asserts the set equals `spawn.ROLES`. Fails if the doc and
  `wakes.py`'s role set drift.
- Proposal clause 5 (test run): `python3 test_gates.py` run once. All 10
  existing `t_wake_*` cases plus the new `t_wake_routing_doc_matches_rows`
  pass unmodified (verified directly via `test_gates.t_wake_*()` calls,
  since the full-suite run hits an unrelated sandbox read-only-FS error
  in `t_repo_local_claude_config_stops_the_spawn` that reproduces
  identically on the pre-change tree via `git stash` — confirmed
  pre-existing, not caused by this change).

## What did not work

- None — the write set matched the proposal exactly; no plan changes
  mid-build.

## Hunt

No warrant-hunter dispatch this round: the change is comment/docstring
rewording plus one new doc and one new structural test, with the
proposal itself requiring byte-identical `_rows()` logic — no new
runtime surface for a hunter to probe. Verified instead by direct
before/after diff review confirming zero non-comment lines changed in
`wakes.py`.

## Test plan (verified)

- `python3 test_gates.py` — full run hits the pre-existing sandbox
  OSError above (confirmed present on the pre-change tree too, not
  introduced here).
- Direct invocation of every `t_wake_*` test function (11 total:
  10 pre-existing + 1 new) — all pass.
- `python3 -c "import ast; ast.parse(open('wakes.py').read())"` —
  syntax OK.

## Open findings

None.
