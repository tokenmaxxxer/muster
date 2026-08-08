"""Tests for accumulation-claim-guard.sh (issue #424 check ported per issue #512)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "accumulation-claim-guard.sh"


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


_SHAPE_1_CONTENT = (
    'import subprocess\n'
    'subprocess.run(["a"])\n'
    'subprocess.run(["b"])\n'
    'subprocess.run(["c"])\n'
)


def t_non_shape_write_is_ignored(tmp_path):
    repo = _init_repo(tmp_path)
    r = _run({"file_path": str(repo / "foo.py"), "content": "x = 1\n"}, cwd=repo)
    assert r.returncode == 0


def t_shape1_with_no_proposal_on_disk_is_noop(tmp_path):
    repo = _init_repo(tmp_path)
    r = _run({"file_path": str(repo / "foo.py"), "content": _SHAPE_1_CONTENT},
              cwd=repo)
    assert r.returncode == 0


def t_shape1_with_unfilled_accumulation_is_denied(tmp_path):
    repo = _init_repo(tmp_path)
    _commit(repo, "docs/issue-999/proposals/x.md",
            "files:\n  - foo.py\n\n## Accumulation\n\n## Out of scope\n")
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "-b",
                    "issue-999/implementation"], check=True)
    r = _run({"file_path": str(repo / "foo.py"), "content": _SHAPE_1_CONTENT},
              cwd=repo)
    assert r.returncode == 2
    assert "issue #424" in r.stderr


def t_shape1_with_filled_accumulation_passes(tmp_path):
    repo = _init_repo(tmp_path)
    _commit(repo, "docs/issue-999/proposals/x.md",
            "files:\n  - foo.py\n\n## Accumulation\n\nAt N=10 sites this needs "
            "a shared helper.\n\n## Out of scope\n")
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "-b",
                    "issue-999/implementation"], check=True)
    r = _run({"file_path": str(repo / "foo.py"), "content": _SHAPE_1_CONTENT},
              cwd=repo)
    assert r.returncode == 0


def t_shape5_roles_json_with_unfilled_accumulation_is_denied(tmp_path):
    repo = _init_repo(tmp_path)
    _commit(repo, "docs/issue-999/proposals/x.md",
            "files:\n  - roles/foo.json\n\n## Accumulation\n\n## Out of scope\n")
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "-b",
                    "issue-999/implementation"], check=True)
    r = _run({"file_path": str(repo / "roles" / "foo.json"), "content": "{}"},
              cwd=repo)
    assert r.returncode == 0  # not a .py write — this hook only fires on .py


def t_empty_repo_git_ls_files_does_not_crash(tmp_path):
    repo = _init_repo(tmp_path)
    r = _run({"file_path": str(repo / "foo.py"), "content": "x = 1\n"}, cwd=repo)
    assert r.returncode == 0
