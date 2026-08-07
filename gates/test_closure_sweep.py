#!/usr/bin/env python3
"""issue #287 S1/S7: `gh` 호출 실패가 "위반 없음"으로 둔갑하면 안 된다.

  python3 -m pytest gates/test_closure_sweep.py
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
import closure_sweep
import spawn


class IssueViewFailure(unittest.TestCase):
    def test_gh_failure_yields_ok_false(self):
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=1, stdout="")
            state, ok = closure_sweep._issue_view(Path("."), 1)
        self.assertFalse(ok)
        self.assertIsNone(state)

    def test_gh_success_yields_ok_true(self):
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="OPEN\n")
            state, ok = closure_sweep._issue_view(Path("."), 1)
        self.assertTrue(ok)
        self.assertEqual(state, "OPEN")


class PrViewFailure(unittest.TestCase):
    def test_gh_failure_yields_ok_false(self):
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=1, stdout="")
            view, ok = closure_sweep._pr_view_state_body(Path("."), 1)
        self.assertFalse(ok)
        self.assertIsNone(view)

    def test_unparseable_json_yields_ok_false(self):
        with mock.patch.object(closure_sweep.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="not-json")
            view, ok = closure_sweep._pr_view_state_body(Path("."), 1)
        self.assertFalse(ok)
        self.assertIsNone(view)


class FindViolationsSkips(unittest.TestCase):
    """gh 실패로 확인 못한 subject 는 skips 에 남는다 — violations 가 0건
    이어도 "checked, clean" 이 아니다."""

    def setUp(self):
        self.orig_issue_view = closure_sweep._issue_view
        self.orig_pr_for_branch = spawn._pr_for_branch
        self.addCleanup(setattr, closure_sweep, "_issue_view", self.orig_issue_view)
        self.addCleanup(setattr, spawn, "_pr_for_branch", self.orig_pr_for_branch)

    def test_issue_view_failure_is_a_skip_not_a_silent_pass(self):
        closure_sweep._issue_view = lambda root, issue: (None, False)
        spawn._pr_for_branch = lambda root, branch: None
        subjects = {"issue-135": {"implementation": {}}}
        violations, skips = closure_sweep.find_violations(Path("."), subjects=subjects)
        self.assertEqual(violations, [])
        self.assertEqual(len(skips), 1)
        self.assertEqual(skips[0]["subject"], "issue-135")
        self.assertEqual(skips[0]["reason"], "gh-issue-view-failed")

    def test_pr_view_failure_is_a_skip(self):
        closure_sweep._issue_view = lambda root, issue: ("OPEN", True)
        spawn._pr_for_branch = lambda root, branch: 42
        orig_pr_view = closure_sweep._pr_view_state_body
        closure_sweep._pr_view_state_body = lambda root, pr: (None, False)
        self.addCleanup(setattr, closure_sweep, "_pr_view_state_body", orig_pr_view)
        subjects = {"issue-135": {"implementation": {}}}
        violations, skips = closure_sweep.find_violations(Path("."), subjects=subjects)
        self.assertEqual(violations, [])
        self.assertEqual(len(skips), 1)
        self.assertEqual(skips[0]["reason"], "gh-pr-view-failed")


class MainExitCode(unittest.TestCase):
    """issue #287 S1: gh 를 강제로 실패시키면 exit 0("위반 없음")도 exit
    1("위반 발견")도 아니라 exit 2("확인 불가")여야 한다."""

    def test_exit_code_is_2_and_prints_could_not_check(self):
        orig_find_violations = closure_sweep.find_violations
        closure_sweep.find_violations = lambda root, subjects=None, issue_states=None: (
            [], [{"subject": "issue-135", "reason": "gh-issue-view-failed"}])
        self.addCleanup(setattr, closure_sweep, "find_violations", orig_find_violations)

        argv = sys.argv
        sys.argv = ["closure_sweep.py"]
        self.addCleanup(setattr, sys, "argv", argv)

        buf = []
        orig_print = __builtins__["print"] if isinstance(__builtins__, dict) else __builtins__.print
        with mock.patch("builtins.print", side_effect=lambda *a, **k: buf.append(" ".join(str(x) for x in a))):
            rc = closure_sweep.main()
        self.assertEqual(rc, 2)
        joined = "\n".join(buf)
        self.assertIn("확인 불가", joined)
        self.assertNotIn("위반 없음", joined)


if __name__ == "__main__":
    unittest.main()
