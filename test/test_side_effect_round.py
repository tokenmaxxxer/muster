#!/usr/bin/env python3
"""issue-497 — side-effect round: repro for the one reproduced finding
(attempt 5, retired-Actions edge). See docs/issue-497/reports/defect-verification.md
for the full six-attempt outcome table; the other five attempts are
not-reproduced and have no runnable repro here by design.

  python3 -m pytest -q test/test_side_effect_round.py
"""
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "acceptance_gate", ROOT / "gates" / "acceptance_gate.py"
)
acceptance_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(acceptance_gate)
check_issue_body = acceptance_gate.check_issue_body


def test_acceptance_gate_flags_phantom_github_workflows_reference():
    """attempt 5 repro, fixed (issue-499): `.github/workflows/` is confirmed
    absent from the repo (gates/test_boundary_workflow_migration.py, retired
    by #460 with no replacement path). acceptance_gate.py's _ARTIFACT_REF
    regex no longer accepts a backtick-quoted `.github/workflows/...` path
    as satisfying the executable-artifact-reference requirement — an issue
    citing that path can never execute it, so the gate now flags it as
    prose-only instead of passing it.
    """
    body = (
        "## Acceptance\n"
        "- checked via `.github/workflows/ci.yml` on every push\n"
        "empty state: not applicable — repo has no workflows fixture\n"
        "provenance: read\n"
    )
    violations = check_issue_body(999, body)
    assert violations != [], (
        "expected the gate to flag a phantom .github/workflows/ reference "
        f"as invalid (retired by #460); got violations={violations!r}"
    )
