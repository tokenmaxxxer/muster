#!/usr/bin/env python3
"""issue #407: per-PR 랜딩 준비도 판정 — 네트워크 없는 순수 `classify()` 테스트.

  python3 -m pytest gates/test_landing_readiness.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import landing_readiness as lr


class ClassifyOwnPr(unittest.TestCase):
    def test_not_open_is_ready(self):
        kind, reason = lr.classify("MERGED", "pass", True, True)
        self.assertEqual(kind, lr.READY)
        self.assertIsNone(reason)

    def test_failing_checks_blocks_on_pr(self):
        kind, reason = lr.classify("OPEN", "fail", True, True)
        self.assertEqual(kind, lr.BLOCKED_ON_PR)
        self.assertIn("checks", reason)

    def test_pending_checks_blocks_on_pr(self):
        kind, _ = lr.classify("OPEN", "pending", True, True)
        self.assertEqual(kind, lr.BLOCKED_ON_PR)

    def test_no_record_blocks_on_pr(self):
        kind, reason = lr.classify("OPEN", "pass", False, True)
        self.assertEqual(kind, lr.BLOCKED_ON_PR)
        self.assertIn("record", reason)

    def test_no_approval_blocks_on_pr(self):
        kind, reason = lr.classify("OPEN", "pass", True, False)
        self.assertEqual(kind, lr.BLOCKED_ON_PR)
        self.assertIn("approval", reason)

    def test_all_clear_no_causes_is_ready(self):
        kind, reason = lr.classify("OPEN", "pass", True, True)
        self.assertEqual(kind, lr.READY)
        self.assertIsNone(reason)


class ClassifyScopedCauses(unittest.TestCase):
    def test_global_cause_covers_everyone(self):
        cause = {"reason": "shared baseline broken", "scope": None}
        kind, reason = lr.classify("OPEN", "pass", True, True,
                                   frozenset({"gates/ci.py"}), (cause,))
        self.assertEqual(kind, lr.BLOCKED_ON_SCOPE)
        self.assertEqual(reason, "shared baseline broken")

    def test_scoped_cause_covers_matching_pr(self):
        cause = {"reason": "gates/ collection broken (#398)",
                  "scope": frozenset({"gates/"})}
        kind, reason = lr.classify("OPEN", "pass", True, True,
                                   frozenset({"gates/test_foo.py"}), (cause,))
        self.assertEqual(kind, lr.BLOCKED_ON_SCOPE)
        self.assertEqual(reason, "gates/ collection broken (#398)")

    def test_scoped_cause_does_not_cover_unrelated_pr(self):
        cause = {"reason": "gates/ collection broken (#398)",
                  "scope": frozenset({"gates/"})}
        kind, reason = lr.classify("OPEN", "pass", True, True,
                                   frozenset({"src/parser.py"}), (cause,))
        self.assertEqual(kind, lr.READY)
        self.assertIsNone(reason)


class ReconstructedIncidentShape(unittest.TestCase):
    """이슈 본문의 측정치(열린 PR 30건, 정지 19건)를 그대로 재현하지는
    않는다 — 그 정확한 30개 목록은 복구 불가(제안서 확인됨). 대신 측정된
    사실 규모(gates/ 전용 원인, 부분 스코프)로 재구성한 시나리오다."""

    def test_only_gates_touching_prs_blocked(self):
        cause = {"reason": "gates/test_gates.py collection collision (#398)",
                  "scope": frozenset({"gates/"})}
        prs = {
            1: frozenset({"gates/spawn_coverage.py"}),
            2: frozenset({"docs/issue-1/proposals/x.md"}),
            3: frozenset({"src/app.py", "gates/test_x.py"}),
            4: frozenset({"README.md"}),
        }
        results = {n: lr.classify("OPEN", "pass", True, True, files, (cause,))[0]
                   for n, files in prs.items()}
        self.assertEqual(results[1], lr.BLOCKED_ON_SCOPE)
        self.assertEqual(results[2], lr.READY)
        self.assertEqual(results[3], lr.BLOCKED_ON_SCOPE)
        self.assertEqual(results[4], lr.READY)


class ReexecutionBlockingCause(unittest.TestCase):
    """issue #476 H1 — `.reexecution/<issue>-<role>.json` verdict를
    레코드 경로로 스코프된 blocking_cause로 바꾸는 지점."""

    def test_no_verdict_file_is_no_cause(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            cause = lr.reexecution_blocking_cause(Path(td), 476, "implementation")
            self.assertIsNone(cause)

    def test_pass_verdict_is_no_cause(self):
        import tempfile
        import reexecution_gate as rg
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            v = rg.Verdict(rg.PASS, "sh x", "deadbeef", 0, "", 0.0)
            rg.write_verdict(root, 476, "implementation", v)
            cause = lr.reexecution_blocking_cause(root, 476, "implementation")
            self.assertIsNone(cause)

    def test_fail_verdict_scopes_to_own_record_path_not_gates(self):
        import tempfile
        import reexecution_gate as rg
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            v = rg.Verdict(rg.FAIL, "sh x", "deadbeef", 1, "boom", 0.0)
            rg.write_verdict(root, 476, "implementation", v)
            cause = lr.reexecution_blocking_cause(root, 476, "implementation")
            self.assertIsNotNone(cause)
            self.assertEqual(cause["scope"],
                             frozenset({"docs/issue-476/reports/implementation.md"}))

    def test_fail_verdict_blocks_pr_whose_files_never_touch_gates(self):
        """after-proposal hunt가 재현한 bypass: gates/-스코프 원인은 gates/를
        건드리지 않는 정상 role PR을 놓친다. 자기 레코드 경로 스코프는
        그 PR이 항상 건드리는 파일이라 놓치지 않는다."""
        import tempfile
        import reexecution_gate as rg
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            v = rg.Verdict(rg.FAIL, "sh x", "deadbeef", 1, "boom", 0.0)
            rg.write_verdict(root, 476, "implementation", v)
            cause = lr.reexecution_blocking_cause(root, 476, "implementation")
            pr_files = frozenset({"docs/issue-476/reports/implementation.md",
                                  "src/widget.py"})
            kind, _ = lr.classify("OPEN", "pass", True, True, pr_files, (cause,))
            self.assertEqual(kind, lr.BLOCKED_ON_SCOPE)


if __name__ == "__main__":
    unittest.main()
