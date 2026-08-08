"""Tests for decision-queue-stopgate.sh (issue #466, carrying #374's design)."""
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "decision-queue-stopgate.sh"


def _fake_checkout(tmp_path, flows_payload):
    """Writes a stub spawn.py at tmp_path that prints flows_payload for
    `flows --json` and points TOKENMAXXXER_CHECKOUT at it."""
    spawn_py = tmp_path / "spawn.py"
    spawn_py.write_text(
        "import sys, json\n"
        "print(json.dumps(" + repr(flows_payload) + "))\n"
    )
    return tmp_path


def _run(flows_payload, role=None, orchestrate_off=""):
    with tempfile.TemporaryDirectory() as td:
        checkout = _fake_checkout(Path(td), flows_payload)
        env = dict(os.environ)
        env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
        env["ORCHESTRATE_OFF"] = orchestrate_off
        if role:
            env["CLAUDE_ROLE"] = role
        else:
            env.pop("CLAUDE_ROLE", None)
        payload = json.dumps({"last_assistant_message": "ok"})
        return subprocess.run(
            ["bash", str(HOOK)],
            input=payload, capture_output=True, text=True, env=env, timeout=20,
        )


def t_empty_queue_is_silent():
    r = _run({"decision_queue": []})
    assert r.returncode == 0
    assert r.stdout == ""


def t_under_1h_item_is_silent():
    r = _run({"decision_queue": [
        {"issue": 100, "pr": 200, "age_hours": 0.5},
    ]})
    assert r.returncode == 0
    assert r.stdout == ""


def t_1h_to_4h_item_gets_additional_context():
    r = _run({"decision_queue": [
        {"issue": 100, "pr": 200, "age_hours": 2.0},
    ]})
    assert r.returncode == 0
    out = json.loads(r.stdout)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "#100" in ctx
    assert "PR#200" in ctx
    assert "2.0h" in ctx


def t_4h_plus_item_blocks():
    r = _run({"decision_queue": [
        {"issue": 100, "pr": 200, "age_hours": 4.5},
    ]})
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["decision"] == "block"
    assert "#100" in out["reason"]
    assert "PR#200" in out["reason"]


def t_mixed_tiers_reports_only_tier2_block():
    r = _run({"decision_queue": [
        {"issue": 1, "pr": 11, "age_hours": 0.2},
        {"issue": 2, "pr": 22, "age_hours": 2.0},
        {"issue": 3, "pr": 33, "age_hours": 5.0},
    ]})
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["decision"] == "block"
    assert "#3" in out["reason"]


def t_orchestrate_off_is_silent():
    r = _run({"decision_queue": [
        {"issue": 100, "pr": 200, "age_hours": 5.0},
    ]}, orchestrate_off="1")
    assert r.returncode == 0
    assert r.stdout == ""


def t_role_session_is_silent():
    r = _run({"decision_queue": [
        {"issue": 100, "pr": 200, "age_hours": 5.0},
    ]}, role="implementation")
    assert r.returncode == 0
    assert r.stdout == ""
