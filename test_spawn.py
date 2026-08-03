#!/usr/bin/env python3
"""spawn.py 의 순수 함수들 — 세션을 띄우지 않고 검사한다."""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock
from pathlib import Path
from unittest import mock

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
        cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
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
        cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False,
                                 core_plugins=["/x/tokenmaxxxer-core/core",
                                               "/x/tokenmaxxxer-core/terse"])
        dirs = [cmd[i + 1] for i, tok in enumerate(cmd) if tok == "--plugin-dir"]
        self.assertIn("/x/tokenmaxxxer-core/core", dirs)
        self.assertIn("/x/tokenmaxxxer-core/terse", dirs)

    def test_core_dir_resolves_or_halts(self):
        # A role session without core loses token forgery protection and the
        # contract-drift check silently. That is a halt, not a warning.
        # core_dir 이 보는 자리 **둘 다** 를 막아야 검사가 성립한다. 하나라도
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

    def test_core_root_prefers_managed_clone_over_sibling_directory(self):
        # 이슈#220: 형제 디렉터리(마켓플레이스 설치 부산물, ROOT.parent /
        # "tokenmaxxxer-core")가 관리 클론보다 먼저 매치되면 sha 비교 없이
        # 그대로 반환돼, 관리 클론(원격과 항상 동기화되는 유일한 경로)이
        # 영구히 도달 불가였다 — 후보 목록에서 형제 디렉터리를 제거한
        # 뒤에도 둘이 공존할 때 관리 클론이 선택되는지 회귀 확인.
        saved = {k: os.environ.pop(k, None)
                 for k in ("TOKENMAXXXER_CORE", "TOKENMAXXXER_RULEBOOKS")}
        try:
            with tempfile.TemporaryDirectory() as td:
                fake_root = Path(td) / "workspace"
                fake_root.mkdir()
                saved_root, spawn.ROOT = spawn.ROOT, fake_root
                try:
                    sibling = fake_root.parent / "tokenmaxxxer-core"
                    (sibling / "core" / ".claude-plugin").mkdir(parents=True)
                    (sibling / "core" / ".claude-plugin" / "plugin.json").write_text("{}")

                    managed = fake_root / "runs" / "rulebooks" / "tokenmaxxxer-core"
                    (managed / "core" / ".claude-plugin").mkdir(parents=True)
                    (managed / "core" / ".claude-plugin" / "plugin.json").write_text("{}")

                    self.assertEqual(spawn.core_root(), managed)
                finally:
                    spawn.ROOT = saved_root
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v

    def test_core_version_reports_managed_clone_sha_when_sibling_also_present(self):
        # 같은 공존 셋업에서 core_version() 도 관리 클론 쪽 sha·라벨을
        # 보고해야 core_root() 가 실제로 고르는 체크아웃과 로그가 일치한다
        # — 형제 디렉터리 쪽 sha 가 섞여 나오면 안 된다.
        saved = {k: os.environ.pop(k, None)
                 for k in ("TOKENMAXXXER_CORE", "TOKENMAXXXER_RULEBOOKS")}
        try:
            with tempfile.TemporaryDirectory() as td:
                fake_root = Path(td) / "workspace"
                fake_root.mkdir()
                saved_root, spawn.ROOT = spawn.ROOT, fake_root
                try:
                    def make_repo(d: Path, marker: str) -> str:
                        # marker 로 트리 내용을 다르게 해 두 저장소가 우연히
                        # 같은 커밋 해시를 갖는 것(같은 초 안에 동일 내용으로
                        # init 하면 발생)을 막는다.
                        (d / "core" / ".claude-plugin").mkdir(parents=True)
                        (d / "core" / ".claude-plugin" / "plugin.json").write_text(
                            json.dumps({"marker": marker}))

                        def git(*a: str) -> str:
                            r = subprocess.run(["git", "-C", str(d), *a],
                                               capture_output=True, text=True)
                            return r.stdout.strip()

                        git("init", "-q")
                        git("config", "user.email", "t@t.t")
                        git("config", "user.name", "t")
                        git("add", "-A")
                        git("commit", "-q", "-m", f"init-{marker}")
                        return git("rev-parse", "--short", "HEAD")

                    sibling = fake_root.parent / "tokenmaxxxer-core"
                    sibling_sha = make_repo(sibling, "sibling")

                    managed = fake_root / "runs" / "rulebooks" / "tokenmaxxxer-core"
                    managed_sha = make_repo(managed, "managed")

                    v = spawn.core_version()
                    self.assertIn(managed_sha, v)
                    self.assertIn("on-the-record 클론", v)
                    self.assertNotIn(sibling_sha, v)
                finally:
                    spawn.ROOT = saved_root
        finally:
            for k, val in saved.items():
                if val is not None:
                    os.environ[k] = val

    def test_core_version_reports_sha_date_and_label_for_local_override(self):
        # 이슈#218: core_root() 는 plugin.json 존재만 보고 sha·신선도는
        # 보지도 보고도 않는다 — core_version() 은 checkout_version() 의
        # core 쪽 대칭으로, 로컬 오버라이드(TOKENMAXXXER_CORE)가 실제로
        # 무슨 sha 를 물었는지 읽기 전용으로 드러낸다.
        with tempfile.TemporaryDirectory() as td:
            core_dir = Path(td) / "tokenmaxxxer-core"
            (core_dir / "core" / ".claude-plugin").mkdir(parents=True)
            (core_dir / "core" / ".claude-plugin" / "plugin.json").write_text("{}")

            def git(*a: str) -> str:
                r = subprocess.run(["git", "-C", str(core_dir), *a],
                                   capture_output=True, text=True)
                return r.stdout.strip()

            git("init", "-q")
            git("config", "user.email", "t@t.t")
            git("config", "user.name", "t")
            git("add", "-A")
            git("commit", "-q", "-m", "init")
            expected_sha = git("rev-parse", "--short", "HEAD")
            expected_date = git("log", "-1", "--format=%cs")

            saved = os.environ.get("TOKENMAXXXER_CORE")
            os.environ["TOKENMAXXXER_CORE"] = str(core_dir)
            try:
                v = spawn.core_version()
            finally:
                if saved is None:
                    os.environ.pop("TOKENMAXXXER_CORE", None)
                else:
                    os.environ["TOKENMAXXXER_CORE"] = saved
            self.assertIn(expected_sha, v)
            self.assertIn(expected_date, v)
            self.assertIn("TOKENMAXXXER_CORE", v)
            self.assertNotIn("커밋 안 된 변경", v)

    def test_core_version_reports_unknown_without_network_when_nothing_found(self):
        # 로컬 후보 둘 + 관리 클론까지 전부 없을 때 core_version() 은
        # core_root() 처럼 halt 하지 않고(로깅용이라 halt 는 core_root() 의
        # 몫), 그렇다고 core_root() 처럼 새로 clone 을 시도하지도 않는다.
        saved = {k: os.environ.pop(k, None)
                 for k in ("TOKENMAXXXER_CORE", "TOKENMAXXXER_RULEBOOKS")}
        saved_root = spawn.ROOT
        try:
            with tempfile.TemporaryDirectory() as broot:
                spawn.ROOT = Path(broot)
                with mock.patch("spawn.subprocess.run") as run:
                    v = spawn.core_version()
                self.assertIn("버전 불명", v)
                # 후보 전부 미스면 describe() 자체가 안 불려 위 mock 이 한
                # 번도 안 불린다 — "clone 이 없다" 는 이 경로에서 자명하다.
                # 진짜 위험은 관리 클론이 **있는** 경로(core_root() 는
                # 거기서 pull 을 돈다)인데, core_version() 은 거기서도
                # pull/clone 을 걸지 않는지를 아래서 실제 subprocess 호출을
                # 가로채 검사한다.
                run.assert_not_called()

                d = Path(broot) / "runs" / "rulebooks" / "tokenmaxxxer-core"
                (d / "core" / ".claude-plugin").mkdir(parents=True)
                (d / "core" / ".claude-plugin" / "plugin.json").write_text("{}")

                def git(*a: str) -> str:
                    r = subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True)
                    return r.stdout.strip()

                git("init", "-q")
                git("config", "user.email", "t@t.t")
                git("config", "user.name", "t")
                git("add", "-A")
                git("commit", "-q", "-m", "init")
                expected_sha = git("rev-parse", "--short", "HEAD")

                with mock.patch("spawn.subprocess.run", wraps=subprocess.run) as spied:
                    v2 = spawn.core_version()
                self.assertIn(expected_sha, v2)
                self.assertIn("on-the-record 클론", v2)
                for cmd in spied.call_args_list:
                    self.assertNotIn("pull", cmd.args[0], "core_version() 이 관리 클론을 pull 했다")
                    self.assertNotIn("clone", cmd.args[0], "core_version() 이 네트워크 clone 을 시도했다")
        finally:
            spawn.ROOT = saved_root
            for k, val in saved.items():
                if val is not None:
                    os.environ[k] = val

    def test_claude_plugin_root_core_matches_attached_core_dir(self):
        # 이슈#182: 룰북 게이트는 core 공유 라이브러리를
        # ${CLAUDE_PLUGIN_ROOT_CORE:-<상대경로>/core} 로 참조한다. 이 변수가
        # 없으면 상대 fallback 이 룰북 클론 내부를 가리켜 실배포에서 해석
        # 실패 → 게이트 전면 fail-open. 주입된 경로는 --plugin-dir 로 실제
        # 로드되는 core 플러그인 경로와 문자열까지 정확히 일치해야 한다.
        _, env = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False,
                                  core_plugins=["/x/tokenmaxxxer-core/core",
                                                "/x/tokenmaxxxer-core/terse"])
        self.assertEqual(env["CLAUDE_PLUGIN_ROOT_CORE"], "/x/tokenmaxxxer-core/core")

    def test_claude_plugin_root_core_unset_without_core_plugin(self):
        # core 가 결손 상태(plugin.json 없음)여서 core_plugin_dirs() 목록에서
        # 아예 빠지면 변수를 주입하지 않는다 — 조용히 fallback 에 빠지게
        # 두지 않고 stderr 경고로 드러낸다.
        _, env = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False,
                                  core_plugins=["/x/tokenmaxxxer-core/terse"])
        self.assertNotIn("CLAUDE_PLUGIN_ROOT_CORE", env)

    def test_env_stamps(self):
        # D1: 스폰된 세션의 UserPromptSubmit 은 오케스트레이터가 쓴 텍스트다.
        # 그 턴이 사람 턴으로 오인되어 mint 되는 일이 없도록 도장을 찍는다.
        _, env = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
        self.assertEqual(env["CLAUDE_ROLE"], "execution-observation")
        self.assertEqual(env["TOKENMAXXXER_SPAWNED"], "1")
        self.assertNotIn("TOKENMAXXXER_UNATTENDED", env)

    def test_unattended_is_separate(self):
        # SPAWNED(사람 턴 아님)와 UNATTENDED(사람 부재)는 다른 사실이다.
        # 겹쳐 쓰면 attended 스폰이 깨진다.
        _, env = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=True)
        self.assertEqual(env["TOKENMAXXXER_UNATTENDED"], "1")
        self.assertEqual(env["TOKENMAXXXER_SPAWNED"], "1")

    def test_role_model_unset_uses_builtin_default(self):
        # 이슈#93: MUSTER_ROLE_MODEL/config 둘 다 미설정이면 built-in
        # "sonnet" 이 --model 로 붙는다.
        saved = os.environ.pop("MUSTER_ROLE_MODEL", None)
        try:
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_role_model_set_appends_flag(self):
        # MUSTER_ROLE_MODEL 설정 시 --model <value> 가 argv 에 붙는다.
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "sonnet"
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_role_model_whitespace_only_uses_builtin_default(self):
        # 이슈#35+#93: 공백만 있는 MUSTER_ROLE_MODEL 은 미설정과 동일하게
        # 취급되어 built-in "sonnet" 이 붙는다 - "--model '   '" 은 안 된다.
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "   "
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_role_model_config_only_appends_flag(self):
        # 이슈#60: MUSTER_ROLE_MODEL 미설정, role_model.txt 만 있으면
        # --model <config value> 가 argv 에 붙는다.
        saved_env = os.environ.pop("MUSTER_ROLE_MODEL", None)
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.write_text("sonnet")
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved_cfg is None:
                spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            else:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

    def test_role_model_env_overrides_config(self):
        # 이슈#60: 둘 다 설정되면 env 값이 이긴다.
        saved_env = os.environ.get("MUSTER_ROLE_MODEL")
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.write_text("haiku")
            os.environ["MUSTER_ROLE_MODEL"] = "opus"
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertEqual(cmd[cmd.index("--model") + 1], "opus")
        finally:
            if saved_cfg is None:
                spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            else:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

    def test_role_model_whitespace_only_config_uses_builtin_default(self):
        # 이슈#60+#93: 공백만 있는 config 값도 미설정과 동일하게 취급되어
        # built-in "sonnet" 이 붙는다.
        saved_env = os.environ.pop("MUSTER_ROLE_MODEL", None)
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.write_text("   ")
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved_cfg is None:
                spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            else:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

    def test_role_model_non_utf8_config_uses_builtin_default(self):
        # 이슈#60+#93: role_model.txt 가 UTF-8 이 아니면 read_role_model_config()
        # 는 (docstring 대로) 미설정처럼 "" 를 돌려주고, resolved_role_model()
        # 은 built-in "sonnet" 으로 떨어진다 — 스폰이 UnicodeDecodeError 로
        # 죽으면 안 된다.
        saved_env = os.environ.pop("MUSTER_ROLE_MODEL", None)
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.write_bytes(b"\xff\xfe\x00\x01")
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved_cfg is None:
                spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            else:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

    def test_role_model_no_config_file_uses_builtin_default(self):
        # 이슈#60+#93: role_model.txt 자체가 없으면 미설정과 동일하게 취급되어
        # built-in "sonnet" 이 붙는다.
        saved_env = os.environ.pop("MUSTER_ROLE_MODEL", None)
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "execution-observation", unattended=False)
            self.assertIn("--model", cmd)
            self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        finally:
            if saved_cfg is not None:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

    def test_resolved_role_model_builtin_default_is_sonnet(self):
        # 이슈#93: env, config 둘 다 없으면 resolved_role_model() 은 "sonnet"
        # 을 직접 돌려준다 — never no --model.
        saved_env = os.environ.pop("MUSTER_ROLE_MODEL", None)
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            self.assertEqual(spawn.resolved_role_model(), "sonnet")
        finally:
            if saved_cfg is not None:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env

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
        role_model = spawn.resolved_role_model()
        if role_model:
            out["model"] = role_model
        return out

    def test_unset_output_reflects_builtin_default(self):
        saved = os.environ.pop("MUSTER_ROLE_MODEL", None)
        try:
            out = self._dry_run_output("execution-observation")
            self.assertEqual(out.get("model"), "sonnet")
        finally:
            if saved is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_set_output_reflects_model(self):
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "sonnet"
            out = self._dry_run_output("execution-observation")
            self.assertEqual(out.get("model"), "sonnet")
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_whitespace_only_output_reflects_builtin_default(self):
        # 이슈#35+#93: --dry-run 경로도 공백만 있는 값을 미설정처럼 취급해
        # built-in "sonnet" 을 반영한다.
        saved = os.environ.get("MUSTER_ROLE_MODEL")
        try:
            os.environ["MUSTER_ROLE_MODEL"] = "   "
            out = self._dry_run_output("execution-observation")
            self.assertEqual(out.get("model"), "sonnet")
        finally:
            if saved is None:
                os.environ.pop("MUSTER_ROLE_MODEL", None)
            else:
                os.environ["MUSTER_ROLE_MODEL"] = saved

    def test_config_only_output_reflects_model(self):
        # 이슈#60: env 없이 role_model.txt 만 있어도 dry-run 출력이 반영한다.
        saved_env = os.environ.pop("MUSTER_ROLE_MODEL", None)
        saved_cfg = spawn.ROLE_MODEL_CONFIG.read_text() if spawn.ROLE_MODEL_CONFIG.is_file() else None
        try:
            spawn.ROLE_MODEL_CONFIG.write_text("sonnet")
            out = self._dry_run_output("execution-observation")
            self.assertEqual(out.get("model"), "sonnet")
        finally:
            if saved_cfg is None:
                spawn.ROLE_MODEL_CONFIG.unlink(missing_ok=True)
            else:
                spawn.ROLE_MODEL_CONFIG.write_text(saved_cfg)
            if saved_env is not None:
                os.environ["MUSTER_ROLE_MODEL"] = saved_env


