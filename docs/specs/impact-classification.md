---
name: impact-classification
description: >
  Four-axis structural impact classification (issue #511), replacing
  `gates/risk_report.py`'s low/high binary. Implemented in
  `gates/risk_report.py:classify_axes()`.
---

# Impact classification

Every axis is derived mechanically from the target repo's structure —
never from reading proposal prose for intent (issue #511 requirement 1).
Each grade is a machine-checkable objective condition (requirement 2,
AIAG-VDA FMEA's anchored-scale shape). Axes are never summed or averaged
(requirement 3); see [[standing-decisions]] for the dominant-axis rule
text and the s19 amendment it is part of.

Grades run 1 (lowest) .. 4 (`AXIS_MAX`, highest). Unparseable or
undecidable input takes grade 4, fail-closed — implemented once per axis
in `gates/risk_report.py`, matching the file-level fail-closed default
already in `classify()`.

## Axes

1. **Blast radius** (`blast_radius_grade`) — count of roles whose
   `roles/*.json` `write_scope` overlaps the touched paths, plus the
   count of other open proposals whose own `files:` write-set intersects
   this one. 0–1 → grade 1, 2–3 → grade 2, 4–6 → grade 3, >6 or
   unreadable `roles/` → grade 4.
2. **Reversibility** (`reversibility_grade`) — path-class ordering, worst
   path wins: leaf docs (grade 1) < application code (grade 2) <
   `gates/`/`roles/`/`agents/`/`on-the-record/`/`.claude-plugin/` or any
   `gates.is_protected()` path (grade 3) < a named contract/approval-rule
   file (`protocol.md`, `protocol.ko.md`, `spawn.py`,
   `docs/specs/approvers.md`) or anything under a `hooks/` directory
   (grade 4). Empty write-set → grade 4.
3. **Propagation** (`propagation_grade`) — count of distinct roles whose
   `write_scope` touches the path plus the number of
   `docs/specs/enforcement-boundary.md` rows naming the touched
   filename. Same 0–1/2–3/4–6/>6 grade bands as blast radius. Unreadable
   `roles/` and unreadable `enforcement-boundary.md` together → grade 4.
4. **Existing signals** (`existing_signal_grade`) — carried forward from
   `classify()` unchanged: any protected path → grade 4; changed-line
   count over `SIZE_THRESHOLD` (30) → grade 3; any change → grade 2; no
   change → grade 1; empty write-set → grade 4.

## Dominant-axis rule

`classify_axes()` returns all four grades plus
`requires_individual_approval = (reversibility_grade == AXIS_MAX)` and
its negation `batchable`. The other three axes are read-only signal for
review ordering inside a batch; they never flip
`requires_individual_approval` on their own — a grade-4 reversibility
axis routes to individual approval even when the other three sit at
grade 1 (`gates/test_risk_report.py::DominantAxisRule`).

## Rejected: weighted composite / RPN

A summed or averaged score was rejected — see the approved proposal
(`docs/issue-511/proposals/2026-08-08-multi-axis-impact-classification.md`)
for the FMEA-RPN-retirement and CVSS-v4-Scope-retirement citations this
rejection is based on.

## Batch-approval wiring

`gates/risk_report.py:batch_blocked(proposals, root)` returns the subset
of a proposal batch whose `requires_individual_approval` is true.
`on-the-record/hooks/impact-guard.sh` is the `PreToolUse`/`Bash` hook
that calls the same classification inline and denies a batch-merge
Bash command containing two or more `gh pr merge` invocations when any
one of them targets a high-reversibility proposal (issue #511
requirement 5, 7).
