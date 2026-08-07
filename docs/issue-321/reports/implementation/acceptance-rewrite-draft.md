## Acceptance

Per #310, prose does not discharge this. Each criterion below names the
executable artifact that fails when it regresses; a criterion with no
mechanical check says so explicitly via `unverifiable:`.

- The operator's requirement is recorded as a first-class, identifiable
  entry (verbatim quote + source issue), not folded into prose.
  check: `docs/specs/requirements.md` (the `R001` entry — `quote` and
  `source_issue` fields)
- A registered requirement's enforcement cannot silently regress: if its
  named artifact stops existing at HEAD, the check fails instead of
  passing quietly.
  gate: `gates/gates.py::requirement_registry`
- The gate is actually wired into CI, not just defined.
  check: `test_gates.py::t_ci_check_wires_requirement_registry`
- Re-checkability against the current system state (not only the issue
  that preceded it) — i.e. the registry is consulted at HEAD on every
  run, not snapshotted once.
  unverifiable: whether future readers actually re-check against current
  state, as opposed to merely being able to, is a practice/discipline
  question no test can observe from the repo alone; the mechanism above
  (`requirement_registry` failing on a stale `check` path) is the
  practical stand-in this issue can enforce.
