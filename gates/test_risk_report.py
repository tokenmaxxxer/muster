#!/usr/bin/env python3
"""issue #511 — four-axis structural impact classification.

Covers: each axis's grade boundaries, the dominant-axis rule (worst
reversibility grade alone forces individual approval regardless of the
other three axes), and fail-closed-to-highest-grade on unparseable
input. Plus the pre-existing low/high `classify()` behavior, unchanged.

  python3 gates/test_risk_report.py
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
import risk_report  # noqa: E402


class ClassifyLegacy(unittest.TestCase):
    """issue #319's original acceptance tests, consolidated here from the
    repo-root `test_risk_report.py` (moved, not duplicated — issue #511's
    acceptance requires this exact path, and a second `test_risk_report.py`
    basename trips `gates/test_duplicate_test_basenames.py`)."""

    def test_empty_write_set_is_high(self):
        self.assertEqual(risk_report.classify([], 0, 0), "high")

    def test_protected_path_is_high(self):
        self.assertEqual(risk_report.classify(["gates/gates.py"], 1, 0), "high")

    def test_small_unprotected_change_is_low(self):
        self.assertEqual(risk_report.classify(["docs/proposals/x.md"], 1, 0), "low")

    def test_docs_only_small_change_is_low(self):
        self.assertEqual(risk_report.classify(["docs/handbooks/foo.md"], 5, 3), "low")

    def test_protected_path_is_high_regardless_of_size(self):
        for path in ["gates/gates.py", ".github/workflows/ci.yml", "auth.py",
                     "migrations/0001.sql"]:
            self.assertEqual(risk_report.classify([path], 1, 0), "high", path)

    def test_oversized_docs_change_is_high(self):
        self.assertEqual(
            risk_report.classify(["docs/handbooks/foo.md"],
                                  risk_report.SIZE_THRESHOLD + 1, 0),
            "high")

    def test_missing_or_unparseable_files_is_high(self):
        self.assertEqual(risk_report.classify([], 0, 0), "high")
        self.assertIsNone(risk_report._parse_files("status: proposed\nno files here\n"))
        self.assertIsNone(risk_report._parse_files("status: proposed\nfiles:\n"))

    def test_blank_line_inside_files_block_does_not_truncate_write_set(self):
        text = ("status: proposed\n\nfiles:\n  - src/harmless.py\n\n"
                "  - gates/gates.py\n")
        files = risk_report._parse_files(text)
        self.assertEqual(files, ["src/harmless.py", "gates/gates.py"])
        self.assertEqual(risk_report.classify(files, 0, 0), "high")

    def test_report_orders_high_before_low_and_drops_nothing(self):
        proposals = [
            {"path": "docs/issue-1/proposals/a.md", "files": ["docs/a.md"],
             "added": 2, "removed": 0},
            {"path": "docs/issue-2/proposals/b.md", "files": ["gates/gates.py"],
             "added": 1, "removed": 0},
            {"path": "docs/issue-3/proposals/c.md", "files": [], "added": 0,
             "removed": 0},
        ]
        out = risk_report.report(proposals)
        self.assertEqual(out.count("docs/issue-1/proposals/a.md"), 1)
        self.assertEqual(out.count("docs/issue-2/proposals/b.md"), 1)
        self.assertEqual(out.count("docs/issue-3/proposals/c.md"), 1)
        idx_a = out.index("docs/issue-1/proposals/a.md")
        idx_b = out.index("docs/issue-2/proposals/b.md")
        idx_c = out.index("docs/issue-3/proposals/c.md")
        self.assertLess(idx_b, idx_a)
        self.assertLess(idx_c, idx_a)


class ReversibilityGrade(unittest.TestCase):
    def test_leaf_doc_is_grade_1(self):
        self.assertEqual(risk_report.reversibility_grade(["docs/proposals/x.md"]), 1)

    def test_application_code_is_grade_2(self):
        self.assertEqual(risk_report.reversibility_grade(["src/app.py"]), 2)

    def test_gates_dir_is_grade_3(self):
        self.assertEqual(risk_report.reversibility_grade(["gates/some_gate.py"]), 3)

    def test_contract_root_file_is_grade_4(self):
        self.assertEqual(risk_report.reversibility_grade(["protocol.md"]), 4)

    def test_worst_of_mixed_paths_wins(self):
        self.assertEqual(
            risk_report.reversibility_grade(["docs/x.md", "protocol.md"]), 4)

    def test_empty_paths_fail_closed_to_max(self):
        self.assertEqual(risk_report.reversibility_grade([]), risk_report.AXIS_MAX)


class BlastRadiusGrade(unittest.TestCase):
    def test_untouched_path_is_low_grade(self):
        grade = risk_report.blast_radius_grade(
            ["docs/issue-999/proposals/nobody-writes-here.md"], ROOT)
        self.assertLessEqual(grade, 2)

    def test_root_owned_path_reaches_higher_grade(self):
        grade = risk_report.blast_radius_grade(["gates/risk_report.py"], ROOT)
        self.assertGreaterEqual(grade, 1)

    def test_empty_paths_fail_closed(self):
        self.assertEqual(risk_report.blast_radius_grade([], ROOT),
                          risk_report.AXIS_MAX)


class PropagationGrade(unittest.TestCase):
    def test_empty_paths_fail_closed(self):
        self.assertEqual(risk_report.propagation_grade([], ROOT),
                          risk_report.AXIS_MAX)

    def test_computes_a_grade_within_range(self):
        grade = risk_report.propagation_grade(["gates/risk_report.py"], ROOT)
        self.assertTrue(1 <= grade <= risk_report.AXIS_MAX)


class ExistingSignalGrade(unittest.TestCase):
    def test_empty_paths_fail_closed(self):
        self.assertEqual(
            risk_report.existing_signal_grade([], 0, 0), risk_report.AXIS_MAX)

    def test_protected_path_is_max(self):
        self.assertEqual(
            risk_report.existing_signal_grade(["gates/gates.py"], 1, 0),
            risk_report.AXIS_MAX)

    def test_large_diff_is_grade_3(self):
        self.assertEqual(
            risk_report.existing_signal_grade(["docs/x.md"], 100, 0), 3)

    def test_small_diff_is_grade_2(self):
        self.assertEqual(
            risk_report.existing_signal_grade(["docs/x.md"], 1, 0), 2)

    def test_no_diff_is_grade_1(self):
        self.assertEqual(
            risk_report.existing_signal_grade(["docs/x.md"], 0, 0), 1)


class DominantAxisRule(unittest.TestCase):
    """CVSS v4/FMEA 승계: 축은 합산·평균되지 않는다 — reversibility 최고
    등급 하나가 나머지 세 축과 무관하게 개별 승인을 강제한다."""

    def test_severe_reversibility_alone_forces_individual_approval(self):
        # protocol.md는 reversibility=4를 강제한다. 다른 축은 최소값이 되도록
        # 아무도 안 쓰는 가짜 경로/작은 diff를 섞는다.
        axes = risk_report.classify_axes(["protocol.md"], 1, 0, ROOT)
        self.assertEqual(axes["reversibility"], risk_report.AXIS_MAX)
        self.assertTrue(axes["requires_individual_approval"])
        self.assertFalse(axes["batchable"])

    def test_mild_axes_do_not_average_away_severe_reversibility(self):
        # on-the-record/hooks/*는 "hook 디렉터리 밑" 취급으로 reversibility=4
        # 지만 gates.is_protected()의 PROTECTED_* 목록에는 없다 —
        # existing_signals는 작은 diff 그대로 낮게 남는데도 reversibility=4
        # 하나가 이긴다.
        axes = risk_report.classify_axes(
            ["on-the-record/hooks/impact-guard.sh"], 1, 0, ROOT)
        self.assertEqual(axes["reversibility"], risk_report.AXIS_MAX)
        self.assertLessEqual(axes["existing_signals"], 2)
        self.assertTrue(axes["requires_individual_approval"])

    def test_low_reversibility_is_batchable_regardless_of_other_axes(self):
        axes = risk_report.classify_axes(
            ["docs/issue-999/proposals/unused.md"], 1, 0, ROOT)
        self.assertLess(axes["reversibility"], risk_report.AXIS_MAX)
        self.assertTrue(axes["batchable"])
        self.assertFalse(axes["requires_individual_approval"])


class FailClosedUnparseable(unittest.TestCase):
    def test_classify_axes_on_empty_write_set_is_max_every_axis(self):
        axes = risk_report.classify_axes([], 0, 0, ROOT)
        for key in ("blast_radius", "reversibility", "propagation",
                    "existing_signals"):
            self.assertEqual(axes[key], risk_report.AXIS_MAX,
                              f"{key} did not fail closed on unparseable input")
        self.assertTrue(axes["requires_individual_approval"])


class BatchBlocked(unittest.TestCase):
    def test_high_reversibility_proposal_is_batch_blocked(self):
        proposals = [
            {"path": "docs/proposals/a.md", "files": ["protocol.md"],
             "added": 1, "removed": 0},
            {"path": "docs/proposals/b.md",
             "files": ["docs/issue-999/proposals/unused.md"],
             "added": 1, "removed": 0},
        ]
        blocked = risk_report.batch_blocked(proposals, ROOT)
        self.assertEqual([b["path"] for b in blocked], ["docs/proposals/a.md"])

    def test_all_low_reversibility_proposals_are_not_blocked(self):
        proposals = [
            {"path": "docs/proposals/a.md",
             "files": ["docs/issue-999/proposals/unused.md"],
             "added": 1, "removed": 0},
        ]
        self.assertEqual(risk_report.batch_blocked(proposals, ROOT), [])


if __name__ == "__main__":
    unittest.main()
