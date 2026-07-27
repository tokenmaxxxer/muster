#!/usr/bin/env python3
"""spawn.py 의 순수 함수들 — 세션을 띄우지 않고 검사한다."""
import json
import os
import tempfile
import unittest
from pathlib import Path

import spawn


class RepoConfigRefusal(unittest.TestCase):
    def test_agents_and_mcp_are_rogue(self):
        # 프로젝트 스코프 에이전트 파일은 hooks/permissionMode frontmatter 를
        # 존중하고(sub-agents 문서), .mcp.json 은 레포가 적은 프로세스 실행
        # 표면이다 — 실측된 레포-커밋-훅 탈출과 같은 부류.
        for p in (".claude/agents", ".mcp.json"):
            self.assertIn(p, spawn.REPO_CONFIG, p)

    def test_refusal_fires_on_agents_dir(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / ".claude" / "agents").mkdir(parents=True)
            with self.assertRaises(SystemExit):
                spawn.require_no_repo_config(td, override=False)


class SpawnCmd(unittest.TestCase):
    def test_flags(self):
        cmd, _ = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=False)
        self.assertEqual(cmd[:2], ["claude", "-p"])
        self.assertIn("--settings", cmd)
        self.assertEqual(cmd[cmd.index("--settings") + 1], "/tmp/s.json")
        # 실측 2026-07-27: 권한 설정 없는 headless 는 Write 를 조용히 거부한다
        # (permission_denials 에만 남고 겉은 성공). acceptEdits 가 그 프롬프트를
        # 없애고, PreToolUse exit 2 게이트는 acceptEdits 아래서도 여전히 막는다.
        self.assertIn("acceptEdits", cmd)
        self.assertEqual(cmd[cmd.index("--permission-mode") + 1], "acceptEdits")
        # 결과 포착 없이는 세션이 "아무것도 안 하고 exit 0" 해도 모른다.
        self.assertEqual(cmd[cmd.index("--output-format") + 1], "json")

    def test_core_is_attached_by_path(self):
        # core carries the consent token format and the board gate. It rides
        # in as --plugin-dir, not as a second marketplace: a directory-loaded
        # plugin's hooks fire headless (measured 2026-07-27, CLI 2.1.220) and
        # nothing is installed, so the cache-vs-clone divergence and the
        # registry-name-wins trap never enter this path.
        cmd, _ = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=False,
                                 core="/x/tokenmaxxxer-core/core")
        self.assertEqual(cmd[cmd.index("--plugin-dir") + 1],
                         "/x/tokenmaxxxer-core/core")

    def test_core_dir_resolves_or_halts(self):
        # A role session without core loses token forgery protection and the
        # contract-drift check silently. That is a halt, not a warning.
        old = os.environ.pop("TOKENMAXXXER_CORE", None)
        try:
            os.environ["TOKENMAXXXER_CORE"] = "/nonexistent/core"
            saved_root, spawn.ROOT = spawn.ROOT, Path("/nonexistent/muster")
            try:
                with self.assertRaises(SystemExit):
                    spawn.core_dir()
            finally:
                spawn.ROOT = saved_root
        finally:
            os.environ.pop("TOKENMAXXXER_CORE", None)
            if old is not None:
                os.environ["TOKENMAXXXER_CORE"] = old

    def test_env_stamps(self):
        # D1: 스폰된 세션의 UserPromptSubmit 은 오케스트레이터가 쓴 텍스트다.
        # 그 턴이 사람 턴으로 오인되어 mint 되는 일이 없도록 도장을 찍는다.
        _, env = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=False)
        self.assertEqual(env["CLAUDE_ROLE"], "qa")
        self.assertEqual(env["TOKENMAXXXER_SPAWNED"], "1")
        self.assertNotIn("TOKENMAXXXER_UNATTENDED", env)

    def test_unattended_is_separate(self):
        # SPAWNED(사람 턴 아님)와 UNATTENDED(사람 부재)는 다른 사실이다.
        # 겹쳐 쓰면 attended 스폰이 깨진다.
        _, env = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=True)
        self.assertEqual(env["TOKENMAXXXER_UNATTENDED"], "1")
        self.assertEqual(env["TOKENMAXXXER_SPAWNED"], "1")


