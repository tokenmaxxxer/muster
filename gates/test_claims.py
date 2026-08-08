#!/usr/bin/env python3
"""issue-377 — stale-description claim checker unit tests.

  python3 -m pytest gates/test_claims.py
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import claims


def _init_repo(tmp: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp)], check=True)
    subprocess.run(["git", "-C", str(tmp), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(tmp), "config", "user.name", "t"], check=True)
    return tmp


def _commit_all(tmp: Path):
    subprocess.run(["git", "-C", str(tmp), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp), "commit", "-q", "-m", "t"], check=True)


def t_enum_subset_pass():
    with tempfile.TemporaryDirectory() as t:
        tmp = _init_repo(Path(t))
        (tmp / "roles.json").write_text(
            '{"record_fields": {"loop_state": ["open", "closed"]}}',
            encoding="utf-8")
        recdir = tmp / "docs" / "issue-1" / "reports"
        recdir.mkdir(parents=True)
        (recdir / "implementation.md").write_text(
            "---\nloop_state: open\n---\nbody\n", encoding="utf-8")
        (tmp / "marker.py").write_text(
            "# CLAIM-CHECK: enum-subset roles.json:record_fields.loop_state "
            "docs/issue-*/reports/*.md:loop_state\n", encoding="utf-8")
        _commit_all(tmp)
        assert claims.check_claims(tmp) == []


def t_enum_subset_fail_on_drift():
    with tempfile.TemporaryDirectory() as t:
        tmp = _init_repo(Path(t))
        (tmp / "roles.json").write_text(
            '{"record_fields": {"loop_state": ["open", "closed"]}}',
            encoding="utf-8")
        recdir = tmp / "docs" / "issue-1" / "reports"
        recdir.mkdir(parents=True)
        (recdir / "implementation.md").write_text(
            "---\nloop_state: drifted-value\n---\nbody\n", encoding="utf-8")
        (tmp / "marker.py").write_text(
            "# CLAIM-CHECK: enum-subset roles.json:record_fields.loop_state "
            "docs/issue-*/reports/*.md:loop_state\n", encoding="utf-8")
        _commit_all(tmp)
        bad = claims.check_claims(tmp)
        assert any("drifted-value" in b for b in bad), bad


def t_producer_exists_pass():
    with tempfile.TemporaryDirectory() as t:
        tmp = _init_repo(Path(t))
        (tmp / "spec.md").write_text("x", encoding="utf-8")
        (tmp / "marker.py").write_text(
            "# CLAIM-CHECK: producer-exists spec.md\n", encoding="utf-8")
        _commit_all(tmp)
        assert claims.check_claims(tmp) == []


def t_producer_exists_fail_when_missing():
    with tempfile.TemporaryDirectory() as t:
        tmp = _init_repo(Path(t))
        (tmp / "marker.py").write_text(
            "# CLAIM-CHECK: producer-exists nonexistent.md\n", encoding="utf-8")
        _commit_all(tmp)
        bad = claims.check_claims(tmp)
        assert any("nonexistent.md" in b for b in bad), bad


def t_producer_exists_ignores_gitignored_runs_dir():
    # issue #529 — a copy under runs/ (gitignored session checkout) must
    # not satisfy producer-exists; the same filename outside runs/ still
    # does.
    with tempfile.TemporaryDirectory() as t:
        tmp = _init_repo(Path(t))
        (tmp / ".gitignore").write_text("runs/\n", encoding="utf-8")
        (tmp / "marker.py").write_text(
            "# CLAIM-CHECK: producer-exists spec.md\n", encoding="utf-8")
        runs_dir = tmp / "runs" / "rulebooks" / "checkout"
        runs_dir.mkdir(parents=True)
        (runs_dir / "spec.md").write_text("x", encoding="utf-8")
        _commit_all(tmp)
        bad = claims.check_claims(tmp)
        assert any("spec.md" in b for b in bad), bad

        (tmp / "spec.md").write_text("x", encoding="utf-8")
        assert claims.check_claims(tmp) == []


def t_producer_exists_no_runs_dir_behaves_identically():
    with tempfile.TemporaryDirectory() as t:
        tmp = _init_repo(Path(t))
        (tmp / ".gitignore").write_text("runs/\n", encoding="utf-8")
        (tmp / "marker.py").write_text(
            "# CLAIM-CHECK: producer-exists nonexistent.md\n", encoding="utf-8")
        _commit_all(tmp)
        bad = claims.check_claims(tmp)
        assert any("nonexistent.md" in b for b in bad), bad


def t_malformed_kind_fails_closed():
    with tempfile.TemporaryDirectory() as t:
        tmp = _init_repo(Path(t))
        (tmp / "marker.py").write_text(
            "# CLAIM-CHECK: bogus-kind whatever\n", encoding="utf-8")
        _commit_all(tmp)
        bad = claims.check_claims(tmp)
        assert any("bogus-kind" in b for b in bad), bad


def t_no_markers_is_clean():
    with tempfile.TemporaryDirectory() as t:
        tmp = _init_repo(Path(t))
        (tmp / "a.py").write_text("x = 1\n", encoding="utf-8")
        _commit_all(tmp)
        assert claims.check_claims(tmp) == []


def t_actual_tree_two_markers_land_and_are_evaluable():
    root = Path(__file__).resolve().parent.parent
    markers = subprocess.run(
        ["git", "-C", str(root), "grep", "-c", "CLAIM-CHECK:"],
        capture_output=True, text=True)
    assert "gates/gates.py" in markers.stdout
    bad = claims.check_claims(root)
    assert isinstance(bad, list)


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
