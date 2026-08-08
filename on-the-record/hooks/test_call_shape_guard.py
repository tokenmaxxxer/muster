"""Tests for call-shape-guard.sh (issue #419 checks ported per issue #512)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "call-shape-guard.sh"


def _run(tool_input, tool_name="Write", cwd=None):
    payload = json.dumps({
        "tool_name": tool_name,
        "tool_input": tool_input,
        "cwd": str(cwd) if cwd else os.getcwd(),
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def _init_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    return tmp_path


def _commit(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    subprocess.run(["git", "-C", str(repo), "add", rel], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "x"], check=True)


def t_non_py_write_is_ignored(tmp_path):
    repo = _init_repo(tmp_path)
    r = _run({"file_path": str(repo / "foo.txt"), "content": "hi"}, cwd=repo)
    assert r.returncode == 0


def t_divergent_flag_shape_is_denied(tmp_path):
    repo = _init_repo(tmp_path)
    _commit(repo, "a.py",
            'import subprocess\n'
            'subprocess.run(["gh", "api", "-X", "POST"])\n')
    r = _run({"file_path": str(repo / "b.py"),
              "content": 'import subprocess\n'
                         'subprocess.run(["gh", "api"])\n'},
             cwd=repo)
    assert r.returncode == 2
    assert "gh api" in r.stderr


def t_matching_flag_shape_passes(tmp_path):
    repo = _init_repo(tmp_path)
    _commit(repo, "a.py",
            'import subprocess\n'
            'subprocess.run(["gh", "api", "-X", "POST"])\n')
    r = _run({"file_path": str(repo / "b.py"),
              "content": 'import subprocess\n'
                         'subprocess.run(["gh", "api", "-X", "POST"])\n'},
             cwd=repo)
    assert r.returncode == 0


def t_sibling_marker_unmentioned_in_record_is_denied(tmp_path):
    repo = _init_repo(tmp_path)
    _commit(repo, "docs/issue-999/reports/implementation.md",
            "## Siblings\n\nnothing here\n")
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "-b",
                    "issue-999/implementation"], check=True)
    r = _run({"file_path": str(repo / "foo.py"),
              "content": "# sibling: bar\ndef foo():\n    pass\n"},
             cwd=repo)
    assert r.returncode == 2
    assert "issue #419" in r.stderr


def t_sibling_marker_mentioned_in_record_passes(tmp_path):
    repo = _init_repo(tmp_path)
    _commit(repo, "docs/issue-999/reports/implementation.md",
            "## Siblings\n\nfoo mirrors bar.\n")
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "-b",
                    "issue-999/implementation"], check=True)
    r = _run({"file_path": str(repo / "foo.py"),
              "content": "# sibling: bar\ndef foo():\n    pass\n"},
             cwd=repo)
    assert r.returncode == 0


def t_no_record_file_is_noop(tmp_path):
    repo = _init_repo(tmp_path)
    _commit(repo, "README.md", "x")
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "-b",
                    "issue-999/implementation"], check=True)
    r = _run({"file_path": str(repo / "foo.py"),
              "content": "# sibling: bar\ndef foo():\n    pass\n"},
             cwd=repo)
    assert r.returncode == 0
