---
status: proposed
files:
  - docs/decisions/2026-08-07-check-must-not-retroactively-invalidate.md
  - gates/gates.py
  - test_gates.py
  - docs/issue-362/reports/implementation.md
---

## Request

#362, filed from the #284 closes-gate incident: a check must not fail an
artifact for a reason its author could not have addressed at authoring time.
Scope: (1) give the rule a durable home so it constrains future gate
authoring instead of being rediscovered per gate, (2) audit the existing
gates for other instances of the same shape, (3) land an executable artifact
per #310 — and say plainly if a full mechanical check isn't possible.

## Constraints

- Do not duplicate #284/#312's closes-gate fix — that PR (#364) is open and
  owns that instance.
- Per #362's own acceptance text: a per-run assertion inside a gate is
  probably the wrong shape, because "could the author have satisfied this at
  authoring time" is a property of the check's *design*, not of one run. The
  fix cannot pretend to be more mechanical than that.
- Per #310: prose alone does not discharge the issue; whatever ships must
  include something that runs and fails on regression.

## Rationale

Considered making `record_enums` itself refuse to tighten an already-declared
enum value (reject a `roles/<role>.json` edit that would drop a value a live
record currently uses). Rejected: that requires the gate to reconstruct the
history of every open PR's record state at edit time, which `gates/gates.py`
has no access to (it only sees one PR's diff per invocation) and which #362
already names as the wrong shape — a per-run check cannot verify a
design-level property.

Considered folding the rule only into the `docs/decisions/` record with no
code change. Rejected: `docs/decisions/` is read by someone looking up *why*
a past decision was made, not proactively by someone about to write a new
gate — `gates/gates.py`'s own docstring is the file every gate author already
opens, so the pointer belongs there too, one paragraph, not the full
reasoning duplicated inline.

## What will be done

- Add `docs/decisions/2026-08-07-check-must-not-retroactively-invalidate.md`:
  states the rule, the three-property test from #362 (unpreventable at
  authoring time / system-caused transition / repeated unactionable
  notification), and the audit table from the survey (closes-gate — tracked
  by #284/#312, not duplicated; `record_enums` — new confirmed instance;
  `deps`/`registry_status` — considered and explicitly ruled out, with why).
- Add one paragraph to `gates/gates.py`'s module docstring naming the rule
  and pointing at the decision record, next to the existing "how a gate
  dies" reasoning it is already adjacent to.
- Add a verdict-stability test in `test_gates.py` for `record_enums`: build a
  fixed board-repo record file/commit, run `record_enums` against two
  different `roles/<role>.json` enum declarations (representing the tool
  state before and after an unrelated edit), and assert the verdict does
  *not* differ. Mark it `@pytest.mark.xfail(strict=True, reason=...)`
  pointing at this decision record and #362 — it demonstrates the instance
  is real and reproducible today (XFAIL) without turning the suite red for a
  known, tracked, and explicitly out-of-scope gap; `strict=True` means the
  moment someone fixes `record_enums`'s live-state read, this test starts
  reporting XPASS and CI forces the xfail marker's removal instead of
  letting a silent fix go unnoticed.
- Write the phase-2 record at `docs/issue-362/reports/implementation.md`
  stating explicitly that `record_enums`'s behavior itself is not changed by
  this pass — the audit and the durable rule are the deliverable; fixing
  `record_enums`'s live-state read is separate follow-on work, named as such
  in the decision record so it isn't lost.

## Out of scope

- Fixing `record_enums`'s live external-state read (making it pin to the
  enum state at the record's own commit, or some other mechanism) — that is
  a design decision on its own (how would a board-repo record know the
  on-the-record tool's historical config?) and belongs to a follow-on issue,
  named in the decision record.
- closes-gate itself — owned by #284/#312 (PR #364).
- `deps`/`registry_status` — audited and explicitly excluded as a different
  shape (real-world package existence, not a system-caused reclassification),
  not carried forward as a task.

## How you'll know it worked

- `docs/decisions/2026-08-07-check-must-not-retroactively-invalidate.md`
  exists and is linked from `gates/gates.py`'s docstring.
- `python3 -m pytest test_gates.py -k record_enums` runs the new
  verdict-stability test; it reports `XFAIL` (strict), proving the instance
  is real and reproducible today without failing the suite for a gap this
  pass explicitly does not fix. The test's docstring states plainly that
  this is a tracked regression test for follow-on work, not a passing
  guarantee.
