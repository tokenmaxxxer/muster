"""위험도 분류 + 배치 보고 — 승인 피로 완화용 비차단 도구 (issue #319).

`gates.py`의 게이트는 병합 가부를 결정하고, 여기 있는 분류는 그 전에 사람이
무엇을 보는지만 바꾼다. `classify()`가 "low"를 반환해도 phase-2 전환에
필요한 GitHub 승인 행위(APPROVED 리뷰 또는 `APPROVE issue-<n>/<role>` 코멘트)는
전혀 대체되지 않는다 — 이 파일은 그 판정에 관여하지 않는다.

원칙(gates.py와 동일): **불확실하면 막는다.** write-set을 파싱할 수 없는
제안은 "낮음"이 아니라 "high"로 분류한다.
"""
from __future__ import annotations
import json
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


# ---------------------------------------------------------------------------
# Four-axis structural impact classification (issue #511).
#
# Every axis grades 1 (lowest) .. AXIS_MAX (highest), anchored to a
# machine-checkable structural condition — never a felt/text-interpreted
# score. AIAG-VDA FMEA supplies the anchored-grade shape; CVSS v4 supplies
# the non-averaging composition below (dominant_grade). Fail-closed: any
# axis that cannot be computed from the target repo's current structure
# (unparseable write-set, unreadable roles/enforcement-boundary data)
# takes AXIS_MAX, never a middle grade.
# ---------------------------------------------------------------------------
AXIS_MAX = 4

# Path-class tiers for reversibility, extended one tier beyond
# gates.py's single "protected" bucket per the approved proposal: leaf
# docs < application code < gates/hooks < contract/approval-rule files.
CONTRACT_ROOT_FILES = {
    "protocol.md", "protocol.ko.md", "spawn.py",
}
CONTRACT_PATHS = {"docs/specs/approvers.md"}
# "anything under a hook directory" (proposal wording) — the plugin's own
# wiring, one tier above ordinary gates/roles code.
HOOK_DIRS = {"hooks"}
GATES_DIRS = {"gates", "roles", "agents", "on-the-record", ".claude-plugin"}


