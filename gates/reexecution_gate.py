#!/usr/bin/env python3
"""SHA-pinned worktree 재실행 — issue #476 H1.

주장 언어에 인접한 커맨드를, 그 커맨드를 주장한 세션이 아니라 게이트가
직접 SHA-pinned worktree 에서 재실행한다. 판정 아티팩트는
`.reexecution/<issue>-<role>.json` 에 게이트가 쓴다 — 감사 대상 세션이
자기 판정을 스스로 적어 넣을 수 있는 경로가 아니다(ADR §3, §5).

worktree 생성 자체가 실패하면 verdict 는 `error` 로 fail closed —
"검사 못 했다"를 "통과했다"로 읽지 않는다.

  python3 gates/reexecution_gate.py --issue <n> --role <role> \
      --sha <target_sha> --command "<cmd>" [--repo <경로>] [--timeout <초>]
"""
from __future__ import annotations
import json
import shlex
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_TIMEOUT = 300

PASS = "pass"
FAIL = "fail"
ERROR = "error"


@dataclass(frozen=True)
class Verdict:
    kind: str  # pass | fail | error
    command: str
    target_sha: str
    exit_code: int | None
    detail: str
    timestamp: float


def run_reexecution(command: str, target_sha: str, repo: Path,
                     timeout: int = DEFAULT_TIMEOUT) -> Verdict:
    """`command` 를 `target_sha` 에 고정된 임시 worktree 안에서 실행하고
    Verdict 를 돌려준다. worktree 생성 실패는 ERROR(fail closed) — 절대
    조용히 건너뛰지 않는다."""
    ts = time.time()
    with tempfile.TemporaryDirectory() as td:
        wt = Path(td) / "wt"
        add = subprocess.run(
            ["git", "worktree", "add", "--detach", str(wt), target_sha],
            cwd=repo, capture_output=True, text=True)
        if add.returncode != 0:
            return Verdict(ERROR, command, target_sha, None,
                           f"worktree 생성 실패: {add.stderr.strip()[:300]}", ts)
        try:
            try:
                run = subprocess.run(
                    shlex.split(command), cwd=wt, capture_output=True,
                    text=True, timeout=timeout)
            except subprocess.TimeoutExpired:
                return Verdict(ERROR, command, target_sha, None,
                               f"{timeout}s 안에 끝나지 않았다", ts)
            except (OSError, ValueError) as e:
                return Verdict(ERROR, command, target_sha, None,
                               f"커맨드 실행 실패: {e}", ts)
            kind = PASS if run.returncode == 0 else FAIL
            tail = (run.stdout + run.stderr).strip()[-500:]
            return Verdict(kind, command, target_sha, run.returncode, tail, ts)
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                           cwd=repo, capture_output=True, text=True)


def verdict_path(repo: Path, issue: int, role: str) -> Path:
    return repo / ".reexecution" / f"{issue}-{role}.json"


def write_verdict(repo: Path, issue: int, role: str, verdict: Verdict) -> Path:
    path = verdict_path(repo, issue, role)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(verdict), ensure_ascii=False, indent=2))
    return path


def read_verdict(repo: Path, issue: int, role: str) -> Verdict | None:
    path = verdict_path(repo, issue, role)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return Verdict(**data)


def _arg(argv: list[str], name: str, default: str | None = None) -> str | None:
    if name in argv:
        return argv[argv.index(name) + 1]
    return default


def main(argv: list[str]) -> int:
    issue = _arg(argv, "--issue")
    role = _arg(argv, "--role")
    sha = _arg(argv, "--sha")
    command = _arg(argv, "--command")
    repo = Path(_arg(argv, "--repo", ".")).resolve()
    timeout = int(_arg(argv, "--timeout", str(DEFAULT_TIMEOUT)))
    if not (issue and role and sha and command):
        print("reexecution_gate: --issue --role --sha --command 모두 필요하다")
        return 2
    verdict = run_reexecution(command, sha, repo, timeout)
    path = write_verdict(repo, int(issue), role, verdict)
    print(f"reexecution_gate: {verdict.kind} ({path})")
    if verdict.detail:
        print(f"    {verdict.detail}")
    return 0 if verdict.kind == PASS else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
