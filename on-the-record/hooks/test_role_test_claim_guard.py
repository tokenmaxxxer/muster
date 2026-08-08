"""Tests for role-test-claim-guard.sh (issue #457 Group C porting)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "role-test-claim-guard.sh"


def _run(message, role="implementation"):
    payload = json.dumps({"last_assistant_message": message})
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    if role:
        env["CLAUDE_ROLE"] = role
    else:
        env.pop("CLAUDE_ROLE", None)
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def t_orchestrator_session_skipped(tmp_path):
    r = _run("all tests pass\n```\nSKIPPED test_x.py:1: reason\n```", role=None)
    assert r.returncode == 0
    assert r.stdout == ""


def t_no_test_output_is_fine():
    r = _run("Implemented the feature and wrote docs.")
    assert r.returncode == 0


def t_skip_conflated_with_clean_pass_flagged():
    msg = ("모두 통과했습니다.\n```\n"
           "SKIPPED test_x.py:10: dependency missing\n"
           "3 passed\n```")
    r = _run(msg)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert "issue #334" in out["hookSpecificOutput"]["additionalContext"]


def t_skip_acknowledged_is_not_flagged():
    msg = ("2 passed, 1 skipped (dependency missing).\n```\n"
           "SKIPPED test_x.py:10: dependency missing\n"
           "2 passed\n```")
    r = _run(msg)
    assert r.returncode == 0
    assert r.stdout == ""


def t_hand_typed_count_mismatch_flagged():
    msg = "5개가 통과했습니다.\n```\n3 passed\n```"
    r = _run(msg)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert "issue #435" in out["hookSpecificOutput"]["additionalContext"]


def t_hand_typed_count_match_passes():
    msg = "3개가 통과했습니다.\n```\n3 passed\n```"
    r = _run(msg)
    assert r.returncode == 0
    assert r.stdout == ""


def t_malformed_payload_is_allowed():
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env["CLAUDE_ROLE"] = "implementation"
    r = subprocess.run(["bash", str(GUARD)], input="not json",
                        capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 0
