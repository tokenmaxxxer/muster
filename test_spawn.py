#!/usr/bin/env python3
"""spawn.py 의 순수 함수들 — 세션을 띄우지 않고 검사한다."""
import io
import json
import os
import sys
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
        # core_dir 이 보는 자리 **셋 전부** 를 막아야 검사가 성립한다. 하나라도
        # 살려 두면 그 환경이 있는 머신에서만 통과하는 테스트가 된다 — 실제로
        # TOKENMAXXXER_RULEBOOKS 가 설정된 셸에서 이 케이스가 조용히 통과했다.
        saved = {k: os.environ.pop(k, None)
                 for k in ("TOKENMAXXXER_CORE", "TOKENMAXXXER_RULEBOOKS")}
        saved_root, spawn.ROOT = spawn.ROOT, Path("/nonexistent/muster")
        try:
            os.environ["TOKENMAXXXER_CORE"] = "/nonexistent/core"
            with self.assertRaises(SystemExit):
                spawn.core_dir()
        finally:
            spawn.ROOT = saved_root
            os.environ.pop("TOKENMAXXXER_CORE", None)
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

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

    def test_refused_is_not_silent_failure(self):
        # 실측 2026-07-27, reflect 를 실제로 띄운 run: 룰북의 record-fields-gate
        # 가 §20 필수 섹션이 없다며 쓰기를 거부했고, 세션은 이유를 또렷이 말하고
        # 끝났다. 그건 아무 일도 안 일어났는데 이유를 모르는 것과 **정반대
        # 처분**을 받아야 한다 — 게이트가 막은 것은 시스템이 작동한 것이다.
        refused = {"permission_denials": [{"tool_name": "Write"}]}
        self.assertEqual(spawn.classify(0, refused, [], []), "refused")

    def test_progress_outranks_refusal(self):
        # 일부가 막혔어도 보드가 움직였으면 그 run 의 처분은 progressed 다.
        # 거부 건수는 따로 찍히므로 사라지지 않는다.
        refused = {"permission_denials": [{"tool_name": "Write"}]}
        self.assertEqual(spawn.classify(0, refused, ["records/a/qa.md"], []),
                         "progressed")

    def test_human_gate_outranks_refusal(self):
        refused = {"permission_denials": [{"tool_name": "Write"}]}
        self.assertEqual(spawn.classify(0, refused, [], [("coding", "§19")]),
                         "waiting-on-human")

    def test_silent_failure_is_loud(self):
        # 실측된 침묵-사망 모드: exit 0, 보드 무변화, 막힌 줄도 없고,
        # **거부당한 것도 없다** — 그래서 아무도 이유를 모른다.
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


class OwnershipReport(unittest.TestCase):
    """세션 안 게이트가 안 돌았을 때의 마지막 흔적. 막지는 않고 말만 한다."""
    B = spawn.BOARD

    def test_own_record_and_subtree_are_silent(self):
        self.assertEqual(spawn.ownership_report(
            "/x", "qa", [f"{self.B}/alpha/qa.md", f"{self.B}/alpha/qa/run.log"]), [])

    def test_foreign_record_is_named(self):
        out = spawn.ownership_report("/x", "qa", [f"{self.B}/alpha/coding.md"])
        self.assertTrue(out and "coding.md" in out[1])

    def test_a_token_is_called_a_forgery(self):
        out = spawn.ownership_report(
            "/x", "qa", [f"{self.B}/alpha/tokens/scope-proposed--scope-approved.token"])
        self.assertIn("위조", "\n".join(out))

    def test_paths_outside_the_board_are_not_its_business(self):
        self.assertEqual(spawn.ownership_report("/x", "qa", ["src/app.py"]), [])


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


class _TTY(io.StringIO):
    """터미널인 척하는 stdin. approve 의 가드는 isatty() 하나뿐이라 이것으로
    긍정 경로까지 검사할 수 있다."""
    def isatty(self):
        return True


def _repo_with_contract(td):
    root = Path(td) / "repo"
    (root / "docs" / "specs").mkdir(parents=True)
    src = spawn.ROOT / "contract" / "role-handoff-contract.md"
    (root / "docs" / "specs" / "role-handoff-contract.md").write_bytes(src.read_bytes())
    return root


