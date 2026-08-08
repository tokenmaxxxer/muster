#!/usr/bin/env python3
"""issue-472 — gates/open_work.py 의 red-green 테스트.

  python3 gates/test_open_work.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from open_work import build_open_work_query  # noqa: E402


def t_build_open_work_query_rejects_empty_keyword():
    try:
        build_open_work_query("")
    except ValueError:
        pass
    else:
        raise AssertionError("empty keyword must raise ValueError")


def t_build_open_work_query_rejects_whitespace_only_keyword():
    try:
        build_open_work_query("   ")
    except ValueError:
        pass
    else:
        raise AssertionError("whitespace-only keyword must raise ValueError")


def t_build_open_work_query_builds_expected_search_string():
    q = build_open_work_query("gates/open_work.py")
    assert q["issue_search"] == "is:open gates/open_work.py"
    assert q["pr_search"] == "is:open gates/open_work.py"


def t_build_open_work_query_strips_surrounding_whitespace():
    q = build_open_work_query("  approval shape  ")
    assert q["issue_search"] == "is:open approval shape"


def t_build_open_work_query_builds_gh_cli_args():
    q = build_open_work_query("open_work")
    assert q["issue_args"] == [
        "gh", "issue", "list", "--state", "open", "--search", "is:open open_work",
    ]
    assert q["pr_args"] == [
        "gh", "pr", "list", "--state", "open", "--search", "is:open open_work",
    ]


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
