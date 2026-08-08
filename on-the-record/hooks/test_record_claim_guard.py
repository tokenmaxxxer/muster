"""Tests for record-claim-guard.sh (issue #457 Group A+B porting)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "record-claim-guard.sh"


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


def _record_path(tmp_path):
    p = tmp_path / "docs" / "issue-999" / "reports" / "implementation.md"
    p.parent.mkdir(parents=True)
    return p


def t_non_record_path_is_ignored(tmp_path):
    r = _run({"file_path": str(tmp_path / "src" / "foo.py"),
              "content": "count: 5 of 10 items with no derivation"})
    assert r.returncode == 0


def t_unverifiable_without_reason_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "content": "unverifiable:\n"})
    assert r.returncode == 2
    assert "issue #310" in r.stderr


def t_unverifiable_with_reason_passes(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "unverifiable: this is a subjective UX judgment.\n"})
    assert r.returncode == 0


def t_checked_unverifiable_without_reason_is_denied(tmp_path):
    p = _record_path(tmp_path)
    line = "- did the thing — checked: test/foo.py::t_x — result: unverifiable\n"
    r = _run({"file_path": str(p), "content": line})
    assert r.returncode == 2
    assert "issue #331" in r.stderr


def t_bare_count_claim_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "content": "25 of 107 works are done.\n"})
    assert r.returncode == 2
    assert "issue #333" in r.stderr


def t_derived_count_claim_passes(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "25 of 107 `derived: pytest -q` works are done.\n"})
    assert r.returncode == 0


def t_count_inside_fence_is_ignored(tmp_path):
    p = _record_path(tmp_path)
    content = "```\n25 of 107 passed\n```\n"
    r = _run({"file_path": str(p), "content": content})
    assert r.returncode == 0


def t_bare_test_count_claim_is_denied(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "We ran 38 tests passing with no failures.\n"})
    assert r.returncode == 2
    assert "issue #333" in r.stderr


def t_orphaned_path_reference_is_denied(tmp_path):
    (tmp_path / ".git").mkdir()
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "See `src/does_not_exist.py` for details.\n"},
             cwd=tmp_path)
    assert r.returncode == 2
    assert "issue #330" in r.stderr


def t_existing_path_reference_passes(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "real.py").write_text("x = 1\n")
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p),
              "content": "See `src/real.py` for details.\n"},
             cwd=tmp_path)
    assert r.returncode == 0


def t_malformed_payload_is_allowed_not_denied(tmp_path):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    r = subprocess.run(["bash", str(GUARD)], input="not json",
                        capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 0


def t_edit_tool_uses_new_string(tmp_path):
    p = _record_path(tmp_path)
    r = _run({"file_path": str(p), "old_string": "x", "new_string": "5 of 9 tests"},
             tool_name="Edit")
    assert r.returncode == 2
    assert "issue #333" in r.stderr