class WebToolPermissionAccess(unittest.TestCase):
    """이슈 #65: #58 이 연 것은 샌드박스 네트워크 층(allowedDomains)뿐이었다.
    headless 세션은 --permission-mode acceptEdits 로 뜨고 답할 사람이 없어서
    permissions.allow 에 규칙이 없는 도구는 별개로 거부된다 — 그 TOOL-PERMISSION
    층을 role_settings() 가 채우는지 검증한다."""

    def test_web_tools_allowed_for_every_role(self):
        for role_file in (Path(spawn.ROOT) / "roles").glob("*.json"):
            role = role_file.stem
            out = spawn.role_settings(role)
            allow = out["permissions"]["allow"]
            self.assertIn("WebSearch", allow, role)
            self.assertIn("WebFetch", allow, role)

    def test_read_only_tools_allowed_for_every_role(self):
        """이슈 #153: Read/Grep/Glob 은 sandbox.filesystem 경계를 넓히지 않는
        읽기 전용 조회이므로, WebSearch/WebFetch 와 같은 TOOL-PERMISSION 층에서
        모든 역할에 대해 허용된다."""
        for role_file in (Path(spawn.ROOT) / "roles").glob("*.json"):
            role = role_file.stem
            out = spawn.role_settings(role)
            allow = out["permissions"]["allow"]
            self.assertIn("Read", allow, role)
            self.assertIn("Grep", allow, role)
            self.assertIn("Glob", allow, role)

    def test_role_declared_permissions_allow_entries_preserved(self):
        """이슈 #38 의 registry-host 병합과 같은 패턴: 병합이지 교체가 아니다."""
        f = Path(spawn.ROOT) / "roles" / "implementation.json"
        original_text = f.read_text()
        spec = json.loads(original_text)
        spec["permissions"] = {"allow": ["Bash(git *)"]}
        try:
            f.write_text(json.dumps(spec))
            out = spawn.role_settings("implementation")
            allow = out["permissions"]["allow"]
            self.assertIn("Bash(git *)", allow)
            self.assertIn("WebSearch", allow)
            self.assertIn("WebFetch", allow)
        finally:
            f.write_text(original_text)


class PackageRegistryAccess(unittest.TestCase):
    """이슈 #38: 패키지 레지스트리 접근 — 호스트 캐시 마운트 + 레지스트리 허용목록."""

    def test_registry_hosts_merged_into_allowed_domains(self):
        out = spawn.role_settings("implementation")
        domains = out["sandbox"]["network"]["allowedDomains"]
        for host in ("proxy.golang.org", "crates.io", "repo.maven.apache.org"):
            self.assertIn(host, domains)

    def test_web_access_domain_merged_alongside_registry_hosts(self):
        """이슈 #58: WEB_ACCESS_DOMAINS 도 같은 병합 지점에서 추가되고,
        역할 선언 도메인·레지스트리 호스트는 여전히 남아있다(안 지워짐)."""
        out = spawn.role_settings("implementation")
        domains = out["sandbox"]["network"]["allowedDomains"]
        for host in spawn.WEB_ACCESS_DOMAINS:
            self.assertIn(host, domains)
        # 역할이 선언한 도메인 (roles/coding.json)
        for host in ("api.anthropic.com", "*.github.com", "github.com"):
            self.assertIn(host, domains)
        # 레지스트리 호스트도 지워지지 않았다
        for host in spawn.PACKAGE_REGISTRY_HOSTS:
            self.assertIn(host, domains)

    def test_present_cache_dir_added_to_allow_read(self):
        with tempfile.TemporaryDirectory() as td:
            saved = os.environ.get("GOMODCACHE")
            os.environ["GOMODCACHE"] = td
            try:
                out = spawn.role_settings("implementation")
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
            out = spawn.role_settings("implementation")  # should not raise
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
                out = spawn.role_settings("implementation")
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
            out = spawn.role_settings("implementation")
            self.assertIsNone(spawn.go_proxy_layer(out))
        finally:
            if saved is None:
                os.environ.pop("GOMODCACHE", None)
            else:
                os.environ["GOMODCACHE"] = saved

    def test_file_at_cache_path_is_skipped(self):
        with tempfile.NamedTemporaryFile() as tf:
            saved = os.environ.get("GOMODCACHE")
            os.environ["GOMODCACHE"] = tf.name
            try:
                out = spawn.role_settings("implementation")  # should not raise
                allow_read = out["sandbox"]["filesystem"].get("allowRead", [])
                self.assertNotIn(tf.name, allow_read)
            finally:
                if saved is None:
                    os.environ.pop("GOMODCACHE", None)
                else:
                    os.environ["GOMODCACHE"] = saved


class SandboxDefaultOpenAccess(unittest.TestCase):
    """이슈 #72: 나머지 기본값 제한적인 샌드박스 스위치를 전부 연다. sandbox.enabled
    와 allowUnsandboxedCommands=False 는 그대로 유지되는지도 함께 검증한다."""

    def test_open_switches_set_for_every_sandboxed_role(self):
        for role_file in (Path(spawn.ROOT) / "roles").glob("*.json"):
            role = role_file.stem
            spec = json.loads(role_file.read_text())
            if not spec.get("sandbox", {}).get("enabled"):
                continue
            out = spawn.role_settings(role)
            net = out["sandbox"]["network"]
            self.assertIs(net["allowAllUnixSockets"], True, role)
            self.assertIs(net["allowLocalBinding"], True, role)
            self.assertEqual(net["allowMachLookup"], ["*"], role)
            self.assertIs(out["sandbox"]["enableWeakerNetworkIsolation"], True, role)
            self.assertIs(out["sandbox"]["allowAppleEvents"], True, role)
            self.assertIs(out["sandbox"]["enableWeakerNestedSandbox"], True, role)
            self.assertIs(out["sandbox"]["enabled"], True, role)
            self.assertIs(out["sandbox"]["allowUnsandboxedCommands"], False, role)

    def test_role_declared_values_not_clobbered(self):
        """이슈 #38 의 registry-host 병합과 같은 패턴: 병합이지 교체가 아니다."""
        f = Path(spawn.ROOT) / "roles" / "implementation.json"
        original_text = f.read_text()
        spec = json.loads(original_text)
        spec.setdefault("sandbox", {})["enableWeakerNetworkIsolation"] = False
        spec["sandbox"].setdefault("network", {})["allowLocalBinding"] = False
        try:
            f.write_text(json.dumps(spec))
            out = spawn.role_settings("implementation")
            self.assertIs(out["sandbox"]["enableWeakerNetworkIsolation"], False)
            self.assertIs(out["sandbox"]["network"]["allowLocalBinding"], False)
        finally:
            f.write_text(original_text)


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
        blocked = [("implementation", "…§19 가 막는다")]
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
        self.assertEqual(spawn.classify(0, refused, [], [("implementation", "§19")]),
                         "waiting-on-human")

    def test_silent_failure_is_loud(self):
        # 실측된 침묵-사망 모드: exit 0, 보드 무변화, 막힌 줄도 없고,
        # **거부당한 것도 없다** — 그래서 아무도 이유를 모른다.
        self.assertEqual(spawn.classify(0, {}, [], []), "silent-failure")


