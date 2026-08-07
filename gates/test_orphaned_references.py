#!/usr/bin/env python3
"""issue #330 — orphaned_references/reach_check 단위 테스트.

네트워크 없이, 실제 git 저장소(임시 디렉터리에 초기화) 위에서 돈다 —
`test_closes_gate_ci.py`와 같은 오프라인 관례. 각 테스트가 자기 repo를
만들고 지운다.

  python3 gates/test_orphaned_references.py
"""
from __future__ import annotations
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates


def _run(*args, cwd):
    p = subprocess.run(["git", "-C", str(cwd), *args],
                        capture_output=True, text=True)
    assert p.returncode == 0, (args, p.stdout, p.stderr)
    return p.stdout


def _repo_with_diff(base_files: dict[str, str], head_ops):
    """origin/main 에 base_files 를 커밋하고, head_ops(work) 로 HEAD 를 바꾼
    임시 git repo 를 만들어 work 경로를 낸다. head_ops 는 (path, content|None)
    쌍의 리스트 — content None 이면 삭제."""
    d = Path(tempfile.mkdtemp())
    _run("init", "-q", "-b", "main", cwd=d)
    _run("config", "user.email", "t@example.com", cwd=d)
    _run("config", "user.name", "t", cwd=d)
    for path, content in base_files.items():
        (d / path).parent.mkdir(parents=True, exist_ok=True)
        (d / path).write_text(content)
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "base", cwd=d)
    _run("update-ref", "refs/remotes/origin/main", "HEAD", cwd=d)
    _run("checkout", "-q", "-b", "issue-330/implementation", cwd=d)
    for path, content in head_ops:
        p = d / path
        if content is None:
            p.unlink()
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "head", cwd=d)
    return d


def t_orphaned_references_empty_when_nothing_deleted_or_renamed():
    d = _repo_with_diff(
        {"a.txt": "hello"},
        [("a.txt", "hello world")])
    try:
        assert gates.orphaned_references(d, base="origin/main") == []
    finally:
        shutil.rmtree(d)


def t_orphaned_references_finds_live_reference_to_deleted_path():
    d = _repo_with_diff(
        {"markers/ttl.txt": "1", "bench/run.py": "path = 'markers/ttl.txt'"},
        [("markers/ttl.txt", None)])
    try:
        hits = gates.orphaned_references(d, base="origin/main")
        assert hits == [("markers/ttl.txt", "bench/run.py")], hits
    finally:
        shutil.rmtree(d)


def t_orphaned_references_finds_reference_to_renamed_old_path():
    d = _repo_with_diff(
        {"old/marker.txt": "1", "reader.py": "open('old/marker.txt')"},
        [("old/marker.txt", None), ("new/marker.txt", "1")])
    try:
        hits = gates.orphaned_references(d, base="origin/main")
        assert ("old/marker.txt", "reader.py") in hits, hits
    finally:
        shutil.rmtree(d)


def t_reach_check_fails_when_orphan_undeclared():
    d = _repo_with_diff(
        {"markers/ttl.txt": "1", "bench/run.py": "path = 'markers/ttl.txt'"},
        [("markers/ttl.txt", None)])
    try:
        bad = gates.reach_check(d, "## Reach\nNone.\n", base="origin/main")
        assert bad and "markers/ttl.txt" in bad[0], bad
    finally:
        shutil.rmtree(d)


def t_reach_check_passes_when_orphan_declared():
    d = _repo_with_diff(
        {"markers/ttl.txt": "1", "bench/run.py": "path = 'markers/ttl.txt'"},
        [("markers/ttl.txt", None)])
    try:
        bad = gates.reach_check(
            d, "## Reach\nmarkers/ttl.txt is still read by bench/run.py; "
               "handled in this PR.\n",
            base="origin/main")
        assert bad == [], bad
    finally:
        shutil.rmtree(d)


def t_reach_check_passes_trivially_with_no_deletions():
    d = _repo_with_diff({"a.txt": "hello"}, [("a.txt", "hello world")])
    try:
        assert gates.reach_check(d, "## Reach\nNone.\n", base="origin/main") == []
    finally:
        shutil.rmtree(d)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
