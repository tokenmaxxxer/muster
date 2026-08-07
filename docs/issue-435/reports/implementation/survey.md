# Survey — issue #435

Write set actually touched:
- `gates/test_closes_gate_ci.py` — 13 stubs assigned to `spawn._issue_comments`
  still returned the pre-#287 bare-list shape (`lambda repo, n: [...]`);
  production code (`spawn._issue_comments`, `gates/ci.py:154`) expects
  `(list[dict], bool)` since #287. One stub
  (`t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`)
  also had a second, independent staleness once the unpack crash no
  longer masked it: its `pr_reference._issue_view_body` stub predates
  `acceptance_gate` (issue #310) and has no `## Acceptance` section, so
  `pr_reference.check`'s phase-2 path correctly flagged it — fixed by
  giving that stub a valid Acceptance section.
- `shape_contracts.py` — read in full. Its module docstring and the
  issue-335 proposal scope it to two *external* interfaces spawn.py
  parses (`gh api --paginate --slurp` JSON, Claude CLI `stream-json`
  events). Neither leg inspects a function's own return shape — there was
  no mechanism there for "does this test's stub match the signature of
  the internal function it replaces." That is a third, narrower kind:
  `spawn._issue_comments` is not an external interface, it's this repo's
  own function, and the stub is a hand-typed replacement for it, not a
  parsed payload. So `shape_contracts.py` does not cover this case, by
  design (its docstring scopes it to two interfaces, both external) — not
  an oversight, but also not something to build a parallel mechanism for:
  extending the same module with one generic function keeps one place for
  "does a fixture/stub match the real thing" (issue #376).
- `docs/handbooks/operations.md` — the two self-check sections
  (한국어/English) documented `python3 test_gates.py` only; neither said
  anything about `--ignore=gates`, so there was no config or doc line to
  flip. Confirmed via grep across `.github/workflows/`, `pytest.ini`,
  `pyproject.toml`: no CI job runs pytest at all, and no config sets a
  default `--ignore`. The flag was purely a habit typed on the CLI
  (visible only in various `docs/issue-*/` prose, never in an
  authoritative config). Made the no-ignore run the documented default by
  adding it to both self-check sections with the reason it matters now
  (#398 fixed, so the flag only re-hides `gates/` if it breaks again).

No design decision is open — the failing shape and its fix are fully
specified by #287 (the target return shape) and #398 (why the flag
existed). Scout-directive skip condition applies: pure bugfix.