class FailClosedDowngrade(unittest.TestCase):
    """issue #89 phase 2: progressed self-report but no verifiable commit
    must be downgraded, unless a blocked signal is present."""

    def test_no_new_commit_clean_tree_is_downgraded(self):
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, [], False, []),
            "failed-no-commit")

    def test_no_new_commit_dirty_tree_is_downgraded(self):
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, [], False,
                                        ["M some/file.py"]),
            "failed-no-commit")

    def test_new_commit_dirty_tree_is_promoted_not_downgraded(self):
        # issue #205 defect 1: a new commit landed but the tree is dirty
        # afterwards — this is not "no commit", so it must not collapse
        # into failed-no-commit. It gets its own outcome value instead.
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, [], True,
                                        ["M some/file.py"]),
            "progressed-dirty-tree")

    def test_new_commit_clean_tree_is_left_alone(self):
        # honest-success path: real commit landed, tree is clean — no
        # false positive, no friction.
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, [], True, []),
            "progressed")

    def test_blocked_signal_exempts_progressed_from_downgrade(self):
        # hunt-phase1.md: classify() checks delta before blocked, so a
        # run that touched the board while a human gate is still open is
        # classified "progressed" today. The downgrade must not silently
        # erase that honest blocked signal by demoting it to FAILED.
        blocked = [("implementation", "§19")]
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, blocked, False, []),
            "progressed")

    def test_non_progressed_outcomes_are_never_touched(self):
        for outcome in ("waiting-on-human", "refused", "errored",
                        "silent-failure", "uncommitted-work"):
            self.assertEqual(
                spawn.fail_closed_downgrade(outcome, 3, [], False, []),
                outcome, outcome)

    def test_adhoc_spawns_are_out_of_scope(self):
        # issue is None -> no dedicated git workspace to check; leave as-is.
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", None, [], False, []),
            "progressed")

    def test_already_delivered_branch_exempts_verify_only_session(self):
        # issue-129 survey root cause 4 (issue-126's phase-2 sequence): a
        # phase-2 session on a branch that already carries phase-1's
        # commit+PR made no new commit of its own (before_head ==
        # after_head) but only read/verified — that is not a failure.
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, [], False, [],
                                        already_delivered=True),
            "progressed")

    def test_already_delivered_with_dirty_tree_still_downgrades(self):
        # "already delivered" covers prior commits, not this session's own
        # uncommitted leftovers.
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, [], False,
                                        ["M some/file.py"],
                                        already_delivered=True),
            "failed-no-commit")


class PriorEventDetails(unittest.TestCase):
    """issue #129 root cause 1: `pr-opened` must not re-fire for a PR URL
    already recorded in this workspace's `.events.jsonl` from an earlier
    process (e.g. issue-123's repeated PR #124 URL across respawns)."""

    def test_empty_when_file_missing(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(
                spawn._prior_event_details(Path(td) / "missing.events.jsonl",
                                           "pr-opened"),
                set())

    def test_reads_prior_matching_details(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / ".events.jsonl"
            p.write_text(
                json.dumps({"ts": 1, "type": "pr-opened",
                           "detail": "https://github.com/o/r/pull/124"}) + "\n"
                + json.dumps({"ts": 2, "type": "gate-refusal",
                             "detail": "x"}) + "\n")
            self.assertEqual(
                spawn._prior_event_details(p, "pr-opened"),
                {"https://github.com/o/r/pull/124"})


class PreambleWarning(unittest.TestCase):
    """The issue-workspace task preamble in `_spawn_one` (spawn.py source,
    not a re-implementation) must warn that the turn is headless/single-turn
    and that run_in_background work dies at turn end."""

    def test_issue_preamble_source_warns_about_headless_background_death(self):
        src = Path(spawn.__file__).read_text(encoding="utf-8")
        start = src.index('task = (f"당신의 이슈:')
        end = src.index(") + task", start)
        preamble_src = src[start:end]
        self.assertIn("headless", preamble_src)
        self.assertIn("run_in_background", preamble_src)


class GitHead(unittest.TestCase):
    def test_head_of_empty_repo_is_none(self):
        with tempfile.TemporaryDirectory() as td:
            import subprocess
            subprocess.run(["git", "init", "-q"], cwd=td)
            self.assertIsNone(spawn._git_head(td))

    def test_head_of_repo_with_commit_is_a_sha(self):
        with tempfile.TemporaryDirectory() as td:
            import subprocess
            subprocess.run(["git", "init", "-q"], cwd=td)
            subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=td)
            subprocess.run(["git", "config", "user.name", "t"], cwd=td)
            (Path(td) / "a.txt").write_text("x")
            subprocess.run(["git", "add", "a.txt"], cwd=td)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=td)
            head = spawn._git_head(td)
            self.assertIsNotNone(head)
            self.assertEqual(len(head), 40)


class IsNewCommit(unittest.TestCase):
    def test_fresh_repo_first_commit_is_new(self):
        self.assertTrue(spawn._is_new_commit("ignored", None, "abc123"))

    def test_no_after_head_is_not_new(self):
        self.assertFalse(spawn._is_new_commit("ignored", "abc123", None))

    def test_unchanged_head_is_not_new(self):
        self.assertFalse(spawn._is_new_commit("ignored", "abc123", "abc123"))

    def test_checkout_of_preexisting_branch_is_not_new_commit(self):
        # Reproduces hunt-phase2 finding: a session that checks out an
        # unrelated pre-existing branch (no new commit created) must not be
        # counted as new_commit, even though HEAD moved.
        with tempfile.TemporaryDirectory() as td:
            import subprocess

            def git(*a):
                return subprocess.run(["git", "-C", td, *a],
                                       capture_output=True, text=True, check=True)

            git("init", "-q")
            git("config", "user.email", "t@t.t")
            git("config", "user.name", "t")
            (Path(td) / "a.txt").write_text("x")
            git("add", "a.txt")
            git("commit", "-q", "-m", "init")
            init_branch = subprocess.run(
                ["git", "-C", td, "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()
            # Orphan branch with unrelated history — not a descendant of
            # init_branch — so its tip is a pre-existing commit that is in
            # no ancestry relationship with before_head at all.
            git("checkout", "-q", "--orphan", "other")
            (Path(td) / "b.txt").write_text("y")
            git("add", "b.txt")
            git("commit", "-q", "-m", "pre-existing unrelated commit")
            git("checkout", "-q", init_branch)

            before_head = spawn._git_head(td)
            git("checkout", "-q", "other")  # no new commit — just a checkout
            after_head = spawn._git_head(td)

            self.assertNotEqual(before_head, after_head)
            self.assertFalse(spawn._is_new_commit(td, before_head, after_head))

    def test_real_new_commit_is_new(self):
        with tempfile.TemporaryDirectory() as td:
            import subprocess

            def git(*a):
                return subprocess.run(["git", "-C", td, *a],
                                       capture_output=True, text=True, check=True)

            git("init", "-q")
            git("config", "user.email", "t@t.t")
            git("config", "user.name", "t")
            (Path(td) / "a.txt").write_text("x")
            git("add", "a.txt")
            git("commit", "-q", "-m", "init")
            before_head = spawn._git_head(td)
            (Path(td) / "a.txt").write_text("y")
            git("add", "a.txt")
            git("commit", "-q", "-m", "progress")
            after_head = spawn._git_head(td)
            self.assertTrue(spawn._is_new_commit(td, before_head, after_head))


class Ledger(unittest.TestCase):
    def test_appends_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            old = spawn.ROOT
            spawn.ROOT = Path(td)
            try:
                p = spawn.ledger_write({"role": "execution-observation", "outcome": "progressed"})
                p2 = spawn.ledger_write({"role": "review", "outcome": "errored"})
            finally:
                spawn.ROOT = old
            self.assertEqual(p, p2)
            lines = [json.loads(l) for l in p.read_text().splitlines()]
            self.assertEqual([l["role"] for l in lines], ["execution-observation", "review"])

    def test_entry_carries_the_live_log_path(self):
        # 이슈 #192 요구사항 2: ledger 엔트리의 `log` 필드가 그 세션이 실제
        # 쓴 라이브 로그(로스터에 등록된 값)와 같아야, 세션 종료 뒤 그
        # 로그를 session_id 로 되짚어 찾을 수 있다.
        import subprocess as sp
        from unittest import mock

        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "issue-9-eo"
            work.mkdir()
            run = lambda *a: sp.run(a, cwd=str(work), capture_output=True,
                                    text=True, check=True)
            run("git", "init", "-q")
            run("git", "config", "user.email", "t@example.com")
            run("git", "config", "user.name", "t")
            (work / "f.txt").write_text("x")
            run("git", "add", "f.txt")
            run("git", "commit", "-q", "-m", "init")

            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            entries = []
            roster_calls = []
            orig_roster_register = spawn.roster_register

            def spy_roster_register(key, entry):
                roster_calls.append((key, dict(entry)))
                return orig_roster_register(key, entry)

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register",
                                       spy_roster_register), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda entry: entries.append(entry)):
                    spawn._spawn_one(str(work), "execution-observation", "task\n",
                                     unattended=True, issue=9)
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster

            roster_entry = dict([e for k, e in roster_calls
                                 if k == "issue-9/execution-observation"][0])
            self.assertEqual(len(entries), 1, entries)
            self.assertEqual(entries[0]["log"], roster_entry["log"])
            self.assertTrue(Path(entries[0]["log"]).exists())


class OwnershipReport(unittest.TestCase):
    """세션 안 게이트가 안 돌았을 때의 마지막 흔적. 막지는 않고 말만 한다."""
    B = spawn.BOARD

    def test_own_record_and_subtree_are_silent(self):
        self.assertEqual(spawn.ownership_report(
            "/x", "execution-observation", [f"{self.B}/issue-3/reports/execution-observation.md",
                         f"{self.B}/issue-3/reports/execution-observation/run.log"]), [])

    def test_foreign_record_is_named(self):
        out = spawn.ownership_report("/x", "execution-observation",
                                     [f"{self.B}/issue-3/reports/coding.md"])
        self.assertTrue(out and "coding.md" in out[1])

    def test_granted_subtrees_are_silent(self):
        self.assertEqual(spawn.ownership_report(
            "/x", "release-engineering", [f"{self.B}/issue-3/reports/postmortems/x.md"]), [])

    def test_paths_outside_the_board_are_not_its_business(self):
        self.assertEqual(spawn.ownership_report("/x", "execution-observation", ["src/app.py"]), [])


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
    """드라이버의 유일한 일은 **멈추는 것**이다 — 누구를 다음에 띄울지는
    자동 라우팅 표가 아니라 오케스트레이터의 판단이다(이슈 #120), 그래서
    drive() 는 스스로 역할을 고르지 않고 항상 즉시 멈춘다."""

    def test_stops_when_nothing_to_spawn(self):
        self.assertEqual(spawn.drive("/x", False), 0)

    def test_never_calls_spawn_one(self):
        calls = []
        old_spawn = spawn._spawn_one
        spawn._spawn_one = lambda *a, **k: calls.append(a) or 0
        try:
            spawn.drive("/x", False, limit=3)
            self.assertEqual(calls, [], "drive 가 역할을 자동으로 스폰했다")
        finally:
            spawn._spawn_one = old_spawn


class IssueScopedPrompt(unittest.TestCase):
    """이슈 스코프 준비는 정확히 한 번 일어난다.

    프리앰블이 두 번 붙으면 역할은 같은 지시를 두 벌 읽는다 — 모델이 중복을
    모순으로 읽을 여지를 주는 것도 문제지만, 준비 자체가 두 번 돌면
    워크스페이스 준비와 브랜치 체크아웃도 두 번 돈다. 세션이 실제로 받는
    프롬프트를 관측해서 잡는다: 스폰 명령을 `cat` 으로 갈아끼우면 stdin 으로
    넘어간 맡길 일이 그대로 라이브 로그에 떨어진다.
    """

    def test_preparation_and_preamble_happen_once(self):
        import subprocess as sp
        from unittest import mock

        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "issue-7-qa"
            work.mkdir()
            run = lambda *a: sp.run(a, cwd=str(work), capture_output=True,
                                    text=True, check=True)
            run("git", "init", "-q")
            run("git", "config", "user.email", "t@example.com")
            run("git", "config", "user.name", "t")
            (work / "f.txt").write_text("x")
            run("git", "add", "f.txt")
            run("git", "commit", "-q", "-m", "init")

            prep = []

            def fake_workspace(cwd, issue, role):
                prep.append(("workspace", str(cwd)))
                return str(work)

            def fake_branch(cwd, issue, role):
                prep.append(("branch", str(cwd)))
                return f"issue-{issue}-{role}"

            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            roster_calls = []
            orig_roster_register = spawn.roster_register

            def spy_roster_register(key, entry):
                roster_calls.append((key, dict(entry)))
                return orig_roster_register(key, entry)

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "issue_workspace", fake_workspace), \
                     mock.patch.object(spawn, "checkout_issue_branch", fake_branch), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register",
                                       spy_roster_register), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda *a, **k: None):
                    spawn._spawn_one(str(work), "execution-observation", "원래 맡긴 일.\n",
                                     unattended=True, issue=7)
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster

            log_path = [e for k, e in roster_calls
                       if k == "issue-7/execution-observation"][0]["log"]
            delivered = Path(log_path).read_text()
            self.assertEqual(delivered.count("당신의 이슈:"), 1, delivered)
            self.assertEqual(delivered.count("원래 맡긴 일."), 1, delivered)
            self.assertEqual([p for p, _ in prep].count("workspace"), 1, prep)
            self.assertEqual([p for p, _ in prep].count("branch"), 1, prep)


