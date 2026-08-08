#!/usr/bin/env python3
"""issue #419 — `subprocess_call_shape_divergence`/`sibling_mention_check`
단위테스트.

파일명 참고: #419 proposal 은 `gates/test_gates.py`를 지정했지만, 그 이름
자체가 이미 배달된 `duplicate_test_basenames` 게이트(#398)가 잡는 충돌
모양(루트 `test_gates.py`와 베이스네임 충돌)이라 이 이슈의 delivery
(issue-474)가 스스로 그 게이트를 실패시키게 된다 — `test_duplicate_test_basenames.py`
가 같은 이유로 리네임된 전례를 따라 `test_recurrence.py`로 붙였다. 자세한
근거는 `docs/issue-474/reports/implementation.md`의
"Rationale for deviations".

네트워크 없이, 임시 git 저장소 위에서 돈다.

  python3 gates/test_recurrence.py
"""
from __future__ import annotations
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates


def _git(*args, cwd):
    p = subprocess.run(["git", "-C", str(cwd), *args],
                       capture_output=True, text=True)
    assert p.returncode == 0, (args, p.stdout, p.stderr)
    return p.stdout


def _git_repo(files: dict[str, str]) -> Path:
    """`subprocess_call_shape_divergence` 처럼 전-트리를 훑는 검사엔 커밋
    하나로 충분하다."""
    d = Path(tempfile.mkdtemp())
    _git("init", "-q", cwd=d)
    _git("config", "user.email", "t@example.com", cwd=d)
    _git("config", "user.name", "t", cwd=d)
    for path, content in files.items():
        f = d / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
    _git("add", "-A", cwd=d)
    _git("commit", "-q", "-m", "init", cwd=d)
    return d


def _git_repo_with_diff(base_files: dict[str, str], head_ops):
    """`sibling_mention_check` 처럼 `changed_files()`(origin/main...HEAD diff)
    를 쓰는 검사용 — `test_orphaned_references.py` 의 관례를 그대로 재사용."""
    d = Path(tempfile.mkdtemp())
    _git("init", "-q", "-b", "main", cwd=d)
    _git("config", "user.email", "t@example.com", cwd=d)
    _git("config", "user.name", "t", cwd=d)
    for path, content in base_files.items():
        (d / path).parent.mkdir(parents=True, exist_ok=True)
        (d / path).write_text(content)
    _git("add", "-A", cwd=d)
    _git("commit", "-q", "-m", "base", cwd=d)
    _git("update-ref", "refs/remotes/origin/main", "HEAD", cwd=d)
    _git("checkout", "-q", "-b", "issue-419/implementation", cwd=d)
    for path, content in head_ops:
        p = d / path
        if content is None:
            p.unlink()
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
    _git("add", "-A", cwd=d)
    _git("commit", "-q", "-m", "head", cwd=d)
    return d


def t_subprocess_call_shape_divergence_flags_388_shape():
    d = _git_repo({
        "a.py": (
            "import subprocess\n"
            "subprocess.run(['gh', 'api', '-f', 'x=1'])\n"
        ),
        "b.py": (
            "import subprocess\n"
            "subprocess.run(['gh', 'api', '-X', 'GET'])\n"
        ),
    })
    try:
        bad = gates.subprocess_call_shape_divergence(d)
        assert bad, "diverging flag sets across gh api call sites must flag"
    finally:
        shutil.rmtree(d)


def t_subprocess_call_shape_divergence_passes_on_identical_flag_sets():
    d = _git_repo({
        "a.py": (
            "import subprocess\n"
            "subprocess.run(['gh', 'api', '-X', 'GET'])\n"
        ),
        "b.py": (
            "import subprocess\n"
            "subprocess.run(['gh', 'api', '-X', 'GET'])\n"
        ),
    })
    try:
        assert gates.subprocess_call_shape_divergence(d) == []
    finally:
        shutil.rmtree(d)


def t_sibling_mention_check_passes_when_mentioned():
    d = _git_repo_with_diff(
        {"README.md": "x\n"},
        [("spawn.py", "# sibling: core_version\ndef core_root():\n    pass\n")])
    try:
        bad = gates.sibling_mention_check(d, "## Siblings\ncore_root is unaffected.\n")
        assert bad == [], bad
    finally:
        shutil.rmtree(d)


def t_sibling_mention_check_fails_when_unmentioned():
    d = _git_repo_with_diff(
        {"README.md": "x\n"},
        [("spawn.py", "# sibling: core_version\ndef core_root():\n    pass\n")])
    try:
        bad = gates.sibling_mention_check(d, "## Siblings\nNone.\n")
        assert bad, "marked-and-unmentioned sibling must fail"
    finally:
        shutil.rmtree(d)


def t_sibling_mention_check_returns_empty_with_no_marker():
    d = _git_repo_with_diff(
        {"README.md": "x\n"},
        [("spawn.py", "def core_root():\n    pass\n")])
    try:
        assert gates.sibling_mention_check(d, "## Siblings\nNone.\n") == []
    finally:
        shutil.rmtree(d)


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("t_") and callable(f)]
    _run(tests)
