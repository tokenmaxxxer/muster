#!/usr/bin/env python3
"""spawn.py 의 순수 함수들 — 세션을 띄우지 않고 검사한다."""
import argparse
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import unittest.mock
from pathlib import Path
from unittest import mock

import spawn
import shape_contracts


def _event(type_, **kw):
    """Build a stream-json event fixture and validate its shape against
    what spawn.py's parser reads (issue #335) before returning it."""
    event = {"type": type_, **kw}
    shape_contracts.assert_claude_stream_event_shape(event)
    return event


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

    def _core_checkout(self, td, plugin_names):
        # marketplace.json + plugin.json 을 갖춘 core 체크아웃 모양을
        # 흉내낸다 — 실제 tokenmaxxxer-core 와 같은 형태.
        root = Path(td)
        (root / ".claude-plugin").mkdir(parents=True)
        (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
            "name": "tokenmaxxxer-core",
            "plugins": [{"name": n, "source": f"./{n}"} for n in plugin_names],
        }))
        for n in plugin_names:
            d = root / n / ".claude-plugin"
            d.mkdir(parents=True, exist_ok=True)
            (d / "plugin.json").write_text(json.dumps({"name": n}))

    def test_core_plugin_dirs_pins_five_plugin_set(self):
        # 이슈#282: marketplace.json 이 5개(core, terse, freelunch, scout,
        # warrant)를 선언하면 core_plugin_dirs() 는 하드코드 튜플이 아니라
        # 그 5개 전부를 돌려줘야 한다 — warrant 가 빠지던 원래 버그의 회귀
        # 방지.
        names = ("core", "terse", "freelunch", "scout", "warrant")
        saved = {k: os.environ.pop(k, None)
                 for k in ("TOKENMAXXXER_CORE", "TOKENMAXXXER_RULEBOOKS")}
        try:
            with tempfile.TemporaryDirectory() as td:
                self._core_checkout(td, names)
                os.environ["TOKENMAXXXER_CORE"] = td
                dirs = spawn.core_plugin_dirs()
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    os.environ.pop(k, None)
        self.assertEqual({p.name for p in dirs}, set(names))

    def test_core_plugin_dirs_halts_on_missing_plugin_dir(self):
        # marketplace.json 이 선언한 플러그인의 디렉터리가 없으면
        # core_plugin_dirs() 는 조용히 건너뛰지 않고 그 이름을 대며 halt
        # 한다 — 공유 게이트 장치가 빠지는 걸 경고 없이 넘기지 않는다.
        saved = {k: os.environ.pop(k, None)
                 for k in ("TOKENMAXXXER_CORE", "TOKENMAXXXER_RULEBOOKS")}
        try:
            with tempfile.TemporaryDirectory() as td:
                self._core_checkout(td, ("core", "terse"))
                root = Path(td)
                mkt = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
                mkt["plugins"].append({"name": "warrant", "source": "./warrant"})
                (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(mkt))
                os.environ["TOKENMAXXXER_CORE"] = td
                with self.assertRaises(SystemExit) as cm:
                    spawn.core_plugin_dirs()
        finally:
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v
                else:
                    os.environ.pop(k, None)
        self.assertIn("warrant", str(cm.exception))

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


class MustMcpAllowEnv(unittest.TestCase):
    """MUSTER_MCP_ALLOW: #58/#65 와 같은 TOOL-PERMISSION 결함이 사용자가 직접
    붙인 MCP 서버에도 있다 — 서버는 연결되는데 도구 호출은 permissions.allow
    에 규칙이 없어 거부된다(실측: reasona issue-3, world-data MCP,
    permission_denials 에 mcp__world-data__korean_law__search_laws 가 남았다).
    #58/#65 와 달리 대상 도구명을 tokenmaxxxer 코드가 미리 알 수 없으므로
    (사용자마다 다른 이름의 개인 MCP 서버), 운영자가 스폰 시점에 콤마로
    나열한다."""

    def setUp(self):
        self._saved = os.environ.pop("MUSTER_MCP_ALLOW", None)

    def tearDown(self):
        os.environ.pop("MUSTER_MCP_ALLOW", None)
        if self._saved is not None:
            os.environ["MUSTER_MCP_ALLOW"] = self._saved

    def test_unset_env_leaves_allow_list_unchanged(self):
        out = spawn.role_settings("implementation")
        allow = out["permissions"]["allow"]
        self.assertEqual(allow, ["WebSearch", "WebFetch", "Read", "Grep", "Glob"])

    def test_single_pattern_is_merged_in(self):
        os.environ["MUSTER_MCP_ALLOW"] = "mcp__world-data__korean_law__*"
        out = spawn.role_settings("implementation")
        self.assertIn("mcp__world-data__korean_law__*", out["permissions"]["allow"])

    def test_multiple_patterns_with_whitespace_are_all_merged(self):
        os.environ["MUSTER_MCP_ALLOW"] = (
            " mcp__world-data__korean_law__* , mcp__world-data__finnhub__* ")
        out = spawn.role_settings("implementation")
        allow = out["permissions"]["allow"]
        self.assertIn("mcp__world-data__korean_law__*", allow)
        self.assertIn("mcp__world-data__finnhub__*", allow)

    def test_empty_segments_between_commas_are_ignored(self):
        os.environ["MUSTER_MCP_ALLOW"] = "mcp__world-data__korean_law__*,,  ,"
        out = spawn.role_settings("implementation")
        allow = out["permissions"]["allow"]
        self.assertIn("mcp__world-data__korean_law__*", allow)
        self.assertEqual(len(allow), 6)  # 5 고정 + 이 항목 하나뿐

    def test_non_mcp_prefixed_entries_are_dropped(self):
        """안전장치: 이 통로로 Write/Edit/Bash 처럼 board-gate/approval-gate
        가 지키는 도구를 열 수 없다 — 운영자 실수로도, 접두사가 mcp__ 가
        아니면 조용히 버린다."""
        os.environ["MUSTER_MCP_ALLOW"] = "Bash,Write,Edit,mcp__world-data__korean_law__*"
        out = spawn.role_settings("implementation")
        allow = out["permissions"]["allow"]
        self.assertIn("mcp__world-data__korean_law__*", allow)
        self.assertNotIn("Bash", allow)
        self.assertNotIn("Write", allow)
        self.assertNotIn("Edit", allow)

    def test_duplicate_within_env_var_is_not_duplicated_in_output(self):
        os.environ["MUSTER_MCP_ALLOW"] = ("mcp__world-data__korean_law__*,"
                                          "mcp__world-data__korean_law__*")
        out = spawn.role_settings("implementation")
        allow = out["permissions"]["allow"]
        self.assertEqual(allow.count("mcp__world-data__korean_law__*"), 1)

    def test_duplicate_against_role_declared_entry_is_not_duplicated(self):
        f = Path(spawn.ROOT) / "roles" / "implementation.json"
        original_text = f.read_text()
        spec = json.loads(original_text)
        spec["permissions"] = {"allow": ["mcp__world-data__korean_law__*"]}
        os.environ["MUSTER_MCP_ALLOW"] = "mcp__world-data__korean_law__*"
        try:
            f.write_text(json.dumps(spec))
            out = spawn.role_settings("implementation")
            allow = out["permissions"]["allow"]
            self.assertEqual(allow.count("mcp__world-data__korean_law__*"), 1)
        finally:
            f.write_text(original_text)

    def test_applies_to_every_role_not_just_one(self):
        os.environ["MUSTER_MCP_ALLOW"] = "mcp__world-data__korean_law__*"
        for role_file in (Path(spawn.ROOT) / "roles").glob("*.json"):
            role = role_file.stem
            out = spawn.role_settings(role)
            self.assertIn("mcp__world-data__korean_law__*",
                          out["permissions"]["allow"], role)


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


