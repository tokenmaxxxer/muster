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
UNENFORCED = ROOT / "on-the-record" / "UNENFORCED-CLAUSES.md"
RUN_MD = ROOT / "on-the-record" / "commands" / "run.md"

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


_GATE_PORTING_MARKER = "<!-- gate-porting-additions (issue #457)"


def _unenforced_mechanism_names(spec_text: str) -> set[str]:
    """mechanisms whose verdict is `contract, CI-supplement` or an
    `out of scope — operator decision` variant — the set issue-452's
    shipped list must match exactly."""
    recorded = _recorded_mechanisms(spec_text)
    return {
        name
        for name, verdict in recorded.items()
        if "CI-supplement" in verdict or "out of scope — operator decision" in verdict
    }


def t_unenforced_clauses_file_matches_spec_exactly():
    """issue-452: `on-the-record/UNENFORCED-CLAUSES.md` must ship inside the
    deployed plugin tree and its mechanism rows must be *exactly* the set of
    CI-supplement / out-of-scope-operator-decision rows in the boundary
    spec — an equal-set check, not one-directional, so a truncated or
    emptied UNENFORCED-CLAUSES.md fails instead of vacuously passing.

    issue-457 appends its own gate-porting justification tables below a
    `_GATE_PORTING_MARKER` comment in the same file; only the text above
    that marker is the #452 spec-verdict extract, so only that slice is
    compared here."""
    assert UNENFORCED.is_file(), f"{UNENFORCED} 가 없다 — issue-452 로 배포됐어야 한다."
    contract_section = UNENFORCED.read_text(encoding="utf-8").split(
        _GATE_PORTING_MARKER, 1
    )[0]
    expected = _unenforced_mechanism_names(SPEC.read_text(encoding="utf-8"))
    shipped = set(_recorded_mechanisms(contract_section).keys())
    assert shipped == expected, (
        f"on-the-record/UNENFORCED-CLAUSES.md 의 mechanism 집합이 스펙과 다르다.\n"
        f"missing: {sorted(expected - shipped)}\nextra: {sorted(shipped - expected)}"
    )


def t_run_md_references_unenforced_clauses():
    assert RUN_MD.is_file(), f"{RUN_MD} 가 없다."
    assert "UNENFORCED-CLAUSES.md" in RUN_MD.read_text(encoding="utf-8"), (
        "run.md 가 UNENFORCED-CLAUSES.md 를 참조하는 줄이 없다(#452)."
    )


GATE_PORTING_ISSUES = [
    310, 312, 319, 322, 325, 330, 331, 332, 333, 334, 369, 383, 388, 396,
    407, 435,
]

_HOOKS_DIR = ROOT / "on-the-record" / "hooks"


def t_gate_porting_rows_are_ported_or_justified():
    """issue #457 acceptance: 각 16개 카테고리-2 이슈 번호가
    `on-the-record/hooks/**` 안에 실제로 그 이슈를 언급하는 강제 항목으로
    존재하거나(포팅), `on-the-record/UNENFORCED-CLAUSES.md` 안에 정당화
    행으로 존재해야(justify) 한다 — 조용한 공백이 하나도 없어야 한다."""
    hook_text = "\n".join(
        p.read_text(encoding="utf-8") for p in sorted(_HOOKS_DIR.glob("*.sh"))
    )
    unenforced_text = UNENFORCED.read_text(encoding="utf-8")
    missing = []
    for n in GATE_PORTING_ISSUES:
        tag = f"#{n}"
        ported = tag in hook_text
        justified = re.search(rf"\|\s*{tag}\s*\|", unenforced_text) is not None
        if not (ported or justified):
            missing.append(n)
    assert not missing, (
        f"issue #457 카테고리-2 행이 포팅도 정당화도 안 됐다: {missing} — "
        f"{_HOOKS_DIR}/**.sh 에 강제 항목이 있거나 {UNENFORCED} 에 정당화 "
        "행이 있어야 한다."
    )


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
