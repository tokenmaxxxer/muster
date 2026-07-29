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
        # stream-json: 결과 이벤트 포착 + 라이브 로그 tee 둘 다 여기서 나온다.
        self.assertEqual(cmd[cmd.index("--output-format") + 1], "stream-json")

    def test_core_is_attached_by_path(self):
        # core carries the consent token format and the board gate. It rides
        # in as --plugin-dir, not as a second marketplace: a directory-loaded
        # plugin's hooks fire headless (measured 2026-07-27, CLI 2.1.220) and
        # nothing is installed, so the cache-vs-clone divergence and the
        # registry-name-wins trap never enter this path.
        cmd, _ = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=False,
                                 core_plugins=["/x/tokenmaxxxer-core/core",
                                               "/x/tokenmaxxxer-core/terse"])
        dirs = [cmd[i + 1] for i, tok in enumerate(cmd) if tok == "--plugin-dir"]
        self.assertIn("/x/tokenmaxxxer-core/core", dirs)
        self.assertIn("/x/tokenmaxxxer-core/terse", dirs)

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
                spawn.core_root()
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

    def test_role_model_unset_is_unchanged(self):
        # MUSTER_ROLE_MODEL 미설정 시 오늘과 동일 - --model 이 붙지 않는다.
        saved = os.environ.pop("MUSTER_ROLE_MODEL", None)
        try:
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=False)
            self.assertNotIn("--model", cmd)
        finally:
            if saved is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_role_model_set_appends_flag(self):
        # MUSTER_ROLE_MODEL 설정 시 --model <value> 가 argv 에 붙는다.
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "sonnet"
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_role_model_whitespace_only_is_unchanged(self):
        # 이슈#35: 공백만 있는 MUSTER_ROLE_MODEL 은 미설정과 동일하게 취급한다
        # - "--model '   '" 같은 값이 argv 에 붙으면 안 된다.
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "   "
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "qa", unattended=False)
            self.assertNotIn("--model", cmd)
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_role_model_does_not_affect_haiku_probe(self):
        # doctor() 의 haiku 프로브는 spawn_cmd 를 거치지 않는다 - 소스에서
        # 하드코딩된 "--model", "haiku" 가 여전히 남아 있는지 직접 확인한다.
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "sonnet"
            src = Path(spawn.__file__).read_text()
            self.assertIn('"--model", "haiku"', src)
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved


class DryRunModelReflection(unittest.TestCase):
    """--dry-run 은 spawn_cmd 를 안 거치므로(세션을 안 띄우니까) 이슈#31
    acceptance 커맨드(MUSTER_ROLE_MODEL=... --dry-run)가 실제로 뭔가
    보여주는지는 main() 의 dry-run 분기가 role_settings() 출력에 model 을
    얹는지에 달려 있다 — 여기서 그 분기를 직접 재현해 검사한다
    (docs/reports/2026-07-29-hunt-muster-role-model-build.md).
    """

    @staticmethod
    def _dry_run_output(role: str) -> dict:
        out = spawn.role_settings(role)
        role_model = (os.environ.get("MUSTER_ROLE_MODEL") or "").strip()
        if role_model:
            out["model"] = role_model
        return out

    def test_unset_output_has_no_model_key(self):
        saved = os.environ.pop("MUSTER_ROLE_MODEL", None)
        try:
            out = self._dry_run_output("qa")
            self.assertNotIn("model", out)
        finally:
            if saved is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_set_output_reflects_model(self):
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "sonnet"
            out = self._dry_run_output("qa")
            self.assertEqual(out.get("model"), "sonnet")
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_whitespace_only_output_has_no_model_key(self):
        # 이슈#35: --dry-run 경로도 공백만 있는 값을 미설정처럼 취급한다.
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "   "
            out = self._dry_run_output("qa")
            self.assertNotIn("model", out)
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved


