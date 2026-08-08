# issue-472 current-state survey

## Scope named by the issue

Batch B of the issue-467 ADR: rows #318 (approval-request content shape),
#363 (generator-not-symptom), #379 (constraint-framed choice must be
re-checked). Touches: `gates/gates.py`, `gates/ci.py`, new
`gates/approval_request_shape.py` and `gates/open_work.py`. Batch A
(issue-471, merged in `9554c53`) already added the shared 13-row
`ISSUE_467_DISPOSITION_ROWS` table and `t_class_b_disposition_rows_cited`
to `gates/test_boundary.py`; this batch extends the citation map, it does
not recreate the table.

## What already exists for each row

**#318 (approval-request shape).** Not undelivered from scratch —
`on-the-record/hooks/stop-gate.sh` (added for issue #411, live on `main`)
already runs a Stop-hook structural check on the orchestrator's own
`last_assistant_message`: when the reply looks approval-shaped (regex
trigger on "승인 요청" / "please approve" / etc.), it requires an issue
reference (`#<n>`), a change statement, and a risk/tradeoff statement, else
returns `additionalContext` asking for a same-turn correction. The three
regexes and the missing-clause list live inline in a Python heredoc inside
the shell script — there is no importable Python module and no `gates/`
test file exercising this logic directly. `run.md` step 5 (lines 84-116)
separately carries prose contract text for phase-1/phase-2 approval
requests (four required items: what/why/what-changed/how-verified) but
that prose has no named check behind it — `gates/test_boundary.py` has no
row for #318 yet (`ISSUE_467_DISPOSITION_ROWS` lists it, uncited).
Nothing under `gates/` currently imports or unit-tests stop-gate.sh's
clause logic.

**#363 (generator-not-symptom).** No delivery anywhere. `proposal-shape-
gate.sh` (a separate plugin hook, not `gates/`) enforces the seven-section
phase-1 proposal shape (files/Request/Constraints/Rationale/What will be
done/Out of scope/How you'll know it worked) but has no "## Generator"
heading requirement and is not part of this repo's `gates/` tree (it lives
in the harness plugin, out of this batch's write set). No proposal
template or check anywhere asks whether the change addresses the
generator or only an instance. The issue's own acceptance text pre-empts
the obvious shallow answer: a present-but-unexamined "## Generator"
heading is named as a symptom-fix-for-the-symptom-fix trap, and the issue
asks the delivering batch to say so explicitly if that is the honest
ceiling.

**#379 (constraint-framed choice re-checked).** No delivery anywhere.
Nothing greps open issues/PRs before an actor states "X is not possible" /
frames a workaround choice. The issue itself names the honest ceiling:
"did this actor check before asking" is not computable from question text
alone; what is reachable is (a) the orchestrator's Stop-hook inspection
point (same mechanism stop-gate.sh already uses for #318) and (b) a
mechanical open-issue/open-PR lookup function. Role-session coverage is
explicitly named as the harder, likely-uncovered half.

## Write-set files as they exist today

- `gates/gates.py` (943 lines): retroactivity-rule docstring already
  carries #362's paragraph (Batch A). No approval/generator/open-work
  logic present.
- `gates/ci.py` (538 lines): PR-level `closes-gate` checks (branch/issue
  parsing, phase evidence, CI-claim checks). No hook into Stop-hook output
  or issue/PR-lookup logic — this file's checks run against merged PR
  metadata via `gh api`/`git`, a different trust boundary than "did the
  orchestrator check before asking."
- `gates/test_boundary.py` (267 lines): holds `GATE_PORTING_ISSUES` /
  `t_gate_porting_rows_are_ported_or_justified` (issue #457 precedent) and
  `ISSUE_467_DISPOSITION_ROWS` / `t_class_b_disposition_rows_cited` (Batch
  A). `_ISSUE_467_BATCH_A_CITATIONS` currently maps only {362, 390, 412} →
  file paths; this batch adds {318, 363, 379}.
- `gates/approval_request_shape.py`, `gates/open_work.py`: do not exist.
- `on-the-record/commands/run.md`: has the #362/#390/#412 contract
  sections from Batch A (lines 374-396) and the pre-existing approval-
  request prose (lines 84-116); no #318/#363/#379-specific contract
  section citing a named check yet.
- `on-the-record/hooks/stop-gate.sh`: live Stop-hook check for #318's
  issue/change/risk clauses; not part of this batch's write set (the
  issue scopes this batch to `gates/`, not `hooks/`), but its clause logic
  is the thing `gates/approval_request_shape.py` reuses/tests so the two
  don't drift.

## Adjacent precedent (issue #457, #471)

`GATE_PORTING_ISSUES` + `t_gate_porting_rows_are_ported_or_justified`
(`test_boundary.py:93-175`) is the established shape for "N issues, each
either has a named citation or an explicit justification comment" — Batch
A's `t_class_b_disposition_rows_cited` reuses that shape for the 13-row
issue-467 table. This batch follows the same reuse: extend
`_ISSUE_467_BATCH_A_CITATIONS`, do not invent a new table shape.

## Open unknowns going into the proposal

- Whether #318's `gates/` check re-implements stop-gate.sh's regex logic
  or imports a shared module `stop-gate.sh` also calls. Since
  `stop-gate.sh` invokes its check as an inline heredoc (not a `gates/`
  import today, and rewiring the hook script is outside this batch's
  `gates/`-only write set), the proposal resolves this by extracting the
  three-clause logic into `gates/approval_request_shape.py` as a pure,
  independently testable function, without editing `stop-gate.sh` itself
  (out of scope, flagged as a follow-up in the proposal).
- Whether #363's check can be more than presence-only. Per the issue's own
  trap warning, this survey found no mechanical way to verify that
  "## Generator" content is a real analysis rather than filler — the
  proposal states this ceiling explicitly rather than presenting a
  presence check as if it verified substance.
- Whether #379's open-work lookup can run offline in a test (no network).
  It cannot query live `gh` state in a unit test; the proposal scopes the
  named check to the lookup function's query-construction/parsing logic,
  not a live network assertion, and states that ceiling explicitly too.
