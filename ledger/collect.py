#!/usr/bin/env python3
"""원장 — 리뷰가 값을 하는지 잰다.

  python3 ledger/collect.py [<레포 경로>] [--json]

이 레포가 존재하는 이유다. METR RCT 의 교훈(체감 +20%, 실측 -19%)이 여기 걸려
있다: **체감은 못 믿으므로 재야 한다.** 룰북 개선이 취향 논쟁이 되지 않게 하는
유일한 수단이다.

읽는 것은 `review-cycle` 이 남긴 `review-record.md` 다. 이전 판은 GitHub PR 코멘트를
긁어 "코멘트가 달렸는가"를 셌는데 그건 대리지표였다. 지금은 **판정 자체가 지표다** —
요구사항마다 Present/Surface/Absent/Incorrect 중 하나가 붙는다.

수용률은 그 판정이 **다음 판에서 바뀌었는가**로 잰다. Absent/Incorrect 였던 것이
줄었으면 지적이 반영된 것이다. 파일의 git 이력을 걸어 연속한 두 판을 비교하므로
사람이 손으로 라벨링할 필요가 없다.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# 계약 v2 의 보드 자리. subject 마다 한 판씩 있고, 전부 합쳐서 센다.
BOARD = "docs/reports/records"
# v1 은 레포 루트에 한 파일이었다. 아직 안 옮긴 레포를 "리뷰를 돈 적 없다"로
# 보고하면 원장이 거짓말을 한다 — 없는 것과 옛 자리에 있는 것은 정반대 처분을
# 받아야 한다.
LEGACY = "review-record.md"
VERDICTS = ("Present", "Surface", "Absent", "Incorrect")
# 요구사항 한 블록에 verdict 한 줄. 상태기계 스펙이 "정확히 하나"를 요구한다.
VERDICT_RE = re.compile(r"^\s*verdict:\s*(\w+)\s*$", re.M)


def parse(text: str) -> dict:
    """한 판의 판정 분포. 어휘 밖의 값은 세지 않고 따로 보고한다 —
    조용히 버리면 요구사항 수가 맞지 않는 것을 아무도 모른다."""
    found = VERDICT_RE.findall(text or "")
    status = re.search(r"^status:\s*(\S+)", text or "", re.M)
    counts = {v: found.count(v) for v in VERDICTS}
    return {"status": status.group(1) if status else None,
            "counts": counts, "total": sum(counts.values()),
            "unknown": sorted({v for v in found if v not in VERDICTS})}


def history(repo: Path, path: str) -> list[str]:
    """오래된 순으로 각 커밋 시점의 파일 내용."""
    log = subprocess.run(
        ["git", "-C", str(repo), "log", "--reverse", "--format=%H", "--", path],
        capture_output=True, text=True)
    out = []
    for sha in log.stdout.split():
        blob = subprocess.run(["git", "-C", str(repo), "show", f"{sha}:{path}"],
                              capture_output=True, text=True)
        if blob.returncode == 0:
            out.append(blob.stdout)
    return out


def unresolved(text: str) -> int:
    """미해결 지적 수 = Absent + Incorrect."""
    c = parse(text)["counts"]
    return c["Absent"] + c["Incorrect"]


def records(repo: Path) -> list[str]:
    """셀 review 기록들의 레포 상대 경로. v2 를 먼저 보고, 없으면 v1 자리."""
    board = repo / BOARD
    if board.is_dir():
        found = sorted(str(p.relative_to(repo))
                       for p in board.glob("*/review.md") if p.is_file())
        if found:
            return found
    return [LEGACY] if (repo / LEGACY).exists() else []


def _one(repo: Path, rel: str) -> tuple[list[str], int, int]:
    revs = history(repo, rel)
    cur = repo / rel
    if cur.exists():                       # 아직 커밋 안 된 최신 판도 한 판으로 센다
        text = cur.read_text()
        if not revs or revs[-1] != text:
            revs = revs + [text]
    fixed = seen = 0
    for a, b in zip(revs, revs[1:]):
        # 요구사항 텍스트를 짝지어 추적하는 편이 정확하지만 블록 형식이 룰북 쪽에서
        # 아직 고정되지 않았다. **셈이 확실한 것만** 센다 — 과소평가는 하되
        # 과대평가는 하지 않는다. 형식이 굳으면 요구사항 단위로 올린다.
        before = unresolved(a)
        fixed += max(0, before - unresolved(b))
        seen += before
    return revs, seen, fixed


def collect(repo: Path) -> dict:
    rels = records(repo)
    legacy = rels == [LEGACY]
    revisions = fixed = seen = 0
    latest = None
    for rel in rels:
        revs, s, f = _one(repo, rel)
        revisions += len(revs)
        seen += s
        fixed += f
        if revs:
            latest = parse(revs[-1])       # subject 가 여럿이면 마지막 판 하나를 보여준다

    return {"repo": str(repo), "found": bool(rels), "legacy": legacy,
            "subjects": len(rels), "records": rels,
            "current": latest,
            "revisions": revisions, "findings_seen": seen, "findings_fixed": fixed,
            "acceptance_pct": round(fixed / seen * 100, 1) if seen else None}


def report(d: dict) -> str:
    if not d["found"]:
        return (f"{d['repo']}\n  {BOARD}/<subject>/review.md 없음 — 이 레포로 "
                f"리뷰 사이클을 돈 적이 없다.\n"
                f"  python3 spawn.py review \"<맡길 일>\" -C {d['repo']}")
    c = d["current"]
    out = [d["repo"]]
    if d["legacy"]:
        # 옛 자리에 있는 것을 "없다"로 보고하면 원장이 거짓말을 시작한다.
        out.append(f"  ⚠ v1 자리({LEGACY})를 읽었다 — 계약 v2 는 "
                   f"{BOARD}/<subject>/review.md 다. 아직 안 옮긴 레포다.")
    elif d["subjects"] > 1:
        out.append(f"  subject {d['subjects']}개를 합쳐서 셌다: "
                   f"{', '.join(r.split('/')[-2] for r in d['records'])}")
    out += [f"  상태 {c['status'] or '(없음)'}   요구사항 {c['total']}건   개정 {d['revisions']}판",
            "  판정: " + (", ".join(f"{k} {v}" for k, v in c["counts"].items() if v) or "없음")]
    if c["unknown"]:
        out.append(f"  ⚠ 어휘 밖 판정: {', '.join(c['unknown'])} — 스펙은 "
                   f"{'/'.join(VERDICTS)} 넷만 허용한다")
    out.append(f"  수용률: {d['acceptance_pct']}% "
               f"({d['findings_fixed']}/{d['findings_seen']} 해소, 목표 60%)"
               if d["acceptance_pct"] is not None else
               "  수용률: 아직 없음 — 지적이 달린 개정이 2판 이상 쌓여야 나온다")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    if not (repo / ".git").exists():
        sys.exit(f"git 레포가 아니다: {repo}")
    d = collect(repo)
    print(json.dumps(d, ensure_ascii=False, indent=2) if a.json else report(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
