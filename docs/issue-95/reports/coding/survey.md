# Issue #95 — current-state survey

## Skip record (scout-directive)

Scouting skipped: pure relocation of already-fixed routing semantics
(spec forbids any edge change), no product-facing or design decision
open — issue names the exact table to move and requires byte-identical
behavior.

## Where the routing semantics live today

- `wakes.py` is the sole implementation. Its module docstring and
  per-branch comments cite "계약 §3" (contract s3) as the source of
  truth for all nine WAKES-ON rows, "§15" for the findings-resolved
  re-verify edge, and "§19" for the first-build approval gate. The logic
  itself (the `_rows()` function and its seven mechanical branches, plus
  `JUDGEMENT` and `HUMAN_ONLY` dicts) does not read any external
  contract file — it is hardcoded Python. Only the *comments* attribute
  ownership to the external contract.
- `README.md` also attributes ownership to the contract in three spots:
  line 63 (file-purpose table), lines 280-281 ("`wake` evaluates
  contract §3's WAKES-ON table"), line 316 (inline comment on the `wake`
  example command), and line 508-509 (documenting the known §3/§5
  table disagreement wakes.py resolves in §5's favor).
- No local doc in this repo currently states the routing table as this
  repo's own artifact — there is no `docs/specs/wake-routing.md` or
  equivalent.

## Test coverage today

- `test_gates.py` (imports `wakes`) already exercises the seven
  mechanical rows end-to-end via `wakes.evaluate()` /
  `wakes.fresh()` / `wakes.report()`: hypothesis→feasibility,
  acknowledged-hypothesis-goes-quiet, first-build needs scope-approval
  (the s19 guard), rebuild-not-gated, finding→addressed role (the s15-
  style re-verify edge for coding — `t_wake_finding_wakes_the_addressed_role`),
  answered-row-does-not-refire, refires-on-evidence-change, report never
  hides a suppressed row, and per-repo observed-store isolation.
- `test_spawn.py` covers the driver-side consumption of `wakes.fresh`/
  `wakes.observed`/`wakes.consume` (mocked), not the routing logic
  itself.
- No existing test is a documented "equivalence fixture" — i.e. nothing
  currently asserts the *rendered routing doc* (new artifact) matches
  what `wakes.py`'s `_rows()` produces. This is the gap issue #95 asks
  to be covered ("add a fixture-based equivalence check if none covers
  this").

## Write surfaces implied by the issue

- A new first-class doc under `docs/specs/` (repo convention: standing
  specs live at `docs/specs/*.md`, confirmed by `ls docs/specs`)
  documenting the role x trigger routing table, the findings-resolved
  re-verify edge, and the s19 first-build guard, as this repo's own
  artifact.
- `wakes.py`: comments/docstring updated to point at the new local doc
  instead of "계약 §3/§15/§19" as the source of ownership. No logic
  change — `_rows()`, `JUDGEMENT`, `HUMAN_ONLY`, and every branch's
  condition stay byte-identical, since the issue requires identical
  behavior.
- `README.md`: the four spots above reworded to attribute the table to
  the local doc rather than the contract.
- A new equivalence test (likely `test_wake_routing_doc.py` or an
  addition to `test_gates.py`) asserting the doc's table and
  `wakes.py`'s actual branches agree — e.g. every row/edge documented
  in the new doc has a corresponding covered case in `test_gates.py`,
  and vice versa (no undocumented branch, no un-implemented documented
  row).

## Unknowns for the proposal to freeze

- Exact filename/path for the new routing doc (`docs/specs/wake-routing.md`
  proposed; no naming collision found).
- Whether the equivalence check is a new file or an addition to
  `test_gates.py` (frozen in proposal to keep it a single write-set
  entry).