class WorkspaceSyncFailClosed(unittest.TestCase):
    """issue #221: fetch fail-closed + 재사용 브랜치 origin 트래킹 실 git 회귀.

    mock.patch.object 로 issue_workspace/checkout_issue_branch 를 대체하는
    기존 Ledger/IssueScopedPrompt/EventReporting 테스트들과 달리, 여기는 실
    git 저장소 두 개(origin 역할 + 그걸 clone 한 work_dir)로 함수 자체의
    동작을 검사한다.
    """

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    def test_fetch_halts_on_nonzero_returncode(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            self._init_repo(work)
            (work / "a.txt").write_text("x")
            self._git(work, "add", "a.txt")
            self._git(work, "commit", "-q", "-m", "init")
            # 존재하지 않는 origin 경로 — 실제 fetch 가 non-zero 로 실패한다.
            self._git(work, "remote", "add", "origin", "/no/such/path-xyz")
            with self.assertRaises(SystemExit):
                spawn._fetch_or_halt(str(work), "test-label")

    def test_fetch_halts_on_exit_zero_with_failed_to_store_stderr(self):
        # core issue-90 실측 재현: fetch 가 stderr 에 "failed to store"를
        # 남기고도 exit 0 으로 끝나는 케이스는 실 git 으로 결정론적으로
        # 재현할 수 없어(개별 ref 갱신 실패는 레이스/서버 상태 의존), fetch
        # 를 가로채는 실행 가능한 wrapper 로 그 정확한 관측 결과(stdout
        # 없음, stderr 에 그 문구, returncode 0)를 만든다 — 이 프로세스가
        # 실제로 실행되고 실제로 반환하는 실 subprocess 호출이라는 점에서
        # Python mock 과 다르다.
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            self._init_repo(work)
            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            git_wrapper = fake_bin / "git"
            git_wrapper.write_text(
                "#!/bin/sh\n"
                "for a in \"$@\"; do\n"
                "  if [ \"$a\" = fetch ]; then\n"
                "    echo 'failed to store: 100001' 1>&2\n"
                "    exit 0\n"
                "  fi\n"
                "done\n"
                "exit 1\n"
            )
            git_wrapper.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            try:
                with self.assertRaises(SystemExit):
                    spawn._fetch_or_halt(str(work), "test-label")
            finally:
                os.environ["PATH"] = old_path

    def test_set_head_attempted_even_when_fresh_clone_fetch_fails(self):
        # hunt 발견(composition-regression stance): _fetch_or_halt 가 halt
        # 하기 전에 after=(remote set-head) 를 먼저 시도하지 않으면, 신규
        # clone 의 첫 fetch 가 실패할 때마다 origin/HEAD 정정 기회를 영영
        # 잃는다 — 재사용 분기는 set-head 를 다시 안 부른다. fetch 만
        # 실패시키고 나머지(clone/remote/set-head)는 real git 에 위임하는
        # wrapper 로, halt 되고도 set-head 는 실제로 실행됐는지 검사한다.
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        with tempfile.TemporaryDirectory() as td:
            github = Path(td) / "github"
            src = Path(td) / "src"
            self._init_repo(github)
            (github / "a.txt").write_text("x")
            self._git(github, "add", "a.txt")
            self._git(github, "commit", "-q", "-m", "init")
            self._git(github, "branch", "-m", "main")

            r = subprocess.run(["git", "clone", "-q", str(github), str(src)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(src, "config", "user.email", "t@t.t")
            self._git(src, "config", "user.name", "t")
            self._git(src, "checkout", "-q", "-b", "feature-wip")

            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            git_wrapper = fake_bin / "git"
            git_wrapper.write_text(
                "#!/bin/sh\n"
                "for a in \"$@\"; do\n"
                "  if [ \"$a\" = fetch ]; then\n"
                "    echo 'failed to store: 100001' 1>&2\n"
                "    exit 0\n"
                "  fi\n"
                "done\n"
                f"exec {real_git} \"$@\"\n"
            )
            git_wrapper.chmod(0o755)

            work_base = Path(td) / "workbase"
            old_path = os.environ.get("PATH", "")
            old_base = os.environ.get("MUSTER_WORK_DIR")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            os.environ["MUSTER_WORK_DIR"] = str(work_base)
            try:
                with self.assertRaises(SystemExit):
                    spawn.issue_workspace(str(src), 999904, "implementation")
            finally:
                os.environ["PATH"] = old_path
                if old_base is None:
                    os.environ.pop("MUSTER_WORK_DIR", None)
                else:
                    os.environ["MUSTER_WORK_DIR"] = old_base

            work_dirs = list(work_base.glob("*-issue-999904-implementation"))
            self.assertEqual(len(work_dirs), 1, work_dirs)
            head = subprocess.run(
                ["git", "-C", str(work_dirs[0]), "symbolic-ref", "--short",
                 "refs/remotes/origin/HEAD"],
                capture_output=True, text=True).stdout.strip()
            self.assertEqual(head, "origin/main")

    def test_checkout_tracks_origin_only_branch(self):
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")
            base_branch = subprocess.run(
                ["git", "-C", str(origin), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()

            issue, role = 999901, "implementation"
            br = f"issue-{issue}/{role}"
            self._git(origin, "checkout", "-q", "-b", br)
            (origin / "b.txt").write_text("origin-only work")
            self._git(origin, "add", "b.txt")
            self._git(origin, "commit", "-q", "-m", "origin-only commit")
            self._git(origin, "checkout", "-q", base_branch)

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            # 사전 조건: 로컬엔 아직 br 브랜치가 없다.
            self.assertNotEqual(
                self._git(work, "rev-parse", "--verify", "-q", br).returncode, 0)

            result = spawn.checkout_issue_branch(str(work), issue, role)
            self.assertEqual(result, br)
            log = self._git(work, "log", "--oneline", br).stdout
            self.assertIn("origin-only commit", log)

    def test_checkout_preserves_existing_local_branch_with_unpushed_commit(self):
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")
            base_branch = subprocess.run(
                ["git", "-C", str(origin), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999902, "implementation"
            br = f"issue-{issue}/{role}"
            self._git(work, "checkout", "-q", "-b", br)
            (work / "c.txt").write_text("local wip")
            self._git(work, "add", "c.txt")
            self._git(work, "commit", "-q", "-m", "local unpushed commit")
            self._git(work, "checkout", "-q", base_branch)
            before = self._git(work, "rev-parse", br).stdout.strip()

            result = spawn.checkout_issue_branch(str(work), issue, role)
            self.assertEqual(result, br)
            after = self._git(work, "rev-parse", br).stdout.strip()
            self.assertEqual(before, after)
            log = self._git(work, "log", "--oneline", br).stdout
            self.assertIn("local unpushed commit", log)


class WorkspaceExcludesHomeDotfiles(unittest.TestCase):
    """이슈 #289 H1: 샌드박스가 홈 dotfile 을 워크스페이스 루트에 오버레이해
    `git status`에 untracked 로 잡힌다 — `.muster-cache/`와 같은 방식으로
    `.git/info/exclude`에 등록해 `git add -A`가 이들을 못 줍게 한다."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    def test_fresh_workspace_excludes_dotfile_set(self):
        with tempfile.TemporaryDirectory() as td:
            github = Path(td) / "github.git"
            self._git(github.parent, "init", "-q", "--bare", str(github))
            src = Path(td) / "src"
            r = subprocess.run(["git", "clone", "-q", str(github), str(src)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(src, "config", "user.email", "t@t.t")
            self._git(src, "config", "user.name", "t")
            (src / "a.txt").write_text("x")
            self._git(src, "add", "a.txt")
            self._git(src, "commit", "-q", "-m", "init")
            self._git(src, "push", "-q", "origin", "HEAD:main")

            work_base = Path(td) / "workbase"
            old_base = os.environ.get("MUSTER_WORK_DIR")
            os.environ["MUSTER_WORK_DIR"] = str(work_base)
            try:
                work = spawn.issue_workspace(str(src), 999905, "implementation")
            finally:
                if old_base is None:
                    os.environ.pop("MUSTER_WORK_DIR", None)
                else:
                    os.environ["MUSTER_WORK_DIR"] = old_base

            exclude = (Path(work) / ".git" / "info" / "exclude").read_text()
            for dotfile in (".bashrc", ".bash_profile", ".profile",
                            ".zshrc", ".zprofile", ".gitconfig",
                            ".gitmodules", ".mcp.json", ".claude",
                            ".idea", ".vscode", ".ripgreprc"):
                self.assertIn(dotfile, exclude, exclude)


class OrchestratorGitToken(unittest.TestCase):
    """실측: reasona issue-3 검증 중, GH_TOKEN 없이 `python3 spawn.py` 를
    그냥 돌리면 재사용 워크스페이스 fetch 가 인증 실패로 막힌다.
    `issue_workspace()` 가 작업 클론에 심는 credential.helper 는 그 helper
    를 실행하는 프로세스의 $GH_TOKEN 을 읽는데, `spawn_cmd()` 는 역할
    세션의 env 에 그 값을 명시 주입하면서 오케스트레이터 자신의 프로세스에는
    아무도 넣어주지 않았다. `_fetch_or_halt()`/`ensure_pushed()` 의 git
    호출에 `_git_env()` 를 통해 주입되는지, fake git wrapper 로 실제
    프로세스 env 를 검사해 확인한다."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    def setUp(self):
        spawn._GH_TOKEN_CACHE = None
        self._saved_agent = os.environ.pop("MUSTER_AGENT_GH_TOKEN", None)

    def tearDown(self):
        spawn._GH_TOKEN_CACHE = None
        os.environ.pop("MUSTER_AGENT_GH_TOKEN", None)
        if self._saved_agent is not None:
            os.environ["MUSTER_AGENT_GH_TOKEN"] = self._saved_agent

    def _token_recording_git_wrapper(self, fake_bin, record_path):
        """`$GH_TOKEN` 을 record_path 에 적고 real git 에 위임하는 wrapper —
        어느 값이 실제로 이 프로세스에 도달했는지 실 subprocess 실행으로
        검사한다(mock 이 아니라)."""
        real_git = shutil.which("git")
        wrapper = fake_bin / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            f"echo \"${{GH_TOKEN}}\" > {record_path}\n"
            f"exec {real_git} \"$@\"\n"
        )
        wrapper.chmod(0o755)

    def test_fetch_or_halt_injects_muster_agent_gh_token(self):
        os.environ["MUSTER_AGENT_GH_TOKEN"] = "test-token-abc"
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("x")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "init")
            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            record = Path(td) / "seen-token.txt"
            self._token_recording_git_wrapper(fake_bin, record)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            try:
                spawn._fetch_or_halt(str(work), "test-label")
            finally:
                os.environ["PATH"] = old_path
            self.assertEqual(record.read_text().strip(), "test-token-abc")

    def test_ensure_pushed_push_call_injects_token_too(self):
        os.environ["MUSTER_AGENT_GH_TOKEN"] = "test-token-xyz"
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("x")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "init")
            self._git(origin, "branch", "-m", "main")
            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999903, "implementation"
            br = f"issue-{issue}/{role}"
            self._git(work, "checkout", "-q", "-b", br)
            (work / "c.txt").write_text("wip")
            self._git(work, "add", "c.txt")
            self._git(work, "commit", "-q", "-m", "wip")

            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            record = Path(td) / "seen-token.txt"
            self._token_recording_git_wrapper(fake_bin, record)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            gh_stub = fake_bin / "gh"
            gh_stub.write_text("#!/bin/sh\nexit 1\n")  # gh pr list/create no-op
            gh_stub.chmod(0o755)
            try:
                spawn.ensure_pushed(str(work), issue, role)
            finally:
                os.environ["PATH"] = old_path
            self.assertEqual(record.read_text().strip(), "test-token-xyz")

    def test_token_resolution_shells_out_to_gh_at_most_once(self):
        """캐시 검증: gh auth token 을 두 번 부르지 않는다 — 한 스폰 안에서
        _fetch_or_halt 가 여러 번 불려도(issue_workspace + checkout_issue_branch)."""
        with tempfile.TemporaryDirectory() as td:
            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            call_count_file = Path(td) / "gh-calls.txt"
            gh_wrapper = fake_bin / "gh"
            gh_wrapper.write_text(
                "#!/bin/sh\n"
                f"echo x >> {call_count_file}\n"
                "echo fake-shelled-out-token\n"
            )
            gh_wrapper.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            try:
                first = spawn._resolve_gh_token()
                second = spawn._resolve_gh_token()
            finally:
                os.environ["PATH"] = old_path
            self.assertEqual(first, "fake-shelled-out-token")
            self.assertEqual(second, "fake-shelled-out-token")
            self.assertEqual(len(call_count_file.read_text().splitlines()), 1)

    def test_unresolvable_token_returns_none_not_empty_override(self):
        """토큰을 못 구하면 _git_env() 는 None 이어야 한다 — 빈 문자열로
        덮어쓰면 subprocess.run 이 부모 env 를 안 물려받아, 사용자의 다른
        자격증명 경로(ssh-agent, osxkeychain)까지 막힌다."""
        with tempfile.TemporaryDirectory() as td:
            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            gh_wrapper = fake_bin / "gh"
            gh_wrapper.write_text("#!/bin/sh\nexit 1\n")  # gh auth token 실패
            gh_wrapper.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            try:
                self.assertIsNone(spawn._git_env())
            finally:
                os.environ["PATH"] = old_path

    def test_muster_agent_gh_token_wins_over_gh_auth_token(self):
        os.environ["MUSTER_AGENT_GH_TOKEN"] = "explicit-agent-token"
        with tempfile.TemporaryDirectory() as td:
            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            gh_wrapper = fake_bin / "gh"
            # gh 가 불리면 다른 토큰을 낸다 — 실제로 불렸다면 테스트가 잡는다.
            gh_wrapper.write_text("#!/bin/sh\necho should-not-be-used\n")
            gh_wrapper.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            try:
                token = spawn._resolve_gh_token()
            finally:
                os.environ["PATH"] = old_path
            self.assertEqual(token, "explicit-agent-token")


class EnsurePushedResult(unittest.TestCase):
    """이슈 #301 B2: `ensure_pushed()` 가 `None` 대신 구조화된
    `{"status": ..., "reason": ...}` 를 리턴하고, `_spawn_one()` 이 push
    거부를 `silent-failure` 와 구분되는 `push-rejected` 로 승격하는지 —
    이슈가 명시한 세 시나리오(거부됨/미푸시 다른 사유/진짜 무無)가 실제로
    구분되는지 실 git 리포로 검증한다."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    def _clone_with_commit(self, td, issue, role):
        # bare origin: 로컬 file:// transport 라도 push 가 항상 pack
        # 프로토콜(receive-pack)을 타야 pre-receive hook 이 실제로 걸린다 —
        # non-bare 로는 hardlink 최적화 경로로 hook 을 건너뛸 수 있다.
        seed = Path(td) / "seed"
        origin = Path(td) / "origin.git"
        work = Path(td) / "work"
        self._init_repo(seed)
        (seed / "a.txt").write_text("x")
        self._git(seed, "add", "a.txt")
        self._git(seed, "commit", "-q", "-m", "init")
        self._git(seed, "branch", "-m", "main")
        r = subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(origin)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self._git(work, "config", "user.email", "t@t.t")
        self._git(work, "config", "user.name", "t")
        br = f"issue-{issue}/{role}"
        self._git(work, "checkout", "-q", "-b", br)
        (work / "c.txt").write_text("wip")
        self._git(work, "add", "c.txt")
        self._git(work, "commit", "-q", "-m", "wip")
        return origin, work, br

    def test_push_rejected_by_remote_is_named_and_distinct(self):
        """(a) 원격이 push 를 거부한 경우 — pre-receive hook 으로 실제
        거부를 재현한다. `status` 가 `push-rejected` 이고 `reason` 이
        비어있지 않아야 하며, `_spawn_one` 의 outcome 이 `silent-failure`
        가 아니라 `push-rejected` 로 승격돼야 한다."""
        with tempfile.TemporaryDirectory() as td:
            issue, role = 999910, "implementation"
            origin, work, br = self._clone_with_commit(td, issue, role)
            hooks = origin / "hooks"
            hooks.mkdir(exist_ok=True)
            hook = hooks / "pre-receive"
            hook.write_text(
                "#!/bin/sh\n"
                "echo 'refusing to allow an OAuth App to create or update "
                "workflow without workflow scope' >&2\n"
                "exit 1\n"
            )
            hook.chmod(0o755)
            with mock.patch.object(spawn, "_git_env", return_value=None):
                result = spawn.ensure_pushed(str(work), issue, role)
            self.assertEqual(result["status"], "push-rejected")
            self.assertTrue(result["reason"])
            self.assertIn("workflow", result["reason"])

            outcome = "silent-failure"
            uncommitted = []
            if outcome == "silent-failure" and uncommitted:
                outcome = "uncommitted-work"
            elif outcome == "silent-failure" and result and result["status"] == "push-rejected":
                outcome = "push-rejected"
            self.assertEqual(outcome, "push-rejected")

    def test_nothing_to_push_stays_silent_failure(self):
        """(c) 진짜 아무것도 안 만든 세션 — 원격에 앞선 커밋도, 브랜치
        자체도 없으면 `nothing-to-push` 이고, `_spawn_one` 의 outcome 은
        오늘과 같이 `silent-failure` 로 남는다."""
        with tempfile.TemporaryDirectory() as td:
            issue, role = 999911, "implementation"
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("x")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "init")
            self._git(origin, "branch", "-m", "main")
            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            # 이 이슈/역할용 브랜치가 아예 없다 — 세션이 아무것도 안 만든 상태.
            with mock.patch.object(spawn, "_git_env", return_value=None):
                result = spawn.ensure_pushed(str(work), issue, role)
            self.assertEqual(result, {"status": "nothing-to-push", "reason": None})

            outcome = "silent-failure"
            uncommitted = []
            if outcome == "silent-failure" and uncommitted:
                outcome = "uncommitted-work"
            elif outcome == "silent-failure" and result and result["status"] == "push-rejected":
                outcome = "push-rejected"
            self.assertEqual(outcome, "silent-failure")

    def test_commits_ahead_but_dirty_tree_prefers_uncommitted_work(self):
        """(b) 세션 종료 시 커밋은 로컬에 있지만(원격엔 아직) 트리도
        더러운 경우 — push 자체가 거부됐더라도 더 즉각적인 문제인
        `uncommitted-work` 가 우선한다는 기존 순서를 그대로 지킨다."""
        with tempfile.TemporaryDirectory() as td:
            issue, role = 999912, "implementation"
            origin, work, br = self._clone_with_commit(td, issue, role)
            hooks = origin / "hooks"
            hooks.mkdir(exist_ok=True)
            hook = hooks / "pre-receive"
            hook.write_text("#!/bin/sh\necho rejected >&2\nexit 1\n")
            hook.chmod(0o755)
            with mock.patch.object(spawn, "_git_env", return_value=None):
                result = spawn.ensure_pushed(str(work), issue, role)
            self.assertEqual(result["status"], "push-rejected")

            outcome = "silent-failure"
            uncommitted = ["M dirty.txt"]  # 세션이 더러운 트리를 남겼다
            if outcome == "silent-failure" and uncommitted:
                outcome = "uncommitted-work"
            elif outcome == "silent-failure" and result and result["status"] == "push-rejected":
                outcome = "push-rejected"
            self.assertEqual(outcome, "uncommitted-work")


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

    @staticmethod
    def _tool_use_line(tool_use_id, name):
        # 이슈 #246 결함 3: 실제 스트림에서 tool_result 는 언제나 그 도구를
        # 요청한 assistant 의 tool_use 블록(같은 id) 뒤에 온다 — 건별
        # 상관관계 픽스처가 그 순서를 재현한다.
        event = _event("assistant", message={"content": [
            {"type": "tool_use", "id": tool_use_id, "name": name, "input": {}}]})
        return json.dumps(event)

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

    def test_denials_with_no_correlating_tool_result_are_unclassified(self):
        # 층을 확정할 tool_result 줄이 없어도(스트림 누락 등) 최종 result 의
        # permission_denials 가 실려 있으면 거부 자체는 놓치지 않는다 — 다만
        # 예전처럼 layer-1 로 위장하지 않고 별도 라벨(unclassified-refusal)로
        # 남는다(제안서 5번). 옛 코드는 이 케이스에서 gate-refusal 을 냈다.
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(), result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "unclassified-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_gate_hook_denial_is_gate_refusal_with_gate_name(self):
        # 이슈 #232 층 1 실물 샘플: PreToolUse hook 이 감싼 gate-lib.sh 의
        # gate_deny 메시지(`<게이트>: refused — <사유>`) — 게이트 이름과
        # 사유가 이미 이 텍스트 안에 있다. 옛 코드는 detail 에
        # `str(denials)[:200]` 만 실어 게이트 이름을 못 냈다.
        text = ("PreToolUse:Bash hook error: "
                "[/Users/jk/.claude/plugins/marketplaces/tokenmaxxxer-core/core/hooks/board-gate.sh] "
                "board-gate: refused — 보드에 없는 파일을 쓰려 했다")
        tool_use = self._tool_use_line("t1", "Write")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        refusals = [e for e in events if e["type"] == "gate-refusal"]
        self.assertEqual(len(refusals), 1, events)
        self.assertEqual(refusals[0]["detail"]["gate"], "board-gate", events)
        self.assertFalse([e for e in events if e["type"] == "unclassified-refusal"], events)

    def test_harness_permission_denial_is_not_labeled_gate_refusal(self):
        # 이슈 #232 실측 사건 재현: 순수 읽기 명령이 하네스 권한(2층)에
        # 막혔는데 옛 코드는 이걸 gate-refusal 로 잘못 보고해 오케스트레이터가
        # "board-gate 가 오탐한다"고 사용자에게 근거 없이 전달했다. 다섯
        # 샘플 모두 이슈 본문에서 그대로 가져온 실물 문자열이다.
        samples = (
            "Permission to use Bash has been denied",
            "This Bash command contains multiple operations. The "
            "following part requires approval: git show <sha>:<path>",
            "This command requires approval",
            "Contains shell syntax (string) that cannot be statically analyzed",
            "Contains simple_expansion",
        )
        for text in samples:
            with self.subTest(text=text):
                tool_use = self._tool_use_line("t1", "Bash")
                tool_result = json.dumps({"type": "user", "message": {"content": [
                    {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
                     "content": text}]}})
                result_line = json.dumps({"type": "result", "is_error": False,
                                          "permission_denials": [{"tool_name": "Bash"}]})
                events = self._run(tempfile.mkdtemp(),
                                   tool_use + "\n" + tool_result + "\n" + result_line + "\n")
                self.assertTrue([e for e in events if e["type"] == "harness-refusal"], events)
                self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_sandbox_denial_is_not_labeled_gate_refusal(self):
        # 이슈 #232 층 3 실물 샘플 — 옛 코드는 이것도 gate-refusal 로 뭉갰다.
        samples = (
            "mkdir: /tmp/foo: Operation not permitted",
            "Claude requested permissions to write to /some/path, but "
            "you haven't granted it yet",
        )
        for text in samples:
            with self.subTest(text=text):
                tool_use = self._tool_use_line("t1", "Write")
                tool_result = json.dumps({"type": "user", "message": {"content": [
                    {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
                     "content": text}]}})
                result_line = json.dumps({"type": "result", "is_error": False,
                                          "permission_denials": [{"tool_name": "Write"}]})
                events = self._run(tempfile.mkdtemp(),
                                   tool_use + "\n" + tool_result + "\n" + result_line + "\n")
                self.assertTrue([e for e in events if e["type"] == "sandbox-refusal"], events)
                self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_git_lock_masquerade_is_classified_as_sandbox_refusal(self):
        # 이슈 #289 H2: 샌드박스가 거부한 .git/config 쓰기가 EEXIST 로 변환돼
        # git 이 마치 진짜 잠금 경합인 것처럼 보고한다 — 예전엔 분류기가
        # 이 문구를 놓쳐 unclassified-refusal 로 떨어졌다.
        text = "error: cannot lock config file .git/config: File exists"
        tool_use = self._tool_use_line("t1", "Bash")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "sandbox-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "unclassified-refusal"], events)

    def test_non_error_tool_result_matching_refusal_text_fires_nothing(self):
        # issue-129 의 구조적 판정(is_error 우선, 텍스트 매치만으로 판정하지
        # 않기) 회귀 방지를 층 분류에도 적용한다 — 성공한(is_error 없는)
        # tool_result 가 거부 문구를 우연히 담아도 아무 이벤트가 없어야 한다.
        for text in ("Permission to use Bash has been denied",
                     "mkdir: /tmp/foo: Operation not permitted",
                     "PreToolUse:Bash hook error: [board-gate.sh] "
                     "board-gate: refused — x"):
            with self.subTest(text=text):
                tool_result = json.dumps({"type": "user", "message": {"content": [
                    {"type": "tool_result", "is_error": False, "content": text}]}})
                events = self._run(tempfile.mkdtemp(), tool_result + "\n")
                self.assertFalse(
                    [e for e in events if e["type"] in
                     ("gate-refusal", "harness-refusal", "sandbox-refusal",
                      "unclassified-refusal")], events)

    def test_layer2_denial_quoting_gate_marker_is_harness_refusal_not_gate(self):
        # 이슈 #235 요구사항 4(i) / execution-observation Finding 1(b): 층 2
        # 하네스 거부가 명령을 원문 인용하는데, 그 인용된 명령에 게이트
        # 마커(`PreToolUse:<tool> hook error: [<path>]`)가 들어 있으면 옛
        # 코드는 이걸 층 1(gate-refusal)로 오분류했다. 마커가 텍스트 시작이
        # 아니라 인용 안에 있으니, 시작-앵커된 정규식은 여기 안 걸려야 한다.
        text = ("This Bash command contains multiple operations. The "
                "following part requires approval: PreToolUse:Bash hook "
                "error: [/plugins/tokenmaxxxer-core/core/hooks/some-gate.sh] "
                "some-gate: refused — 원문 인용된 명령")
        tool_use = self._tool_use_line("t1", "Bash")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "harness-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_zero_denials_session_with_gate_marker_in_error_output_fires_nothing(self):
        # 이슈 #235 요구사항 4(ii) / execution-observation Finding 1(a): 세션의
        # 최종 result 줄 permission_denials 가 비어 있으면, 실패한 도구 호출의
        # 출력에 게이트 마커가 있어도 거부 이벤트가 전혀 나면 안 된다 — is_error
        # 는 "실패"지 "거부"가 아니라는 요구사항 1의 안전장치.
        text = ("PreToolUse:Write hook error: [/plugins/tokenmaxxxer-core/"
                "core/hooks/some-gate.sh] some-gate: refused — 무관한 실패")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": []})
        events = self._run(tempfile.mkdtemp(),
                           tool_result + "\n" + result_line + "\n")
        self.assertFalse(
            [e for e in events if e["type"] in
             ("gate-refusal", "harness-refusal", "sandbox-refusal",
              "unclassified-refusal")], events)

    def test_spurious_candidate_tool_name_mismatch_does_not_suppress_real_denial_fallback(self):
        # 이슈 #246 결함 3 (범위 확장, 발주자 코멘트): 이슈 #235 요구사항
        # 4(iii)/execution-observation Finding 1(c)가 원래 이름으로 주장했던
        # 비억제 속성의 교체 픽스처 — 옛 픽스처는 앵커된 `_GATE_HOOK_RE` 때문에
        # 아예 분류조차 안 되는 텍스트를 썼다(제안서 결함 3 실측). 이 픽스처는
        # 비-앵커 층 3 패턴("Operation not permitted")에 걸려 실제로 분류되는
        # 스푸리어스 후보를 쓴다 — 그 후보의 tool_use_id 로 상관되는 tool_name
        # ("Read")이 세션의 permission_denials 항목("Write")과 다르므로, 옛
        # 세션 전역 `refusals_seen` 불리언이었다면 이 후보 하나만으로 그
        # unclassified-refusal 폴백이 영구히 억제됐을 것이다. 이슈 #246 결함
        # 3의 건별(tool_name 단위) 상관관계는 그 억제를 없앤다: 스푸리어스
        # 후보 자신은 fire 하지 않지만(진짜 층 라벨을 참칭하지 않음), 상관 안
        # 되는 진짜 거부("Write")의 폴백은 여전히 fire 한다.
        spurious = ("Some unrelated tool output happened to mention: mkdir: "
                    "/tmp/foo: Operation not permitted")
        tool_use = self._tool_use_line("t1", "Read")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": spurious}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "unclassified-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "sandbox-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_spurious_candidate_tool_name_match_correlates_and_fires_as_real_layer(self):
        # 위 픽스처의 컴패니언(제안서 결함 3): 같은 스푸리어스-패턴 텍스트라도
        # 후보의 tool_name 이 실제로 permission_denials 항목과 일치하면 Counter
        # 상관은 그걸 확정하고 진짜 층 이벤트(sandbox-refusal)로 fire 해야
        # 한다 — tool_name 매치가 무조건 통과가 아니라 실제로 판별함을
        # 확인한다.
        text = ("Some unrelated tool output happened to mention: mkdir: "
                "/tmp/foo: Operation not permitted")
        tool_use = self._tool_use_line("t1", "Write")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        refusals = [e for e in events if e["type"] == "sandbox-refusal"]
        self.assertEqual(len(refusals), 1, events)
        self.assertFalse([e for e in events if e["type"] == "unclassified-refusal"], events)

    def test_record_fields_gate_denial_reports_hook_stem_not_role_name(self):
        # 이슈 #235 요구사항 4(iv) / execution-observation Finding 2 실물 샘플:
        # gate_deny 의 첫 토큰이 게이트가 아니라 역할 이름
        # ("execution-observation")이었다 — hook 경로 stem
        # ("record-fields-gate")이 정답인데 옛 코드는 토큰 쪽을 골랐다.
        text = ("PreToolUse:Write hook error: "
                "[/plugins/tokenmaxxxer-core/core/hooks/record-fields-gate.sh]: "
                "execution-observation: refused — record is missing required "
                "section(s): 코드 리뷰")
        tool_use = self._tool_use_line("t1", "Write")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        refusals = [e for e in events if e["type"] == "gate-refusal"]
        self.assertEqual(len(refusals), 1, events)
        self.assertEqual(refusals[0]["detail"]["gate"], "record-fields-gate", events)

    def test_eof_with_pending_candidate_and_no_result_line_flushes_unverified(self):
        # 이슈 #246 결함 1 (S1/S3): 세션이 터미널 result 줄 없이 끝난다 —
        # 크래시/kill/truncation(S1)과 그 줄 자체가 malformed JSON(S3)은
        # `_spawn_one` 관점에서 같은 관찰(루프가 result 줄 없이 EOF)로
        # 수렴한다. 이미 층 분류된 후보를 메모리에서 잃지 않고
        # unverified-refusal 로 flush 한다 — 확정 라벨(gate-refusal)을
        # 참칭하지 않는다.
        text = ("PreToolUse:Write hook error: [/plugins/tokenmaxxxer-core/"
                "core/hooks/some-gate.sh] some-gate: refused — 잘린 세션")
        tool_use = self._tool_use_line("t1", "Write")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        events = self._run(tempfile.mkdtemp(), tool_use + "\n" + tool_result + "\n")
        self.assertEqual(len([e for e in events if e["type"] == "unverified-refusal"]), 1,
                         events)
        self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_result_line_with_untrustworthy_permission_denials_shape_flushes_unverified(self):
        # 이슈 #246 결함 1 (S2): permission_denials 가 absent/None/truthy
        # non-list 면 형태를 신뢰할 수 없다 — `or []`가 이 셋을 "확정 0건"과
        # 구분 없이 뭉갰던 게 원래 결함이었다. 셋 다 같은 unverified-refusal
        # 경로로 간다; 확정된 빈 리스트([])는 별도로
        # test_zero_denials_session_with_gate_marker_in_error_output_fires_nothing
        # 가 이미 "아무 것도 안 남" 을 고정한다.
        text = ("PreToolUse:Write hook error: [/plugins/tokenmaxxxer-core/"
                "core/hooks/some-gate.sh] some-gate: refused — 형태 불량")
        cases = {
            "absent": {"type": "result", "is_error": False},
            "none": {"type": "result", "is_error": False, "permission_denials": None},
            "string": {"type": "result", "is_error": False,
                      "permission_denials": "oops"},
        }
        for label, result_obj in cases.items():
            with self.subTest(shape=label):
                tool_use = self._tool_use_line("t1", "Write")
                tool_result = json.dumps({"type": "user", "message": {"content": [
                    {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
                     "content": text}]}})
                result_line = json.dumps(result_obj)
                events = self._run(tempfile.mkdtemp(),
                                   tool_use + "\n" + tool_result + "\n" + result_line + "\n")
                self.assertEqual(
                    len([e for e in events if e["type"] == "unverified-refusal"]), 1, events)
                self.assertFalse([e for e in events if e["type"] == "gate-refusal"], events)

    def test_two_distinct_same_layer_denials_produce_two_distinct_events(self):
        # 이슈 #246 결함 2: 층 전체를 가리는 옛 dedup 키(예: ("harness",))는
        # 첫 번째 텍스트만 남기고 두 번째(진짜 거부일 수 있는) detail 을
        # 잃었다 — 정규화된 텍스트를 키에 포함해 서로 다른 두 사유가 둘 다
        # 살아남는다.
        text1 = "Permission to use Bash has been denied"
        text2 = "This command requires approval"
        tool_use1 = self._tool_use_line("t1", "Bash")
        tool_result1 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text1}]}})
        tool_use2 = self._tool_use_line("t2", "Bash")
        tool_result2 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t2",
             "content": text2}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"},
                                                          {"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use1 + "\n" + tool_result1 + "\n" +
                           tool_use2 + "\n" + tool_result2 + "\n" + result_line + "\n")
        harness = [e for e in events if e["type"] == "harness-refusal"]
        self.assertEqual(len(harness), 2, events)
        self.assertEqual({h["detail"] for h in harness}, {text1, text2}, events)
        self.assertFalse([e for e in events if e["type"] == "unclassified-refusal"], events)

    def test_two_identical_same_layer_denials_still_collapse_to_one(self):
        # 회귀 방지: 정확히 같은 detail 은 여전히 한 번만 — 이슈
        # #235/spawn.py:2619-2622 의 "같은 detail 은 한 번" 의도가 텍스트를
        # 키에 포함시킨 뒤에도 유지된다.
        text = "Permission to use Bash has been denied"
        tool_use1 = self._tool_use_line("t1", "Bash")
        tool_result1 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        tool_use2 = self._tool_use_line("t2", "Bash")
        tool_result2 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t2",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use1 + "\n" + tool_result1 + "\n" +
                           tool_use2 + "\n" + tool_result2 + "\n" + result_line + "\n")
        self.assertEqual(len([e for e in events if e["type"] == "harness-refusal"]), 1, events)

    def test_two_hook_paths_sharing_filename_stem_are_not_collapsed(self):
        # 이슈 #246 결함 2: `Path(...).stem` 만으로 걸면 서로 다른 디렉터리의
        # 동일 파일명 hook(둘 다 "some-gate")이 충돌했다 — 키는 이제 hook 의
        # 전체 경로를 쓴다. `detail["gate"]` 표시 필드는 여전히 stem.
        text1 = ("PreToolUse:Write hook error: [/plugins/a/some-gate.sh] "
                "some-gate: refused — 사유 A")
        text2 = ("PreToolUse:Write hook error: [/plugins/b/some-gate.sh] "
                "some-gate: refused — 사유 B")
        tool_use1 = self._tool_use_line("t1", "Write")
        tool_result1 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text1}]}})
        tool_use2 = self._tool_use_line("t2", "Write")
        tool_result2 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t2",
             "content": text2}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"},
                                                          {"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use1 + "\n" + tool_result1 + "\n" +
                           tool_use2 + "\n" + tool_result2 + "\n" + result_line + "\n")
        refusals = [e for e in events if e["type"] == "gate-refusal"]
        self.assertEqual(len(refusals), 2, events)
        self.assertEqual({r["detail"]["gate"] for r in refusals}, {"some-gate"}, events)
        self.assertEqual({r["detail"]["reason"] for r in refusals}, {"사유 A", "사유 B"}, events)

    def test_whitespace_variant_same_layer_denials_still_collapse_to_one(self):
        # 이슈 #246 dedup 키 텍스트 정규화: multi-block tool_result 가 넣는
        # 내부 개행(`_tool_result_text`의 "\n".join)과 우연한 공백 차이는
        # 사유가 실질적으로 같으면 같은 키로 뭉쳐야 한다. denials 를 일부러
        # 2건 실어 둔다 — 정규화가 안 됐다면 두 후보가 서로 다른 키로 갈려
        # 둘 다(2건) fire 하고 남는 denial 이 없다; 정규화가 됐다면 후보가
        # 1개뿐이라 1건만 fire 하고 나머지 denial 1건이 unclassified-refusal
        # 로 남는다 — 그 잔여가 정규화가 실제로 일어났다는 증거다.
        text1 = "mkdir: /tmp/foo: Operation not permitted"
        tool_use1 = self._tool_use_line("t1", "Write")
        tool_result1 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text1}]}})
        tool_use2 = self._tool_use_line("t2", "Write")
        tool_result2 = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t2", "content": [
                {"type": "text", "text": "mkdir: /tmp/foo:"},
                {"type": "text", "text": "Operation not permitted"}]}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Write"},
                                                          {"tool_name": "Write"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use1 + "\n" + tool_result1 + "\n" +
                           tool_use2 + "\n" + tool_result2 + "\n" + result_line + "\n")
        self.assertEqual(len([e for e in events if e["type"] == "sandbox-refusal"]), 1, events)
        self.assertTrue([e for e in events if e["type"] == "unclassified-refusal"], events)

    def test_denial_entry_missing_tool_name_still_fires_unclassified_fallback(self):
        # 헌트 finding 2: permission_denials 항목이 dict 가 아니거나
        # tool_name 이 없으면 Counter 에서 그냥 빠진다 — 그 항목을 leftover
        # 판정에도 안 넣으면, 매치될 수 없는 denial 자체가 흔적 없이
        # 사라진다(이슈 #246 결함 1 이 없애려던 "0건 = 무해"를 다른 문으로
        # 재도입). 후보의 tool_name 이 그 이상한 모양과 매치되지 않아 real
        # layer 로는 안 뜨더라도, unclassified-refusal 폴백은 반드시 떠야
        # 한다.
        text = "Permission to use Bash has been denied"
        tool_use = self._tool_use_line("t1", "Bash")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"other_field": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" + result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "unclassified-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "harness-refusal"], events)

    def test_unresolved_tool_use_id_with_well_shaped_denials_degrades_to_unclassified(self):
        # 헌트 finding 3 (커버리지 공백 메움): 후보의 tool_use_id 가 못
        # 풀렸어도(예: assistant 의 tool_use 줄 자체가 유실됐다면) denials 가
        # 정상 모양이면 폴백으로 정확히 떨어져야 한다 — 확정 라벨을
        # 참칭하지 않되, 조용히 사라지지도 않는다. assistant tool_use 줄을
        # 아예 안 보내 tool_use_id 를 의도적으로 못 풀리게 한다.
        text = "Permission to use Bash has been denied"
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "unknown-id",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_result + "\n" + result_line + "\n")
        self.assertTrue([e for e in events if e["type"] == "unclassified-refusal"], events)
        self.assertFalse([e for e in events if e["type"] == "harness-refusal"], events)

    def test_repeated_result_line_does_not_double_flush(self):
        # 헌트 finding 5: 옛 코드는 refusals_seen 이 세션 전체에 걸쳐 남아
        # 두 번째 result 줄에 대해 flush 가 no-op 이었다 — result 가 "언제나
        # 스트림의 마지막 줄"이라는 가정은 문서화만 됐을 뿐 강제되지 않는다
        # (docs/issue-235/reports/execution-observation/research-evidence.md:160-164).
        # result_seen 가드가 두 번째 result 줄에서 재-flush 를 막는다.
        text = "Permission to use Bash has been denied"
        tool_use = self._tool_use_line("t1", "Bash")
        tool_result = json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": text}]}})
        result_line = json.dumps({"type": "result", "is_error": False,
                                  "permission_denials": [{"tool_name": "Bash"}]})
        events = self._run(tempfile.mkdtemp(),
                           tool_use + "\n" + tool_result + "\n" +
                           result_line + "\n" + result_line + "\n")
        self.assertEqual(len([e for e in events if e["type"] == "harness-refusal"]), 1, events)

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

    def test_refusal_parsing_still_works_alongside_progress(self):
        # 거부 판별과 같은 obj 를 재사용하도록 바꾼 뒤에도 기존 동작이
        # 그대로인지 — result 라인은 여전히 result 로만 처리된다. 여기엔
        # 층을 확정할 tool_result 줄이 없으니 unclassified-refusal 이 된다
        # (이슈 #232) — 예전엔 이 케이스가 gate-refusal 이었다.
        events = self._run(tempfile.mkdtemp(), [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Write", "input": {"file_path": "x.py"}},
            ]}},
            {"type": "result", "is_error": False,
             "permission_denials": [{"tool_name": "Write"}]},
        ])
        self.assertEqual(len([e for e in events if e["type"] == "progress"]), 1, events)
        self.assertEqual(len([e for e in events if e["type"] == "unclassified-refusal"]), 1, events)


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

    def test_clean_issue_scopes_sweep_to_that_issue_only(self):
        # #288 N1: clean --issue N accepted the flag but swept every
        # workspace regardless. Pin: with issue 51 and 52 workspaces both
        # eligible for removal, `--issue 51` removes only 51's and leaves
        # 52's untouched, and 52 isn't even reported.
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            ws51 = wb / "myrepo-issue-51-coding"
            ws52 = wb / "myrepo-issue-52-coding"
            self._make_clean_repo(ws51, Path(td) / "remote-a.git")
            self._make_clean_repo(ws52, Path(td) / "remote-b.git")

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({}))

            old_roster = spawn.ROSTER
            old_argv = sys.argv
            old_environ = dict(os.environ)
            spawn.ROSTER = roster_path
            os.environ["MUSTER_WORK_DIR"] = str(wb)
            sys.argv = ["spawn.py", "clean", "--issue", "51"]
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
            self.assertFalse(ws51.exists())
            self.assertTrue(ws52.exists())
            self.assertNotIn(ws52.name, out)

    def test_clean_issue_with_no_matching_workspace_removes_nothing(self):
        # #288 N1 acceptance: clean --issue 424242 against workspaces that
        # exist for other issues must report zero removed/kept, not sweep
        # everything.
        with tempfile.TemporaryDirectory() as td:
            wb = Path(td) / "work"
            wb.mkdir()
            ws51 = wb / "myrepo-issue-51-coding"
            self._make_clean_repo(ws51, Path(td) / "remote-a.git")

            roster_path = Path(td) / "runs" / "active.json"
            roster_path.parent.mkdir(parents=True)
            roster_path.write_text(json.dumps({}))

            old_roster = spawn.ROSTER
            old_argv = sys.argv
            old_environ = dict(os.environ)
            spawn.ROSTER = roster_path
            os.environ["MUSTER_WORK_DIR"] = str(wb)
            sys.argv = ["spawn.py", "clean", "--issue", "424242"]
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
            self.assertTrue(ws51.exists())
            self.assertIn("지움 0, 남김 0", out)


class Watchdog(unittest.TestCase):
    """이슈 #90 phase-2: observe-only 이상 신호 네 가지."""

    def _entry(self, log, work=None, ts=None, before_head=None, pid=None):
        return {"log": str(log), "work": work, "ts": ts or int(time.time()),
                "before_head": before_head, "pid": pid}

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

    def test_roster_watchdog_returns_zero_for_clean_non_empty_roster(self):
        with tempfile.TemporaryDirectory() as td:
            roster_path = Path(td) / "active.json"
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            roster_path.write_text(json.dumps({
                "k": self._entry(log, pid=os.getpid())}))
            old_roster = spawn.ROSTER
            old_state = spawn.WATCHDOG_STATE
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                result = spawn.roster_watchdog()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
            self.assertEqual(result, 0)

    def test_roster_watchdog_returns_anomaly_count_for_stalled_entry(self):
        with tempfile.TemporaryDirectory() as td:
            roster_path = Path(td) / "active.json"
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            stale = time.time() - (spawn.WATCHDOG_SILENCE_MIN + 5) * 60
            os.utime(log, (stale, stale))
            roster_path.write_text(json.dumps({
                "k": self._entry(log, pid=os.getpid())}))
            old_roster = spawn.ROSTER
            old_state = spawn.WATCHDOG_STATE
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                result = spawn.roster_watchdog()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
            self.assertEqual(result, 1)


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

    def test_prior_generations_session_end_does_not_mask_new_generations_crash(self):
        # 이슈 #247: self-trigger 재귀가 만드는 다중-세대 이벤트 시퀀스
        # (한 워크스페이스의 events.jsonl 에 세대 여러 개가 이어 쌓인다)
        # 에서도, 이전 세대의 session-end 가 **자기 session-start 뒤,
        # 다음 세대의 session-start 보다 앞**에 제대로 찍혀 있으면
        # (spawn.py `_spawn_one()` 이 이제 강제하는 순서) 마지막
        # session-start(새 세대)의 진짜 죽음이 가려지지 않는다.
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
                {"type": "session-end", "detail": "uncommitted-work"},
                {"type": "respawn-attempt", "detail": {"session_start_ts": 1, "attempt": 1}},
                {"type": "session-start", "detail": {"pid": 222, "ts": 2}},
            ])
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=None,
                                          alive_fn=lambda pid: pid != 222),
                "crashed")

    def test_misordered_prior_session_end_would_mask_new_generations_crash(self):
        # 이 테스트는 회귀를 지키려는 위험을 그대로 문서화한다(hunt finding
        # 1) — session_end_verdict() 자신은 이 이슈에서 안 바뀐다(제안서
        # 스코프 밖). 만약 어떤 호출부가 이전 세대의 session-end 를 다음
        # 세대의 session-start **뒤에** 남기면(제안서 원문 그대로
        # self-trigger 를 session-end 보다 먼저 불렀을 때 실제로 벌어졌던
        # 순서), session_end_verdict() 는 마지막 session-start 뒤에 있는
        # 아무 session-end 나 매치로 보고 새 세대가 진짜 죽어도 `crashed`
        # 대신 `normal` 을 낸다 — `_spawn_one()` 이 이제 자기 session-end
        # 를 self-trigger 보다 먼저 남기는 이유가 바로 이 시퀀스를 절대
        # 만들지 않기 위해서다.
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
                {"type": "respawn-attempt", "detail": {"session_start_ts": 1, "attempt": 1}},
                {"type": "session-start", "detail": {"pid": 222, "ts": 2}},
                {"type": "session-end", "detail": "uncommitted-work"},
            ])
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=None,
                                          alive_fn=lambda pid: pid != 222),
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


