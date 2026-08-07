#!/usr/bin/env python3
"""per-PR 랜딩 준비도 판정 게이트 — issue #407.

오케스트레이터가 "머지를 멈췄다"고 말할 때, 그 정지가 실제로 어느 PR을
덮는지는 계산 가능하다: 체크 통과, 기록 존재, 승인 기록, 그리고 정지 원인이
선언한 파일-스코프가 이 PR이 건드린 경로와 겹치는지. `closure_sweep.py`의
`classify` 와 같은 모양(순수 함수, 네트워크 없음)으로, 오케스트레이터가
"이 PR 하나가 지금 준비됐는가"를 매 항목마다 물을 수 있게 한다 — 보드 전체
재스캔을 기다리지 않고, 그리고 대칭적으로 "방금 겪은 실패가 정확히 이
PR들만 덮는다"를 표현할 수 있게 한다.

  python3 gates/landing_readiness.py [--repo <경로>]
  각 열린 PR에 대해 한 줄씩 분류를 찍는다. 네트워크(`gh`)만 쓰고 아무것도
  쓰지 않는다.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ci  # noqa: E402

READY = "READY"
BLOCKED_ON_PR = "BLOCKED_ON_PR"
BLOCKED_ON_SCOPE = "BLOCKED_ON_SCOPE"


def classify(pr_state: str, checks: str, has_record: bool, has_approval: bool,
             pr_files: frozenset[str] = frozenset(),
             blocking_causes: tuple[dict, ...] = ()) -> tuple[str, str | None]:
    """(분류, 사유) 를 돌려준다. 네트워크 없는 순수 판정 (테스트 용이).

    `checks` 는 `gh pr checks` 가 요약하는 상태 문자열(예: "pass"/"fail"/
    "pending") — 이 PR 자신의 체크가 통과하지 않으면 그 자체로
    BLOCKED_ON_PR 이고, 외부 원인은 볼 필요가 없다.

    `blocking_causes` 는 `[{"reason": str, "scope": frozenset[str] | None}]`
    모양이다 — `scope` 가 None 이면 보드 전체를 덮는 원인(무조건 적용),
    `scope` 가 파일-경로 접두어 집합이면 `pr_files` 중 하나라도 그 접두어
    아래 있을 때만 이 PR을 덮는다. 이게 #398 의 "gates/ 전용 원인이
    gates/ 를 안 건드린 PR 까지 덮는다" 과잉 일반화를 막는 지점이다."""
    if pr_state != "OPEN":
        return READY, None
    if checks != "pass":
        return BLOCKED_ON_PR, f"checks: {checks}"
    if not has_record:
        return BLOCKED_ON_PR, "no phase-2 record"
    if not has_approval:
        return BLOCKED_ON_PR, "no approval recorded"
    for cause in blocking_causes:
        scope = cause.get("scope")
        if scope is None or any(f.startswith(tuple(scope)) for f in pr_files):
            return BLOCKED_ON_SCOPE, cause.get("reason", "unnamed cause")
    return READY, None


def _pr_list(root: Path) -> list[dict] | None:
    r = subprocess.run(
        ["gh", "pr", "list", "--state", "open", "--json",
         "number,headRefName"],
        cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def _pr_checks_summary(root: Path, pr: int) -> str:
    r = subprocess.run(["gh", "pr", "checks", str(pr)], cwd=root,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return "fail"
    out = r.stdout.lower()
    if "fail" in out:
        return "fail"
    if "pending" in out:
        return "pending"
    return "pass"


def _pr_files(root: Path, pr: int) -> frozenset[str]:
    r = subprocess.run(["gh", "pr", "diff", str(pr), "--name-only"], cwd=root,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return frozenset()
    return frozenset(line.strip() for line in r.stdout.splitlines() if line.strip())


def main() -> int:
    root = Path(".").resolve()
    argv = sys.argv[1:]
    if "--repo" in argv:
        root = Path(argv[argv.index("--repo") + 1]).resolve()

    prs = _pr_list(root)
    if prs is None:
        print("landing-readiness: gh pr list 실패")
        return 2
    for pr in prs:
        n = pr["number"]
        branch = pr.get("headRefName", "")
        checks = _pr_checks_summary(root, n)
        files = _pr_files(root, n)
        detected = ci._issue_and_role_from_branch(branch)
        if detected is None:
            has_record = False
            has_approval = False
        else:
            issue, role = detected
            has_record = ci._phase2_record_evidence(root, n, branch, issue)
            has_approval = role in ci._approved_roles_on_issue(root, issue)
        kind, reason = classify("OPEN", checks, has_record, has_approval, files, ())
        suffix = f" ({reason})" if reason else ""
        print(f"PR #{n}: {kind}{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