class Approve(unittest.TestCase):
    KIND, SUB = "scope-proposed--scope-approved", "alpha"

    def _run(self, root, typed, kind=None, subject=None):
        old = sys.stdin
        sys.stdin = _TTY(typed + "\n")
        try:
            # None 과 "" 를 구분한다 — `or` 로 기본값을 주면 빈 문자열 케이스가
            # 조용히 유효한 값으로 바뀌어 검사가 성립하지 않는다.
            return spawn.approve(str(root),
                                 self.KIND if kind is None else kind,
                                 self.SUB if subject is None else subject)
        finally:
            sys.stdin = old

    def _token(self, root):
        p = root / spawn.BOARD / self.SUB / "tokens" / (self.KIND + ".token")
        return p.read_text() if p.exists() else None

    def test_no_tty_refuses(self):
        # 모델이 이 명령을 부르면 stdin 이 TTY 가 아니다 (실측 2026-07-27).
        with tempfile.TemporaryDirectory() as td:
            root = _repo_with_contract(td)
            old, sys.stdin = sys.stdin, io.StringIO("APPROVE x y\n")
            try:
                with self.assertRaises(SystemExit):
                    spawn.approve(str(root), self.KIND, self.SUB)
            finally:
                sys.stdin = old

    def test_exact_line_mints_a_consumable_token(self):
        with tempfile.TemporaryDirectory() as td:
            root = _repo_with_contract(td)
            rc = self._run(root, f"APPROVE {self.KIND} {self.SUB}")
            self.assertEqual(rc, 0)
            t = self._token(root)
            self.assertIn("actor: user", t)
            self.assertIn(f"kind: {self.KIND}", t)
            self.assertIn(f"subject: {self.SUB}", t)
            # core 가 실제로 읽고 소비할 수 있어야 한다 — 형식을 손으로 베낀
            # 두 번째 구현이 되면 안 된다.
            sys.path.insert(0, str(spawn.core_dir() / "hooks" / "lib"))
            import consent
            d = str(root / spawn.BOARD / self.SUB / "tokens")
            got = consent.consume(d, self.KIND, subject=self.SUB)
            self.assertEqual(got["actor"], "user")
            self.assertIsNone(consent.find(d, self.KIND))

    def test_the_token_is_not_committable(self):
        with tempfile.TemporaryDirectory() as td:
            root = _repo_with_contract(td)
            self._run(root, f"APPROVE {self.KIND} {self.SUB}")
            ig = root / spawn.BOARD / self.SUB / "tokens" / ".gitignore"
            self.assertEqual(ig.read_text().strip(), "*")

    def test_anything_but_the_exact_line_mints_nothing(self):
        for typed in ("approve scope-proposed--scope-approved alpha",
                      "APPROVE scope-proposed--scope-approved alpha please",
                      "yes", ""):
            with tempfile.TemporaryDirectory() as td:
                root = _repo_with_contract(td)
                self.assertEqual(self._run(root, typed), 1, typed)
                self.assertIsNone(self._token(root), typed)

    def test_unsafe_identifiers_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = _repo_with_contract(td)
            for k, s in (("../escape", "alpha"), (self.KIND, "../escape"),
                         ("", "alpha"), (self.KIND, "")):
                with self.assertRaises(SystemExit):
                    self._run(root, "x", kind=k, subject=s)


class Drive(unittest.TestCase):
    """드라이버의 유일한 일은 **멈추는 것**이다. 무엇을 띄울지는 wakes 가 정한다."""

    def _fake_rows(self, rows):
        return lambda cwd: (rows, [])

    def test_stops_when_nothing_stands(self):
        import wakes
        old = wakes.fresh
        wakes.fresh = self._fake_rows([])
        try:
            self.assertEqual(spawn.drive("/x", False), 0)
        finally:
            wakes.fresh = old

    def test_stops_when_the_board_did_not_change(self):
        """§6. 이게 없으면 같은 줄을 영원히 다시 띄운다."""
        import wakes
        row = wakes.Row("qa", "why", "qa|k", "sig-1")
        old_fresh, old_obs, old_spawn = wakes.fresh, wakes.observed, spawn._spawn_one
        calls = []
        wakes.fresh = self._fake_rows([row])
        wakes.observed = lambda cwd: {}          # consume 이 안 찍혔다 = 무변화
        spawn._spawn_one = lambda *a, **k: calls.append(a) or 0
        try:
            self.assertEqual(spawn.drive("/x", False), 0)
            self.assertEqual(len(calls), 1, "무변화인데 두 번 띄웠다")
        finally:
            wakes.fresh, wakes.observed, spawn._spawn_one = old_fresh, old_obs, old_spawn

    def test_stops_on_a_failed_session(self):
        import wakes
        row = wakes.Row("qa", "why", "qa|k", "sig-1")
        old_fresh, old_spawn = wakes.fresh, spawn._spawn_one
        wakes.fresh = self._fake_rows([row])
        spawn._spawn_one = lambda *a, **k: 2
        try:
            self.assertEqual(spawn.drive("/x", False), 2)
        finally:
            wakes.fresh, spawn._spawn_one = old_fresh, old_spawn

    def test_honours_the_runaway_limit(self):
        import wakes
        row = wakes.Row("qa", "why", "qa|k", "sig-1")
        old_fresh, old_obs, old_spawn = wakes.fresh, wakes.observed, spawn._spawn_one
        calls = []
        wakes.fresh = self._fake_rows([row])
        wakes.observed = lambda cwd: {"qa|k": "sig-1"}   # 항상 진전했다고 친다
        spawn._spawn_one = lambda *a, **k: calls.append(a) or 0
        try:
            spawn.drive("/x", False, limit=3)
            self.assertEqual(len(calls), 3)
        finally:
            wakes.fresh, wakes.observed, spawn._spawn_one = old_fresh, old_obs, old_spawn


if __name__ == "__main__":
    unittest.main()
