"""Issue #445 — reproduction scripts for the phase-2 attempt list in
docs/issue-445/proposals/2026-08-08-spawn-path-silent-failure-hunt.md.

Each test is one attempt from that list. A `reproduced` outcome asserts the
failure-mode claim directly; a `not-reproduced` outcome asserts the disproof
(the notice/bound the attempt looked for turns out to be present).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn  # noqa: E402


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def origin_and_src(tmp_path):
    """A bare 'origin' repo plus a working checkout (src) that clones from it,
    reachable with no network — mirrors the local-clone shape issue_workspace()
    drives."""
    origin = tmp_path / "origin.git"
    origin.mkdir()
    _git("init", "-q", "--bare", cwd=origin)

    seed = tmp_path / "seed"
    seed.mkdir()
    _git("init", "-q", cwd=seed)
    _git("config", "user.email", "t@t.t", cwd=seed)
    _git("config", "user.name", "t", cwd=seed)
    (seed / "f.txt").write_text("x")
    _git("add", "f.txt", cwd=seed)
    _git("commit", "-q", "-m", "seed", cwd=seed)
    _git("push", "-q", str(origin), "HEAD:main", cwd=seed)

    src = tmp_path / "src"
    _git("clone", "-q", str(origin), str(src), cwd=tmp_path)
    _git("config", "user.email", "t@t.t", cwd=src)
    _git("config", "user.name", "t", cwd=src)
    return origin, src


def test_attempt_1_exclude_write_swallowed_no_warning(tmp_path, origin_and_src, monkeypatch, capsys):
    """Attempt 1 (proposal item 1, fixed per issue #450): force the
    `.git/info/exclude` write in issue_workspace() to fail with OSError and
    confirm the function still returns a workspace with the credential-leak
    guard skipped, but now surfaces a warning naming the workspace and the
    skipped entries on stderr."""
    origin, src = origin_and_src
    work_base = tmp_path / "work"
    monkeypatch.setenv("MUSTER_WORK_DIR", str(work_base))
    monkeypatch.setenv("MUSTER_KEEP_SSH", "1")  # keep the local file:// origin untouched

    real_open = Path.open

    def failing_open(self, mode="r", *a, **kw):
        if self.name == "exclude" and self.parent.name == "info" and "a" in mode:
            raise OSError(13, "Permission denied (simulated)")
        return real_open(self, mode, *a, **kw)

    monkeypatch.setattr(Path, "open", failing_open)

    work = spawn.issue_workspace(str(src), issue=99999, role="probe")

    captured = capsys.readouterr()
    exclude_path = Path(work) / ".git" / "info" / "exclude"
    exclude_text = exclude_path.read_text() if exclude_path.exists() else ""

    # The guard's own entries (issue #289 H1) never landed...
    assert ".mcp.json" not in exclude_text
    assert ".gitconfig" not in exclude_text
    # ...but the caller is now told the guard didn't take.
    assert str(work) in captured.err
    assert ".mcp.json" in captured.err
    # FIXED: issue_workspace() still returns a workspace (no sys.exit, no
    # exception), but the skipped credential-exclude guard is now surfaced
    # as a warning on stderr naming the workspace and the missing entries.


def test_attempt_2_follow_loop_unbounded_on_absent_roster_entry(tmp_path, monkeypatch):
    """Attempt 2 (proposal item 2), updated by the issue-451 fix: with a
    workspace-index entry registered but no matching roster entry (simulated
    crash-before-registration) and no events ever appearing, the real
    `_watch(follow=True)` loop must now bound its wait via the cumulative
    stall tracker (spawn.py:2199-2242) instead of re-polling forever."""
    monkeypatch.setattr(spawn, "WORKSPACE_INDEX", tmp_path / "workspaces.json")

    work = tmp_path / "work"
    log_path = tmp_path / "session.log"
    log_path.write_text("hello\n")
    spawn._workspace_index_put(99999, "probe", str(work), str(log_path))

    monkeypatch.setattr(spawn, "_roster_load", lambda: {})  # no roster entry, ever

    STALL_S = 0.05  # keep the real bound fast for the test
    rc = spawn._watch(99999, "probe", STALL_S / 60, follow=True)

    # FIXED: the loop no longer spins forever — the cumulative-elapsed-since
    # -last-progress tracker times it out and returns a stall report, the
    # same way `_await_bounded()` already does for a single call.
    assert rc == 0


def test_attempt_3_doctor_reprobe_prints_pre_charge_notice(tmp_path, monkeypatch, capsys):
    """Attempt 3 (proposal item 3): drive require_doctor() with a version
    that does not match the stored runs/doctor-ok version, and check whether
    a live billed doctor() probe fires with no notice distinguishable from
    a routine spawn."""
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "doctor-ok").write_text("1.0.0")
    monkeypatch.setattr(spawn, "ROOT", tmp_path)

    called = {}

    def fake_doctor():
        called["ran"] = True
        return 1  # fail fast; we only care whether it's invoked + whether a notice preceded it

    monkeypatch.setattr(spawn, "doctor", fake_doctor)
    monkeypatch.setattr(spawn, "_claude_version", lambda: "2.0.0")

    # version=None: the auto-detect path that live-probes silently inside a
    # routine (non-`doctor`) spawn call — the explicit-version path (used by
    # tests/callers who already know the version) stops instead of probing.
    with pytest.raises(SystemExit):
        spawn.require_doctor(version=None)

    captured = capsys.readouterr()
    assert called.get("ran") is True
    # NOT REPRODUCED: a pre-charge notice IS printed before the billed probe
    # runs, naming both the cost and that a real session is about to launch.
    assert "실 세션 1회" in captured.err
    assert "소액 과금" in captured.err


def test_attempt_4_bundling_gate_is_documented_comment_only(tmp_path):
    """Attempt 4 (proposal item 4): trace whether issue-bundling-gate's
    workflow only ever posts a comment (never blocks a PR/merge), and
    whether that's a hidden defect or documented, intentional scope."""
    workflow = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "issue-bundling-gate.yml"
    text = workflow.read_text()
    assert "issues:\n    types: [opened]" in text or "types: [opened]" in text
    # NOT REPRODUCED as a silent/hidden defect: the workflow's own header
    # comment states plainly that GitHub Actions cannot block issue
    # creation, that posting a comment is the closest enforcement point for
    # an issues:opened event, and that branch-protection required-check
    # registration doesn't apply because there's no PR to block at this
    # trigger. The comment-only behavior is documented, not decorative.
    assert "GitHub Actions는 이슈" in text
    assert "생성 자체를 막을 수 없다" in text
