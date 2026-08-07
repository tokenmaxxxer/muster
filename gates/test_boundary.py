#!/usr/bin/env python3
"""issue-441 — 계약/집행 경계 게이트: `docs/specs/enforcement-boundary.md`
가 `gates/*.py`, `on-the-record/hooks/*.sh`, `.github/workflows/*.yml`,
`spawn.py` 를 전부 덮는지 도출해서 검사한다(#333, #376: 손으로 유지하는
목록이 아니라 파일시스템에서 도출).

기록된 verdict 없는 메커니즘이 하나라도 있으면 실패한다 — "판정이 기록
안 된 게이트가 조용히 존재한다"(#441 acceptance)를 기계적으로 잡는다.

  python3 gates/test_boundary.py
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "docs" / "specs" / "enforcement-boundary.md"

_ROW_RE = re.compile(r"^\|\s*`?([^`|]+?)`?\s*\|\s*(.+?)\s*\|", re.MULTILINE)
_SEP_ROW = re.compile(r"^\|[\s:-]+\|")


def _recorded_mechanisms(spec_text: str) -> dict[str, str]:
    """스펙의 모든 마크다운 표에서 `| \\`이름\\` | verdict | ...` 행을 뽑는다.

    첫 컬럼이 백틱으로 감싸이지 않은 서술적 헤더 행("mechanism", "act" 등)
    과 구분선(`|---|---|`)은 건너뛴다."""
    out: dict[str, str] = {}
    for line in spec_text.splitlines():
        if not line.startswith("|") or _SEP_ROW.match(line):
            continue
        m = _ROW_RE.match(line)
        if not m:
            continue
        name, verdict = m.group(1).strip(), m.group(2).strip()
        if name in ("mechanism", "act"):
            continue
        if not verdict:
            continue
        out[name] = verdict
    return out


def _actual_mechanisms() -> set[str]:
    names = set()
    for p in sorted((ROOT / "gates").glob("*.py")):
        if p.name.startswith("test_") or p.name == "__init__.py":
            continue
        names.add(p.name)
    for p in sorted((ROOT / "on-the-record" / "hooks").glob("*.sh")):
        names.add(p.name)
    for p in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        names.add(p.name)
    names.add("spawn.py")
    return names


def check() -> list[str]:
    if not SPEC.is_file():
        return [f"{SPEC} 가 없다 — 경계 스펙 자체가 없으면 판정할 근거가 없다."]
    recorded = _recorded_mechanisms(SPEC.read_text(encoding="utf-8"))
    missing = sorted(name for name in _actual_mechanisms() if name not in recorded)
    if not missing:
        return []
    return [
        f"{name} 가 {SPEC.relative_to(ROOT)} 에 판정(verdict)이 기록된 행으로 "
        f"없다 — 기록되지 않은 게이트가 조용히 존재한다(#441)."
        for name in missing
    ]


def t_all_gates_modules_recorded():
    bad = check()
    assert not bad, "\n".join(bad)


def t_a_new_unrecorded_module_is_caught():
    """도출 로직 자체가 "없으면 통과"로 무너지지 않는지: 실제 파일셋에
    가짜 이름 하나를 섞으면 그 이름은 당연히 스펙에 없다."""
    recorded = _recorded_mechanisms(SPEC.read_text(encoding="utf-8"))
    assert "definitely_not_a_recorded_mechanism.py" not in recorded


def t_spec_records_the_operator_boundary_decision():
    text = SPEC.read_text(encoding="utf-8")
    assert "out of scope — operator decision, 2026-08-07" in text
    assert "closure_sweep.py" in text and "spawn_coverage.py" in text


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    _run(tests)
    sys.exit(0)
