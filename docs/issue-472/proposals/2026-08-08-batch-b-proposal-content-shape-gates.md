---
status: proposed
files:
  - gates/approval_request_shape.py
  - gates/open_work.py
  - gates/test_approval_request_shape.py
  - gates/test_open_work.py
  - gates/test_boundary.py
  - on-the-record/commands/run.md
  - docs/issue-472/reports/implementation.md
---

## Request

Batch B of the issue-467 ADR: deliver deployed-surface enforcement for
#318 (an approval request must name issue/change/risk, not just point at
a PR), #363 (a proposal must state what produced the issue and whether
this change removes the generator or only an instance), and #379 (an
actor must check for open issues/PRs before framing a constraint as fixed
choices). Each needs `run.md` contract text plus a named check that fails
on regression, and the shared `ISSUE_467_DISPOSITION_ROWS` table
(`gates/test_boundary.py`, added by Batch A) gets citations for these
three rows.

## Constraints

- Per issue #472: only this batch's three rows get citations added to
  `_ISSUE_467_BATCH_A_CITATIONS` — the diff must not touch Batch A's
  {362, 390, 412} entries or remove any existing `t_*` function.
- Per issue #472's stated write set: only `gates/gates.py`, `gates/ci.py`,
  a new `gates/approval_request_shape.py`, and a new `gates/open_work.py`
  are the code surfaces — `on-the-record/hooks/stop-gate.sh` is not in
  this batch's write set, so #318's check must not require editing it;
  the survey found stop-gate.sh's clause logic is inline and untested, so
  this batch extracts an equivalent, independently testable function into
  `gates/approval_request_shape.py` rather than rewiring the hook.
- Per #363's own acceptance text: a presence-only "## Generator" heading
  check must not be presented as if it verified the analysis — the
  `run.md` contract text and the check's own docstring must say plainly
  that content is unverified.
- Per #379's own acceptance text: the named check is scoped to what is
  mechanically reachable — the open-issue/open-PR lookup's query
  construction — not a live-network assertion inside a unit test.
- No new dependency, no new secret, no `.github/workflows/*.yml` (Actions
  is retired, per the issue-467 ADR already applied in Batch A).

## Rationale

Considered making `gates/approval_request_shape.py` import and drive
`stop-gate.sh` directly (e.g. shelling out to the hook script from a
`gates/` test) so there is exactly one copy of the clause logic. Rejected:
issue #472 scopes this batch's write set to `gates/` files only —
`stop-gate.sh` lives in `on-the-record/hooks/` and rewiring it to import
from `gates/` is a cross-cutting change to a live Stop-hook (risk of
breaking every session's stop path) that the issue does not authorize for
this batch. Extracting an equivalent pure function into
`gates/approval_request_shape.py` gives #318 a named, independently
runnable check now; keeping the two implementations in sync is flagged as
a follow-up rather than solved by silently widening the write set.

Considered giving #363 a check that inspects "## Generator" content for
one of the two sanctioned answers ("removes the generator" / "instance
only, filed as #N") via a keyword/pattern match. Rejected: the issue's own
acceptance text calls this exact move out as the trap — a keyword match on
free text is gameable in the same way a bare presence check is, and
presenting it as content verification would be dishonest about what it
catches. The proposal instead keeps the check to presence-of-heading and
states the ceiling explicitly in both the check's docstring and the
`run.md` contract text, per the issue's own instruction to say so if that
is the honest limit.

## What will be done

- `gates/approval_request_shape.py` (new): a pure function
  `missing_approval_clauses(text: str) -> list[str]` — issue-reference,
  change-statement, and risk/tradeoff regexes ported from
  `stop-gate.sh`'s inline heredoc, returning the same three possible
  missing-clause labels. A second function,
  `has_generator_section(proposal_text: str) -> bool`, checks for a
  `## Generator` (or `## 생성자`) heading in a proposal document; its
  docstring states plainly that only presence is checked, not content.
- `gates/test_approval_request_shape.py` (new): red-green tests —
  `missing_approval_clauses` against an approval-shaped string missing
  each clause in turn and against a complete one; `has_generator_section`
  against a proposal fixture with/without the heading.
- `gates/open_work.py` (new): `build_open_work_query(keyword: str) -> dict`
  constructing the `gh issue list --search` / `gh pr list --search` query
  parameters for a constraint keyword (no network call inside the
  function itself — callers pass the result to `subprocess`); docstring
  states the network-lookup half is out of this check's reach in a unit
  test.
- `gates/test_open_work.py` (new): asserts the query-construction shape
  for representative keywords (e.g. rejects an empty keyword, builds the
  expected `--search` string).
- `gates/test_boundary.py`: extend `_ISSUE_467_BATCH_A_CITATIONS` with
  `318: gates/test_approval_request_shape.py`,
  `363: gates/test_approval_request_shape.py`,
  `379: gates/test_open_work.py` — additions only, `t_class_b_
  disposition_rows_cited` already iterates the dict so no other change to
  that function is needed.
- `on-the-record/commands/run.md`: add one contract section (mirroring
  Batch A's #362/#390/#412 sections) naming #318/#363/#379, the run.md
  requirement each backs, and the named check each row cites.
- `docs/issue-472/reports/implementation.md`: phase-2 record (written when
  phase 2 opens).

## Out of scope

- Rewiring `stop-gate.sh` to import `gates/approval_request_shape.py`
  (would keep the two implementations in sync but touches `hooks/`,
  outside this batch's write set — filed as a follow-up note in the
  phase-2 record, not a new issue, since it is a refactor of already-
  delivered #411 code, not a new requirement).
- A live-network test asserting `gates/open_work.py`'s query actually
  finds an open issue/PR — the honest ceiling per #379's own acceptance
  text.
- Content verification of "## Generator" text — the honest ceiling per
  #363's own acceptance text.
- Wiring `gates/ci.py` into either new check — the issue's write set lists
  `gates/ci.py` among touched files but the survey found no PR-level
  `closes-gate` hook point that fits either check's trust boundary
  (orchestrator chat output and pre-question lookups aren't PR metadata);
  if phase 2 finds a fit, it is noted in the record, not forced here.

## How you'll know it worked

- `gates/test_approval_request_shape.py` and `gates/test_open_work.py`
  are new, named, and red-green (fail before the corresponding function
  exists, pass after).
- `gates/test_boundary.py::t_class_b_disposition_rows_cited` stays green
  with {318, 363, 379} added to `_ISSUE_467_BATCH_A_CITATIONS` and Batch
  A's three rows untouched.
- `run.md` carries contract text for #318/#363/#379 naming their checks,
  matching Batch A's #362/#390/#412 section shape.