class EventReporting(unittest.TestCase):
    """issue #129 phase 2: `.events.jsonl` 기록의 정확성 — 실측된 오탐 3건
    (gate-refusal 오탐 2건, pr-opened 중복 1건)을 보존된 fixture 로 재현."""

    def _run(self, td, task, roster_key="e", pr_for_branch=lambda *a, **k: None,
             branch="b"):
        import subprocess as sp
        from unittest import mock

        work = Path(td) / "work"
        if not work.exists():
            work.mkdir()
            run = lambda *a: sp.run(a, cwd=str(work), capture_output=True,
                                    text=True, check=True)
            run("git", "init", "-q")
            run("git", "config", "user.email", "t@example.com")
            run("git", "config", "user.name", "t")
            (work / "f.txt").write_text("x")
            run("git", "add", "f.txt")
            run("git", "commit", "-q", "-m", "init")
        roster = Path(td) / "active.json"
        old_roster = spawn.ROSTER
        spawn.ROSTER = roster
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            with mock.patch.object(spawn, "issue_workspace",
                                   lambda cwd, issue, role: str(work)), \
                 mock.patch.object(spawn, "checkout_issue_branch",
                                   lambda cwd, issue, role: branch), \
                 mock.patch.object(spawn, "spawn_cmd",
                                   lambda *a, **k: (["cat"], {})), \
                 mock.patch.object(spawn, "ensure_pushed",
                                   lambda *a, **k: None), \
                 mock.patch.object(spawn, "ledger_write",
                                   lambda *a, **k: None), \
                 mock.patch.object(spawn, "_pr_for_branch", pr_for_branch):
                spawn._spawn_one(str(work), "execution-observation", task, unattended=True, issue=7)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            spawn.ROSTER = old_roster
        events_path = Path(str(work) + spawn.EVENTS_SUFFIX)
        if not events_path.exists():
            return []
        return [json.loads(l) for l in events_path.read_text().splitlines()]

    def test_end_turn_result_is_not_a_gate_refusal(self):
        # issue-46/49 survey fixture: a normal end_turn result JSON line
        # contains the literal key name "permission_denials" — the old
        # raw-text regex misfired on the key name itself.
        line = json.dumps({"type": "result", "stop_reason": "end_turn",
                           "is_error": False, "permission_denials": []})
        events = self._run(tempfile.mkdtemp(), line + "\n")
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_echoed_source_mentioning_denied_is_not_a_gate_refusal(self):
        # issue-126 survey fixture: mid-session tool output echoing this
        # file's own `_DENIAL_RE = re.compile(r"permission_denial|denied", ...)`
        # source line used to trip the raw-text scan.
        echoed = ('{"type":"user","message":{"content":[{"type":"tool_result",'
                  '"content":"_DENIAL_RE = re.compile(r\\"permission_denial|denied\\", re.IGNORECASE)"}]}}\n')
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": []})
        events = self._run(tempfile.mkdtemp(), echoed + result_line + "\n")
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_real_denial_still_reported(self):
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(), result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "gate-refusal"], events)

    def test_pr_opened_does_not_refire_across_respawns(self):
        # issue-123 survey fixture: PR #124's URL, echoed again on a later
        # respawn of the same workspace, must not append a second
        # pr-opened event — dedup is durable across process restarts.
        td = tempfile.mkdtemp()
        url = "https://github.com/o/r/pull/124"
        pr_for_branch = lambda *a, **k: 124  # 이 브랜치의 실제 PR — 두 respawn 모두 같은 값
        self._run(td, url + "\n", pr_for_branch=pr_for_branch)
        events = self._run(td, "이미 있는 PR 링크를 또 echo 한다: " + url + "\n",
                           pr_for_branch=pr_for_branch)
        opened = [e for e in events if e["type"] == "pr-opened" and e["detail"] == url]
        self.assertEqual(len(opened), 1, events)

    def test_read_only_repo_url_does_not_fire_pr_opened_when_no_pr_exists(self):
        # issue-180 실측: 세션이 자기 레포 PR URL 을 텍스트로 읽기만 했다 —
        # `_pr_for_branch` 는 이 브랜치에 PR 이 없다는 뜻으로 None 을 낸다.
        url = "https://github.com/tokenmaxxxer/on-the-record/pull/142"
        events = self._run(tempfile.mkdtemp(), url + "\n",
                           pr_for_branch=lambda *a, **k: None)
        self.assertFalse([e for e in events if e["type"] == "pr-opened"], events)

    def test_read_only_repo_url_does_not_fire_pr_opened_when_different_pr_open(self):
        # 언급된 번호(142)와 실제 열린 PR 번호(99)가 다르면 여전히 "읽기만"이다.
        url = "https://github.com/tokenmaxxxer/on-the-record/pull/142"
        events = self._run(tempfile.mkdtemp(), url + "\n",
                           pr_for_branch=lambda *a, **k: 99)
        self.assertFalse([e for e in events if e["type"] == "pr-opened"], events)

    def test_pull_new_branch_url_does_not_fire_pr_opened(self):
        # 이슈가 명시적으로 요청한 신규 케이스: `git push` 안내가 찍는
        # `.../pull/new/<branch>` 는 PR 번호가 없어 `_PR_URL_RE` 자체가 안 잡는다.
        calls = []
        url = "https://github.com/tokenmaxxxer/on-the-record/pull/new/issue-180/implementation"
        events = self._run(tempfile.mkdtemp(), url + "\n",
                           pr_for_branch=lambda *a, **k: calls.append(a) or 555)
        self.assertFalse([e for e in events if e["type"] == "pr-opened"], events)
        self.assertEqual(calls, [])  # 후보가 아예 안 뽑혔으니 gh 도 안 불렸다

    def test_actually_opened_pr_fires_pr_opened(self):
        # 실패 신호(제안서): 이게 없으면 "영원한 대기" 회귀를 못 잡는다.
        url = "https://github.com/tokenmaxxxer/on-the-record/pull/555"
        events = self._run(tempfile.mkdtemp(), url + "\n",
                           pr_for_branch=lambda *a, **k: 555)
        opened = [e for e in events if e["type"] == "pr-opened"]
        self.assertEqual(opened, [{"ts": opened[0]["ts"], "type": "pr-opened",
                                   "detail": url}], events)

    def test_pr_for_branch_call_count_not_proportional_to_candidate_urls(self):
        # PR #184 리뷰 코멘트의 수용 기준: 브랜치의 실제 PR 번호가 한 번
        # 풀리고 나면, 그 뒤 후보 URL 이 몇 개 더 나와도(실측: 세션 하나가
        # 5개 이상 흘렸다) _pr_for_branch 는 다시 불리지 않는다.
        calls = []

        def counting(root, br):
            calls.append((str(root), br))
            return 555

        urls = [f"https://github.com/tokenmaxxxer/on-the-record/pull/{n}\n"
               for n in (1, 142, 124, 555, 142, 7, 8, 555)]  # 8개 후보, 서로 다른 번호 다수
        events = self._run(tempfile.mkdtemp(), "".join(urls),
                           pr_for_branch=counting)
        self.assertEqual(len(calls), 1, calls)  # 후보 8개인데 호출은 1번
        opened = [e["detail"] for e in events if e["type"] == "pr-opened"]
        self.assertEqual(opened, ["https://github.com/tokenmaxxxer/on-the-record/pull/555"])

    def test_pr_for_branch_keeps_retrying_while_unresolved(self):
        # 위 메모이제이션이 "PR 이 아직 없을 때의 재시도" 성질까지 죽이면
        # 안 된다 — None 인 동안은 새 후보마다 계속 다시 묻는다.
        calls = []

        def always_none(root, br):
            calls.append((str(root), br))
            return None

        urls = [f"https://github.com/tokenmaxxxer/on-the-record/pull/{n}\n"
               for n in (1, 142, 124)]
        events = self._run(tempfile.mkdtemp(), "".join(urls), pr_for_branch=always_none)
        self.assertEqual(len(calls), 3, calls)  # 미해결 상태론 후보마다 재시도
        self.assertFalse([e for e in events if e["type"] == "pr-opened"], events)


