"""위험도 분류 + 배치 보고 — 승인 피로 완화용 비차단 도구 (issue #319).

`gates.py`의 게이트는 병합 가부를 결정하고, 여기 있는 분류는 그 전에 사람이
무엇을 보는지만 바꾼다. `classify()`가 "low"를 반환해도 phase-2 전환에
필요한 GitHub 승인 행위(APPROVED 리뷰 또는 `APPROVE issue-<n>/<role>` 코멘트)는
전혀 대체되지 않는다 — 이 파일은 그 판정에 관여하지 않는다.

원칙(gates.py와 동일): **불확실하면 막는다.** write-set을 파싱할 수 없는
제안은 "낮음"이 아니라 "high"로 분류한다.
"""
from __future__ import annotations
import re
import subprocess
from pathlib import Path

import gates

# gates.py의 warrant 훅 크기 등급(20/200줄)과 같은 근거로 고정한 단일 임계값.
# 그 등급의 하한(20)보다 살짝 높게 잡아, 딱 그 경계에 걸리는 "한 줄 마커
# 이동" 같은 사례가 확실히 low로 남게 한다.
SIZE_THRESHOLD = 30

_STATUS = re.compile(r"^status:\s*(\S+)\s*$", re.M)
_FILES_BLOCK = re.compile(r"^files:\s*\n((?:^\s*-\s*\S+\s*\n|^[ \t]*\n)+)", re.M)
_FILE_LINE = re.compile(r"^\s*-\s*(\S+)\s*$", re.M)


def classify(paths: list[str], added_lines: int, removed_lines: int) -> str:
    """경로/크기로 "high"/"low" 위험도 판정. write-set이 비어 있으면 fail closed."""
    if not paths:
        return "high"
    if any(gates.is_protected(p) for p in paths):
        return "high"
    if added_lines + removed_lines > SIZE_THRESHOLD:
        return "high"
    return "low"


def _parse_files(text: str) -> list[str] | None:
    """proposal 본문에서 `files:` 목록을 뽑는다. 파싱 불가면 None (fail closed)."""
    m = _FILES_BLOCK.search(text)
    if not m:
        return None
    files = _FILE_LINE.findall(m.group(1))
    return files or None


def _diff_stat(root: Path, path: str) -> tuple[int, int]:
    """`path`의 origin/main 대비 추가/삭제 줄 수. git이 추적하지 않거나 diff가
    실패하면 (0, 0) — 새로 생긴 파일이라 아직 origin에 없는 흔한 경우이고,
    분류는 어차피 protected-path/파싱-실패 검사가 우선이라 크기만으로 low를
    잘못 내주지 않는다(파싱 성공 + 미보호 + 신규파일 low 사례는 실제로 안전).
    """
    p = subprocess.run(
        ["git", "-C", str(root), "diff", "--numstat", f"{gates.BASE}...HEAD",
         "--", path],
        capture_output=True, text=True)
    if p.returncode != 0 or not p.stdout.strip():
        return (0, 0)
    added, removed = 0, 0
    for line in p.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        a, r = parts[0], parts[1]
        added += int(a) if a.isdigit() else 0
        removed += int(r) if r.isdigit() else 0
    return (added, removed)


def scan_open_proposals(root: Path) -> list[dict]:
    """`docs/issue-*/proposals/*.md`와 `docs/proposals/*.md` 중 `status: proposed`
    인 것을 찾아 `{path, files, added, removed}` 레코드 목록으로 반환한다.
    `files:`를 못 읽은 proposal도 레코드에 포함시킨다 (files=[] → classify가 high로
    처리하도록) — 스캔 단계에서 조용히 빼면 fail closed 원칙이 무력화된다.
    """
    out = []
    candidates = list((root / "docs" / "proposals").glob("*.md"))
    for issue_dir in (root / "docs").glob("issue-*/proposals"):
        candidates += list(issue_dir.glob("*.md"))
    for path in sorted(candidates):
        text = path.read_text()
        status = _STATUS.search(text)
        if not status or status.group(1) != "proposed":
            continue
        files = _parse_files(text) or []
        added = removed = 0
        for f in files:
            a, r = _diff_stat(root, f)
            added += a
            removed += r
        out.append({
            "path": str(path.relative_to(root)),
            "files": files,
            "added": added,
            "removed": removed,
        })
    return out


def report(proposals: list[dict]) -> str:
    """`proposals`를 위험도별로 묶은 Markdown 표. high를 먼저 낸다.

    입력 하나가 결과에서 빠지거나 두 번 나오면 배치 검토의 전제(모든 대기 항목이
    한 자리에 보인다)가 깨지므로, 각 proposal이 정확히 한 번 나오는지는
    test_risk_report.py가 직접 검사한다.
    """
    rows = []
    for p in proposals:
        risk = classify(p["files"], p["added"], p["removed"])
        rows.append((risk, p))
    rows.sort(key=lambda r: 0 if r[0] == "high" else 1)

    lines = ["| risk | proposal | files | +/- |", "| --- | --- | --- | --- |"]
    for risk, p in rows:
        files = ", ".join(p["files"]) if p["files"] else "(unparseable)"
        lines.append(f"| {risk} | {p['path']} | {files} | "
                     f"+{p['added']}/-{p['removed']} |")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    print(report(scan_open_proposals(root)))
