#!/usr/bin/env python3
"""issue #319 실행 가능 수용 기준.

  python3 test_risk_report.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "gates"))
sys.path.insert(0, str(Path(__file__).parent))
import risk_report


def t_docs_only_small_change_is_low():
    risk = risk_report.classify(["docs/handbooks/foo.md"], 5, 3)
    assert risk == "low", risk


def t_protected_path_is_high_regardless_of_size():
    for path in ["gates/gates.py", ".github/workflows/ci.yml", "auth.py",
                 "migrations/0001.sql"]:
        risk = risk_report.classify([path], 1, 0)
        assert risk == "high", (path, risk)


def t_oversized_docs_change_is_high():
    risk = risk_report.classify(["docs/handbooks/foo.md"],
                                 risk_report.SIZE_THRESHOLD + 1, 0)
    assert risk == "high", risk


def t_missing_or_unparseable_files_is_high():
    assert risk_report.classify([], 0, 0) == "high"
    assert risk_report._parse_files("status: proposed\nno files here\n") is None
    assert risk_report._parse_files("status: proposed\nfiles:\n") is None


def t_blank_line_inside_files_block_does_not_truncate_write_set():
    # warrant-hunter finding, before-landing dispatch: a blank line between
    # `- path` entries used to silently truncate the parse, dropping later
    # (possibly protected) paths and turning a "high" proposal into "low".
    text = ("status: proposed\n\nfiles:\n  - src/harmless.py\n\n"
            "  - gates/gates.py\n")
    files = risk_report._parse_files(text)
    assert files == ["src/harmless.py", "gates/gates.py"], files
    assert risk_report.classify(files, 0, 0) == "high"


def t_report_orders_high_before_low_and_drops_nothing():
    proposals = [
        {"path": "docs/issue-1/proposals/a.md", "files": ["docs/a.md"],
         "added": 2, "removed": 0},
        {"path": "docs/issue-2/proposals/b.md", "files": ["gates/gates.py"],
         "added": 1, "removed": 0},
        {"path": "docs/issue-3/proposals/c.md", "files": [], "added": 0,
         "removed": 0},
    ]
    out = risk_report.report(proposals)
    assert out.count("docs/issue-1/proposals/a.md") == 1
    assert out.count("docs/issue-2/proposals/b.md") == 1
    assert out.count("docs/issue-3/proposals/c.md") == 1
    idx_b = out.index("docs/issue-2/proposals/b.md")
    idx_c = out.index("docs/issue-3/proposals/c.md")
    idx_a = out.index("docs/issue-1/proposals/a.md")
    assert idx_b < idx_a and idx_c < idx_a, out


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("t_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as e:
                fails += 1
                print(f"FAIL {name}: {e}")
    sys.exit(1 if fails else 0)