class SelfTriggeredRespawn(unittest.TestCase):
    """이슈 #247: 정상 종료(crashed 아님)했지만 미커밋 작업을 남긴 헤드리스
    세션이, 워치독 틱을 기다리지 않고 `_spawn_one()` 자기 프로세스 안에서
    같은 claim/attempt-cap/cap-comment 헬퍼(`_respawn_or_cap()`)를 직접
    부른다(`_self_trigger_respawn()`)."""

    def test_fires_on_uncommitted_work(self):
        called = []
        orig_respawn = spawn._respawn_or_cap
        orig_state = spawn._respawn_state_load
        spawn._respawn_or_cap = lambda *a, **k: called.append(a)
        spawn._respawn_state_load = lambda: {"seen": True}
        try:
            spawn._self_trigger_respawn("uncommitted-work", "issue-247/coding",
                                        "w", 247, "implementation", "l", 123)
        finally:
            spawn._respawn_or_cap = orig_respawn
            spawn._respawn_state_load = orig_state
        self.assertEqual(len(called), 1)
        (key, work, issue, role, log, ts, state, trigger) = called[0]
        self.assertEqual(key, "issue-247/coding")
        self.assertEqual((work, issue, role, log, ts), ("w", 247, "implementation", "l", 123))
        self.assertEqual(state, {"seen": True})
        self.assertEqual(trigger, "self-triggered-abandoned")

    def test_fires_on_failed_no_commit(self):
        called = []
        orig_respawn = spawn._respawn_or_cap
        spawn._respawn_or_cap = lambda *a, **k: called.append(a)
        try:
            spawn._self_trigger_respawn("failed-no-commit", "issue-247/coding",
                                        "w", 247, "implementation", "l", 123)
        finally:
            spawn._respawn_or_cap = orig_respawn
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0][-1], "self-triggered-abandoned")

    def test_does_not_fire_on_legitimate_stops(self):
        # refused/waiting-on-human 은 사람이 봐야 할 정당한 정지고,
        # 맨 silent-failure 는 정말 할 일이 없던 정당한 무변화다 — 이
        # 결함의 모양(방치된-미커밋-작업)이 아니므로 재스폰하지 않는다
        # (프로포절의 두 번째 기각안).
        for outcome in ("refused", "waiting-on-human", "silent-failure",
                        "progressed", "errored", "progressed-dirty-tree"):
            called = []
            orig_respawn = spawn._respawn_or_cap
            spawn._respawn_or_cap = lambda *a, **k: called.append(1)
            try:
                spawn._self_trigger_respawn(outcome, "issue-247/coding", "w",
                                            247, "implementation", "l", 123)
            finally:
                spawn._respawn_or_cap = orig_respawn
            self.assertEqual(called, [], outcome)

    def test_respects_cap_and_posts_comment_with_trigger_label(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            state = {"issue-247/coding": {"attempts": spawn.RESPAWN_MAX_ATTEMPTS}}
            called = []
            orig_spawn = spawn._spawn_one
            orig_comment = spawn._post_crash_comment
            spawn._spawn_one = lambda *a, **k: called.append(("spawn", a))
            spawn._post_crash_comment = lambda *a, **k: called.append(("comment", a))
            try:
                spawn._respawn_or_cap("issue-247/coding", str(work), 247,
                                      "implementation", "l", 123, state,
                                      "self-triggered-abandoned")
            finally:
                spawn._spawn_one = orig_spawn
                spawn._post_crash_comment = orig_comment
            self.assertEqual(len(called), 1)
            self.assertEqual(called[0][0], "comment")
            self.assertEqual(called[0][1][-1], "self-triggered-abandoned")

    def test_under_cap_claims_and_respawns(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            Path(str(work) + ".task.txt").write_text("원래 맡길 일")
            state = {}
            called = []
            orig = spawn._spawn_one
            spawn._spawn_one = lambda *a, **k: called.append((a, k))
            try:
                spawn._respawn_or_cap("issue-247/coding", str(work), 247,
                                      "implementation", "l", 456, state,
                                      "self-triggered-abandoned")
            finally:
                spawn._spawn_one = orig
            self.assertEqual(len(called), 1)
            self.assertEqual(state["issue-247/coding"]["attempts"], 1)
            events = Path(str(work) + ".events.jsonl").read_text()
            self.assertIn("respawn-attempt", events)

    def test_self_trigger_and_watchdog_do_not_double_respawn(self):
        # 이 세션 자신의 self-trigger 와, 같은 워크스페이스를 보는 동시
        # 워치독 틱(`_auto_respawn_check` 이 재구성한 같은 session_start_ts)
        # 이 동시에 `_respawn_or_cap` 에 도달해도, claim 하나만 통과해야
        # 한다 — 트리거 라벨이 다를 뿐 같은 원자적 claim 파일을 공유한다
        # (프로포절: "reuses the existing atomic claim's race protection —
        # no new concurrency mechanism").
        import threading
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            Path(str(work) + ".task.txt").write_text("원래 맡길 일")
            called = []
            lock = threading.Lock()
            orig = spawn._spawn_one

            def fake_spawn(*a, **k):
                with lock:
                    called.append(1)
            spawn._spawn_one = fake_spawn
            try:
                threads = [
                    threading.Thread(
                        target=spawn._respawn_or_cap,
                        args=("issue-247/coding", str(work), 247, "implementation",
                              "l", 1, {}, "self-triggered-abandoned")),
                    threading.Thread(
                        target=spawn._respawn_or_cap,
                        args=("issue-247/coding", str(work), 247, "implementation",
                              "l", 1, {}, "watchdog-observed-crashed")),
                ]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
            finally:
                spawn._spawn_one = orig
            self.assertEqual(len(called), 1)

    def _prep_repo(self, td):
        work = Path(td) / "w"
        work.mkdir()
        run = lambda *a: subprocess.run(a, cwd=str(work), capture_output=True,
                                        text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (work / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")
        return work

    def test_spawn_one_call_site_fires_after_own_session_end_event(self):
        # 이슈 #247 통합 테스트: 실제 _spawn_one() bounded/issue 꼬리를(fork
        # 만 모킹해서) 끝까지 돌려, 세션이 미커밋 파일을 남기고 정상
        # 종료하면 self-trigger 가 불릴 때 이 세션 **자신의** session-end
        # 가 이미 남아 있는지 확인한다.
        #
        # 제안서의 원래 문구는 "before the bounded child's terminal
        # session-end event append/exit" 였지만, 구현 중 어써샬-브로큰
        # 헌트가 그 문구 그대로 구현하면(self-trigger 먼저) 깨지는 걸
        # 찾았다: self-trigger 가 상한 안이면 `_respawn_or_cap()` 이
        # `_spawn_one(..., bounded=True)` 를 재귀 호출하고, 그 재귀 호출은
        # 새 세대가 자기 session-start 를 남길 때까지 이 프로세스를
        # `_await_bounded()` 안에서 블록한다 — session-end 를 그 뒤로
        # 미루면 이 세션 자신의 session-end 가 새 세대의 session-start
        # **뒤에** events.jsonl 에 찍혀, `session_end_verdict()` 가 새
        # 세대의 진짜 죽음을 이 세션의(남의) session-end 로 가리고
        # 영원히 `normal` 로 오판한다. session-end 를 먼저 남기면 순서가
        # 뒤집혀 그 오판이 구조적으로 불가능해진다 — 이 테스트는 그
        # 순서(session-end 가 self-trigger 보다 먼저)를 고정한다.
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            (work / "left-behind.txt").write_text("uncommitted")
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            triggered = []

            def fake_trigger(outcome, roster_key, w, issue, role, log, ts):
                events_text = Path(str(w) + ".events.jsonl").read_text()
                self.assertIn("session-end", events_text)
                triggered.append(outcome)

            saved_fds = [os.dup(0), os.dup(1), os.dup(2)]
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "plugin_dirs", lambda *a, **k: []), \
                     mock.patch.object(spawn, "checkout_version", lambda *a, **k: "v0"), \
                     mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                     mock.patch.object(spawn, "core_version", lambda: "v0"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed", lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register", lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_remove", lambda *a, **k: None), \
                     mock.patch.object(spawn, "ledger_write", lambda *a, **k: None), \
                     mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
                     mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
                     mock.patch.object(spawn, "_self_trigger_respawn", fake_trigger), \
                     mock.patch.object(os, "fork", return_value=0), \
                     mock.patch.object(os, "setsid", lambda: None), \
                     mock.patch.object(os, "_exit", lambda *a: None):
                    spawn._spawn_one(str(work), "implementation", "task\n",
                                     unattended=True, issue=247, bounded=True)
            finally:
                for fd, real in zip((0, 1, 2), saved_fds):
                    os.dup2(real, fd)
                    os.close(real)
                spawn.ROSTER = old_roster
            self.assertEqual(triggered, ["uncommitted-work"])


class SpawnOneIssueRoleClaim(unittest.TestCase):
    """이슈 #223: 재스폰 경로(`AutoRespawnClaim`)에만 있던 (issue,role) 클레임을
    주 스폰 경로(`_spawn_one()` 자체)에도 넣는다."""

    def _prep_repo(self, td, name="work"):
        work = Path(td) / name
        work.mkdir()
        run = lambda *a: subprocess.run(a, cwd=str(work), capture_output=True,
                                        text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (work / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")
        return work

    def test_concurrent_spawn_one_calls_let_exactly_one_through(self):
        # 이슈 #223 증상 재현: 같은 (issue, role)로 main() 이 부르는 몸통
        # (_spawn_one) 을 두 번(스레드 두 개로) 겹쳐 부르면, 클레임이 없던
        # 시절엔 둘 다 checkout_issue_branch 까지 통과해 같은 워크스페이스에
        # 두 세션을 띄운다 — 클레임이 있으면 정확히 하나만 통과해야 한다.
        import threading
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            checkout_calls = []
            checkout_lock = threading.Lock()

            def fake_checkout(cwd, issue, role):
                with checkout_lock:
                    checkout_calls.append(1)
                return "b"

            results = []
            results_lock = threading.Lock()

            def run_spawn():
                rc = spawn._spawn_one(str(work), "implementation", "task\n",
                                      unattended=True, issue=223)
                with results_lock:
                    results.append(rc)

            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            try:
                # plugin_dirs/checkout_version/core_plugin_dirs/core_version
                # 는 실제 룰북/코어 클론을 건드린다 — 이 테스트가 검증하려는
                # 건 클레임 하나뿐이므로, 그 뒤(클레임 통과 후) 경로는 나머지
                # 기존 테스트들과 같은 수준으로 모킹해 무관한 네트워크/환경
                # 의존을 없앤다.
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch", fake_checkout), \
                     mock.patch.object(spawn, "plugin_dirs", lambda *a, **k: []), \
                     mock.patch.object(spawn, "checkout_version", lambda *a, **k: "v0"), \
                     mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                     mock.patch.object(spawn, "core_version", lambda: "v0"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda *a, **k: None):
                    threads = [threading.Thread(target=run_spawn) for _ in range(2)]
                    for t in threads:
                        t.start()
                    for t in threads:
                        t.join()
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                spawn.ROSTER = old_roster

            self.assertEqual(len(checkout_calls), 1, checkout_calls)
            self.assertEqual(len(results), 2)

    def test_stale_claim_from_dead_pid_is_cleaned_and_retried(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            dead = subprocess.Popen(["true"])
            dead.wait()
            claim_path = Path(str(work) + ".spawn-claim")
            claim_path.write_text(json.dumps({"pid": dead.pid, "ts": 1}))
            rejection = spawn._acquire_spawn_claim(str(work), 223, "implementation")
            self.assertIsNone(rejection)
            self.assertEqual(json.loads(claim_path.read_text())["pid"], os.getpid())

    def test_rejection_names_the_live_claimant_pid_and_ts(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            claim_path = Path(str(work) + ".spawn-claim")
            claim_path.write_text(json.dumps({"pid": os.getpid(), "ts": 555}))
            rejection = spawn._acquire_spawn_claim(str(work), 223, "implementation")
            self.assertIsNotNone(rejection)
            self.assertIn(str(os.getpid()), rejection)
            self.assertIn("555", rejection)

    def test_fork_child_rewrites_claim_pid_before_setsid(self):
        # 이슈 #223 착수 프롬프트가 지목한 함정: bounded 분기는 fork 후 부모가
        # 곧 리턴/종료하므로, 클레임에 fork-전 pid 를 남겨 두면 생존검사가
        # stale 로 오판한다. 자식 분기(child_pid == 0)에서 pid 재기록 헬퍼가
        # os.setsid() 보다 먼저 불려야 한다 — os.fork/os.setsid/os._exit 를
        # 모킹해 실제 fork 없이 자식 분기만 강제하고, dup2 로 바뀌는 표준
        # 입출력 fd 는 테스트 프로세스 자신의 것이므로 호출 전후로 저장·복원한다.
        import threading
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster

            order = []
            orig_rewrite = spawn._rewrite_spawn_claim_pid

            def spy_rewrite(w):
                order.append("rewrite")
                return orig_rewrite(w)

            saved_fds = [os.dup(0), os.dup(1), os.dup(2)]
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "plugin_dirs", lambda *a, **k: []), \
                     mock.patch.object(spawn, "checkout_version", lambda *a, **k: "v0"), \
                     mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                     mock.patch.object(spawn, "core_version", lambda: "v0"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed", lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register", lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_remove", lambda *a, **k: None), \
                     mock.patch.object(spawn, "ledger_write", lambda *a, **k: None), \
                     mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
                     mock.patch.object(spawn, "_rewrite_spawn_claim_pid", spy_rewrite), \
                     mock.patch.object(os, "fork", return_value=0), \
                     mock.patch.object(os, "setsid",
                                       lambda: order.append("setsid")), \
                     mock.patch.object(os, "_exit", lambda *a: None):
                    spawn._spawn_one(str(work), "implementation", "task\n",
                                     unattended=True, issue=224, bounded=True)
            finally:
                for fd, real in zip((0, 1, 2), saved_fds):
                    os.dup2(real, fd)
                    os.close(real)
                spawn.ROSTER = old_roster

            self.assertEqual(order, ["rewrite", "setsid"])
            claim = json.loads(Path(str(work) + ".spawn-claim").read_text())
            self.assertEqual(claim["pid"], os.getpid())


class EnsurePushedStrandedComment(unittest.TestCase):
    """이슈 #326: `ensure_pushed()`의 두 침묵 dead-end(호스트 push 실패,
    PR 생성 실패)가 이제 이슈에 코멘트를 남기는지, 그리고 멱등한지."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    def _make_work_with_commit(self, td, issue, role):
        origin = Path(td) / "origin"
        work = Path(td) / "work"
        self._init_repo(origin)
        (origin / "a.txt").write_text("x")
        self._git(origin, "add", "a.txt")
        self._git(origin, "commit", "-q", "-m", "init")
        self._git(origin, "branch", "-m", "main")
        r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self._git(work, "config", "user.email", "t@t.t")
        self._git(work, "config", "user.name", "t")
        br = f"issue-{issue}/{role}"
        self._git(work, "checkout", "-q", "-b", br)
        (work / "c.txt").write_text("wip")
        self._git(work, "add", "c.txt")
        self._git(work, "commit", "-q", "-m", "wip")
        return work, br

    def test_ensure_pushed_posts_comment_on_push_failure(self):
        issue, role = 999910, "implementation"
        with tempfile.TemporaryDirectory() as td:
            work, br = self._make_work_with_commit(td, issue, role)
            orig_slug = spawn._repo_slug
            orig_comments = spawn._issue_comments
            orig_run = spawn.subprocess.run
            spawn._repo_slug = lambda root: "acme/repo"
            spawn._issue_comments = lambda root, n: []
            calls = []

            def fake_run(cmd, *a, **k):
                calls.append(cmd)
                if cmd[:2] == ["git", "-C"] and "push" in cmd:
                    return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="push rejected")
                if cmd[:2] == ["git", "-C"]:
                    return orig_run(cmd, *a, **k)
                if cmd[0] == "gh":
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
                return orig_run(cmd, *a, **k)

            spawn.subprocess.run = fake_run
            try:
                spawn.ensure_pushed(str(work), issue, role)
            finally:
                spawn._repo_slug = orig_slug
                spawn._issue_comments = orig_comments
                spawn.subprocess.run = orig_run

            comment_calls = [c for c in calls if c[0] == "gh" and any("comments" in x for x in c)]
            self.assertEqual(len(comment_calls), 1)
            body = comment_calls[0][comment_calls[0].index("-f") + 1]
            self.assertIn(br, body)
            self.assertIn("push-failed", body)

    def test_ensure_pushed_posts_comment_on_pr_create_failure(self):
        issue, role = 999911, "implementation"
        with tempfile.TemporaryDirectory() as td:
            work, br = self._make_work_with_commit(td, issue, role)
            orig_slug = spawn._repo_slug
            orig_comments = spawn._issue_comments
            orig_run = spawn.subprocess.run
            spawn._repo_slug = lambda root: "acme/repo"
            spawn._issue_comments = lambda root, n: []
            calls = []

            def fake_run(cmd, *a, **k):
                calls.append(cmd)
                if cmd[:2] == ["git", "-C"]:
                    return orig_run(cmd, *a, **k)
                if cmd[0] == "gh" and cmd[1:3] == ["pr", "list"]:
                    return subprocess.CompletedProcess(cmd, 0, stdout="0", stderr="")
                if cmd[0] == "gh" and cmd[1:3] == ["pr", "create"]:
                    return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="pr create rejected")
                if cmd[0] == "gh":
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
                return orig_run(cmd, *a, **k)

            spawn.subprocess.run = fake_run
            try:
                spawn.ensure_pushed(str(work), issue, role)
            finally:
                spawn._repo_slug = orig_slug
                spawn._issue_comments = orig_comments
                spawn.subprocess.run = orig_run

            comment_calls = [c for c in calls if c[0] == "gh" and any("comments" in x for x in c)]
            self.assertEqual(len(comment_calls), 1)
            body = comment_calls[0][comment_calls[0].index("-f") + 1]
            self.assertIn(br, body)
            self.assertIn("pr-create-failed", body)

    def test_ensure_pushed_stranded_comment_is_idempotent(self):
        issue, role = 999912, "implementation"
        with tempfile.TemporaryDirectory() as td:
            work, br = self._make_work_with_commit(td, issue, role)
            orig_slug = spawn._repo_slug
            orig_comments = spawn._issue_comments
            orig_run = spawn.subprocess.run
            spawn._repo_slug = lambda root: "acme/repo"
            marker = spawn._STRANDED_PUSH_COMMENT_MARKER.format(key=f"{br}:push-failed")
            spawn._issue_comments = lambda root, n: [{"login": "bot", "body": marker}]
            calls = []

            def fake_run(cmd, *a, **k):
                calls.append(cmd)
                if cmd[:2] == ["git", "-C"] and "push" in cmd:
                    return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="push rejected")
                if cmd[:2] == ["git", "-C"]:
                    return orig_run(cmd, *a, **k)
                if cmd[0] == "gh":
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
                return orig_run(cmd, *a, **k)

            spawn.subprocess.run = fake_run
            try:
                spawn.ensure_pushed(str(work), issue, role)
                spawn.ensure_pushed(str(work), issue, role)
            finally:
                spawn._repo_slug = orig_slug
                spawn._issue_comments = orig_comments
                spawn.subprocess.run = orig_run

            comment_calls = [c for c in calls if c[0] == "gh" and any("comments" in x for x in c)]
            self.assertEqual(len(comment_calls), 0)


class PostCrashComment(unittest.TestCase):
    """이슈 #132: 상한-코멘트 멱등성 — 마커 문자열이 이미 있으면 재포스팅 안 함."""

    def test_skips_when_marker_already_present(self):
        marker = spawn._CRASH_COMMENT_MARKER.format(key="issue-132/coding",
                                                     cap=spawn.RESPAWN_MAX_ATTEMPTS)
        orig_comments = spawn._issue_comments
        spawn._issue_comments = lambda root, n: ([{"login": "bot", "body": marker}], True)
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
        spawn._issue_comments = lambda root, n: ([], True)
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

    def test_post_failure_is_logged_not_silent(self):
        """issue #287 S7: 코멘트 POST 자체가 실패하면(returncode!=0)
        stderr 에 경고가 남아야 한다 — "사람 개입 필요" 알림이 조용히
        사라지면 안 된다."""
        orig_comments = spawn._issue_comments
        orig_slug = spawn._repo_slug
        spawn._issue_comments = lambda root, n: ([], True)
        spawn._repo_slug = lambda root: "acme/repo"
        orig_run = subprocess.run

        def fake_run(cmd, *a, **k):
            return orig_run(["false"], capture_output=True, text=True)
        subprocess.run = fake_run
        try:
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                spawn._post_crash_comment(Path("."), 132, "issue-132/coding", "w", "l")
            self.assertIn("게시 실패", buf.getvalue())
        finally:
            spawn._issue_comments = orig_comments
            spawn._repo_slug = orig_slug
            subprocess.run = orig_run


class PostStallComment(unittest.TestCase):
    """이슈 #325: stalled 판정이 최초 1회만 이슈 코멘트로 남는다."""

    def test_skips_when_marker_already_present(self):
        marker = spawn._STALL_COMMENT_MARKER.format(key="issue-325/coding")
        orig_comments = spawn._issue_comments
        spawn._issue_comments = lambda root, n: [{"login": "bot", "body": marker}]
        calls = []
        orig_run = subprocess.run
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        try:
            spawn._post_stall_comment(Path("."), 325, "issue-325/coding", "w", "l")
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
            spawn._post_stall_comment(Path("."), 325, "issue-325/coding", "w", "l")
        finally:
            spawn._issue_comments = orig_comments
            spawn._repo_slug = orig_slug
            subprocess.run = orig_run
        self.assertEqual(len(calls), 1)
        self.assertIn("gh", calls[0])

    def test_auto_respawn_check_posts_stall_comment_once_across_two_ticks(self):
        """워치독 두 번 연속 틱에서도 코멘트 호출은 정확히 한 번(멱등)."""
        orig_verdict = spawn.session_end_verdict
        orig_post = spawn._post_stall_comment
        spawn.session_end_verdict = lambda work, log_path: "stalled"
        calls = []
        posted_markers = []

        def fake_post(root, issue, key, work, log):
            marker = spawn._STALL_COMMENT_MARKER.format(key=key)
            if marker in posted_markers:
                return
            posted_markers.append(marker)
            calls.append((issue, key))

        spawn._post_stall_comment = fake_post
        try:
            entry = {"work": "w", "issue": 325, "role": "coding", "log": "l"}
            spawn._auto_respawn_check("issue-325/coding", entry, {})
            spawn._auto_respawn_check("issue-325/coding", entry, {})
        finally:
            spawn.session_end_verdict = orig_verdict
            spawn._post_stall_comment = orig_post
        self.assertEqual(len(calls), 1)


class IssueComments(unittest.TestCase):
    """이슈 #224: `--paginate --slurp`로 30개 코멘트 상한을 넘긴다 —
    페이지 리스트를 평탄화해 기존과 같은 dict 리스트를 돌려줘야 한다."""

    def test_flattens_multi_page_slurp_response(self):
        orig_slug = spawn._repo_slug
        orig_run = subprocess.run
        spawn._repo_slug = lambda root: "acme/repo"
        page1 = [{"user": {"login": "a"}, "body": "one"}]
        page2 = [{"user": {"login": "b"}, "body": "two"}]
        shape_contracts.assert_gh_paginate_slurp_shape([page1, page2])
        calls = []

        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps([page1, page2]), stderr="")

        spawn.subprocess.run = fake_run
        try:
            out, ok = spawn._issue_comments(Path("."), 999)
        finally:
            spawn._repo_slug = orig_slug
            spawn.subprocess.run = orig_run
        self.assertTrue(ok)
        self.assertEqual(out, [{"login": "a", "body": "one"},
                               {"login": "b", "body": "two"}])
        self.assertIn("--paginate", calls[0])
        self.assertIn("--slurp", calls[0])

    def test_empty_slurp_response_yields_empty_list(self):
        # 실측: 코멘트 0건이면 gh api --paginate --slurp 는 [[]] (빈 페이지
        # 하나)를 낸다 — 평탄화하면 빈 리스트.
        orig_slug = spawn._repo_slug
        orig_run = subprocess.run
        spawn._repo_slug = lambda root: "acme/repo"

        shape_contracts.assert_gh_paginate_slurp_shape([[]])

        def fake_run(cmd, *a, **k):
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps([[]]), stderr="")

        spawn.subprocess.run = fake_run
        try:
            out, ok = spawn._issue_comments(Path("."), 999)
        finally:
            spawn._repo_slug = orig_slug
            spawn.subprocess.run = orig_run
        self.assertTrue(ok)
        self.assertEqual(out, [])

    def test_gh_failure_yields_ok_false(self):
        """gh 호출 자체가 실패하면(returncode!=0) ok=False — 빈 리스트를
        "코멘트 0개"로 읽으면 안 된다(issue #287 S6)."""
        orig_slug = spawn._repo_slug
        orig_run = subprocess.run
        spawn._repo_slug = lambda root: "acme/repo"

        def fake_run(cmd, *a, **k):
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="rate limited")

        spawn.subprocess.run = fake_run
        try:
            out, ok = spawn._issue_comments(Path("."), 999)
        finally:
            spawn._repo_slug = orig_slug
            spawn.subprocess.run = orig_run
        self.assertFalse(ok)
        self.assertEqual(out, [])


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
        self._patch(spawn, "_issue_comments", lambda root, n: ([], True))
        self._patch(spawn, "_roster_load", lambda: {})
        old_root = spawn.ROOT
        spawn.ROOT = self.root
        self.addCleanup(setattr, spawn, "ROOT", old_root)
        sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
        import flows
        self.flows = flows
        self._patch(flows, "_pr_list_all", lambda root: ([], True))
        self._patch(flows, "_issue_list_all", lambda root: ([], True))
        import closure_sweep
        self.closure_sweep = closure_sweep
        self._patch(closure_sweep, "find_violations",
                    lambda root, subjects=None, issue_states=None: ([], []))

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
        self._patch(self.flows, "_pr_list_all", lambda root: ([
            {"number": 99, "headRefName": "issue-20/product-discovery",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ], True))
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(len(payload["decision_queue"]), 1)
        entry = payload["decision_queue"][0]
        self.assertEqual(entry["pr"], 99)
        self.assertEqual(entry["phase"], 1)
        self.assertEqual(entry["awaiting"], "approve-scope")

    def test_decision_queue_from_open_pr_with_no_board_record(self):
        """issue #216 결함 1 회귀: 머지된 레코드도 계획 블록도 없는 이슈의
        PR(PR #86 재현)이 decision_queue 에 phase 1 로 떠야 한다."""
        self._patch(self.flows, "_pr_list_all", lambda root: ([
            {"number": 86, "headRefName": "issue-86/product-discovery",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ], True))
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
        self._patch(self.flows, "_pr_list_all", lambda root: ([
            {"number": 56, "headRefName": "issue-31/implementation",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ], True))
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
        self._patch(self.flows, "_pr_list_all", lambda root: ([
            {"number": 55, "headRefName": "issue-30/implementation",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ], True))
        self._patch(self.closure_sweep, "find_violations",
                    lambda root, subjects=None, issue_states=None: ([{"kind": "open-pr-on-closed-issue"}], []))
        payload = self.flows.flows_payload(self.root)
        self.assertEqual(payload["hygiene"]["closure_sweep"],
                         [{"kind": "open-pr-on-closed-issue"}])
        self.assertEqual(len(payload["hygiene"]["unapproved_open_prs"]), 1)
        self.assertEqual(payload["hygiene"]["unapproved_open_prs"][0]["pr"], 55)

    def test_flows_plan_is_null_without_plan_block(self):
        self._write_record("issue-40", "product-discovery", "scope-proposed")
        self._patch(self.flows, "_issue_list_all", lambda root: ([
            {"number": 40, "state": "OPEN", "body": "일반 이슈 본문, 계획 없음"},
        ], True))
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
        self._patch(self.flows, "_issue_list_all", lambda root: ([
            {"number": 41, "state": "OPEN", "body": body},
        ], True))
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
        self._patch(self.flows, "_issue_list_all", lambda root: ([
            {"number": 50, "state": "OPEN", "body": body},
        ], True))
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
        self._patch(self.flows, "_issue_list_all", lambda root: ([
            {"number": 189, "state": "OPEN", "body": body},
        ], True))
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
        self._patch(self.flows, "_issue_list_all", lambda root: ([
            {"number": 51, "state": "OPEN", "body": body},
        ], True))
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
        self._patch(self.flows, "_issue_list_all", lambda root: ([
            {"number": 52, "state": "OPEN", "body": body},
        ], True))
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[52]["plan"],
                         [{"step": 1, "roles": ["product-discovery"], "done": False}])

    def test_flows_prs_includes_open_prs_for_roles_with_no_board_record(self):
        """issue #248 재현 회귀 (issue-27 실물 사례): board 레코드가 있는
        role은 하나뿐이고(해당 role의 PR은 이미 머지돼 `pr_by_branch`에
        없음), 레코드 없는 두 role의 open PR이 있을 때 `flows[].prs`에
        그 두 PR 번호가 모두 채워져야 한다 — 이전에는 `roles`(레코드가
        있는 role만) 필터 때문에 빈 배열이었다."""
        self._write_record("issue-27", "implementation", "scope-approved")
        self._patch(self.flows, "_pr_list_all", lambda root: ([
            {"number": 31, "headRefName": "issue-27/execution-observation",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
            {"number": 32, "headRefName": "issue-27/conformance-review",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ], True))
        payload = self.flows.flows_payload(self.root)
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(by_issue[27]["prs"], [31, 32])

    def test_flows_prs_and_decision_queue_share_the_same_pr_set(self):
        """issue #248 일관성 회귀: `decision_queue`에 등장하는 PR 번호는
        모두 같은 subject의 `flows[].prs`에도 포함된다 — 승인된 PR과
        미승인 PR을 섞어 `decision_queue`가 부분집합만 가질 때도
        `flows[].prs`는 열려 있는 PR 전체를 갖는지 확인한다."""
        (self.root / "docs" / "specs").mkdir(parents=True, exist_ok=True)
        (self.root / "docs" / "specs" / "approvers.md").write_text(
            "- reviewer1\n", encoding="utf-8")
        self._write_record("issue-45", "conformance-review", "scope-approved")
        self._write_record("issue-45", "execution-observation", "scope-approved")
        self._patch(self.flows, "_pr_list_all", lambda root: ([
            {"number": 101, "headRefName": "issue-45/conformance-review",
             "createdAt": "2026-07-30T00:00:00Z", "body": "",
             "reviews": [{"state": "APPROVED",
                         "author": {"login": "reviewer1"}}]},
            {"number": 102, "headRefName": "issue-45/execution-observation",
             "createdAt": "2026-07-30T00:00:00Z", "body": "", "reviews": []},
        ], True))
        payload = self.flows.flows_payload(self.root)
        dq_prs = {d["pr"] for d in payload["decision_queue"] if d["issue"] == 45}
        by_issue = {f["issue"]: f for f in payload["flows"]}
        self.assertEqual(dq_prs, {102})
        self.assertEqual(by_issue[45]["prs"], [101, 102])
        self.assertTrue(dq_prs.issubset(set(by_issue[45]["prs"])))


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
        # 로스터에 살아있는 wrapper_pid(자기 자신)를 심어 둔다 — 이슈 #224의
        # pid 사망 감지가 기존 stall 회귀 테스트를 오탐으로 깨지 않는지
        # 명시적으로 지킨다. `pid`(claude 서브프로세스 자리)는 아무 값이나
        # 넣어도 무방하다 — `_watch` 의 크래시 판정은 `wrapper_pid` 만
        # 본다.
        old_roster = spawn.ROSTER
        spawn.ROSTER = Path(self.td) / "active.json"
        self.addCleanup(setattr, spawn, "ROSTER", old_roster)
        spawn.roster_register("issue-180/implementation", {
            "pid": 999999, "wrapper_pid": os.getpid(), "role": "implementation",
            "issue": 180, "ts": int(time.time()), "work": str(self.work),
            "log": str(self.log)})

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

    def test_follow_detects_dead_session_and_returns_crash_rc(self):
        # 이슈 #224 결함 3: 세션이 크래시해 session-end 가 영영 안 오면
        # --follow 가 무한정 stall 을 반복하면 안 된다 — 로스터 엔트리는
        # 있지만 그 wrapper_pid 가 죽어 있으면(PR #255 피드백 1: session-end
        # 가 이미 잔여로 남아있지 않은 경우에만) 유한 반복 안에
        # WATCH_CRASH_RC 로 리턴한다. 이 events.jsonl 에는 session-end 가
        # 전혀 없다(크래시 세션이라 못 남겼다).
        # 이슈 #266으로 갱신: 이전에는 로스터 엔트리 부재 자체를 pid 사망과
        # 동치로 다뤄 이 시나리오를 재현했으나, #266이 그 동치를 깼다(엔트리
        # 부재는 더 이상 사망 신호가 아니다) — 실제로 남아 있어야 하는
        # 트리거(엔트리는 존재, wrapper_pid 는 죽음)를 여기서 직접
        # 구성한다.
        from unittest import mock
        dead = subprocess.Popen(["true"])
        dead.wait()
        spawn.roster_register("issue-180/implementation", {
            "pid": 999999, "wrapper_pid": dead.pid, "role": "implementation",
            "issue": 180, "ts": int(time.time()), "work": str(self.work),
            "log": str(self.log)})
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path):
            calls.append(1)
            return 0  # 매번 stall 흉내 — offset 진행 없음

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True)
        self.assertEqual(rc, spawn.WATCH_CRASH_RC)
        self.assertLess(len(calls), 5, calls)  # 유한 반복 — 무한 루프 없음

    def test_follow_prioritizes_pending_session_end_over_pid_check(self):
        # PR #255 피드백 1의 벤인 레이스: 세션이 정상 종료해 session-end 를
        # 이미 events.jsonl 에 남겼는데(progress 다음 줄), 그 줄이 아직
        # 소비되지 않은 첫 반복에서 pid 가 죽어 있어도 잔여 session-end 를
        # 먼저 소진해야지, 그 반복에서 곧장 크래시로 오판하면 안 된다 —
        # spawn.py:1943-1953 의 드레인-우선 블록이 지키는 순서.
        #
        # 이슈 #271 관찰(survey.md §5): 이전 버전은 로스터 엔트리를
        # `roster_remove`로 아예 지워 죽음 신호를 흉내냈는데, 이슈 #266이
        # "엔트리 부재는 사망 신호가 아니다"로 바꾼 뒤로는 그 배치가 드레인
        # 블록과 무관하게(entry-absence 자체가 이미 pid 체크를 건너뛰므로)
        # 같은 결과를 내 더 이상 이 블록을 판별하지 못했다 — 살아있는
        # 로스터 엔트리 + 죽은 wrapper_pid(`test_follow_detects_dead_session_and_returns_crash_rc`
        # 와 같은 구성, test_spawn.py:3719-3747) 로 다시 배치해 판별력을
        # 복원한다: 드레인 블록이 없으면 첫 반복에서 곧장 WATCH_CRASH_RC 로
        # 리턴하고(session-end 잔여를 못 보고 죽은 pid 부터 본다), 있으면
        # 이 테스트가 기대하는 대로 session-end 를 먼저 소진하고 rc=0 이다.
        from unittest import mock
        dead = subprocess.Popen(["true"])
        dead.wait()
        spawn.roster_register("issue-180/implementation", {
            "pid": 999999, "wrapper_pid": dead.pid, "role": "implementation",
            "issue": 180, "ts": int(time.time()), "work": str(self.work),
            "log": str(self.log)})
        spawn._append_event(self.events, "progress", {"kind": "tool_use", "detail": "x"})
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
        self.assertEqual(len(calls), 2, calls)

    def test_follow_tolerates_post_processing_tail_before_session_end(self):
        # 헌트로 확인된 결함: `_spawn_one()`의 claude 서브프로세스
        # (roster `pid`)는 proc.wait() 리턴과 함께 정상 종료에서도 먼저
        # 죽는다 — push/게이트·소유권 리포트/classify/ledger_write 를
        # 거쳐야 session-end 가 남는다. 이 후처리 구간 동안은 `pid`가
        # 이미 죽어 있어도(여기서는 아예 안 심는다) `wrapper_pid`(호출자
        # 자신)가 살아있는 한 크래시로 오판하면 안 된다 — session-end 가
        # 나중에 나타나면 정상 리턴.
        from unittest import mock
        spawn.roster_register("issue-180/implementation", {
            "pid": 999999, "wrapper_pid": os.getpid(), "role": "implementation",
            "issue": 180, "ts": int(time.time()), "work": str(self.work),
            "log": str(self.log)})
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path):
            calls.append(1)
            if len(calls) < 3:
                return 0  # 후처리 구간 흉내: session-end 가 아직 없다
            spawn._append_event(events_path, "session-end", "progressed")
            spawn._write_offset(offset_path, spawn._read_offset(offset_path) + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 3, calls)

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

    def test_follow_tolerates_roster_entry_fully_absent_before_session_end(self):
        # 이슈 #266: `_spawn_one()`의 후처리 꼬리 동안 `roster_remove(roster_key)`
        # (spawn.py:2995)가 `session-end` 기록(spawn.py:3097)보다 먼저 실행돼,
        # 그 구간 전체에서 명부 엔트리가 아예 없다(setUp 이 심어 둔 엔트리를
        # 여기서 지워 그 상태를 실제로 구성한다 — 이전 회귀
        # test_follow_tolerates_post_processing_tail_before_session_end 는
        # wrapper_pid 가 살아있는 엔트리를 다시 심어서 이 창을 구성하지 않았다).
        # 엔트리 부재는 사망이 아니라 불명으로 다뤄 stall 안전망을 거쳐 계속
        # 대기해야 한다 — 수정 전에는 이 테스트가 WATCH_CRASH_RC 로 fail 한다.
        from unittest import mock
        spawn.roster_remove("issue-180/implementation")
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min, log_path):
            calls.append(1)
            if len(calls) < 3:
                return 0  # 엔트리 부재 꼬리 구간 흉내: session-end 가 아직 없다
            spawn._append_event(events_path, "session-end", "progressed")
            spawn._write_offset(offset_path, spawn._read_offset(offset_path) + 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(180, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 3, calls)


class AwaitBoundedTiming(unittest.TestCase):
    """이슈 #285 P1: `_await_bounded()` 가 고정 2초 sleep 대신 escalating
    poll 을 쓰는지 — session-start 가 거의 즉시 찍혀도 caller-return 이
    2초 가까이 걸리면 회귀."""

    def test_returns_quickly_after_early_event(self):
        with tempfile.TemporaryDirectory() as td:
            events_path = Path(td) / "events.jsonl"
            offset_path = Path(td) / "offset"
            log_path = Path(td) / "session.log"
            log_path.write_text("")

            def writer():
                time.sleep(0.1)
                spawn._append_event(events_path, "session-start", "spawned")

            t = threading.Thread(target=writer)
            t.start()
            t0 = time.monotonic()
            rc = spawn._await_bounded(events_path, offset_path, 5.0, log_path)
            elapsed = time.monotonic() - t0
            t.join()
            self.assertEqual(rc, 0)
            self.assertLess(elapsed, 1.5, f"caller-return took {elapsed:.3f}s")

    def test_still_bounded_by_stall_timeout(self):
        # 회귀 방지: escalating poll 이 stall 판정 자체를 늦추지 않는다 —
        # 이슈 #114 계약(무한정 블록하지 않는다)은 그대로.
        with tempfile.TemporaryDirectory() as td:
            events_path = Path(td) / "events.jsonl"
            offset_path = Path(td) / "offset"
            log_path = Path(td) / "session.log"
            log_path.write_text("")
            t0 = time.monotonic()
            stall_timeout_min = 0.03  # ~1.8s
            rc = spawn._await_bounded(events_path, offset_path,
                                      stall_timeout_min, log_path)
            elapsed = time.monotonic() - t0
            self.assertEqual(rc, 0)
            self.assertGreaterEqual(elapsed, stall_timeout_min * 60 - 0.5)
            self.assertLess(elapsed, stall_timeout_min * 60 + 2.5)


class RulebookCheckoutMemo(unittest.TestCase):
    """이슈 #285 P2/P4: `rulebook_checkout()` 은 한 프로세스 안에서
    marketplace 당 최대 한 번만 `git pull` 을 실제로 부른다(in-process
    memo), 그리고 TTL 창 안이면 새 프로세스에서도 pull 을 건너뛴다(디스크
    마커)."""

    def _counting_git_wrapper(self, fake_bin, call_count_file):
        real_git = shutil.which("git")
        wrapper = fake_bin / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            f'if [ "$1" = "-C" ] && [ "$3" = "pull" ]; then echo pull >> {call_count_file}; fi\n'
            f"exec {real_git} \"$@\"\n"
        )
        wrapper.chmod(0o755)

    def setUp(self):
        spawn._RULEBOOK_CACHE = {}
        self._saved_ttl = os.environ.pop("MUSTER_RULEBOOK_TTL", None)

    def tearDown(self):
        spawn._RULEBOOK_CACHE = {}
        os.environ.pop("MUSTER_RULEBOOK_TTL", None)
        if self._saved_ttl is not None:
            os.environ["MUSTER_RULEBOOK_TTL"] = self._saved_ttl

    def test_pull_at_most_once_per_process_across_real_call_sites(self):
        with tempfile.TemporaryDirectory() as td:
            fake_root = Path(td) / "root"
            clone_dir = fake_root / "runs" / "rulebooks" / "acme-rules"
            clone_dir.mkdir(parents=True)
            (clone_dir / ".claude-plugin").mkdir()
            (clone_dir / ".claude-plugin" / "marketplace.json").write_text(
                json.dumps({"plugins": [{"name": "coding", "source": "./coding"}]}))
            (clone_dir / "coding" / ".claude-plugin").mkdir(parents=True)
            (clone_dir / "coding" / ".claude-plugin" / "plugin.json").write_text("{}")
            subprocess.run(["git", "init", "-q", str(clone_dir)])
            subprocess.run(["git", "-C", str(clone_dir), "commit", "-q",
                           "--allow-empty", "-m", "init",
                           "--author=t <t@t.t>"], capture_output=True)
            subprocess.run(["git", "-C", str(clone_dir), "remote", "add",
                           "origin", str(clone_dir)])

            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            call_count_file = Path(td) / "pull-calls.txt"
            self._counting_git_wrapper(fake_bin, call_count_file)

            spec = {"marketplace": "acme-rules", "repo": "acme/acme-rules"}
            saved_root = spawn.ROOT
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            spawn.ROOT = fake_root
            try:
                spawn.plugin_dirs("implementation", spec)     # call 1
                spawn.checkout_version("implementation", spec)  # call 2
                spawn.checkout_version("implementation", spec)  # call 3 (ledger)
            finally:
                spawn.ROOT = saved_root
                os.environ["PATH"] = old_path

            calls = call_count_file.read_text().splitlines() if call_count_file.exists() else []
            self.assertEqual(len(calls), 1, calls)

    def test_ttl_marker_skips_pull_on_fresh_marker(self):
        with tempfile.TemporaryDirectory() as td:
            fake_root = Path(td) / "root"
            clone_dir = fake_root / "runs" / "rulebooks" / "acme-rules"
            clone_dir.mkdir(parents=True)
            (clone_dir / ".claude-plugin").mkdir()
            (clone_dir / ".claude-plugin" / "marketplace.json").write_text("{}")

            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            call_count_file = Path(td) / "pull-calls.txt"
            self._counting_git_wrapper(fake_bin, call_count_file)

            spec = {"marketplace": "acme-rules", "repo": "acme/acme-rules"}
            saved_root = spawn.ROOT
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            spawn.ROOT = fake_root
            try:
                spawn._ttl_marker(clone_dir).parent.mkdir(parents=True, exist_ok=True)
                spawn._ttl_marker(clone_dir).write_text(str(time.time()))
                spawn.rulebook_checkout("implementation", spec)
            finally:
                spawn.ROOT = saved_root
                os.environ["PATH"] = old_path

            self.assertFalse(call_count_file.exists(), "TTL 창 안인데 pull 이 불렸다")

    def test_muster_rulebook_ttl_zero_forces_pull(self):
        os.environ["MUSTER_RULEBOOK_TTL"] = "0"
        with tempfile.TemporaryDirectory() as td:
            fake_root = Path(td) / "root"
            clone_dir = fake_root / "runs" / "rulebooks" / "acme-rules"
            clone_dir.mkdir(parents=True)
            (clone_dir / ".claude-plugin").mkdir()
            (clone_dir / ".claude-plugin" / "marketplace.json").write_text("{}")
            subprocess.run(["git", "init", "-q", str(clone_dir)])

            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            call_count_file = Path(td) / "pull-calls.txt"
            self._counting_git_wrapper(fake_bin, call_count_file)

            spec = {"marketplace": "acme-rules", "repo": "acme/acme-rules"}
            saved_root = spawn.ROOT
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            spawn.ROOT = fake_root
            try:
                spawn._ttl_marker(clone_dir).parent.mkdir(parents=True, exist_ok=True)
                spawn._ttl_marker(clone_dir).write_text(str(time.time()))
                spawn.rulebook_checkout("implementation", spec)
            finally:
                spawn.ROOT = saved_root
                os.environ["PATH"] = old_path

            calls = call_count_file.read_text().splitlines() if call_count_file.exists() else []
            self.assertEqual(len(calls), 1, calls)

    def test_ttl_marker_does_not_dirty_clone(self):
        """이슈 #296: TTL 마커는 클론 밖(`runs/ttl-markers/`)에 있어야
        한다 — 클론 안에 두면 `git status --porcelain` 이 영영 비지
        않아 `(커밋 안 된 변경 있음)`/`+커밋안됨` 이 모든 클론에 상시로
        붙는다."""
        with tempfile.TemporaryDirectory() as td:
            fake_root = Path(td) / "root"
            clone_dir = fake_root / "runs" / "rulebooks" / "acme-rules"
            clone_dir.mkdir(parents=True)
            subprocess.run(["git", "init", "-q", str(clone_dir)], check=True)
            subprocess.run(["git", "-C", str(clone_dir), "commit", "-q",
                           "--allow-empty", "-m", "init",
                           "--author=t <t@t.t>"], check=True, capture_output=True)

            saved_root = spawn.ROOT
            spawn.ROOT = fake_root
            try:
                spawn._mark_pulled(clone_dir)
                marker = spawn._ttl_marker(clone_dir)
                self.assertTrue(marker.exists())
                self.assertFalse(
                    str(marker.resolve()).startswith(str(clone_dir.resolve()) + os.sep),
                    "TTL 마커가 클론 안에 있다")

                status = subprocess.run(
                    ["git", "-C", str(clone_dir), "status", "--porcelain"],
                    capture_output=True, text=True, check=True)
                self.assertEqual(status.stdout, "", status.stdout)
            finally:
                spawn.ROOT = saved_root


class LegacyTtlMarkerMigration(unittest.TestCase):
    """이슈 #313: #297 이전 코드가 클론 안에 써 둔 `.muster-last-pull` 은
    #297 이후에도 디스크에 남아, 지우기 전까진 `checkout_version()` 의
    dirty 접미사가 그 클론에 상시로 붙는다. `rulebook_checkout()` 이
    관리 클론을 다시 쓸 때마다 그 레거시 마커를 지워야 한다."""

    def setUp(self):
        spawn._RULEBOOK_CACHE = {}

    def tearDown(self):
        spawn._RULEBOOK_CACHE = {}

    def _fake_clone(self, td):
        fake_root = Path(td) / "root"
        clone_dir = fake_root / "runs" / "rulebooks" / "acme-rules"
        clone_dir.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(clone_dir)], check=True)
        (clone_dir / ".claude-plugin").mkdir()
        (clone_dir / ".claude-plugin" / "marketplace.json").write_text("{}")
        subprocess.run(["git", "-C", str(clone_dir), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(clone_dir), "commit", "-q",
                       "-m", "init",
                       "--author=t <t@t.t>"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(clone_dir), "remote", "add",
                       "origin", str(clone_dir)], check=True)
        return fake_root, clone_dir

    def test_stale_in_clone_marker_no_longer_reports_dirty(self):
        with tempfile.TemporaryDirectory() as td:
            fake_root, clone_dir = self._fake_clone(td)
            # pre-#297 코드가 남긴 in-clone 마커 — untracked, gitignore 안 됨.
            (clone_dir / ".muster-last-pull").write_text(str(time.time()))

            spec = {"marketplace": "acme-rules", "repo": "acme/acme-rules"}
            saved_root = spawn.ROOT
            os.environ["MUSTER_RULEBOOK_TTL"] = "0"  # 매번 pull, 마이그레이션 경로를 확실히 탄다
            spawn.ROOT = fake_root
            try:
                version = spawn.checkout_version("implementation", spec)
            finally:
                spawn.ROOT = saved_root
                os.environ.pop("MUSTER_RULEBOOK_TTL", None)

            self.assertNotIn("커밋 안 된 변경 있음", version, version)
            self.assertFalse((clone_dir / ".muster-last-pull").exists())

    def test_genuine_uncommitted_change_still_reports_dirty(self):
        with tempfile.TemporaryDirectory() as td:
            fake_root, clone_dir = self._fake_clone(td)
            (clone_dir / ".muster-last-pull").write_text(str(time.time()))
            (clone_dir / "real-edit.txt").write_text("uncommitted")

            spec = {"marketplace": "acme-rules", "repo": "acme/acme-rules"}
            saved_root = spawn.ROOT
            os.environ["MUSTER_RULEBOOK_TTL"] = "0"
            spawn.ROOT = fake_root
            try:
                version = spawn.checkout_version("implementation", spec)
            finally:
                spawn.ROOT = saved_root
                os.environ.pop("MUSTER_RULEBOOK_TTL", None)

            self.assertIn("커밋 안 된 변경 있음", version, version)


class FetchDedupe(unittest.TestCase):
    """이슈 #285 P3: 같은 work_dir 에 대한 두 번째 `_fetch_or_halt()` 호출은
    (같은 프로세스 안이면) 네트워크로 나가지 않는다 — 단, halt 판정은
    첫 호출의 결과를 그대로 물려받아야 한다(성공만 fresh 로 기록)."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True)

    def setUp(self):
        spawn._FETCHED_THIS_SPAWN = {}

    def tearDown(self):
        spawn._FETCHED_THIS_SPAWN = {}

    def test_second_fetch_of_same_dir_is_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            origin.mkdir()
            self._git(origin, "init", "-q")
            self._git(origin, "config", "user.email", "t@t.t")
            self._git(origin, "config", "user.name", "t")
            (origin / "a.txt").write_text("x")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "init")
            subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                           capture_output=True)

            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            call_count_file = Path(td) / "fetch-calls.txt"
            real_git = shutil.which("git")
            wrapper = fake_bin / "git"
            wrapper.write_text(
                "#!/bin/sh\n"
                f'if [ "$1" = "-C" ] && [ "$3" = "fetch" ]; then echo f >> {call_count_file}; fi\n'
                f"exec {real_git} \"$@\"\n"
            )
            wrapper.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            try:
                spawn._fetch_or_halt(str(work), "first")
                spawn._fetch_or_halt(str(work), "second")
            finally:
                os.environ["PATH"] = old_path

            calls = call_count_file.read_text().splitlines() if call_count_file.exists() else []
            self.assertEqual(len(calls), 1, calls)

    def test_after_callback_still_runs_on_dedupe_skip(self):
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            origin.mkdir()
            self._git(origin, "init", "-q")
            self._git(origin, "config", "user.email", "t@t.t")
            self._git(origin, "config", "user.name", "t")
            (origin / "a.txt").write_text("x")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "init")
            subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                           capture_output=True)
            spawn._fetch_or_halt(str(work), "first")
            called = []
            spawn._fetch_or_halt(str(work), "second", after=lambda: called.append(1))
            self.assertEqual(called, [1])


class NetworkSubprocessTimeout(unittest.TestCase):
    """이슈 #285 P5: 네트워크 subprocess 가 `timeout=` 을 넘기면 조용히
    걸리는 대신 이름 있는 에러로 종료한다."""

    def test_run_net_exits_with_named_error_on_timeout(self):
        def fake_run(*a, **k):
            raise subprocess.TimeoutExpired(cmd=a[0] if a else "git", timeout=k.get("timeout"))

        with mock.patch.object(subprocess, "run", fake_run):
            with self.assertRaises(SystemExit) as ctx:
                spawn._run_net(["git", "fetch"], "테스트 라벨", timeout=1)
        self.assertIn("테스트 라벨", str(ctx.exception))
        self.assertIn("시간초과", str(ctx.exception))

    def test_fetch_or_halt_times_out_within_bound_not_hang(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            work.mkdir()
            spawn._FETCHED_THIS_SPAWN = {}

            def fake_run(*a, **k):
                raise subprocess.TimeoutExpired(cmd=a[0] if a else "git", timeout=k.get("timeout"))

            t0 = time.monotonic()
            with mock.patch.object(subprocess, "run", fake_run):
                with self.assertRaises(SystemExit):
                    spawn._fetch_or_halt(str(work), "네트워크 fetch")
            elapsed = time.monotonic() - t0
            self.assertLess(elapsed, 5, "TimeoutExpired 이 fail-closed 로 즉시 표면화해야 한다")


class GitEnvTimeoutPromptVars(unittest.TestCase):
    """이슈 #285 P5: `_git_env()` 의 dict 분기에만
    GIT_TERMINAL_PROMPT=0/GIT_ASKPASS=true 를 얹는다 — None 폴백은 그대로."""

    def setUp(self):
        spawn._GH_TOKEN_CACHE = None
        self._saved_agent = os.environ.pop("MUSTER_AGENT_GH_TOKEN", None)

    def tearDown(self):
        spawn._GH_TOKEN_CACHE = None
        os.environ.pop("MUSTER_AGENT_GH_TOKEN", None)
        if self._saved_agent is not None:
            os.environ["MUSTER_AGENT_GH_TOKEN"] = self._saved_agent

    def test_token_present_branch_carries_prompt_suppression(self):
        os.environ["MUSTER_AGENT_GH_TOKEN"] = "tok"
        env = spawn._git_env()
        self.assertIsNotNone(env)
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(env["GIT_ASKPASS"], "true")

    def test_no_token_fallback_stays_none(self):
        with mock.patch.object(spawn, "_resolve_gh_token", lambda: ""):
            env = spawn._git_env()
        self.assertIsNone(env)


class FixtureShapeContracts(unittest.TestCase):
    """이슈 #335: 픽스처 shape 이 실제 인터페이스에서 벗어나면 조용히
    통과하는 대신 여기서 시끄럽게 실패해야 한다."""

    GOLDEN_GH_PATH = os.path.join(
        os.path.dirname(__file__), "tests", "fixtures", "golden",
        "gh_paginate_slurp_sample.json")

    def _golden_gh_payload(self):
        with open(self.GOLDEN_GH_PATH, encoding="utf-8") as f:
            return json.load(f)

    def test_gh_paginate_slurp_golden_sample_matches_own_shape_check(self):
        # 실제 dependency(gh api)에 대해 완전히 검증되는 유일한 리그: 이
        # 픽스처는 실측 캡처본이고(proposal 참고), 그 자체를 shape-check로
        # 검증한다 — 체크가 자기 자신만 확인하는 게 아님을 보인다.
        payload = self._golden_gh_payload()
        shape_contracts.assert_gh_paginate_slurp_shape(payload)

    def test_gh_paginate_slurp_shape_fails_loudly_on_missing_field(self):
        payload = self._golden_gh_payload()
        broken = [[dict(c) for c in page] for page in payload]
        for page in broken:
            for comment in page:
                del comment["body"]
        if not any(comment for page in broken for comment in page):
            self.skipTest("golden sample has no comments to break")
        with self.assertRaises(AssertionError) as cm:
            shape_contracts.assert_gh_paginate_slurp_shape(broken)
        self.assertIn("body", str(cm.exception))

    def test_gh_paginate_slurp_shape_fails_on_non_list_page(self):
        with self.assertRaises(AssertionError):
            shape_contracts.assert_gh_paginate_slurp_shape([{"not": "a list"}])

    def test_stream_event_shape_accepts_fixtures_spawn_py_reads(self):
        _event("result", permission_denials=[{"tool_name": "Write"}])
        _event("user", message={"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": "boom"}]})
        _event("assistant", message={"content": [
            {"type": "tool_use", "id": "t1", "name": "Write", "input": {}}]})

    def test_stream_event_shape_fails_when_fixture_missing_field_parser_reads(self):
        # tool_use_id 가 spawn.py:1608 부근에서 상관관계 확인에 쓰인다 —
        # 픽스처가 이 필드를 빠뜨리면 시끄럽게 실패해야 한다.
        with self.assertRaises(AssertionError) as cm:
            _event("user", message={"content": [
                {"type": "tool_result", "is_error": True, "content": "boom"}]})
        self.assertIn("tool_use_id", str(cm.exception))

    def test_stream_event_shape_rejects_unknown_top_level_type(self):
        # spawn.py 파서가 읽지 않는 필드를 픽스처가 선언하면(여기서는
        # top-level type 자체가 파서 기대 밖) — 파서가 실제로 읽는 값
        # 집합과 픽스처가 어긋났다는 뜻이므로 실패해야 한다.
        with self.assertRaises(AssertionError):
            shape_contracts.assert_claude_stream_event_shape({"type": "system"})


if __name__ == "__main__":
    unittest.main()


class DryRunCwdValidation(unittest.TestCase):
    """#288 N2: --dry-run 은 -C 를 검증하지 않고 세션 설정 JSON을 찍어
    존재하지 않는 경로도 "검증됨"처럼 보이게 만들었다."""

    def test_dry_run_rejects_nonexistent_cwd(self):
        old_argv = sys.argv
        sys.argv = ["spawn.py", "coding", "task", "--dry-run",
                    "-C", "/nonexistent/path/does-not-exist-288"]
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            with self.assertRaises(SystemExit) as cm:
                spawn.main()
        finally:
            sys.stdout = old_stdout
            sys.argv = old_argv
        self.assertNotEqual(cm.exception.code, 0)
        self.assertEqual(buf.getvalue(), "")

    def test_dry_run_rejects_cwd_that_is_a_file(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "plainfile"
            f.write_text("x")
            old_argv = sys.argv
            sys.argv = ["spawn.py", "coding", "task", "--dry-run", "-C", str(f)]
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with self.assertRaises(SystemExit) as cm:
                    spawn.main()
            finally:
                sys.stdout = old_stdout
                sys.argv = old_argv
            self.assertNotEqual(cm.exception.code, 0)
            self.assertEqual(buf.getvalue(), "")


class IssueArgValidation(unittest.TestCase):
    """#288 N3: --issue 는 argparse type=int 라 0/음수/거대정수도 통과했다."""

    def test_positive_int_accepts_valid(self):
        self.assertEqual(spawn.positive_int("51"), 51)

    def test_positive_int_rejects_zero(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            spawn.positive_int("0")

    def test_positive_int_rejects_negative(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            spawn.positive_int("-5")

    def test_issue_zero_rejected_at_parse_time_before_any_logic(self):
        old_argv = sys.argv
        sys.argv = ["spawn.py", "watch", "--issue", "0"]
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            with self.assertRaises(SystemExit) as cm:
                spawn.main()
        finally:
            sys.stderr = old_stderr
            sys.argv = old_argv
        self.assertEqual(cm.exception.code, 2)

    def test_issue_negative_rejected_at_parse_time(self):
        old_argv = sys.argv
        sys.argv = ["spawn.py", "watch", "--issue", "-5"]
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            with self.assertRaises(SystemExit) as cm:
                spawn.main()
        finally:
            sys.stderr = old_stderr
            sys.argv = old_argv
        self.assertEqual(cm.exception.code, 2)


class BoardNonNumericSubjectWarning(unittest.TestCase):
    """#288 N4: board() 는 issue-NaN 같은 비숫자 issue-* 디렉터리를 아무
    경고 없이 그냥 빼버렸다 — 서브젝트가 오케스트레이터 라우팅에서 조용히
    사라졌다."""

    def test_non_numeric_subject_dir_excluded_and_warned(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs = root / "docs"
            good = docs / "issue-12" / "reports"
            bad = docs / "issue-NaN" / "reports"
            good.mkdir(parents=True)
            bad.mkdir(parents=True)
            role = spawn.ROLES[0]
            (good / f"{role}.md").write_text("---\nloop_state: done\n---\nbody")
            (bad / f"{role}.md").write_text("---\nloop_state: done\n---\nbody")

            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            try:
                found = spawn.board(root)
                warned = sys.stderr.getvalue()
            finally:
                sys.stderr = old_stderr

            self.assertIn("issue-12", found)
            self.assertNotIn("issue-NaN", found)
            self.assertIn("issue-NaN", warned)


class WorkspaceReuseOriginMismatch(unittest.TestCase):
    """#288 N5: 작업 경로에 우연히 다른 origin 을 가진 레포가 이미 있으면
    재사용 분기로 들어가 fetch 실패를 네트워크 문제로 오보했다."""

    def _init_repo(self, path: Path, origin_url: str) -> None:
        path.mkdir(parents=True)
        run = lambda *args: subprocess.run(
            args, cwd=str(path), capture_output=True, text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (path / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")
        run("git", "remote", "add", "origin", origin_url)

    def test_foreign_origin_at_work_path_is_refused_by_identity(self):
        with tempfile.TemporaryDirectory() as td:
            src_remote = Path(td) / "src-remote.git"
            subprocess.run(["git", "init", "-q", "--bare", str(src_remote)], check=True)
            src = Path(td) / "src"
            self._init_repo(src, str(src_remote))
            subprocess.run(["git", "-C", str(src), "push", "-q", "-u", "origin", "HEAD:main"],
                           check=True)

            work_base = Path(td) / "work"
            work_base.mkdir()
            repo_name = "src-remote"  # derived from src_remote's basename, like issue_workspace() does
            issue = 999
            role = "coding"
            work = work_base / f"{repo_name}-issue-{issue}-{role}"
            self._init_repo(work, "https://github.com/someone/unrelated.git")

            old_environ = dict(os.environ)
            os.environ["MUSTER_WORK_DIR"] = str(work_base)
            try:
                with self.assertRaises(SystemExit) as cm:
                    spawn.issue_workspace(str(src), issue, role)
            finally:
                os.environ.clear()
                os.environ.update(old_environ)

            msg = str(cm.exception)
            self.assertIn("origin 불일치", msg)
            self.assertNotIn("fetch 실패", msg)
            self.assertTrue((work / "f.txt").exists())

    def test_ssh_vs_https_origin_form_is_not_treated_as_mismatch(self):
        # warrant hunt finding: toggling MUSTER_KEEP_SSH between spawns of
        # the same issue/role must not make the identity check (N5 fix)
        # falsely refuse a legitimately matching workspace just because
        # one side is ssh-form and the other https-form.
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src"
            self._init_repo(src, "git@github.com:someorg/somerepo.git")

            work_base = Path(td) / "work"
            work_base.mkdir()
            repo_name = "somerepo"
            issue = 998
            role = "coding"
            work = work_base / f"{repo_name}-issue-{issue}-{role}"
            self._init_repo(work, "https://github.com/someorg/somerepo.git")

            old_environ = dict(os.environ)
            os.environ["MUSTER_WORK_DIR"] = str(work_base)
            os.environ.pop("MUSTER_KEEP_SSH", None)
            try:
                with mock.patch.object(spawn, "_fetch_or_halt") as fake_fetch:
                    result = spawn.issue_workspace(str(src), issue, role)
            finally:
                os.environ.clear()
                os.environ.update(old_environ)

            self.assertEqual(result, str(work))
            fake_fetch.assert_called_once()


class AwaitBoundedMissingLog(unittest.TestCase):
    """#288 corroboration item: log_path 가 존재하지 않으면 "stall: N초째
    무변화"가 아니라 "cannot observe" 로 보고해야 한다 — clean 의 전역
    스윕이 로그를 지운 세션을 가짜 stall 로 오보하던 실측 사건."""

    def test_missing_log_reports_cannot_observe_not_stall(self):
        with tempfile.TemporaryDirectory() as td:
            events_path = Path(td) / "s.events.jsonl"
            offset_path = Path(td) / "s.events.offset"
            log_path = Path(td) / "does-not-exist.log"

            buf = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = buf
            try:
                rc = spawn._await_bounded(events_path, offset_path, 0.001, log_path)
            finally:
                sys.stderr = old_stderr

            out = buf.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("cannot observe", out)
            self.assertNotIn("stall:", out)

    def test_existing_unchanged_log_still_reports_stall(self):
        with tempfile.TemporaryDirectory() as td:
            events_path = Path(td) / "s.events.jsonl"
            offset_path = Path(td) / "s.events.offset"
            log_path = Path(td) / "present.log"
            log_path.write_text("x")

            buf = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = buf
            try:
                rc = spawn._await_bounded(events_path, offset_path, 0.001, log_path)
            finally:
                sys.stderr = old_stderr

            out = buf.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("stall:", out)
            self.assertNotIn("cannot observe", out)