def _role_write_scopes(root: Path) -> dict[str, list[str]]:
    """`roles/*.json`의 write_scope glob 목록을 role 이름별로 모은다.
    디렉터리가 없거나 파일이 깨졌으면 그 role만 건너뛴다 — 판정은 어차피
    fail-closed 기본값(AXIS_MAX)이 감싼다."""
    out: dict[str, list[str]] = {}
    roles_dir = root / "roles"
    if not roles_dir.is_dir():
        return out
    for f in sorted(roles_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except (ValueError, OSError):
            continue
        scope = data.get("write_scope")
        if isinstance(scope, list):
            out[f.stem] = [s for s in scope if isinstance(s, str)]
    return out


def _reversibility_of(path: str) -> int:
    parts = Path(path).parts
    if not parts:
        return AXIS_MAX
    lower = path.lower()
    if lower in CONTRACT_ROOT_FILES or lower in CONTRACT_PATHS:
        return AXIS_MAX
    if any(seg in HOOK_DIRS for seg in parts[:-1]):
        return AXIS_MAX
    if parts[0] in GATES_DIRS or gates.is_protected(path):
        return AXIS_MAX - 1
    if parts[0] == "docs":
        return 1
    return 2


def reversibility_grade(paths: list[str]) -> int:
    """path-class 등급 중 최댓값. write-set이 비어 있으면 fail closed."""
    if not paths:
        return AXIS_MAX
    return max(_reversibility_of(p) for p in paths)


def blast_radius_grade(paths: list[str], root: Path,
                        other_proposals: list[dict] | None = None) -> int:
    """DEPENDS-ON 근사치: write_scope가 겹치는 role 수 + 같은 경로를 쓰는
    동시 열린 proposal 수. `roles/*.json`을 읽을 수 없으면 fail closed."""
    if not paths:
        return AXIS_MAX
    scopes = _role_write_scopes(root)
    if not scopes:
        return AXIS_MAX
    reading_roles = set()
    for p in paths:
        for role, globs in scopes.items():
            if any(_glob_matches(p, g) for g in globs):
                reading_roles.add(role)
    overlap = 0
    for other in other_proposals or []:
        other_files = set(other.get("files") or [])
        if other_files & set(paths):
            overlap += 1
    signal = len(reading_roles) + overlap
    if signal <= 1:
        return 1
    if signal <= 3:
        return 2
    if signal <= 6:
        return 3
    return AXIS_MAX


def _glob_matches(path: str, pattern: str) -> bool:
    import fnmatch
    # `**` 접두 glob(roles/*.json의 흔한 형태, 예: "src/**")을 fnmatch가
    # 이해하도록 세그먼트 단위로도 한 번 더 비교한다.
    if fnmatch.fnmatch(path, pattern):
        return True
    prefix = pattern.split("**")[0].rstrip("/")
    return bool(prefix) and (path == prefix or path.startswith(prefix + "/"))


def propagation_grade(paths: list[str], root: Path) -> int:
    """이 경로를 자기 통치 범위로 문서화한 rulebook/role 수. enforcement-
    boundary.md 행 + roles/*.json write_scope를 합쳐 센다. 둘 다 못 읽으면
    fail closed."""
    if not paths:
        return AXIS_MAX
    scopes = _role_write_scopes(root)
    boundary = root / "docs" / "specs" / "enforcement-boundary.md"
    boundary_text = boundary.read_text() if boundary.is_file() else ""
    if not scopes and not boundary_text:
        return AXIS_MAX
    touched_roles = set()
    for p in paths:
        for role, globs in scopes.items():
            if any(_glob_matches(p, g) for g in globs):
                touched_roles.add(role)
    boundary_rows = 0
    for p in paths:
        base = Path(p).name
        if base and re.search(re.escape(base), boundary_text):
            boundary_rows += 1
    signal = len(touched_roles) + boundary_rows
    if signal <= 1:
        return 1
    if signal <= 3:
        return 2
    if signal <= 6:
        return 3
    return AXIS_MAX


def existing_signal_grade(paths: list[str], added_lines: int,
                           removed_lines: int) -> int:
    """기존 `classify()`의 protected-path/크기 판정을 4단 등급으로 그대로
    이식 — 요구사항 1의 "existing signals" 축, 로직 변경 없음."""
    if not paths:
        return AXIS_MAX
    if any(gates.is_protected(p) for p in paths):
        return AXIS_MAX
    total = added_lines + removed_lines
    if total > SIZE_THRESHOLD:
        return 3
    if total > 0:
        return 2
    return 1


def classify_axes(paths: list[str], added_lines: int, removed_lines: int,
                   root: Path, other_proposals: list[dict] | None = None) -> dict:
    """네 축 각각의 등급과, dominant-axis 규칙에 따른 종합 판정을 반환한다.

    축은 합산·평균되지 않는다(요구사항 3) — reversibility 최고 등급 하나가
    다른 세 축과 무관하게 개별 승인을 강제한다. 나머지 세 축은 같은
    reversibility 등급 안에서의 주의 배분(정렬/배치 가능 여부)에만 쓰인다.
    """
    axes = {
        "blast_radius": blast_radius_grade(paths, root, other_proposals),
        "reversibility": reversibility_grade(paths),
        "propagation": propagation_grade(paths, root),
        "existing_signals": existing_signal_grade(paths, added_lines, removed_lines),
    }
    axes["requires_individual_approval"] = axes["reversibility"] >= AXIS_MAX
    axes["batchable"] = not axes["requires_individual_approval"]
    return axes


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


def batch_blocked(proposals: list[dict], root: Path) -> list[dict]:
    """`proposals` 중 dominant-axis 규칙상 배치 승인에 포함될 수 없는(개별
    승인이 강제되는) 항목만 골라 `{path, axes}` 목록으로 반환한다. 요구사항 5
    (risk_report를 배치 승인 경로에 블로킹으로 연결)의 판정 지점 —
    `on-the-record/hooks/impact-guard.sh`가 그대로 호출한다."""
    blocked = []
    for p in proposals:
        others = [o for o in proposals if o is not p]
        axes = classify_axes(p["files"], p["added"], p["removed"], root, others)
        if axes["requires_individual_approval"]:
            blocked.append({"path": p["path"], "axes": axes})
    return blocked


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    print(report(scan_open_proposals(root)))