class BoardSnapshot(unittest.TestCase):
    def test_delta_shows_changed_and_new(self):
        with tempfile.TemporaryDirectory() as td:
            rec = Path(td) / spawn.BOARD / "alpha"
            rec.mkdir(parents=True)
            (rec / "qa.md").write_text("loop_state: probing\n")
            before = spawn.board_snapshot(td)
            (rec / "qa.md").write_text("loop_state: reproduced\n")
            (rec / "coding.md").write_text("new\n")
            after = spawn.board_snapshot(td)
            delta = sorted(p for p in after if after.get(p) != before.get(p))
            self.assertEqual(delta, [f"{spawn.BOARD}/alpha/coding.md",
                                     f"{spawn.BOARD}/alpha/qa.md"])

    def test_no_board_is_empty(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(spawn.board_snapshot(td), {})


class SessionResult(unittest.TestCase):
    def test_parses_json(self):
        got = spawn.session_result('{"session_id": "abc", "total_cost_usd": 0.5}')
        self.assertEqual(got["session_id"], "abc")

    def test_garbage_is_empty_dict(self):
        # 파싱 불가를 성공으로 취급하지 않는다 — 빈 dict 는 아래 classify 에서
        # is_error 도 아니고 필드도 없는, "모른다" 그대로다.
        self.assertEqual(spawn.session_result("not json"), {})
        self.assertEqual(spawn.session_result(""), {})


class Classify(unittest.TestCase):
    def test_errored_wins(self):
        self.assertEqual(spawn.classify(1, {}, [], []), "errored")
        self.assertEqual(spawn.classify(0, {"is_error": True}, ["x"], []), "errored")

    def test_progressed_on_delta(self):
        self.assertEqual(spawn.classify(0, {}, ["records/a/qa.md"], []), "progressed")

    def test_waiting_on_human(self):
        blocked = [("coding", "…§19 가 막는다")]
        self.assertEqual(spawn.classify(0, {}, [], blocked), "waiting-on-human")

    def test_silent_failure_is_loud(self):
        # 실측된 침묵-사망 모드: exit 0, 보드 무변화, 막힌 줄도 없음.
        self.assertEqual(spawn.classify(0, {}, [], []), "silent-failure")


class Ledger(unittest.TestCase):
    def test_appends_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            old = spawn.ROOT
            spawn.ROOT = Path(td)
            try:
                p = spawn.ledger_write({"role": "qa", "outcome": "progressed"})
                p2 = spawn.ledger_write({"role": "review", "outcome": "errored"})
            finally:
                spawn.ROOT = old
            self.assertEqual(p, p2)
            lines = [json.loads(l) for l in p.read_text().splitlines()]
            self.assertEqual([l["role"] for l in lines], ["qa", "review"])


class RequireDoctor(unittest.TestCase):
    def _with_root(self, td):
        old = spawn.ROOT
        spawn.ROOT = Path(td)
        return old

    def test_halts_without_doctor_pass(self):
        with tempfile.TemporaryDirectory() as td:
            old = self._with_root(td)
            try:
                with self.assertRaises(SystemExit):
                    spawn.require_doctor(version="2.1.220 (Claude Code)")
            finally:
                spawn.ROOT = old

    def test_halts_on_version_change(self):
        # CLI 는 자동 업데이트된다. 훅이 headless 에서 도는 것은 문서가 아니라
        # 실측이 보증한다 — 버전이 바뀌면 보증도 끝난다.
        with tempfile.TemporaryDirectory() as td:
            old = self._with_root(td)
            try:
                (Path(td) / "runs").mkdir()
                (Path(td) / "runs" / "doctor-ok").write_text("2.1.219 (Claude Code)")
                with self.assertRaises(SystemExit):
                    spawn.require_doctor(version="2.1.220 (Claude Code)")
            finally:
                spawn.ROOT = old

    def test_passes_on_match(self):
        with tempfile.TemporaryDirectory() as td:
            old = self._with_root(td)
            try:
                (Path(td) / "runs").mkdir()
                (Path(td) / "runs" / "doctor-ok").write_text("2.1.220 (Claude Code)")
                spawn.require_doctor(version="2.1.220 (Claude Code)")  # no raise
            finally:
                spawn.ROOT = old


if __name__ == "__main__":
    unittest.main()
