#!/usr/bin/env python3
"""issue #476 H1 — `gates/reexecution_gate.py` 단위 테스트.
네트워크 없이, 로컬 임시 git repo 안에서 돈다.

  python3 gates/test_reexecution_gate.py
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import reexecution_gate as rg


def _throwaway_repo(td: str) -> tuple[Path, str]:
    repo = Path(td) / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo,
                   check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "script.sh").write_text("#!/bin/sh\nexit 0\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                         capture_output=True, text=True, check=True
                         ).stdout.strip()
    return repo, sha


def t_passing_command_yields_pass_verdict():
    with tempfile.TemporaryDirectory() as td:
        repo, sha = _throwaway_repo(td)
        v = rg.run_reexecution("sh script.sh", sha, repo, timeout=10)
        assert v.kind == rg.PASS, v


def t_failing_command_yields_fail_verdict():
    with tempfile.TemporaryDirectory() as td:
        repo, sha = _throwaway_repo(td)
        v = rg.run_reexecution("sh -c 'exit 1'", sha, repo, timeout=10)
        assert v.kind == rg.FAIL, v
        assert v.exit_code == 1, v


def t_bad_sha_yields_error_verdict_fail_closed():
    with tempfile.TemporaryDirectory() as td:
        repo, _sha = _throwaway_repo(td)
        v = rg.run_reexecution("sh script.sh", "deadbeef", repo, timeout=10)
        assert v.kind == rg.ERROR, v


def t_timeout_yields_error_verdict():
    with tempfile.TemporaryDirectory() as td:
        repo, sha = _throwaway_repo(td)
        v = rg.run_reexecution("sh -c 'sleep 5'", sha, repo, timeout=1)
        assert v.kind == rg.ERROR, v


def t_write_and_read_verdict_roundtrip():
    with tempfile.TemporaryDirectory() as td:
        repo, sha = _throwaway_repo(td)
        v = rg.run_reexecution("sh script.sh", sha, repo, timeout=10)
        rg.write_verdict(repo, 476, "implementation", v)
        loaded = rg.read_verdict(repo, 476, "implementation")
        assert loaded is not None
        assert loaded.kind == v.kind, loaded


def t_missing_verdict_reads_as_none():
    with tempfile.TemporaryDirectory() as td:
        repo, _sha = _throwaway_repo(td)
        assert rg.read_verdict(repo, 999, "nobody") is None


def t_main_exits_nonzero_on_failing_command():
    with tempfile.TemporaryDirectory() as td:
        repo, sha = _throwaway_repo(td)
        rc = rg.main(["--issue", "476", "--role", "implementation", "--sha",
                     sha, "--command", "sh -c 'exit 1'", "--repo", str(repo)])
        assert rc != 0, rc


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
