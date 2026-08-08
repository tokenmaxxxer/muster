#!/usr/bin/env python3
"""issue-310 — `acceptance_gate.check_issue_body`의 단위테스트.

네트워크·GitHub 없이 도는 것만(`test_gates.py`/`test_closes_gate_ci.py` 와
같은 관례). `pr_reference.py`/`check()`와의 배선은 `check_issue_body`가
순수 함수라 여기서 직접 검증한다 — `gates/test_closes_gate_ci.py` 가
`pr_reference.check_body`를 검증하는 것과 같은 분리.

  python3 gates/test_acceptance_gate.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import acceptance_gate


def t_prose_only_acceptance_blocks():
    body = """## Acceptance
- It should work correctly and users should be happy.
- The team agrees this is done.
"""
    bad = acceptance_gate.check_issue_body(310, body)
    assert bad, "prose-only Acceptance should be a violation"


def t_artifact_reference_passes():
    body = """## Acceptance
- `gates/test_acceptance_gate.py` run and shown passing.
- empty state: not applicable — regression test, no empty-state case.
- provenance: executed-unit
"""
    assert acceptance_gate.check_issue_body(310, body) == []


def t_gates_workflow_path_passes():
    body = """## Acceptance
- CI job at `.github/workflows/ci.yml` must be green.
- empty state: not applicable — CI status has no empty-state case.
- provenance: executed-live
"""
    assert acceptance_gate.check_issue_body(310, body) == []


def t_gate_colon_line_passes():
    body = """## Acceptance
- gate: acceptance_gate
- empty state: not applicable — gate invocation has no empty-state case.
- provenance: executed-unit
"""
    assert acceptance_gate.check_issue_body(310, body) == []


def t_unverifiable_escape_passes():
    body = """## Acceptance
unverifiable: this is a subjective UX judgment with no mechanical check.
"""
    assert acceptance_gate.check_issue_body(310, body) == []


def t_missing_acceptance_section_blocks():
    body = "## Request\nDo the thing.\n"
    bad = acceptance_gate.check_issue_body(310, body)
    assert bad, "missing '## Acceptance' section should fail closed"


def t_acceptance_heading_case_and_level_insensitive():
    body = """### acceptance
- `test/foo.py` passes.
- empty state: not applicable — regression test, no empty-state case.
- provenance: executed-unit
"""
    assert acceptance_gate.check_issue_body(310, body) == []


def t_only_reads_acceptance_section_not_whole_body():
    body = """## Acceptance
No artifact here, just prose.

## Out of scope
- `gates/unrelated.py` mentioned here should not count.
"""
    bad = acceptance_gate.check_issue_body(310, body)
    assert bad, "an artifact reference outside the Acceptance section must not count"


def t_artifact_reference_without_empty_state_or_provenance_blocks():
    body = """## Acceptance
- `gates/test_acceptance_gate.py` run and shown passing.
"""
    bad = acceptance_gate.check_issue_body(416, body)
    assert bad, "artifact reference with no empty state/provenance must block"
    assert any("empty state" in b for b in bad), bad
    assert any("provenance" in b for b in bad), bad


def t_empty_state_and_provenance_present_passes():
    body = """## Acceptance
- `gates/test_acceptance_gate.py` run and shown passing.
- empty state: `gates/test_acceptance_gate.py::t_missing_acceptance_section_blocks`
- provenance: executed-unit
"""
    assert acceptance_gate.check_issue_body(416, body) == []


def t_unverifiable_exempts_empty_state_and_provenance():
    body = """## Acceptance
unverifiable: this is a subjective UX judgment with no mechanical check.
"""
    assert acceptance_gate.check_issue_body(416, body) == []


def t_empty_state_not_applicable_passes():
    body = """## Acceptance
- `gates/test_acceptance_gate.py` run and shown passing.
- empty state: not applicable — pure read-only query, no "nothing exists yet" case.
- provenance: executed-unit
"""
    assert acceptance_gate.check_issue_body(416, body) == []


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("t_") and callable(f)]
    _run(tests)
