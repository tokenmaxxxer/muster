"""Tests for retry-loop-bound.sh (issue #507).

Fixture shape reconstructs the issue-474 identical-retry log cited by
#505's mining (docs/issue-505/reports/implementation.md:26-27,47-70) --
25 identical board-gate.sh R4 refusals of a `docs/issue-416/...` write
from an `issue-474/implementation` session -- using board-gate.sh:512's
exact message template (`docs/issue-507/reports/implementation/survey.md`
confirms the template text by direct read; no raw .log file is available
in this checkout to replay).

Red baseline (pre-hook, undocumented before this change): nothing bounds
the loop -- the hook did not exist, so a `pre` payload after any number
of identical `post` denials produced no output and no abort; the 25th
(or 52nd) identical retry proceeded exactly like the 1st. Green (this
file): the K-th identical denial's next attempt carries
`additionalContext`, the 2K-th is denied outright.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "retry-loop-bound.sh"

SESSION = "sess-issue474"
TOOL = "Write"
TARGET = "docs/issue-416/reports/implementation.md"

DENY_REASON = (
    "writing docs/issue-416/ requires branch issue-474/implementation "
    "(current: issue-474/implementation). Every role writes its own "
    "board only from its own issue branch -- never a direct write from "
    "another branch. (contract v3 s10)"
)
DENY_TOOL_RESPONSE = (
    "PreToolUse:Write hook error: [board-gate.sh: refused — " + DENY_REASON + "]"
)


def _run(payload, state_dir, k=5):
    env = dict(os.environ)
    env["OTR_RETRY_BOUND_STATE_DIR"] = str(state_dir)
    env["OTR_RETRY_BOUND_K"] = str(k)
    env.pop("CLAUDE_ROLE", None)
    env["ORCHESTRATE_OFF"] = ""
    mode = payload.pop("_mode")
    return subprocess.run(
        ["bash", str(HOOK), mode],
        input=json.dumps(payload), capture_output=True, text=True, env=env,
        timeout=20,
    )


def _post(state_dir, target=TARGET, k=5):
    return _run(
        {
            "_mode": "post",
            "session_id": SESSION,
            "tool_name": TOOL,
            "tool_input": {"file_path": target},
            "tool_response": DENY_TOOL_RESPONSE,
        },
        state_dir, k,
    )


def _pre(state_dir, target=TARGET, k=5):
    return _run(
        {
            "_mode": "pre",
            "session_id": SESSION,
            "tool_name": TOOL,
            "tool_input": {"file_path": target},
        },
        state_dir, k,
    )


def t_zero_denials_pre_is_silent():
    with tempfile.TemporaryDirectory() as td:
        r = _pre(td)
        assert r.returncode == 0
        assert r.stdout == ""


def t_below_k_denials_pre_is_silent():
    with tempfile.TemporaryDirectory() as td:
        for _ in range(4):
            assert _post(td, k=5).returncode == 0
        r = _pre(td, k=5)
        assert r.returncode == 0
        assert r.stdout == ""


def t_kth_denial_triggers_corrective_context():
    with tempfile.TemporaryDirectory() as td:
        for _ in range(5):
            assert _post(td, k=5).returncode == 0
        r = _pre(td, k=5)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "denied 5 times" in ctx
        assert "requires branch issue-474/implementation" in ctx


def t_25_identical_denials_issue_474_shape_aborts_at_2k():
    """Reproduces #505's issue-474 citation: 25 identical R4 refusals."""
    with tempfile.TemporaryDirectory() as td:
        k = 5
        nudged = False
        for i in range(1, 26):
            assert _post(td, k=k).returncode == 0
            r = _pre(td, k=k)
            if i >= 2 * k:
                assert r.returncode == 2, "expected abort by denial #%d" % i
                assert "aborted" in r.stderr
                assert str(i if i == 2 * k else 2 * k) in r.stderr or (
                    "denied" in r.stderr
                )
            elif i >= k:
                assert r.returncode == 0
                nudged = True
        assert nudged


def t_non_identical_denials_never_trip_threshold():
    with tempfile.TemporaryDirectory() as td:
        for n in range(10):
            assert _post(td, target="docs/issue-%d/x.md" % n, k=5).returncode == 0
            r = _pre(td, target="docs/issue-%d/x.md" % n, k=5)
            assert r.returncode == 0
            assert r.stdout == ""


def t_2k_denial_is_terminal_deny():
    with tempfile.TemporaryDirectory() as td:
        k = 3
        for _ in range(2 * k):
            assert _post(td, k=k).returncode == 0
        r = _pre(td, k=k)
        assert r.returncode == 2
        assert TARGET in r.stderr


def t_orchestrate_off_is_silent():
    with tempfile.TemporaryDirectory() as td:
        for _ in range(6):
            env_post = dict(os.environ)
            env_post["OTR_RETRY_BOUND_STATE_DIR"] = str(td)
            env_post["OTR_RETRY_BOUND_K"] = "5"
            env_post["ORCHESTRATE_OFF"] = "1"
            env_post.pop("CLAUDE_ROLE", None)
            subprocess.run(
                ["bash", str(HOOK), "post"],
                input=json.dumps({
                    "session_id": SESSION, "tool_name": TOOL,
                    "tool_input": {"file_path": TARGET},
                    "tool_response": DENY_TOOL_RESPONSE,
                }),
                capture_output=True, text=True, env=env_post, timeout=20,
            )
        env_pre = dict(os.environ)
        env_pre["OTR_RETRY_BOUND_STATE_DIR"] = str(td)
        env_pre["OTR_RETRY_BOUND_K"] = "5"
        env_pre["ORCHESTRATE_OFF"] = "1"
        env_pre.pop("CLAUDE_ROLE", None)
        r = subprocess.run(
            ["bash", str(HOOK), "pre"],
            input=json.dumps({
                "session_id": SESSION, "tool_name": TOOL,
                "tool_input": {"file_path": TARGET},
            }),
            capture_output=True, text=True, env=env_pre, timeout=20,
        )
        assert r.returncode == 0
        assert r.stdout == ""
