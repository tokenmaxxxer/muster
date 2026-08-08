#!/usr/bin/env python3
"""issue #508 — self-hosted hook wiring: parity pin + live-fire deny test.

Two things are checked:

1. Every command entry in `on-the-record/hooks/hooks.json` has a matching
   entry (same event, same matcher, same script basename) in what
   `spawn.py:role_settings(role, cwd)` actually registers when the spawn
   target `cwd` resolves to on-the-record itself. A hand-copied second
   list drifts; this reads spawn.py's real output, not a restatement.
2. A real `git commit` attempt in a temp clone is DENIED before it lands
   when `spec-index-preflight.sh` (as registered via the self-hosted
   merge) is invoked the way the PreToolUse hook would invoke it, and the
   same attempt SUCCEEDS when the guard is bypassed — a genuine red/green
   pair, not fixture-only.

  python3 gates/test_hooks_parity.py
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import spawn  # noqa: E402

HOOKS_JSON = ROOT / "on-the-record" / "hooks" / "hooks.json"


def _entries(hooks: dict) -> set[tuple[str, str, str]]:
    """(event, matcher, script basename) 삼중항 집합으로 평평하게 편다."""
    out: set[tuple[str, str, str]] = set()
    for event, groups in hooks.items():
        for group in groups:
            matcher = group.get("matcher", "")
            for h in group.get("hooks", []):
                cmd = h.get("command", "")
                out.add((event, matcher, Path(cmd).name))
    return out


def _self_hosted_target(tmp: Path) -> Path:
    """cwd 아래 on-the-record/hooks/hooks.json 이 있는 최소 셀프호스트 레이아웃을
    실제 `on-the-record/hooks/*` 를 복사해 만든다 — self_hosted_hooks() 가
    찾는 그 경로 그대로."""
    target = tmp / "target"
    dest_hooks = target / "on-the-record" / "hooks"
    dest_hooks.mkdir(parents=True)
    for f in (ROOT / "on-the-record" / "hooks").iterdir():
        if f.is_file():
            shutil.copy2(f, dest_hooks / f.name)
    return target


def t_registered_hooks_match_hooksjson_entries():
    raw = json.loads(HOOKS_JSON.read_text())
    expected = _entries(raw["hooks"])

    with tempfile.TemporaryDirectory() as td:
        target = _self_hosted_target(Path(td))
        injected = spawn.self_hosted_hooks(str(target))
        assert injected is not None, "self_hosted_hooks() found nothing for a self-hosted target"
        actual = _entries(injected)

    assert actual == expected, (
        f"registration drifted from hooks.json\n"
        f"  missing from registration: {expected - actual}\n"
        f"  extra in registration:     {actual - expected}"
    )


def t_non_self_hosted_target_gets_no_injection():
    with tempfile.TemporaryDirectory() as td:
        assert spawn.self_hosted_hooks(td) is None


def t_role_settings_merges_hooks_only_for_self_hosted_target():
    with tempfile.TemporaryDirectory() as td:
        target = _self_hosted_target(Path(td))
        out = spawn.role_settings("implementation", str(target))
        assert "hooks" in out and out["hooks"], "self-hosted role_settings() carries no hooks key"

    with tempfile.TemporaryDirectory() as td2:
        out2 = spawn.role_settings("implementation", td2)
        assert "hooks" not in out2, "non-self-hosted target got a hooks key injected"


def _plugin_root_command(hooks: dict, event: str, matcher: str, basename: str) -> str:
    for group in hooks[event]:
        if group.get("matcher", "") == matcher:
            for h in group["hooks"]:
                if Path(h["command"]).name == basename:
                    return h["command"]
    raise AssertionError(f"no ({event}, {matcher}, {basename}) entry in injected hooks")


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def _spec_index_preflight_denies(repo: Path, script: str, staged_ok: bool) -> int:
    """spec-index-preflight.sh 가 PreToolUse 훅으로서 받는 것과 같은 모양의
    CG_PAYLOAD 를 채워 실제로 실행하고, 그 종료코드를 돌려준다."""
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m wip"},
    })
    r = subprocess.run(["bash", script], cwd=repo, input=payload, capture_output=True,
                        text=True, env=os.environ)
    return r.returncode


def t_live_fire_deny_before_commit_lands():
    """spec-tracked 파일을 index 갱신 없이 스테이징 -> 훅이 실제로 거부 -> 커밋이
    안 만들어짐. index 를 갱신해 다시 스테이징 -> 같은 훅이 통과 -> 커밋이 성공.
    둘 다 실제 git 저장소에서, 실제 훅 스크립트를 돌려 확인한다."""
    with tempfile.TemporaryDirectory() as td:
        target = _self_hosted_target(Path(td))
        injected = spawn.self_hosted_hooks(str(target))
        script = _plugin_root_command(injected, "PreToolUse", "Bash",
                                       "spec-index-preflight.sh")

        repo = Path(td) / "repo"
        repo.mkdir()
        _run_git(["init", "-q"], repo)
        _run_git(["config", "user.email", "t@example.com"], repo)
        _run_git(["config", "user.name", "t"], repo)

        specs = repo / "docs" / "specs"
        specs.mkdir(parents=True)
        tracked = repo / "spec.md"
        tracked.write_text("v1\n")
        import hashlib
        h1 = hashlib.sha256(tracked.read_bytes()).hexdigest()
        (specs / "reconciled-index.md").write_text(
            "| path | sha256 |\n|---|---|\n" f"| `spec.md` | `{h1}` |\n"
        )
        _run_git(["add", "."], repo)
        _run_git(["commit", "-q", "-m", "init"], repo)

        # RED: spec.md 내용을 바꿔 스테이징하고 index 는 그대로 둔다.
        tracked.write_text("v2 drift\n")
        _run_git(["add", "spec.md"], repo)
        rc_red = _spec_index_preflight_denies(repo, script, staged_ok=False)
        assert rc_red == 2, f"expected deny (2), got {rc_red}"
        commit_red = _run_git(["diff", "--cached", "--name-only"], repo)
        assert "spec.md" in commit_red.stdout, "staged drift should still be staged, uncommitted"

        # GREEN: index 를 실제 내용에 맞게 갱신하고 같이 스테이징한다.
        h2 = hashlib.sha256(tracked.read_bytes()).hexdigest()
        (specs / "reconciled-index.md").write_text(
            "| path | sha256 |\n|---|---|\n" f"| `spec.md` | `{h2}` |\n"
        )
        _run_git(["add", "."], repo)
        rc_green = _spec_index_preflight_denies(repo, script, staged_ok=True)
        assert rc_green == 0, f"expected allow (0), got {rc_green}"
        commit_result = _run_git(["commit", "-q", "-m", "drift+index"], repo)
        assert commit_result.returncode == 0, commit_result.stderr


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