class PackageRegistryAccess(unittest.TestCase):
    """이슈 #38: 패키지 레지스트리 접근 — 호스트 캐시 마운트 + 레지스트리 허용목록."""

    def test_registry_hosts_merged_into_allowed_domains(self):
        out = spawn.role_settings("coding")
        domains = out["sandbox"]["network"]["allowedDomains"]
        for host in ("proxy.golang.org", "crates.io", "repo.maven.apache.org"):
            self.assertIn(host, domains)

    def test_present_cache_dir_added_to_allow_read(self):
        with tempfile.TemporaryDirectory() as td:
            saved = os.environ.get("GOMODCACHE")
            os.environ["GOMODCACHE"] = td
            try:
                out = spawn.role_settings("coding")
                allow_read = out["sandbox"]["filesystem"].get("allowRead", [])
                self.assertIn(td, allow_read)
            finally:
                if saved is None:
                    os.environ.pop("GOMODCACHE", None)
                else:
                    os.environ["GOMODCACHE"] = saved

    def test_absent_cache_dir_is_skipped_without_error(self):
        missing = "/nonexistent/path/for/muster-issue-38-test"
        saved = os.environ.get("GOMODCACHE")
        os.environ["GOMODCACHE"] = missing
        try:
            out = spawn.role_settings("coding")  # should not raise
            allow_read = out["sandbox"]["filesystem"].get("allowRead", [])
            self.assertNotIn(missing, allow_read)
        finally:
            if saved is None:
                os.environ.pop("GOMODCACHE", None)
            else:
                os.environ["GOMODCACHE"] = saved

    def test_go_proxy_layer_prefers_mounted_host_cache(self):
        with tempfile.TemporaryDirectory() as td:
            saved = os.environ.get("GOMODCACHE")
            os.environ["GOMODCACHE"] = td
            try:
                out = spawn.role_settings("coding")
                proxy = spawn.go_proxy_layer(out)
                self.assertIsNotNone(proxy)
                self.assertTrue(proxy.startswith(f"file://{td}/cache/download,"))
            finally:
                if saved is None:
                    os.environ.pop("GOMODCACHE", None)
                else:
                    os.environ["GOMODCACHE"] = saved

    def test_go_proxy_layer_none_when_cache_not_mounted(self):
        missing = "/nonexistent/path/for/muster-issue-38-test"
        saved = os.environ.get("GOMODCACHE")
        os.environ["GOMODCACHE"] = missing
        try:
            out = spawn.role_settings("coding")
            self.assertIsNone(spawn.go_proxy_layer(out))
        finally:
            if saved is None:
                os.environ.pop("GOMODCACHE", None)
            else:
                os.environ["GOMODCACHE"] = saved


class BoardSnapshot(unittest.TestCase):
    def test_delta_shows_changed_and_new(self):
        with tempfile.TemporaryDirectory() as td:
            rec = Path(td) / spawn.BOARD / "issue-3" / "reports"
            rec.mkdir(parents=True)
            (rec / "qa.md").write_text("loop_state: probing\n")
            before = spawn.board_snapshot(td)
            (rec / "qa.md").write_text("loop_state: reproduced\n")
            (rec / "coding.md").write_text("new\n")
            after = spawn.board_snapshot(td)
            delta = sorted(p for p in after if after.get(p) != before.get(p))
            self.assertEqual(delta, [f"{spawn.BOARD}/issue-3/reports/coding.md",
                                     f"{spawn.BOARD}/issue-3/reports/qa.md"])

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
            "/x", "qa", [f"{self.B}/issue-3/reports/qa.md",
                         f"{self.B}/issue-3/reports/qa/run.log"]), [])

    def test_foreign_record_is_named(self):
        out = spawn.ownership_report("/x", "qa",
                                     [f"{self.B}/issue-3/reports/coding.md"])
        self.assertTrue(out and "coding.md" in out[1])

    def test_granted_subtrees_are_silent(self):
        self.assertEqual(spawn.ownership_report(
            "/x", "ops", [f"{self.B}/issue-3/reports/postmortems/x.md"]), [])

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


class Clean(unittest.TestCase):
    def _make_clean_repo(self, path: Path, remote: Path) -> None:
        __import__("subprocess").run(
            ["git", "init", "-q", "--bare", str(remote)], check=True)
        path.mkdir(parents=True)
        run = lambda *args: __import__("subprocess").run(
            args, cwd=str(path), capture_output=True, text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (path / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")
        run("git", "remote", "add", "origin", str(remote))
        run("git", "push", "-q", "-u", "origin", "HEAD:main")

    def test_keeps_live_session_workspace_but_deletes_dead_sibling(self):
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            live_ws = wb / "issue-51-coding"
            dead_ws = wb / "issue-51-review"
            self._make_clean_repo(live_ws, Path(td) / "remote-live.git")
            self._make_clean_repo(dead_ws, Path(td) / "remote-dead.git")

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({
                "issue-51/coding": {
                    "pid": os.getpid(),
                    "work": str(live_ws),
                    "issue": 51,
                    "role": "coding",
                }
            }))

            old_roster = spawn.ROSTER
            old_argv = sys.argv
            old_environ = dict(os.environ)
            spawn.ROSTER = roster_path
            os.environ["MUSTER_WORK_DIR"] = str(wb)
            sys.argv = ["spawn.py", "clean"]
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                spawn.main()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                sys.argv = old_argv
                os.environ.clear()
                os.environ.update(old_environ)

            out = buf.getvalue()
            self.assertTrue(live_ws.is_dir())
            self.assertIn("실행 중인 세션 있음", out)
            self.assertFalse(dead_ws.exists())


if __name__ == "__main__":
    unittest.main()
