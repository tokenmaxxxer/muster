#!/usr/bin/env python3
"""issue-472 — gates/approval_request_shape.py 의 red-green 테스트.

  python3 gates/test_approval_request_shape.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from approval_request_shape import (  # noqa: E402
    has_generator_section,
    missing_approval_clauses,
)

COMPLETE = (
    "#472 승인 요청: gates/open_work.py 를 추가하는 변경입니다. "
    "risk: 기존 검사와 충돌할 tradeoff 가 있습니다."
)


def t_missing_approval_clauses_complete_text_has_no_missing():
    assert missing_approval_clauses(COMPLETE) == []


def t_missing_approval_clauses_flags_missing_issue_reference():
    text = "이 변경은 gates/open_work.py 를 추가합니다. risk: tradeoff 있음."
    assert "issue reference (#<n>)" in missing_approval_clauses(text)


def t_missing_approval_clauses_flags_missing_change_statement():
    text = "#472 요청입니다. risk: tradeoff 있음."
    assert "change statement (what changes)" in missing_approval_clauses(text)


def t_missing_approval_clauses_flags_missing_risk_statement():
    text = "#472 요청입니다. gates/open_work.py 를 추가하는 변경입니다."
    assert "risk/tradeoff statement" in missing_approval_clauses(text)


def t_missing_approval_clauses_flags_all_three_when_bare():
    assert missing_approval_clauses("아무 내용도 없는 문장입니다.") == [
        "issue reference (#<n>)",
        "change statement (what changes)",
        "risk/tradeoff statement",
    ]


def t_has_generator_section_true_with_heading():
    text = "# Proposal\n\n## Generator\n\n원인은 X 다.\n"
    assert has_generator_section(text) is True


def t_has_generator_section_true_with_korean_heading():
    text = "# 제안\n\n## 생성자\n\n원인은 X 다.\n"
    assert has_generator_section(text) is True


def t_has_generator_section_false_without_heading():
    text = "# Proposal\n\n## Rationale\n\n이유는 X 다.\n"
    assert has_generator_section(text) is False


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
    sys.exit(0)
