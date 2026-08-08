#!/usr/bin/env python3
"""issue-471 (Batch A) / issue-390 — PR 의 green 은 검증 당시 상태를
증언하지 실제로 랜딩되는 상태를 증언하지 않는다. 이 파일은 그 격차를 잡는
자기완결형(synthetic git) 회귀 테스트다: `main` 쪽에서 함수 arity 를 바꾸고
그 이전 커밋 위에서 딴 `branch` 쪽은 옛 arity 로 그 함수를 계속 호출한다 —
branch 단독으로 돌리면 통과하지만, merge-tree(실제 랜딩 상태)로 돌리면
`TypeError` 로 실패해야 한다.

이슈-467 ADR 표의 배치 A 행: standalone, `gates/ci.py` 의 `closes-gate` 잡에
배선하지 않는다(GitHub Actions 를 통한 CI 는 은퇴됨 — 이 파일을 로컬에서
직접 돌리는 것이 전달 경로다).

커버리지(#390 이 명명한 3가지 형태 중): stale-base — 잡음. wrong-environment
— 이 메커니즘으로는 안 잡힘(별도 환경 재현이 필요, 범위 밖). mocked-boundary
— 기계적으로 도달 불가(이 저장소에는 그 형태를 재현할 공통 목 경계가 없다),
암시하지 않고 명시적으로 안 잡힌다고 기록한다.

  python3 gates/test_merge_state_gate.py
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path


def _git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
        env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "PATH": "/usr/bin:/bin"},
    )


def _run_py(cwd, script):
    return subprocess.run(
        [sys.executable, script], cwd=cwd, capture_output=True, text=True,
    )


def _build_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")

    (repo / "lib.py").write_text("def f(x):\n    return x\n", encoding="utf-8")
    (repo / "caller.py").write_text(
        "from lib import f\n"
        "def run():\n"
        "    return f(1)\n"
        "if __name__ == '__main__':\n"
        "    run()\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")

    _git(repo, "checkout", "-q", "-b", "branch")
    _git(repo, "checkout", "-q", "main" if _has_main(repo) else "master")

    # main-side: only lib.py's arity changes — caller.py untouched on main.
    (repo / "lib.py").write_text("def f(x, y):\n    return x + y\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "main: change f arity")

    # branch-side: only caller.py touched (unrelated edit), still calls the
    # old one-arg f — based on the pre-arity-change commit, so its diff
    # never conflicts with main's lib.py change and the merge auto-combines
    # branch's stale caller.py with main's new lib.py.
    _git(repo, "checkout", "-q", "branch")
    (repo / "caller.py").write_text(
        "from lib import f\n"
        "# unrelated branch-side comment\n"
        "def run():\n"
        "    return f(1)\n"
        "if __name__ == '__main__':\n"
        "    run()\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "branch: unrelated caller.py edit, stale base")

    return repo


def _has_main(repo: Path) -> bool:
    out = subprocess.run(
        ["git", "branch", "--list", "main"], cwd=repo, capture_output=True, text=True,
    ).stdout
    return bool(out.strip())


def t_branch_alone_passes():
    with tempfile.TemporaryDirectory() as d:
        repo = _build_repo(Path(d))
        _git(repo, "checkout", "-q", "branch")
        result = _run_py(repo, "caller.py")
        assert result.returncode == 0, (
            f"branch 단독 실행이 실패했다(테스트 픽스처 오류): {result.stderr}"
        )


def t_merge_tree_fails_with_stale_base_arity_error():
    with tempfile.TemporaryDirectory() as d:
        repo = _build_repo(Path(d))
        base_branch = "main" if _has_main(repo) else "master"
        _git(repo, "checkout", "-q", "-b", "merge-tree", base_branch)
        merge = subprocess.run(
            ["git", "merge", "-q", "--no-edit", "branch"],
            cwd=repo, capture_output=True, text=True,
        )
        assert merge.returncode == 0, f"merge 자체가 충돌났다(픽스처 오류): {merge.stderr}"
        result = _run_py(repo, "caller.py")
        assert result.returncode != 0, (
            "merge-tree 실행이 통과했다 — stale-base arity 불일치를 못 잡았다."
        )
        assert "TypeError" in result.stderr, result.stderr


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
    sys.exit(0)
