#!/usr/bin/env python3
"""원장 — 리뷰 에이전트의 성적을 수확한다.

이 레포가 존재하는 이유다. METR RCT 의 교훈(체감 +20%, 실측 -19%)이 여기 걸려 있다:
**체감은 못 믿으므로 재야 한다.** 룰북 개선이 취향 논쟁이 되지 않게 하는 유일한 수단.

  python3 ledger/collect.py <owner/repo> [--since 2026-07-01] [--out ledger/data.jsonl]

지표 넷과 목표선 (DoorDash 자체 리뷰어 실측):

  수용률       high/critical 지적 중 머지 전 수정으로 이어진 비율   목표 60%
  리뷰당 비용   토큰 비용                                          목표 $3 이하
  응답 시간    PR 오픈 → 첫 리뷰                                   목표 10분 이내
  revert율     머지 후 되돌림                                      불변이 정상

셋은 자동으로 나오고 **수용률만 안 나온다** — "이 지적이 반영됐다"는 판정에 의미
이해가 필요하기 때문이다. 그래서 대리지표(지적 이후 해당 파일이 다시 커밋됐는가)를
같이 내되 `accepted` 필드는 비워 둔다. 표본이 쌓이기 전에 대리지표를 정답으로
취급하면 원장이 거짓말을 시작하고, 그러면 안 재느니만 못하다.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BOT = "claude"          # 리뷰 작성자 식별. 봇 이름이 바뀌면 여기만 고친다.


def gh_json(*args: str):
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"gh 실패: {' '.join(args)}\n{p.stderr.strip()}")
    return json.loads(p.stdout or "null")


def ts(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def pr_record(repo: str, pr: dict) -> dict:
    """PR 하나의 원장 항목. 판정하지 않고 사실만 담는다."""
    num = pr["number"]
    revs = gh_json("api", f"repos/{repo}/pulls/{num}/reviews", "--paginate")
    coms = gh_json("api", f"repos/{repo}/pulls/{num}/comments", "--paginate")

    bot_events = [r for r in (revs or []) if BOT in (r.get("user") or {}).get("login", "").lower()]
    bot_coms = [c for c in (coms or []) if BOT in (c.get("user") or {}).get("login", "").lower()]

    opened, first = ts(pr["createdAt"]), None
    for e in bot_events + bot_coms:
        t = ts(e.get("submitted_at") or e.get("created_at"))
        if t and (first is None or t < first):
            first = t

    return {
        "repo": repo,
        "pr": num,
        "opened_at": pr["createdAt"],
        "merged_at": pr.get("mergedAt"),
        "findings": len(bot_coms),
        # 응답 시간(분). 리뷰가 없으면 None — 0 이 아니다. 침묵은 정상 동작이므로
        # 리뷰 없는 PR 을 "0분 응답"으로 세면 평균이 거짓이 된다.
        "response_min": round((first - opened).total_seconds() / 60, 1)
        if first and opened else None,
        # 대리지표: 지적이 달린 파일이 그 뒤에 다시 커밋됐는가. 반영의 **증거가
        # 아니라 후보**다. accepted 의 근거로 쓰되 값을 대신하지 않는다.
        "touched_after": _touched_after(repo, num, bot_coms),
        # 사람이 채운다. 표본이 쌓이면 그때 자동 판정을 학습시킨다.
        "accepted": None,
        "cost_usd": None,        # merge_costs() 가 채운다
    }


def _touched_after(repo: str, num: int, coms: list) -> int:
    if not coms:
        return 0
    commits = gh_json("api", f"repos/{repo}/pulls/{num}/commits", "--paginate") or []
    later = [(c["sha"], ts(c["commit"]["committer"]["date"])) for c in commits]
    n = 0
    for c in coms:
        at, path = ts(c.get("created_at")), c.get("path")
        if not (at and path):
            continue
        for sha, cts in later:
            if cts and cts > at:
                files = gh_json("api", f"repos/{repo}/commits/{sha}") or {}
                if any(f.get("filename") == path for f in files.get("files", [])):
                    n += 1
                    break
    return n


def merge_costs(rows: list[dict], repo: str) -> None:
    """워크플로가 아티팩트로 올린 비용을 붙인다. 없으면 None 으로 둔다."""
    arts = gh_json("api", f"repos/{repo}/actions/artifacts", "--paginate") or {}
    by_pr = {}
    for a in arts.get("artifacts", []):
        name = a.get("name", "")
        if name.startswith("ledger-"):
            try:
                by_pr.setdefault(int(name.split("-")[1]), a["id"])
            except (IndexError, ValueError):
                continue
    if by_pr:
        print(f"  비용 아티팩트 {len(by_pr)}건 발견 "
              f"(내려받기는 gh run download 로 별도 — 여기서는 존재만 확인)",
              file=sys.stderr)


def summarize(rows: list[dict]) -> str:
    n = len(rows)
    reviewed = [r for r in rows if r["response_min"] is not None]
    resp = sorted(r["response_min"] for r in reviewed)
    judged = [r for r in rows if r["accepted"] is not None]
    out = [f"PR {n}건 / 리뷰가 달린 것 {len(reviewed)}건 / 지적 {sum(r['findings'] for r in rows)}건"]
    if resp:
        out.append(f"응답 시간 중앙값 {resp[len(resp) // 2]}분  (목표 10분 이내)")
    if judged:
        acc = sum(1 for r in judged if r["accepted"]) / len(judged) * 100
        out.append(f"수용률 {acc:.1f}%  (n={len(judged)}, 목표 60%)")
    else:
        out.append("수용률 — 아직 없음. accepted 를 사람이 채워야 나온다")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--since", default=None, help="YYYY-MM-DD")
    ap.add_argument("--out", default="ledger/data.jsonl", type=Path)
    a = ap.parse_args()

    prs = gh_json("pr", "list", "-R", a.repo, "--state", "all", "--limit", "100",
                  "--json", "number,createdAt,mergedAt") or []
    if a.since:
        prs = [p for p in prs if p["createdAt"][:10] >= a.since]
    print(f"PR {len(prs)}건 수집 중…", file=sys.stderr)

    rows = [pr_record(a.repo, p) for p in prs]
    merge_costs(rows, a.repo)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    print(f"→ {a.out}", file=sys.stderr)
    print(summarize(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