class ProgressEvents(unittest.TestCase):
    """이슈 #180 ②: 세션 진행(산출물 쓰기 + 검증/커밋/푸시)이 `events.jsonl` 에
    `progress` 로 남는다 — 탐색성 호출은 안 남는다(입도 실패 방지)."""

    def _run(self, td, lines):
        return EventReporting()._run(td, "\n".join(json.dumps(l) for l in lines) + "\n")

    def test_write_tool_use_fires_progress(self):
        events = self._run(tempfile.mkdtemp(), [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Write",
                 "input": {"file_path": "docs/issue-180/reports/implementation.md"}},
            ]}},
        ])
        progress = [e for e in events if e["type"] == "progress"]
        self.assertEqual(progress, [{"ts": progress[0]["ts"], "type": "progress",
                                     "detail": {"kind": "tool_use",
                                                "detail": "Write docs/issue-180/reports/implementation.md"}}])

    def test_consecutive_writes_to_same_file_are_deduped(self):
        events = self._run(tempfile.mkdtemp(), [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Edit", "input": {"file_path": "spawn.py"}},
            ]}},
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Edit", "input": {"file_path": "spawn.py"}},
            ]}},
        ])
        self.assertEqual(len([e for e in events if e["type"] == "progress"]), 1, events)

    def test_writes_to_different_files_both_fire(self):
        events = self._run(tempfile.mkdtemp(), [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": "a.py"}},
            ]}},
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": "b.py"}},
            ]}},
        ])
        self.assertEqual(len([e for e in events if e["type"] == "progress"]), 2, events)

    def test_verification_and_commit_commands_fire_progress(self):
        for command in ("git commit -q -m x", "git push -q", "gh pr create --title t",
                        "python3 test_spawn.py", "python3 gates/ci.py ."):
            with self.subTest(command=command):
                events = self._run(tempfile.mkdtemp(), [
                    {"type": "assistant", "message": {"content": [
                        {"type": "tool_use", "name": "Bash", "input": {"command": command}},
                    ]}},
                ])
                progress = [e for e in events if e["type"] == "progress"]
                self.assertEqual(len(progress), 1, events)
                self.assertEqual(progress[0]["detail"]["kind"], "tool_use")

    def test_exploratory_bash_does_not_fire_progress(self):
        # 실패 신호(제안서): 이게 서면 알림 폭탄이 재현된 것이다.
        for command in ("ls docs/", "grep -rn foo .", "cat spawn.py", "git status",
                        "git diff"):
            with self.subTest(command=command):
                events = self._run(tempfile.mkdtemp(), [
                    {"type": "assistant", "message": {"content": [
                        {"type": "tool_use", "name": "Bash", "input": {"command": command}},
                    ]}},
                ])
                self.assertFalse([e for e in events if e["type"] == "progress"], events)

    def test_gate_refusal_parsing_still_works_alongside_progress(self):
        # gate-refusal 판별과 같은 obj 를 재사용하도록 바꾼 뒤에도 기존 동작이
        # 그대로인지 — result 라인은 여전히 result 로만 처리된다.
        events = self._run(tempfile.mkdtemp(), [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": "x.py"}},
            ]}},
            {"type": "result", "is_error": False,
             "permission_denials": [{"tool_name": "Write"}]},
        ])
        self.assertEqual(len([e for e in events if e["type"] == "progress"]), 1, events)
        self.assertEqual(len([e for e in events if e["type"] == "gate-refusal"]), 1, events)


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
                    "role": "implementation",
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

    def test_removes_all_generation_logs_and_sibling_files(self):
        # 이슈 #192 요구사항 4: 재스폰 세대마다 로그가 늘어나므로, `clean`
        # 은 고정 접미사 하나가 아니라 워크스페이스-이름 프리픽스의 형제
        # 파일을 전부(세대별 로그 2개 이상 + events.jsonl + task.txt +
        # respawn-claim 락 파일) 치워야 한다. 살아있는 세션의 형제 파일은
        # 그대로 남는다.
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            live_ws = wb / "issue-51-coding"
            dead_ws = wb / "issue-51-review"
            self._make_clean_repo(live_ws, Path(td) / "remote-live.git")
            self._make_clean_repo(dead_ws, Path(td) / "remote-dead.git")

            live_siblings = [
                Path(str(live_ws) + ".session.20260802T150000.111.log"),
                Path(str(live_ws) + ".events.jsonl"),
            ]
            dead_siblings = [
                Path(str(dead_ws) + ".session.20260802T140000.222.log"),
                Path(str(dead_ws) + ".session.20260802T150500.333.log"),
                Path(str(dead_ws) + ".events.jsonl"),
                Path(str(dead_ws) + ".events.offset"),
                Path(str(dead_ws) + ".task.txt"),
                Path(str(dead_ws) + ".respawn-claim-20260802T140500"),
            ]
            for p in live_siblings + dead_siblings:
                p.write_text("x")

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({
                "issue-51/coding": {
                    "pid": os.getpid(),
                    "work": str(live_ws),
                    "issue": 51,
                    "role": "implementation",
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

            self.assertTrue(live_ws.is_dir())
            for p in live_siblings:
                self.assertTrue(p.exists(), p)
            self.assertFalse(dead_ws.exists())
            for p in dead_siblings:
                self.assertFalse(p.exists(), p)

    def test_directory_sibling_does_not_abort_the_clean_loop(self):
        # issue #205 defect 3: a directory sibling in the glob used to hit
        # sibling.unlink() unguarded and raise IsADirectoryError, aborting
        # the whole clean loop before later workspaces were reached. The
        # glob currently only ever matches files, so this is latent — the
        # guard must not crash and must still let the rest of the sweep run.
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            dead_ws_a = wb / "issue-51-review"
            dead_ws_b = wb / "issue-52-review"
            self._make_clean_repo(dead_ws_a, Path(td) / "remote-a.git")
            self._make_clean_repo(dead_ws_b, Path(td) / "remote-b.git")

            dir_sibling = Path(str(dead_ws_a) + ".somedir")
            dir_sibling.mkdir()
            (dir_sibling / "inner.txt").write_text("x")
            file_sibling = Path(str(dead_ws_a) + ".events.jsonl")
            file_sibling.write_text("x")

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({}))

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

            self.assertFalse(dead_ws_a.exists())
            self.assertFalse(dead_ws_b.exists())
            self.assertFalse(file_sibling.exists())
            self.assertTrue(dir_sibling.is_dir())

    def test_readonly_file_is_removed_via_chmod_retry(self):
        # issue #229: a read-only file (e.g. Go module cache laid down by
        # `go mod download`) used to make bare shutil.rmtree() raise
        # PermissionError. clean must chmod it writable and retry.
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            dead_ws = wb / "issue-51-review"
            self._make_clean_repo(dead_ws, Path(td) / "remote-dead.git")

            # Go's module cache marks the *directory*, not just the file,
            # read-only (0o555) — unlinking a file needs write permission
            # on its parent directory, not the file itself, so this is
            # what actually reproduces the PermissionError on POSIX.
            # Commit it first so `clean`'s git-status safety check still
            # judges the workspace safe to remove (matches the real Go
            # module cache case: it's untracked but .gitignore'd, so it
            # never shows up in `git status --porcelain`).
            ro_dir = dead_ws / "gomod_cache_pkg"
            ro_dir.mkdir()
            ro_file = ro_dir / "readonly.go"
            ro_file.write_text("package x")
            run = lambda *args: __import__("subprocess").run(
                args, cwd=str(dead_ws), capture_output=True, text=True,
                check=True)
            (dead_ws / ".gitignore").write_text("gomod_cache_pkg/\n")
            run("git", "add", ".gitignore")
            run("git", "commit", "-q", "-m", "ignore cache dir")
            run("git", "push", "-q", "origin", "HEAD:main")
            ro_dir.chmod(0o555)
            self.addCleanup(lambda: ro_dir.chmod(0o755) if ro_dir.exists() else None)

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({}))

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
            self.assertFalse(dead_ws.exists())
            self.assertIn("지움", out)
            self.assertNotIn("PermissionError", out)

    def test_failed_workspace_removal_does_not_abort_the_clean_loop(self):
        # issue #229: a workspace whose removal still fails after the
        # chmod retry (e.g. an unremovable parent dir) must not stop
        # clean from processing subsequent workspaces.
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            broken_ws = wb / "issue-51-review"
            healthy_ws = wb / "issue-52-review"
            self._make_clean_repo(broken_ws, Path(td) / "remote-a.git")
            self._make_clean_repo(healthy_ws, Path(td) / "remote-b.git")

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({}))

            old_roster = spawn.ROSTER
            old_argv = sys.argv
            old_environ = dict(os.environ)
            spawn.ROSTER = roster_path
            os.environ["MUSTER_WORK_DIR"] = str(wb)
            sys.argv = ["spawn.py", "clean"]

            import shutil as _shutil
            real_rmtree = _shutil.rmtree

            def _rmtree_fails_for_broken(path, *args, **kwargs):
                if Path(path) == broken_ws:
                    raise PermissionError(f"simulated unremovable: {path}")
                return real_rmtree(path, *args, **kwargs)

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with unittest.mock.patch.object(
                        _shutil, "rmtree", side_effect=_rmtree_fails_for_broken):
                    spawn.main()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                sys.argv = old_argv
                os.environ.clear()
                os.environ.update(old_environ)

            out = buf.getvalue()
            self.assertTrue(broken_ws.exists())
            self.assertFalse(healthy_ws.exists())
            self.assertIn("실패", out)
            self.assertIn("지움", out)


class Watchdog(unittest.TestCase):
    """이슈 #90 phase-2: observe-only 이상 신호 네 가지."""

    def _entry(self, log, work=None, ts=None, before_head=None):
        return {"log": str(log), "work": work, "ts": ts or int(time.time()),
                "before_head": before_head}

    def test_silence_signal_fires_past_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            stale = time.time() - (spawn.WATCHDOG_SILENCE_MIN + 5) * 60
            os.utime(log, (stale, stale))
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertTrue(any("log-silence" in a for a in out))

    def test_no_silence_signal_within_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertFalse(any("log-silence" in a for a in out))

    def test_delegation_phrasing_signal(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text","text":"run_in_background 로 넘겼다"}\n')
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertTrue(any("background-delegation-phrasing" in a for a in out))

    def test_no_delegation_signal_on_clean_log(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text","text":"평범한 진행 로그"}\n')
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertFalse(any("background-delegation-phrasing" in a for a in out))

    def test_denied_tool_calls_signal_fires_at_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text("permission_denial\n" * spawn.WATCHDOG_DENIAL_THRESHOLD)
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertTrue(any("denied-tool-calls" in a for a in out))

    def test_denied_tool_calls_signal_silent_below_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text("permission_denial\n" * (spawn.WATCHDOG_DENIAL_THRESHOLD - 1))
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertFalse(any("denied-tool-calls" in a for a in out))

    def test_only_new_log_content_is_scanned_each_call(self):
        # 이미 스캔한 구간은 다음 호출에서 다시 세지 않는다 (오프셋 추적).
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text("permission_denial\n" * spawn.WATCHDOG_DENIAL_THRESHOLD)
            state = {}
            first = spawn.watchdog_check_one("k", self._entry(log), state=state)
            self.assertTrue(any("denied-tool-calls" in a for a in first))
            second = spawn.watchdog_check_one("k", self._entry(log), state=state)
            self.assertFalse(any("denied-tool-calls" in a for a in second))

    def test_stale_offset_survives_log_truncation_on_respawn(self):
        # spawn() 은 같은 로그 경로를 "w" 로 다시 열어 재시작 시 truncate
        # 한다. 이전 세션에서 쌓인 오프셋이 새 로그(더 짧음)에 그대로 남아
        # 있으면 새 세션의 신호 2/3 이 로그가 옛 길이를 다시 넘어설 때까지
        # 조용히 안 잡힌다 — 재시작 직후 첫 스캔에서 바로 잡혀야 한다.
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text("permission_denial\n" * (spawn.WATCHDOG_DENIAL_THRESHOLD + 5))
            state = {}
            first = spawn.watchdog_check_one("k", self._entry(log), state=state)
            self.assertTrue(any("denied-tool-calls" in a for a in first))
            self.assertGreater(state["k"]["offset"], 0)
            # respawn: 로그가 truncate 되어 이전 오프셋보다 짧아진다
            log.write_text("permission_denial\n" * spawn.WATCHDOG_DENIAL_THRESHOLD)
            second = spawn.watchdog_check_one("k", self._entry(log), state=state)
            self.assertTrue(any("denied-tool-calls" in a for a in second))

    def test_no_commits_late_signal_fires(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            work.mkdir()
            subprocess.run(["git", "init", "-q", str(work)])
            subprocess.run(["git", "-C", str(work), "config", "user.email", "t@t.t"])
            subprocess.run(["git", "-C", str(work), "config", "user.name", "t"])
            (work / "f").write_text("x")
            subprocess.run(["git", "-C", str(work), "add", "f"])
            subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "init"])
            head = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"],
                                  capture_output=True, text=True).stdout.strip()
            log = Path(td) / "s.log"
            log.write_text("")
            ts = time.time() - (spawn.WATCHDOG_NO_COMMIT_MIN + 5) * 60
            out = spawn.watchdog_check_one(
                "k", self._entry(log, work=str(work), ts=ts, before_head=head),
                state={})
            self.assertTrue(any("no-commits-late" in a for a in out))

    def test_no_commits_late_signal_silent_before_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            work.mkdir()
            subprocess.run(["git", "init", "-q", str(work)])
            subprocess.run(["git", "-C", str(work), "config", "user.email", "t@t.t"])
            subprocess.run(["git", "-C", str(work), "config", "user.name", "t"])
            (work / "f").write_text("x")
            subprocess.run(["git", "-C", str(work), "add", "f"])
            subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "init"])
            head = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"],
                                  capture_output=True, text=True).stdout.strip()
            log = Path(td) / "s.log"
            log.write_text("")
            out = spawn.watchdog_check_one(
                "k", self._entry(log, work=str(work), ts=time.time(), before_head=head),
                state={})
            self.assertFalse(any("no-commits-late" in a for a in out))

    def test_roster_watchdog_reports_no_anomaly_on_empty_roster(self):
        with tempfile.TemporaryDirectory() as td:
            roster_path = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            old_state = spawn.WATCHDOG_STATE
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                spawn.roster_watchdog()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
            self.assertIn("돌고 있는 역할 세션 없음", buf.getvalue())


