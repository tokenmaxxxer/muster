#!/usr/bin/env python3
"""spawn.py approve-scope 의 댓글/allowlist 검증 — 이슈 #115.

GitHub 호출은 전부 monkeypatch 로 대체한다: 이 테스트는 네트워크 없이,
frontmatter 읽기/쓰기와 승인자 매칭 로직만 실측한다.
"""
import tempfile
import unittest
from pathlib import Path

import spawn


def _record(root: Path, subject: str, role: str, loop_state: str) -> Path:
    d = root / "docs" / subject / "reports"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{role}.md"
    p.write_text(f"---\nloop_state: {loop_state}\nupstream: []\n---\n\nbody\n",
                 encoding="utf-8")
    return p


def _approvers(root: Path, *logins: str) -> None:
    d = root / "docs" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    (d / "approvers.md").write_text("".join(f"- {l}\n" for l in logins), encoding="utf-8")


class ApproveScope(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        (self.root / ".git").mkdir()          # git 커밋은 아래에서 각각 patch 한다

    def tearDown(self):
        self._td.cleanup()

    def _patch_gh(self, comments, pr=None):
        spawn._repo_slug = lambda root: "acme/repo"
        spawn._pr_for_branch = lambda root, branch: pr
        spawn._issue_comments = lambda root, n: comments

    def test_matching_approver_writes_scope_approved(self):
        record = _record(self.root, "issue-1", "product-discovery", "scope-proposed")
        _approvers(self.root, "alice")
        self._patch_gh([{"login": "alice", "body": "APPROVE issue-1/scope"}])

        committed = {}

        def fake_run(cmd, **kw):
            if cmd[:2] == ["git", "-C"] and "commit" in cmd:
                committed["ran"] = True
            class R:
                returncode = 0
                stdout = ""
            return R()
        spawn.subprocess.run = fake_run

        rc = spawn.approve_scope(str(self.root), 1)
        self.assertEqual(rc, 0)
        self.assertEqual(spawn.frontmatter(record).get("loop_state"), "scope-approved")
        self.assertTrue(committed.get("ran"))

    def test_non_approver_comment_is_rejected(self):
        _record(self.root, "issue-2", "product-discovery", "scope-proposed")
        _approvers(self.root, "alice")
        # 문자열은 정확히 맞지만 승인자 allowlist 에 없는 계정이다.
        self._patch_gh([{"login": "mallory", "body": "APPROVE issue-2/scope"}])
        with self.assertRaises(SystemExit):
            spawn.approve_scope(str(self.root), 2)

    def test_no_matching_comment_text_is_rejected(self):
        _record(self.root, "issue-3", "product-discovery", "scope-proposed")
        _approvers(self.root, "alice")
        self._patch_gh([{"login": "alice", "body": "looks good to me"}])
        with self.assertRaises(SystemExit):
            spawn.approve_scope(str(self.root), 3)

    def test_already_approved_is_idempotent(self):
        _record(self.root, "issue-4", "product-discovery", "scope-approved")
        _approvers(self.root, "alice")
        self._patch_gh([])
        rc = spawn.approve_scope(str(self.root), 4)
        self.assertEqual(rc, 0)

    def test_failed_commit_rolls_back_and_does_not_fake_success(self):
        record = _record(self.root, "issue-6", "product-discovery", "scope-proposed")
        _approvers(self.root, "alice")
        self._patch_gh([{"login": "alice", "body": "APPROVE issue-6/scope"}])

        def fake_run(cmd, **kw):
            class R:
                returncode = 1
                stdout = ""
                stderr = "git: 커밋 실패 (테스트)"
            import subprocess as sp
            raise sp.CalledProcessError(1, cmd, output="", stderr=R.stderr)
        spawn.subprocess.run = fake_run

        with self.assertRaises(SystemExit):
            spawn.approve_scope(str(self.root), 6)
        # 커밋이 실패했으니 파일은 scope-proposed 로 되돌아가 있어야 한다 —
        # 안 그러면 다음 호출이 idempotency 가드에 걸려 커밋 없이 성공을 보고한다.
        self.assertEqual(spawn.frontmatter(record).get("loop_state"), "scope-proposed")

    def test_wrong_loop_state_is_rejected(self):
        _record(self.root, "issue-5", "product-discovery", "in-progress")
        _approvers(self.root, "alice")
        self._patch_gh([{"login": "alice", "body": "APPROVE issue-5/scope"}])
        with self.assertRaises(SystemExit):
            spawn.approve_scope(str(self.root), 5)


if __name__ == "__main__":
    unittest.main()
