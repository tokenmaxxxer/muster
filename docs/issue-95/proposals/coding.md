# Issue #95 — Phase 1 Proposal: relocate wake-routing ownership into this repo

## files: (frozen write set)

- `docs/specs/wake-routing.md` (new): the routing table as this repo's
  own documented artifact — nine role x trigger rows (the seven
  mechanically-judged rows, `product`/`ops` judgment rows), the
  findings-resolved re-verify edge, and the s19 first-build approval
  guard, described in terms of this repo's board state (`loop_state`,
  `verdict`, `addressed_to`, upstream sha), not in terms of contract
  section numbers.
- `wakes.py`: module docstring and inline comments only — every
  reference to "계약 §3/§5/§14/§15/§18/§19 이 정의한다/명시한다" reworded to
  point at `docs/specs/wake-routing.md` as the source this file
  embodies. `_rows()`, `JUDGEMENT`, `HUMAN_ONLY`, `Row`, and every
  branch condition inside `_rows()` stay byte-identical — no edge
  changes.
- `README.md`: the four existing "contract §3" mentions (file-purpose
  table line ~63, the `wake` walkthrough lines ~280-281 and ~316, and
  the §3/§5 disagreement note lines ~508-509) reworded to point at
  `docs/specs/wake-routing.md`.
- `test_gates.py`: one new equivalence test asserting the routing doc
  and `wakes.py`'s actual branches agree in coverage (every documented
  row/edge has a corresponding case already exercised in this file, and
  no branch in `_rows()` is undocumented) — a small structural check,
  not a re-implementation of the routing logic.

**Explicitly excluded from this write set:** the canonical contract
itself (lives outside this repo, out of scope per issue — follow-ups
strip it), the nine rulebooks, and any change to `_rows()`'s actual
conditions, `spawn.py`'s wake-consumption call sites, or `test_spawn.py`
(both already pass unmodified and this issue changes no behavior they
exercise).

## Request (paraphrased)

Today `wakes.py` implements the WAKES-ON routing table correctly, but
its comments and README describe it as sourced from the canonical
contract's §3 (plus §15/§19 edges) — meaning any routing change (new
role, rerouted edge) would read as a contract amendment rather than a
change to this repo's own artifact. Move ownership: write the routing
table as this repo's own doc, have `wakes.py`'s comments describe
themselves as embodying that local doc, and leave every actual routing
decision (`_rows()`'s logic) untouched.

## Constraints

- Zero behavior change: `_rows()`'s branch conditions, `JUDGEMENT`,
  `HUMAN_ONLY`, `Row` fields, `evaluate()`/`fresh()`/`consume()`/
  `report()` signatures and logic are not touched. Only comments/
  docstrings in `wakes.py` change.
- The new doc must cover exactly what's live today: the seven
  mechanically-judged rows (feasibility/hypothesis, coding's four
  wake-branches funneled through the shared s19 guard, ux-design,
  verify, reflect, qa, review), the two judgment-only rows (product,
  ops), the two human-only edges (findings-resolved re-verify, round-
  done value gate), and the §3/§5 table disagreement wakes.py already
  resolves in §5's favor (documented as this repo's own resolved
  decision, not a discrepancy to flag against an external table).
- `test_gates.py`'s nine existing `t_wake_*` cases must keep passing
  unmodified — they are the behavior baseline.

## What will be done (phase 2, after approval)

1. Write `docs/specs/wake-routing.md`: the role x trigger table plus
   the two human-only edges and the s19 guard, phrased against this
   repo's board vocabulary (loop_state values, verdict, addressed_to,
   upstream) so it stands alone without the external contract.
2. Reword `wakes.py`'s docstring/comments to cite the new doc as what
   this file embodies, keeping every existing Korean explanatory note
   about *why* a branch exists (e.g. the qa-latch note, the §3/§5
   disagreement resolution) — only the attributed source changes, not
   the reasoning.
3. Reword the four README.md spots similarly.
4. Add one equivalence test to `test_gates.py`: parse
   `docs/specs/wake-routing.md`'s row list (or a light structural
   marker in it) and assert it names the same role set `wakes.ROLES`-
   adjacent branches cover, catching future drift between the doc and
   `_rows()`.
5. Run `python3 -m pytest test_gates.py test_spawn.py` (or the repo's
   existing test runner) once, confirm all pass unmodified plus the new
   case.

## Out of scope

- Stripping contract §3/§15 text or README mentions from core / the
  nine rulebooks (explicit follow-up issues, blocked on this one).
- Any routing edge change, new role, or new trigger.
- Automating the two human-only edges.

## How we'll know it worked (test plan)

- Existing `test_gates.py` `t_wake_*` cases (9) and `test_spawn.py`'s
  wake-consumption tests pass unmodified — proves no behavior drift.
- New equivalence test in `test_gates.py` fails if the doc and
  `wakes.py` disagree on the row/edge set, passes today.
- Manual read-through: `docs/specs/wake-routing.md` is readable and
  correct standalone, with no remaining "계약 §3" style external
  citation as the routing table's source of truth in `wakes.py` or
  README.md.