class SessionEndVerdict(unittest.TestCase):
    """이슈 #132: session_end_verdict 3분법 — survey.md 사건들 + 벤인 레이스."""

    def _write_events(self, work, lines):
        Path(str(work) + ".events.jsonl").write_text(
            "\n".join(json.dumps(l) for l in lines) + "\n")

    def test_no_events_file_is_normal(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=None), "normal")

    def test_matched_session_end_is_normal(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
                {"type": "session-end", "detail": "progressed"},
            ])
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=None,
                                          alive_fn=lambda pid: False),
                "normal")

    def test_unmatched_and_dead_is_crashed(self):
        # survey.md 사건 #2: 크래시가 roster_remove/종료 이벤트 사이에서 나
        # events.jsonl 에 session-end 가 아예 없다.
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
            ])
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=None,
                                          alive_fn=lambda pid: False),
                "crashed")

    def test_benign_race_resolves_to_normal_not_crashed(self):
        # 벤인 레이스: 워치독의 _alive() 는 죽었다고 보지만 session-end 가
        # 이미 남았다 — session-end 매치를 먼저 확인하므로 normal 이어야
        # 한다(가짜 crashed 로 재스폰하지 않는다).
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
                {"type": "session-end", "detail": "progressed"},
            ])
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=None,
                                          alive_fn=lambda pid: False),
                "normal")

    def test_unmatched_alive_stale_log_is_stalled(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
            ])
            log = Path(str(work) + ".session.20260802T150000.111.log")
            log.write_text("still going")
            stale = time.time() - (spawn.WATCHDOG_SILENCE_MIN + 5) * 60
            os.utime(log, (stale, stale))
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=log,
                                          alive_fn=lambda pid: True),
                "stalled")

    def test_unmatched_alive_fresh_log_is_in_progress(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
            ])
            log = Path(str(work) + ".session.20260802T150000.111.log")
            log.write_text("still going")
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=log,
                                          alive_fn=lambda pid: True),
                "in-progress")


