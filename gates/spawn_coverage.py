#!/usr/bin/env python3
"""스폰-커버리지 게이트 — 열린 이슈가 보드에 아무 기록도 못 올렸으면 보고한다(issue-325).

발행만 되고 세션이 한 번도 스폰되지 않은 이슈는, 보드(`spawn.board(root)`)에
그 이슈의 `issue-<n>` 키가 아예 없다. `closure_sweep.py`와 같은 모양
(injectable pure function + thin CLI, 데몬 아님) — 사람이나 CI 가 원할 때
돌린다.

  python3 gates/spawn_coverage.py [--repo <경로>] [--grace-hours N]
  종료 코드 0 (커버되지 않은 이슈 없음) / 1 (있음)
"""
from __future__ import annotations
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn  # noqa: E402

DEFAULT_GRACE_HOURS = 3.0


def find_uncovered(open_issues: list[dict], board: dict, now: datetime,
                   grace_hours: float = DEFAULT_GRACE_HOURS) -> list[int]:
    """열린 이슈 중 보드에 `issue-<n>` 키가 없고, grace_hours 보다 오래된 것들.

    `open_issues` 는 `{"number": int, "createdAt": "2026-...Z"}` 사전 리스트
    (`gh issue list --json number,createdAt` 모양) — 순수, 네트워크 없음.
    """
    covered = set(board.keys())
    out = []
    for it in open_issues:
        number = it.get("number")
        if number is None:
            continue
        key = f"issue-{number}"
        if key in covered:
            continue
        created = it.get("createdAt")
        if created:
            try:
                created_ts = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                created_ts = None
        else:
            created_ts = None
        if created_ts is not None:
            age_hours = (now - created_ts).total_seconds() / 3600
            if age_hours < grace_hours:
                continue
        out.append(number)
    return sorted(out)


def _list_open_issues(root: Path) -> list[dict] | None:
    r = subprocess.run(
        ["gh", "issue", "list", "--state", "open", "--json", "number,createdAt",
         "--limit", "1000"],
        cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import json
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def main() -> int:
    root = Path(".").resolve()
    argv = sys.argv[1:]
    if "--repo" in argv:
        root = Path(argv[argv.index("--repo") + 1]).resolve()
    grace_hours = DEFAULT_GRACE_HOURS
    if "--grace-hours" in argv:
        grace_hours = float(argv[argv.index("--grace-hours") + 1])

    open_issues = _list_open_issues(root)
    if open_issues is None:
        # gh 실패를 "커버되지 않은 이슈 없음"과 같은 종료 코드(0)로 두면 게이트
        # 자체가 이 이슈가 고치려는 결함(조용한 실패가 진행과 구분 안 됨)을
        # 그대로 재현한다 — 실패는 반드시 비-0으로 알려야 한다.
        print("스폰-커버리지: 이슈 목록을 읽을 수 없다 (gh 실패) — 판정 불가",
              file=sys.stderr)
        return 1
    board = spawn.board(root)
    uncovered = find_uncovered(open_issues, board, datetime.now(timezone.utc), grace_hours)
    if not uncovered:
        print("스폰-커버리지: 커버되지 않은 이슈 없음")
        return 0
    print("스폰-커버리지: 발행됐지만 보드에 기록이 없는 이슈")
    for n in uncovered:
        print(f"  issue #{n}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
