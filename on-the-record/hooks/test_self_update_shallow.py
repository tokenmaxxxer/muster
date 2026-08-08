#!/usr/bin/env python3
"""issue-471 (Batch A) / issue-412 — self-update.sh's shallow-checkout
detection. Plain Python, not bats (survey: no `bats` binary on this
machine, and every existing `on-the-record/hooks/test_*.py` is plain
Python — the project's actual convention).

Builds a local fixture git repo with multiple commits, shallow-clones it,
points self-update.sh at the shallow clone via TOKENMAXXXER_CHECKOUT (which
also makes spawn.py-presence resolution find it directly), runs the hook,
and asserts the `.shallow-check` marker records the unshallow attempt.

  python3 on-the-record/hooks/test_self_update_shallow.py
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
SELF_UPDATE = HOOKS_DIR / "self-update.sh"


def _git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
    )


def _build_source_repo(tmp: Path) -> Path:
    src = tmp / "source"
    src.mkdir()
    _git(src, "init", "-q")
    _git(src, "config", "user.email", "t@t")
    _git(src, "config", "user.name", "t")
    for i in range(3):
        (src / "spawn.py").write_text(f"# rev {i}\n", encoding="utf-8")
        _git(src, "add", "-A")
        _git(src, "commit", "-q", "-m", f"rev {i}")
    return src


def t_shallow_clone_is_detected_and_marker_written():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        src = _build_source_repo(tmp)
        checkout = tmp / "checkout"
        # local clones auto-optimize (hardlink) and can ignore --depth
        # unless the source is addressed as file:// — force the real
        # shallow-clone codepath.
        _git(tmp, "clone", "-q", "--depth", "1", f"file://{src}", str(checkout))
        assert (
            subprocess.run(
                ["git", "-C", str(checkout), "rev-parse", "--is-shallow-repository"],
                capture_output=True, text=True,
            ).stdout.strip() == "true"
        ), "픽스처가 얕은 클론이 아니다."

        marker = checkout / ".shallow-check"
        assert not marker.exists()

        result = subprocess.run(
            ["bash", str(SELF_UPDATE)],
            capture_output=True, text=True,
            env={
                "PATH": "/usr/bin:/bin",
                "TOKENMAXXXER_CHECKOUT": str(checkout),
                "HOME": str(tmp / "home"),
            },
            timeout=30,
        )
        assert result.returncode in (0, 2), (result.returncode, result.stderr)

        assert marker.is_file(), (
            f"{marker} 가 없다 — self-update.sh 가 shallow 상태를 기록하지 않았다."
        )
        content = marker.read_text(encoding="utf-8")
        assert content.startswith("shallow=true"), content
        # source 는 file:// 클론이라 unshallow 가 로컬에서 성공해야 한다.
        assert "unshallow=ok" in content, content
        assert (
            subprocess.run(
                ["git", "-C", str(checkout), "rev-parse", "--is-shallow-repository"],
                capture_output=True, text=True,
            ).stdout.strip() == "false"
        ), "unshallow 성공 후에도 여전히 shallow 로 보고된다."


def t_non_shallow_checkout_records_shallow_false():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        checkout = _build_source_repo(tmp)
        marker = checkout / ".shallow-check"

        result = subprocess.run(
            ["bash", str(SELF_UPDATE)],
            capture_output=True, text=True,
            env={
                "PATH": "/usr/bin:/bin",
                "TOKENMAXXXER_CHECKOUT": str(checkout),
                "HOME": str(tmp / "home"),
            },
            timeout=30,
        )
        assert result.returncode in (0, 2), (result.returncode, result.stderr)
        assert marker.is_file()
        assert marker.read_text(encoding="utf-8").strip() == "shallow=false"


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
