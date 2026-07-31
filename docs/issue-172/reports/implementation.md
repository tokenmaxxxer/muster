---
role: implementation
subject: issue-172
loop_state: progressed
---

# Implementation — `spawn.py flows [--json]` + `docs/specs/flows-schema.md`

Proposal: [[flows-json.md]](../proposals/flows-json.md), approved via
`APPROVE issue-172/implementation` (issue comment, single-account mode).

## What shipped

- `spawn.py`: new `flows` verb (`flows_payload()`, `flows()`), wired into
  `main()`'s dispatch next to `ps`/`closure-sweep`. `--json` flag added to
  the shared argparse. Read-only — no mutation, no posting, matching
  `status()`'s own invariant.
- New helpers: `_pr_list_all()` (one repo-wide `gh pr list` call, replaces
  the O(subjects×roles) `_pr_for_branch` pattern for this verb per the
  proposal's §3 rate-limit design), `_pr_approved()` (two-account PR-review
  check + `APPROVE issue-<n>/<role>` comment check, reusing
  `_approvers`/`_issue_comments`), `_ledger_read()`/`_ledger_issue()`
  (reads `runs/ledger.jsonl`, derives issue from `board_delta` paths),
  `_stage_for()` (loop_state → stage mapping with `stage_derived` fallback).
- `docs/specs/flows-schema.md`: the frozen output contract — all five
  sections, versioning policy (bare int, breaking-only bumps), the
  1+1+S+S GitHub call-count contract, and the local-`runs/`-provenance
  note for `sessions[]`/`ledger[]`.
- Tests: `test_spawn.py::FlowsPayload` (6 cases) — schema top-level keys,
  stage mapping + unmapped fallback, decision_queue from an open PR,
  sessions alive/dead + ledger verdict lookup, per-issue ledger
  aggregation + `unattributed` bucket, hygiene (`closure_sweep` passthrough
  + `unapproved_open_prs`). All `gh`-hitting helpers monkeypatched, no live
  network in tests.

## Deviation from the proposal (schema-doc/implementation reconciliation)

The proposal's field examples used `"issue-<n>"` string form for the
`issue` field in `decision_queue[]`/`flows[]`/`ledger[]`. While writing the
schema doc and implementation in parallel, the schema doc settled on plain
integer issue numbers (`"issue": 172`) for consistency with how consumers
(repo-status-board) would naturally key on issue numbers. Implementation
was aligned to the schema doc's integer form after the fact — this is the
single source of truth going forward; `flows_payload()`'s `issue` fields
are all bare integers, not `"issue-<n>"` strings. Human-table output
(`flows()` without `--json`) still prints the `issue-<n>` label for
readability; only the JSON payload uses the bare integer.

## Verification

- `python3 -m pytest test_spawn.py -q` — 116 passed (110 pre-existing + 6
  new).
- `python3 spawn.py flows --json` and `python3 spawn.py flows` run
  against this repo's own board — both produce well-formed output (2
  subjects, 0 open decision-queue items at time of writing).

## Non-goals (unchanged from proposal)

No mutation, no posting, no exit-code-as-alert semantics, no dashboard
polling-cadence decision.
