#!/usr/bin/env python3
"""WAKES-ON 평가기 — 계약 v2 §3 의 표를 기계로 판정한다.

계약 §3 이 이 자리를 명시적으로 비워 두었다: "WAKES-ON tells the human (**or a
future automated watcher, if one is built**) *whom* to open." 이 파일이 그
감시자다. **일정을 지어내지 않는다** — §3 의 표 여섯 줄이 전부다.

여섯 줄 중 넷만 기계로 판정된다. 나머지 둘은 계약이 판단으로 적은 것이고,
§14("Mechanical checks are not substantive checks")가 그 구분을 지키라고 한다.

  기계 판정 가능        feasibility, coding, qa, review
  판단이 필요           product ("content questions the acceptance criteria")
                        ops    ("ready to roll out")

**판정 불가를 "안 깨어남"으로 보고하지 않는다.** 그 둘은 정반대 처분을 받아야
한다.

§3 표와 §5 의 어긋남: §5 는 "each row in section 3 already includes its role's
finding trigger" 라고 하지만, §3 표에서 finding 을 실제로 적은 줄은 coding
하나뿐이다. §5 의 진술을 따랐다 — 어느 역할이든 자기 앞으로 온 finding 에
깨어난다. 표만 따르면 coding 외의 역할에게 온 finding 은 아무도 안 본다.
"""
import re
import subprocess
from pathlib import Path

import spawn

# §3 이 기계로 못 재는 두 줄. 왜 못 재는지를 같이 들고 다닌다.
JUDGEMENT = {
    "product": "qa/review 결과가 합의된 수용 기준을 흔드는가 — 내용 판단이다",
    "ops": "머지된 변경이 '내보낼 준비가 됐는가' — 판단이다",
}
UPSTREAM = re.compile(r"^\s*-\s*path:\s*(\S+)", re.M)
UP_SHA = re.compile(r"^\s*sha:\s*(\S+)", re.M)


def _git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def _head_sha(root: Path, path: str) -> str:
    """path 를 마지막으로 건드린 커밋 — 계약 §12 가 staleness 를 재는 방식."""
    return _git(root, "log", "-1", "--format=%H", "--", path)


def upstream(record: Path) -> dict[str, str]:
    """기록의 `upstream:` 목록을 path → sha 로 읽는다.

    frontmatter 의 중첩 블록이라 spawn.frontmatter() 의 평면 파서로는 안 잡힌다.
    """
    try:
        text = record.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)
    if len(block) < 3:
        return {}
    out, cur = {}, None
    for line in block[1].splitlines():
        m = UPSTREAM.match(line)
        if m:
            cur = m.group(1)
            out[cur] = ""
            continue
        s = UP_SHA.match(line)
        if s and cur:
            # acknowledged_sha 가 있으면 그쪽이 최신 확인점이다 (§12)
            out[cur] = out[cur] or s.group(1)
    return out


def _hypotheses(root: Path) -> list[Path]:
    d = root / "docs" / "proposals"
    if not d.is_dir():
        return []
    return [p for p in sorted(d.glob("*.md"))
            if spawn.frontmatter(p).get("kind") == "hypothesis"]


def _findings_to(root: Path, role: str) -> list[str]:
    """`finding` 은 다른 역할 기록의 **본문 안에** 인라인으로 산다 (§2 표, §5).
    frontmatter 가 아니므로 본문 전체를 봐야 한다."""
    recs = root / spawn.BOARD
    if not recs.is_dir():
        return []
    hits = []
    for f in sorted(recs.rglob("*.md")):
        try:
            text = f.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        if re.search(rf"^\s*addressed_to:\s*{re.escape(role)}\s*(#.*)?$", text, re.M):
            hits.append(str(f.relative_to(root)))
    return hits


def evaluate(cwd: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """(깨어난 역할, 판정 불가한 줄). **아무것도 쓰지 않는다.**"""
    root = Path(cwd).resolve()
    b = spawn.board(root)
    woken: list[tuple[str, str]] = []

    # ── feasibility: 새롭거나 바뀐 hypothesis 가 보드에 나타남
    feas_records = [(root / spawn.BOARD / s / "feasibility.md")
                    for s, r in b.items() if "feasibility" in r]
    acked = {p: sha for rec in feas_records for p, sha in upstream(rec).items()}
    for h in _hypotheses(root):
        rel = str(h.relative_to(root))
        if rel not in acked:
            woken.append(("feasibility", f"hypothesis {rel} — feasibility 가 아직 안 읽었다"))
        elif acked[rel] and acked[rel] != _head_sha(root, rel):
            woken.append(("feasibility", f"hypothesis {rel} 가 기록된 sha 이후 바뀜"))

    # ── coding: 세 갈래 중 하나만 서도 깨어난다
    for subject, roles in b.items():
        if roles.get("feasibility", {}).get("verdict") == "go":
            woken.append(("coding", f"{subject}: feasibility verdict: go"))
        if roles.get("qa", {}).get("loop_state") == "handed-off":
            woken.append(("coding", f"{subject}: qa handed-off — 사람의 결함 판정이 끝났다"))

    # ── qa: 도는 시스템의 src/ 또는 tests/ 를 건드린 커밋
    if _git(root, "log", "-1", "--format=%H", "--", "src/", "tests/"):
        woken.append(("qa", "src/ 또는 tests/ 를 건드린 커밋이 있다"))

    # ── review: coding 이 착지시킨 변경
    for subject, roles in b.items():
        if roles.get("coding", {}).get("loop_state") == "landed":
            woken.append(("review", f"{subject}: coding loop_state: landed"))

    # ── finding 되돌이 간선 (§5). 표에는 coding 줄에만 적혀 있지만 §5 는 모든
    #    역할이 자기 앞으로 온 finding 에 깨어난다고 말한다.
    for role in spawn.ROLES:
        for f in _findings_to(root, role):
            woken.append((role, f"finding addressed_to: {role} — {f}"))

    seen, uniq = set(), []
    for item in woken:
        if item not in seen:
            seen.add(item)
            uniq.append(item)
    return uniq, sorted(JUDGEMENT.items())


def report(cwd: str) -> list[str]:
    woken, judged = evaluate(cwd)
    out = ["깨어난 역할 (계약 §3):"] if woken else ["기계로 판정되는 네 줄 중 선 것 없음."]
    out += [f"  [{role}] {why}" for role, why in woken]
    out.append("")
    out.append("기계로 판정하지 않는 줄 — **안 깨어난 것이 아니라 못 재는 것이다**:")
    out += [f"  [{role}] {why}" for role, why in judged]
    return out
