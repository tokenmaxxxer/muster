#!/usr/bin/env python3
"""issue #511 — impact-guard.sh: batch-approval blocking path, live-fired.

A synthetic non-marketplace TARGET repo (a bare tmp dir, no
on-the-record checkout of its own — requirement 7) with a `docs/proposals/`
holding a high-reversibility `status: proposed` proposal. The real hook
script is invoked exactly as the `PreToolUse`/`Bash` matcher would invoke
it, against a Bash command batching two `gh pr merge` calls:

1. RED: the batch is denied (exit 2) — the blocking path is wired.
2. GREEN (wiring reverted via the hook's own ORCHESTRATE_OFF kill
   switch): the same batch is allowed (exit 0) — proves the RED result
   came from the wiring actually running, not a vacuous always-deny.
3. A single `gh pr merge` against the same TARGET (not a batch) is
   allowed even with the high-impact proposal still open — proves the
   gate is on *batching*, not a blanket block.
4. A batch of only low-reversibility proposals is allowed.

  python3 on-the-record/hooks/test_impact_guard.py
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "on-the-record" / "hooks" / "impact-guard.sh"


def _run(target: Path, command: str, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    env = dict(os.environ)
    env["TOKENMAXXXER_CHECKOUT"] = str(ROOT)
    env.pop("CLAUDE_ROLE", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(["bash", str(SCRIPT)], cwd=target, input=payload,
                           capture_output=True, text=True, env=env)


def _write_proposal(target: Path, name: str, files: list[str]) -> None:
    proposals = target / "docs" / "proposals"
    proposals.mkdir(parents=True, exist_ok=True)
    body = "---\nstatus: proposed\nfiles:\n" + "".join(f"  - {f}\n" for f in files) + "---\n"
    (proposals / name).write_text(body)


BATCH_CMD = "gh pr merge 101 --squash && gh pr merge 102 --squash"
SINGLE_CMD = "gh pr merge 101 --squash"


def t_batch_with_high_impact_proposal_is_denied(tmp_path: Path):
    target = tmp_path / "target-red"
    target.mkdir()
    _write_proposal(target, "a.md", ["on-the-record/hooks/new-hook.sh"])
    r = _run(target, BATCH_CMD)
    assert r.returncode == 2, f"expected deny (2), got {r.returncode}: {r.stderr}"
    assert "requires individual approval" in r.stderr or "impact-guard" in r.stderr


def t_kill_switch_reverts_the_wiring_and_allows_the_same_batch(tmp_path: Path):
    target = tmp_path / "target-green"
    target.mkdir()
    _write_proposal(target, "a.md", ["on-the-record/hooks/new-hook.sh"])
    r = _run(target, BATCH_CMD, extra_env={"ORCHESTRATE_OFF": "1"})
    assert r.returncode == 0, f"expected allow (0) with wiring off, got {r.returncode}: {r.stderr}"


def t_single_merge_is_not_treated_as_a_batch(tmp_path: Path):
    target = tmp_path / "target-single"
    target.mkdir()
    _write_proposal(target, "a.md", ["on-the-record/hooks/new-hook.sh"])
    r = _run(target, SINGLE_CMD)
    assert r.returncode == 0, f"single merge should pass through, got {r.returncode}: {r.stderr}"


def t_batch_of_only_low_impact_proposals_is_allowed(tmp_path: Path):
    target = tmp_path / "target-low"
    target.mkdir()
    _write_proposal(target, "a.md", ["docs/issue-999/proposals/unused.md"])
    r = _run(target, BATCH_CMD)
    assert r.returncode == 0, f"expected allow (0), got {r.returncode}: {r.stderr}"


if __name__ == "__main__":
    import tempfile
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        with tempfile.TemporaryDirectory() as td:
            t(Path(td))
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