class AutoRespawnClaim(unittest.TestCase):
    """이슈 #132: crashed 한정 최대 2회 재스폰, claim-before-spawn, 상한 코멘트."""

    def _crashed_workspace(self, td, pid=111):
        work = Path(td) / "w"
        Path(str(work) + ".events.jsonl").write_text(
            json.dumps({"type": "session-start", "detail": {"pid": pid, "ts": 1}}) + "\n")
        Path(str(work) + ".task.txt").write_text("원래 맡길 일")
        return str(work)

    def test_no_respawn_when_not_crashed(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            Path(str(work) + ".events.jsonl").write_text(
                json.dumps({"type": "session-start", "detail": {"pid": 111, "ts": 1}})
                + "\n" + json.dumps({"type": "session-end", "detail": "progressed"}) + "\n")
            entry = {"work": str(work), "issue": 132, "role": "implementation", "log": ""}
            state = {}
            called = []
            orig = spawn._spawn_one
            spawn._spawn_one = lambda *a, **k: called.append(1)
            try:
                spawn._auto_respawn_check("issue-132/coding", entry, state)
            finally:
                spawn._spawn_one = orig
            self.assertEqual(called, [])
            self.assertEqual(state, {})

    def test_crashed_under_cap_claims_and_respawns(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._crashed_workspace(td)
            entry = {"work": work, "issue": 132, "role": "implementation", "log": "l"}
            state = {}
            called = []
            orig = spawn._spawn_one
            spawn._spawn_one = lambda *a, **k: called.append((a, k))
            try:
                spawn._auto_respawn_check("issue-132/coding", entry, state)
            finally:
                spawn._spawn_one = orig
            self.assertEqual(len(called), 1)
            self.assertEqual(state["issue-132/coding"]["attempts"], 1)
            events = Path(work + ".events.jsonl").read_text()
            self.assertIn("respawn-attempt", events)

    def test_already_claimed_session_is_not_respawned_twice(self):
        # 두 워치독 인스턴스가 같은 crashed 세션을 동시에 본 상황을 흉내:
        # respawn-attempt 이벤트가 이미 이 session_start_ts 로 남아있으면
        # 두 번째 호출은 아무 것도 하지 않는다.
        with tempfile.TemporaryDirectory() as td:
            work = self._crashed_workspace(td)
            with open(work + ".events.jsonl", "a") as fh:
                fh.write(json.dumps({"type": "respawn-attempt",
                                     "detail": {"session_start_ts": 1, "attempt": 1}}) + "\n")
            entry = {"work": work, "issue": 132, "role": "implementation", "log": "l"}
            state = {}
            called = []
            orig = spawn._spawn_one
            spawn._spawn_one = lambda *a, **k: called.append(1)
            try:
                spawn._auto_respawn_check("issue-132/coding", entry, state)
            finally:
                spawn._spawn_one = orig
            self.assertEqual(called, [])
            self.assertEqual(state, {})

    def test_concurrent_watchdogs_do_not_double_respawn(self):
        # warrant-hunter finding (2026-07-30): the events.jsonl-based
        # already_claimed check is check-then-act with no lock, so two
        # concurrent `watchdog --auto-respawn` invocations on the same
        # crashed entry could both pass it and both call _spawn_one.
        # The atomic O_CREAT|O_EXCL claim file must let exactly one through.
        import threading
        with tempfile.TemporaryDirectory() as td:
            work = self._crashed_workspace(td)
            entry = {"work": work, "issue": 132, "role": "implementation", "log": "l"}
            called = []
            lock = threading.Lock()
            orig = spawn._spawn_one
            def fake_spawn(*a, **k):
                with lock:
                    called.append(1)
            spawn._spawn_one = fake_spawn
            try:
                states = [{}, {}]
                threads = [threading.Thread(target=spawn._auto_respawn_check,
                                            args=("issue-132/coding", entry, states[i]))
                          for i in range(2)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
            finally:
                spawn._spawn_one = orig
            self.assertEqual(len(called), 1)

    def test_cap_reached_posts_comment_instead_of_respawning(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._crashed_workspace(td)
            entry = {"work": work, "issue": 132, "role": "implementation", "log": "l"}
            state = {"issue-132/coding": {"attempts": spawn.RESPAWN_MAX_ATTEMPTS}}
            called = []
            orig_spawn = spawn._spawn_one
            orig_comment = spawn._post_crash_comment
            spawn._spawn_one = lambda *a, **k: called.append(1)
            spawn._post_crash_comment = lambda *a, **k: called.append(("comment", a))
            try:
                spawn._auto_respawn_check("issue-132/coding", entry, state)
            finally:
                spawn._spawn_one = orig_spawn
                spawn._post_crash_comment = orig_comment
            self.assertEqual(len(called), 1)
            self.assertEqual(called[0][0], "comment")


class PostCrashComment(unittest.TestCase):
    """이슈 #132: 상한-코멘트 멱등성 — 마커 문자열이 이미 있으면 재포스팅 안 함."""

    def test_skips_when_marker_already_present(self):
        marker = spawn._CRASH_COMMENT_MARKER.format(key="issue-132/coding",
                                                     cap=spawn.RESPAWN_MAX_ATTEMPTS)
        orig_comments = spawn._issue_comments
        spawn._issue_comments = lambda root, n: [{"login": "bot", "body": marker}]
        calls = []
        orig_run = subprocess.run
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        try:
            spawn._post_crash_comment(Path("."), 132, "issue-132/coding", "w", "l")
        finally:
            spawn._issue_comments = orig_comments
            subprocess.run = orig_run
        self.assertEqual(calls, [])

    def test_posts_when_marker_absent(self):
        orig_comments = spawn._issue_comments
        orig_slug = spawn._repo_slug
        spawn._issue_comments = lambda root, n: []
        spawn._repo_slug = lambda root: "acme/repo"
        calls = []
        orig_run = subprocess.run
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        try:
            spawn._post_crash_comment(Path("."), 132, "issue-132/coding", "w", "l")
        finally:
            spawn._issue_comments = orig_comments
            spawn._repo_slug = orig_slug
            subprocess.run = orig_run
        self.assertEqual(len(calls), 1)
        self.assertIn("gh", calls[0])


class RosterConcurrency(unittest.TestCase):
    """issue #139: 잠금 없는 read-modify-write 가 동시 등록을 잃어버렸던 문제."""

    def test_concurrent_register_survives(self):
        import threading

        with tempfile.TemporaryDirectory() as td:
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            try:
                n = 20
                barrier = threading.Barrier(n)

                def register(i):
                    barrier.wait()
                    spawn.roster_register(f"issue-{i}/coding",
                                           {"pid": i, "role": "implementation",
                                            "issue": i, "ts": 0,
                                            "log": "", "work": ""})

                threads = [threading.Thread(target=register, args=(i,))
                           for i in range(n)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()

                d = json.loads(roster.read_text())
                self.assertEqual(len(d), n, d)
            finally:
                spawn.ROSTER = old_roster


class EventExitScope(unittest.TestCase):
    """이슈 #142 — 스폰은 **이 세션이 낸** 이벤트로만 리턴해야 한다.

    실측 2026-07-30(core issue-53 phase 2): 78분 전 phase 1 이 남긴
    `pr-opened https://github.com/octocat/Hello-World/pull/1` 로 스폰이 exit 0
    을 냈고, 세션은 계속 돌았다. 두 결함이 겹쳤다 — 과거 이벤트를 소비했고,
    그 이벤트의 URL 은 이 레포의 PR 도 아니었다.
    """

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.work = Path(self.td) / "wk"
        self.work.mkdir()
        self.events = spawn._events_path(self.work)
        self.offset = spawn._offset_path(self.work)
        self.log = Path(str(self.work) + ".session.log")
        self.log.write_text("")

    def tearDown(self):
        shutil.rmtree(self.td, ignore_errors=True)

    def test_stale_event_is_not_consumed_after_baseline(self):
        """이전 세션이 남긴 줄은 offset 을 파일 끝으로 민 뒤엔 안 보인다."""
        spawn._append_event(self.events, "pr-opened",
                            "https://github.com/octocat/Hello-World/pull/1")
        spawn._append_event(self.events, "session-end", "progressed")
        # 스폰이 fork 직전에 하는 일
        spawn._write_offset(self.offset, spawn._event_count(self.events))
        self.assertEqual(spawn._read_offset(self.offset), 2)
        # 새 세션이 자기 이벤트를 낸다 — 리턴은 이것으로만 일어나야 한다
        spawn._append_event(self.events, "session-start", {"pid": 111})
        lines = self.events.read_text().splitlines()
        ev = json.loads(lines[spawn._read_offset(self.offset)])
        self.assertEqual(ev["type"], "session-start")
        self.assertEqual(ev["detail"]["pid"], 111)

    def test_without_baseline_the_stale_event_wins(self):
        """기준선을 안 밀면 78분 전 줄이 먼저 잡힌다 — 고치기 전 동작."""
        spawn._append_event(self.events, "pr-opened",
                            "https://github.com/octocat/Hello-World/pull/1")
        spawn._append_event(self.events, "session-start", {"pid": 111})
        ev = json.loads(self.events.read_text().splitlines()[0])
        self.assertEqual(ev["type"], "pr-opened")   # 이게 실측된 오보의 씨앗

    def test_event_count_matches_offset_units(self):
        self.assertEqual(spawn._event_count(self.events), 0)
        spawn._append_event(self.events, "a", "1")
        spawn._append_event(self.events, "b", "2")
        self.assertEqual(spawn._event_count(self.events), 2)
        self.assertEqual(spawn._event_count(Path(self.td) / "nope.jsonl"), 0)

    def _origin(self, url):
        subprocess.run(["git", "init", "-q", str(self.work)], check=False)
        subprocess.run(["git", "-C", str(self.work), "remote", "add", "origin", url],
                       check=False, capture_output=True)
        return spawn._origin_pr_prefix(self.work)

    def test_pr_prefix_from_https_and_ssh_origin(self):
        self.assertEqual(self._origin("https://github.com/tokenmaxxxer/on-the-record.git"),
                         "https://github.com/tokenmaxxxer/on-the-record/pull/")

    def test_pr_prefix_none_without_origin(self):
        subprocess.run(["git", "init", "-q", str(self.work)], check=False)
        self.assertIsNone(spawn._origin_pr_prefix(self.work))

    def test_foreign_pr_url_is_not_this_repos_pr(self):
        prefix = self._origin("git@github.com:tokenmaxxxer/on-the-record.git")
        self.assertEqual(prefix, "https://github.com/tokenmaxxxer/on-the-record/pull/")
        found = spawn._PR_URL_RE.findall(
            'see https://github.com/octocat/Hello-World/pull/1 and '
            'https://github.com/tokenmaxxxer/on-the-record/pull/142')
        kept = [m for m in found if m.startswith(prefix)]
        self.assertEqual(kept, ["https://github.com/tokenmaxxxer/on-the-record/pull/142"])


class FlowsPayload(unittest.TestCase):
    """issue #172: `spawn.py flows --json` payload — schema shape per section,
    all `gh`-hitting helpers monkeypatched (no live network in tests)."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.addCleanup(self.td.cleanup)
        self._patched = []
        self._patch(spawn, "_repo_slug", lambda root: "acme/repo")
        self._patch(spawn, "_issue_comments", lambda root, n: [])
        self._patch(spawn, "_roster_load", lambda: {})
        old_root = spawn.ROOT
        spawn.ROOT = self.root
        self.addCleanup(setattr, spawn, "ROOT", old_root)
        sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
        import flows
        self.flows = flows
        self._patch(flows, "_pr_list_all", lambda root: [])
        self._patch(flows, "_issue_list_all", lambda root: [])
        import closure_sweep
        self.closure_sweep = closure_sweep
        self._patch(closure_sweep, "find_violations",
                    lambda root, subjects=None, issue_states=None: [])

    def _patch(self, obj, name, fn):
        orig = getattr(obj, name)
        setattr(obj, name, fn)
        self.addCleanup(setattr, obj, name, orig)

    def _write_record(self, subject, role, loop_state, verdict=None, upstream=False):
        rec = self.root / spawn.BOARD / subject / "reports"
        rec.mkdir(parents=True, exist_ok=True)
        body = f"---\nloop_state: {loop_state}\n"
        if verdict:
            body += f"verdict: {verdict}\n"
        if upstream:
            body += "upstream:\n  - path: docs/issue-1/reports/other.md\n"
        body += "---\n"
        (rec / f"{role}.md").write_text(body, encoding="utf-8")

    def test_schema_top_level_keys(self):
        payload = self.flows.flows_payload(self.root)
        for key in ("schema_version", "generated_at", "repo", "decision_queue",
                    "flows", "sessions", "ledger", "hygiene"):
            self.assertIn(key, payload)
        self.assertIsInstance(payload["schema_version"], int)
        self.assertIsInstance(payload["hygiene"]["closure_sweep"], list)
        self.assertIsInstance(payload["hygiene"]["unapproved_open_prs"], list)

    def test_flows_section_stage_mapping_and_unmapped_fallback(self):
        self._write_record("issue-10", "product-discovery", "scope-proposed")
        self._write_record("issue-11", "product-discovery", "some-downstream-state")
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[10]["stage"], "proposal")
        self.assertTrue(by_issue[10]["stage_derived"])
        self.assertEqual(by_issue[11]["stage"], "some-downstream-state")
        self.assertFalse(by_issue[11]["stage_derived"])

    def test_decision_queue_from_open_pr(self):
        self._write_record("issue-20", "product-discovery", "scope-proposed")
        self._patch(self.flows, "_pr_list_all", lambda root: [
            {"number": 99, "headRefName": "issue-20/product-discovery",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ])
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(len(payload["decision_queue"]), 1)
        entry = payload["decision_queue"][0]
        self.assertEqual(entry["pr"], 99)
        self.assertEqual(entry["phase"], 1)
        self.assertEqual(entry["awaiting"], "approve-scope")

    def test_decision_queue_from_open_pr_with_no_board_record(self):
        """issue #216 결함 1 회귀: 머지된 레코드도 계획 블록도 없는 이슈의
        PR(PR #86 재현)이 decision_queue 에 phase 1 로 떠야 한다."""
        self._patch(self.flows, "_pr_list_all", lambda root: [
            {"number": 86, "headRefName": "issue-86/product-discovery",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ])
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(len(payload["decision_queue"]), 1)
        entry = payload["decision_queue"][0]
        self.assertEqual(entry["issue"], 86)
        self.assertEqual(entry["pr"], 86)
        self.assertEqual(entry["phase"], 1)
        self.assertEqual(entry["awaiting"], "approve-scope")

    def test_decision_queue_phase_2_when_board_record_is_scope_approved(self):
        """issue #216: 레코드가 scope-approved(scope-proposed 아님)면 기존대로
        phase 2 로 분류돼야 한다 — 회귀 방지."""
        self._write_record("issue-31", "implementation", "scope-approved")
        self._patch(self.flows, "_pr_list_all", lambda root: [
            {"number": 56, "headRefName": "issue-31/implementation",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ])
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(len(payload["decision_queue"]), 1)
        entry = payload["decision_queue"][0]
        self.assertEqual(entry["phase"], 2)
        self.assertEqual(entry["awaiting"], "approve-full")

    def test_sessions_alive_is_pending_dead_looks_up_ledger(self):
        self._patch(spawn, "_roster_load", lambda: {
            "issue-5/coding": {"role": "coding", "issue": 5, "pid": 999999,
                               "ts": int(time.time())},
        })
        spawn.ledger_write({"role": "coding", "cost_usd": 1.0, "outcome": "progressed",
                           "board_delta": ["docs/issue-5/reports/coding.md"],
                           "repo": "repo"})
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(len(payload["sessions"]), 1)
        s = payload["sessions"][0]
        # pid 999999 is assumed not alive in the test sandbox
        if not s["alive"]:
            self.assertEqual(s["verdict"], "progressed")

    def test_sessions_last_activity_from_tool_use_tail(self):
        log = self.root / "wk.session.log"
        log.write_text(
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "writing the role file"},
                {"type": "tool_use", "name": "Write",
                 "input": {"file_path": "roles/data-modeling.json"}},
            ]}}) + "\n",
            encoding="utf-8")
        self._patch(spawn, "_roster_load", lambda: {
            "issue-5/coding": {"role": "coding", "issue": 5, "pid": 999999,
                               "ts": int(time.time()), "log": str(log)},
        })
        payload = self.flows.flows_payload(self.root)
        la = payload["sessions"][0]["last_activity"]
        self.assertEqual(la["kind"], "tool_use")
        self.assertEqual(la["detail"], "Write roles/data-modeling.json")
        self.assertRegex(la["ts"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_sessions_last_activity_none_when_no_log(self):
        self._patch(spawn, "_roster_load", lambda: {
            "issue-5/coding": {"role": "coding", "issue": 5, "pid": 999999,
                               "ts": int(time.time())},
        })
        payload = self.flows.flows_payload(self.root)
        self.assertIsNone(payload["sessions"][0]["last_activity"])

    def test_ledger_aggregation_per_issue_and_unattributed_bucket(self):
        spawn.ledger_write({"role": "coding", "cost_usd": 1.5, "outcome": "progressed",
                           "board_delta": ["docs/issue-7/reports/coding.md"],
                           "repo": "repo"})
        spawn.ledger_write({"role": "coding", "cost_usd": 0.5, "outcome": "refused",
                           "board_delta": [], "repo": "repo"})
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(len(payload["ledger"]), 1)
        self.assertEqual(payload["ledger"][0]["issue"], 7)
        self.assertEqual(payload["ledger"][0]["sessions"], 1)
        self.assertAlmostEqual(payload["ledger"][0]["cost_usd_total"], 1.5)
        self.assertEqual(payload["unattributed"]["sessions"], 1)
        self.assertAlmostEqual(payload["unattributed"]["cost_usd_total"], 0.5)

    def test_ledger_filtered_by_repo_field_and_cwd_fallback(self):
        """issue #216 결함 2 회귀: `repo` 필드가 다른 엔트리는 걸러지고,
        `repo` 필드 없이 `cwd` 만 있는 옛 형태 엔트리도 basename 파싱으로
        올바르게 필터링돼야 한다(매칭/불일치 둘 다)."""
        spawn.ledger_write({"role": "coding", "cost_usd": 1.0, "outcome": "progressed",
                           "board_delta": ["docs/issue-8/reports/coding.md"],
                           "repo": "repo"})
        spawn.ledger_write({"role": "coding", "cost_usd": 5.0, "outcome": "progressed",
                           "board_delta": ["docs/issue-8/reports/coding.md"],
                           "repo": "other-repo"})
        spawn.ledger_write({"role": "coding", "cost_usd": 2.0, "outcome": "progressed",
                           "board_delta": ["docs/issue-9/reports/coding.md"],
                           "cwd": "/work/repo-issue-9-coding"})
        spawn.ledger_write({"role": "coding", "cost_usd": 9.0, "outcome": "progressed",
                           "board_delta": ["docs/issue-9/reports/coding.md"],
                           "cwd": "/work/other-repo-issue-9-coding"})
        payload = self.flows.flows_payload(self.root)
        by_issue = {l["issue"]: l for l in payload["ledger"]}
        self.assertEqual(set(by_issue), {8, 9})
        self.assertAlmostEqual(by_issue[8]["cost_usd_total"], 1.0)
        self.assertAlmostEqual(by_issue[9]["cost_usd_total"], 2.0)

    def test_hygiene_includes_closure_sweep_and_unapproved_prs(self):
        self._write_record("issue-30", "implementation", "scope-approved")
        self._patch(self.flows, "_pr_list_all", lambda root: [
            {"number": 55, "headRefName": "issue-30/implementation",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ])
        self._patch(self.closure_sweep, "find_violations",
                    lambda root, subjects=None, issue_states=None: [{"kind": "open-pr-on-closed-issue"}])
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(payload["hygiene"]["closure_sweep"],
                         [{"kind": "open-pr-on-closed-issue"}])
        self.assertEqual(len(payload["hygiene"]["unapproved_open_prs"]), 1)
        self.assertEqual(payload["hygiene"]["unapproved_open_prs"][0]["pr"], 55)

    def test_flows_plan_is_null_without_plan_block(self):
        self._write_record("issue-40", "product-discovery", "scope-proposed")
        self._patch(self.flows, "_issue_list_all", lambda root: [
            {"number": 40, "state": "OPEN", "body": "일반 이슈 본문, 계획 없음"},
        ])
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertIsNone(by_issue[40]["plan"])

    def test_flows_plan_parses_step_lines(self):
        self._write_record("issue-41", "product-discovery", "scope-proposed")
        body = (
            "본문 설명\n\n"
            "## 실행 계획\n"
            "- [x] step 1  product-discovery\n"
            "- [ ] step 2  architecture ‖ security-threat-model\n"
            "\n## 다른 섹션\n"
            "무시되어야 하는 줄\n"
        )
        self._patch(self.flows, "_issue_list_all", lambda root: [
            {"number": 41, "state": "OPEN", "body": body},
        ])
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[41]["plan"], [
            {"step": 1, "roles": ["product-discovery"], "done": True},
            {"step": 2, "roles": ["architecture", "security-threat-model"], "done": False},
        ])

    def test_flows_plan_only_issue_with_no_board_record_still_gets_entry(self):
        """requirement-4 gap this issue closes: an open issue with a plan
        block but zero merged role records still shows up in `flows[]`."""
        body = "## 실행 계획\n- [ ] step 1  product-discovery\n"
        self._patch(self.flows, "_issue_list_all", lambda root: [
            {"number": 50, "state": "OPEN", "body": body},
        ])
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertIn(50, by_issue)
        self.assertEqual(by_issue[50]["roles"], [])
        self.assertEqual(by_issue[50]["plan"],
                         [{"step": 1, "roles": ["product-discovery"], "done": False}])

    def test_flows_plan_skips_fenced_example_and_matches_variant_header(self):
        """issue #197 (issue-189 execution-observation finding 1 회귀): 실물
        이슈-189 본문은 펜스 안에 4-스텝 문법 견본(`## 실행 계획` 정확일치
        헤더)을 싣고, 실제 3-스텝 계획은 펜스 밖 변형 헤더
        (`## 실행 계획 (이 이슈 자체 — ...)`) 아래에 있다. 고쳐진 파서는 펜스
        안은 건너뛰고 변형 헤더를 매치해 실제 3-스텝을 낸다 — 펜스 안 4-스텝
        견본이 아니다. role 문자열의 em dash 설명 접미사는
        `_PLAN_STEP_RE`(불변)가 그대로 캡처하는 실물 결과이며 다듬지 않고
        그대로 단언한다(proposal Rationale, hunt pass 발견 사항)."""
        body = '## 배경\n\n스텝별 사람 확인(1단계 승인 / 2단계 머지)과 병렬 spawn 은 이미 동작한다. 없는 것은\n진행 형태를 사전에 합의해 **글로 남기는 자리**다. 지금 "다음은 누구"는 오케스트레이터의\n매 턴 판단으로만 존재하고 어디에도 기록되지 않는다.\n\n측정 (2026-08-02, 이 레포 `docs/issue-*/reports/`):\n\n```\n54개 이슈\n├─ 48개  역할 1개로 끝남           89%\n├─  5개  역할 2~3개 (최대 3)\n└─  0개  같은 역할이 두 번 돈 적 없음\n```\n\n즉 이 레포는 아직 멀티 스텝을 거의 안 써봤다. 계획 기능의 값어치는 반복 관리가 아니라\n**안 쓰던 병렬 스텝을 미리 짜두는 쪽**에 있다.\n\n## 요구사항\n\n1. 이슈를 열 때 사용자와 대화로 **실행 계획**(스텝 순서, 각 스텝의 룰북, 어느 스텝이\n   병렬인지)을 합의하고 이슈에 기록한다.\n2. 계획은 수정 가능하되 최소로. 수정 이력이 남을 것.\n3. **자동 진행 없음** — 스텝이 끝나면 사람 확인을 받고 다음 스텝을 spawn 한다.\n   이슈 #120의 "기계가 평가하는 라우팅 표 금지"는 그대로 유효하다.\n4. `repo-status-board` 에서 계획과 진척(현재 몇 번째 스텝, 각 스텝의 stage)을 본다.\n   이 이슈는 `flows --json` 쪽 데이터 계약까지만 책임진다 (§결정됨 D3).\n5. 계획이 소진되면 오케스트레이터가 보고하고, **사용자가 완료를 응답하면 이슈를 닫는다.**\n   자동 종결 아님 — `closure_sweep.py` 의 "탐지만, 종결은 사람 몫" 원칙 유지.\n\n## 이미 결정된 것 (대화에서 확정, 제안이 뒤집지 말 것)\n\n- **D1. 루프 문법을 만들지 않는다.** 위 측정대로 계획된 루프 사례가 0건이고, 가장\n  가까운 사례(이슈 #162: `coding.md` landed → `implementation.md` progressed,\n  "phase 2 follow-up: fix stale role names after PR #164")도 예정에 없던 사후\n  재작업이었다. 반복이 필요해지면 계획에 줄을 하나 더 붙인다 — #162가 실제로 그렇게\n  처리된 케이스다.\n- **D2. 종결은 사람이 한다.** 요구 5. 자동 종결 없음.\n- **D3. `repo-status-board` 레포 수정은 이 이슈 범위 밖.** 별도 이슈로 그쪽 레포에서\n  다룬다. 근거: 현행 계약이 브랜치(`issue-<n>/<role>`)와 보드 레코드(`docs/issue-<n>/`)를\n  레포 하나에 묶고 있어, 한 이슈로 두 레포를 다루면 레코드가 어디 남는지가 미정의다.\n  그 레포도 자체 보드다(`docs/specs/approvers.md` 보유).\n\n## 알려진 제약 (제안이 다룰 것)\n\n- `flows --json` 은 `gates/flows.py:flows_payload` → `spawn.board(root)` 위에 서 있고,\n  보드는 **머지된 레코드만** 본다. 이슈 생성 직후 ~ 첫 머지 전 구간은 flows 에 아예\n  나타나지 않는다. 계획은 생성 직후부터 보여야 하므로 **이것이 요구 4의 핵심 갭이다.**\n- stage 6개 값(`proposal`/`approval`/`implementation`/`verification`/`merge`/`close`)은\n  `gates/flows.py:_stage_for` 로 이미 나온다. 새로 만들 필요 없음.\n- `docs/specs/flows-schema.md` 는 `schema_version` 정수 하나로 관리되고 소비자 1개를\n  전제한다. 필드 추가 = 버전 범프. `repo-status-board` 레포가 이 스키마 문서의 **사본을\n  따로 들고 있다** — 동기화 필요 (실제 수정은 D3에 따라 별도 이슈).\n\n## 방향 (사용자 선호, 제안이 검토할 것)\n\n계획은 이슈 본문에 체크박스 목록으로. 새 파일·새 보드 레코드·새 게이트 없이,\n`gh issue edit` 로 수정하고 GitHub 편집 이력이 곧 요구 2의 감사 추적이 된다.\n병렬 스텝은 한 줄에 `‖` 로 묶는다.\n\n```markdown\n## 실행 계획\n- [ ] step 1  product-discovery\n- [ ] step 2  architecture ‖ security-threat-model\n- [ ] step 3  implementation\n- [ ] step 4  execution-observation ‖ conformance-review\n```\n\n## 실행 계획 (이 이슈 자체 — 요구 1의 첫 적용 사례)\n\n- [x] step 1  product-discovery — 요구사항·수용기준 확정, 위 갭에 대한 접근 결정\n- [x] step 2  implementation — 확정된 스펙대로 구현\n- [x] step 3  execution-observation — 실제 동작 확인\n\nstep 2 이후는 step 1 결과를 보고 조정한다 (요구 2의 "최소 수정" 대상).\n\n\n\n\n'
        self._patch(self.flows, "_issue_list_all", lambda root: [
            {"number": 189, "state": "OPEN", "body": body},
        ])
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[189]["plan"], [
            {"step": 1, "roles": [
                "product-discovery — 요구사항·수용기준 확정, 위 갭에 대한 접근 결정"
            ], "done": True},
            {"step": 2, "roles": [
                "implementation — 확정된 스펙대로 구현"
            ], "done": True},
            {"step": 3, "roles": [
                "execution-observation — 실제 동작 확인"
            ], "done": True},
        ])

    def test_flows_plan_fenced_only_body_has_no_real_plan(self):
        """보조 합성 케이스(주 증거는 위 실물 픽스처) — 펜스 안에만 계획
        헤더가 있고 펜스 밖 실제 헤더가 없으면 계획 블록 없음(`None`)."""
        self._write_record("issue-51", "product-discovery", "scope-proposed")
        body = (
            "본문 설명\n\n"
            "```markdown\n"
            "## 실행 계획\n"
            "- [ ] step 1  product-discovery\n"
            "```\n"
        )
        self._patch(self.flows, "_issue_list_all", lambda root: [
            {"number": 51, "state": "OPEN", "body": body},
        ])
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertIsNone(by_issue[51]["plan"])

    def test_flows_plan_two_unfenced_headers_first_wins(self):
        """보조 합성 케이스 — 펜스 밖 계획 헤더가 둘이면 첫 번째만 파싱된다
        (저작 오류, run.md 저작 규칙)."""
        body = (
            "## 실행 계획\n"
            "- [ ] step 1  product-discovery\n"
            "## 실행 계획 (두 번째, 무시되어야 함)\n"
            "- [ ] step 9  implementation\n"
        )
        self._patch(self.flows, "_issue_list_all", lambda root: [
            {"number": 52, "state": "OPEN", "body": body},
        ])
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[52]["plan"],
                         [{"step": 1, "roles": ["product-discovery"], "done": False}])


class SessionLastActivity(unittest.TestCase):
    """issue #172 FEEDBACK: `_session_last_activity` — tail-based session.log
    parse, never raises, `kind` covers tool_use/text/result."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self.td.cleanup)
        self.log = Path(self.td.name) / "wk.session.log"
        sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
        import flows
        self.flows = flows

    def test_none_when_log_missing(self):
        self.assertIsNone(self.flows._session_last_activity(self.log))

    def test_none_when_log_path_is_none(self):
        self.assertIsNone(self.flows._session_last_activity(None))

    def test_bash_tool_use_detail(self):
        self.log.write_text(
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Bash",
                 "input": {"command": "pytest test_spawn.py"}},
            ]}}) + "\n", encoding="utf-8")
        la = self.flows._session_last_activity(self.log)
        self.assertEqual(la["kind"], "tool_use")
        self.assertEqual(la["detail"], "pytest test_spawn.py 실행")

    def test_result_record_detail(self):
        self.log.write_text(
            json.dumps({"type": "result", "subtype": "success",
                       "result": "done"}) + "\n", encoding="utf-8")
        la = self.flows._session_last_activity(self.log)
        self.assertEqual(la["kind"], "result")
        self.assertEqual(la["detail"], "done")

    def test_last_of_several_lines_wins(self):
        lines = [
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "first"}]}},
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "second"}]}},
        ]
        self.log.write_text("\n".join(json.dumps(l) for l in lines) + "\n",
                            encoding="utf-8")
        la = self.flows._session_last_activity(self.log)
        self.assertEqual(la["detail"], "second")

    def test_malformed_tail_yields_none_not_error(self):
        self.log.write_text("not json at all\n{also not json\n", encoding="utf-8")
        self.assertIsNone(self.flows._session_last_activity(self.log))

    def test_unreadable_log_yields_none_not_error(self):
        self.log.write_text("{}\n", encoding="utf-8")
        self.log.chmod(0o000)
        self.addCleanup(self.log.chmod, 0o644)
        self.assertIsNone(self.flows._session_last_activity(self.log))


class WatchFollow(unittest.TestCase):
    """이슈 #180 ③: `--follow` 는 `_await_bounded` 시그니처·동작을 바꾸지
    않고 반복 호출하기만 한다 — 가장 최근에 소비한 이벤트 타입이
    session-end 일 때만 멈춘다(실패 신호: 안 멈추면 영원한 대기)."""

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        self.work = Path(self.td) / "wk"
        self.work.mkdir()
        self.events = spawn._events_path(self.work)
        self.offset = spawn._offset_path(self.work)
        self.log = Path(str(self.work) + ".session.log")
        self.log.write_text("")
        old_idx = spawn.WORKSPACE_INDEX
        spawn.WORKSPACE_INDEX = Path(self.td) / "workspaces.json"
        self.addCleanup(setattr, spawn, "WORKSPACE_INDEX", old_idx)
        spawn._workspace_index_put(180, "implementation", str(self.work), str(self.log))

    def test_follow_stops_only_at_session_end(self):
        from unittest import mock
        spawn._append_event(self.events, "progress", {"kind": "tool_use", "detail": "x"})
        spawn._append_event(self.events, "gate-refusal", "denied")
        spawn._append_event(self.events, "session-end", "progressed")
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path):
            calls.append(1)
            seen = spawn._read_offset(offset_path)
            lines = events_path.read_text(encoding="utf-8").splitlines()
            if seen < len(lines):
                spawn._write_offset(offset_path, seen + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 3, calls)  # progress, gate-refusal, session-end — 각 한 번

    def test_follow_ignores_stall_and_keeps_going(self):
        from unittest import mock
        spawn._append_event(self.events, "session-end", "progressed")
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path):
            calls.append(1)
            if len(calls) < 3:
                return 0  # stall 흉내: offset 은 그대로
            spawn._write_offset(offset_path, spawn._read_offset(offset_path) + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 3, calls)  # stall 2번을 지나 session-end 에서만 멈춘다

    def test_non_follow_mode_calls_await_bounded_exactly_once(self):
        from unittest import mock
        spawn._append_event(self.events, "progress", {"kind": "tool_use", "detail": "x"})
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path):
            calls.append(1)
            spawn._write_offset(offset_path, spawn._read_offset(offset_path) + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=False)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 1, calls)  # 기존 단일-이벤트 모드는 그대로

    def test_main_wires_follow_flag_through_to_watch(self):
        from unittest import mock
        old_argv = sys.argv
        sys.argv = ["spawn.py", "watch", "--issue", "180", "--follow"]
        captured = {}

        def fake_watch(issue, role, stall_timeout_min, follow=False):
            captured["follow"] = follow
            return 0

        try:
            with mock.patch.object(spawn, "_watch", fake_watch):
                rc = spawn.main()
        finally:
            sys.argv = old_argv
        self.assertEqual(rc, 0)
        self.assertTrue(captured["follow"])

    def test_main_defaults_follow_to_false(self):
        from unittest import mock
        old_argv = sys.argv
        sys.argv = ["spawn.py", "watch", "--issue", "180"]
        captured = {}

        def fake_watch(issue, role, stall_timeout_min, follow=False):
            captured["follow"] = follow
            return 0

        try:
            with mock.patch.object(spawn, "_watch", fake_watch):
                rc = spawn.main()
        finally:
            sys.argv = old_argv
        self.assertEqual(rc, 0)
        self.assertFalse(captured["follow"])


if __name__ == "__main__":
    unittest.main()
