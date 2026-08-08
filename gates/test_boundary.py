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


# issue #464: "justified" 행이 실제로 처분을 밝히고 있는지 확인하는
# 어휘 목록 — 행 자체의 텍스트가 이 중 하나를 인용해야 한다(절 제목으로는
# 통과 못 함 — 절 제목 fallback 은 필러 텍스트를 `### Justified` 절 아래
# 아무데나 끼워 넣어도 통과시키는 우회를 만든다는 게 issue-464 hunt 에서
# 확인됐다: docs/reports/2026-08-08-hunt-class-a-orchestrator-loop-wiring.md).
# 여덟 개 다 UNENFORCED-CLAUSES.md 의 justified 9행 각각이 실제로 쓰고
# 있는 문구다 — 새 어휘를 추가할 땐 그 행 자체의 실제 처분 서술에서
# 가져와야 한다.
_DISPOSITION_VOCAB = ("roster_watchdog", "operator decision", "CI-supplement",
                      "n/a (infrastructure)", "contract-guard.sh",
                      "not a blocking check", "nothing to port",
                      "issue-comment history")


def t_gate_porting_rows_are_ported_or_justified():
    """issue #457 acceptance (issue #464 로 조여짐): 각 16개 카테고리-2
    이슈 번호가 `on-the-record/hooks/**` 안에 실제로 그 이슈를 언급하는
    강제 항목으로 존재하거나(포팅), `on-the-record/UNENFORCED-CLAUSES.md`
    안에 정당화 행으로 존재하고 그 행(또는 그 행이 속한 절 제목)이
    `_DISPOSITION_VOCAB` 어휘 중 하나를 실제로 인용해야(justify) 한다 —
    비어있지 않기만 하면 통과하던 이전 검사(issue #457)와 달리, 처분을
    실제로 밝히지 않는 행은 "정당화 없음"으로 취급한다."""
    hook_text = "\n".join(
        p.read_text(encoding="utf-8") for p in sorted(_HOOKS_DIR.glob("*.sh"))
    )
    unenforced_text = UNENFORCED.read_text(encoding="utf-8")
    lines = unenforced_text.splitlines()
    missing = []
    unjustified = []
    for n in GATE_PORTING_ISSUES:
        tag = f"#{n}"
        ported = tag in hook_text
        row_line = next(
            (line for line in lines if re.search(rf"\|\s*{tag}\s*\|", line)),
            None)
        if row_line is None:
            if not ported:
                missing.append(n)
            continue
        if not any(kw in row_line for kw in _DISPOSITION_VOCAB):
            unjustified.append(n)
    assert not missing, (
        f"issue #457 카테고리-2 행이 포팅도 정당화도 안 됐다: {missing} — "
        f"{_HOOKS_DIR}/**.sh 에 강제 항목이 있거나 {UNENFORCED} 에 정당화 "
        "행이 있어야 한다."
    )
    assert not unjustified, (
        f"issue #464 조여진 검사: 이슈 {unjustified} 의 정당화 행이 "
        f"{_DISPOSITION_VOCAB} 어휘 중 어느 것도 인용하지 않는다 — "
        f"{UNENFORCED} 에서 처분(mechanism 인용 또는 operator-decision/"
        "Justified/Deferred 표시)을 명시하는 문구로 고쳐야 한다."
    )


GATES_PY = ROOT / "gates" / "gates.py"


def t_gates_docstring_states_retroactivity_rule():
    """#362 acceptance: `gates/gates.py` 의 모듈 docstring 이 소급 금지
    원칙(작성 시점에 대응할 수 없었던 이유로 나중에 실패시키지 않는다)을
    명시해야 한다."""
    text = GATES_PY.read_text(encoding="utf-8")
    assert "소급" in text and "작성 시점" in text, (
        f"{GATES_PY} 의 docstring 에 #362 소급 금지 규칙 문구가 없다."
    )


ISSUE_467_DISPOSITION_ROWS = [
    318, 320, 362, 363, 376, 377, 379, 390, 412, 415, 416, 419, 424,
]

_ISSUE_467_BATCH_A_CITATIONS = {
    362: ROOT / "gates" / "test_boundary.py",
    390: ROOT / "gates" / "test_merge_state_gate.py",
    412: ROOT / "on-the-record" / "hooks" / "test_self_update_shallow.py",
}

_ISSUE_467_BATCH_C_CITATIONS = {
    320: ROOT / "gates" / "test_report_framing_check.py",
    376: ROOT / "gates" / "test_capability_gates.py",
    377: ROOT / "gates" / "test_claims.py",
}


def t_class_b_disposition_rows_cited():
    """issue-467 ADR: 13개 `deployed-contract+check` 행이 전부 표에 있어야
    하고, 이미 배달된 배치(A: #362/#390/#412, C: #320/#376/#377)는 실제
    파일 경로 인용이 있어야 한다 — 아직 배달 안 된 나머지 행은 표에
    있는 것만으로 충분하다(뒤 배치가 자기 배달 때 인용을 추가한다)."""
    missing_citation = []
    for n in {**_ISSUE_467_BATCH_A_CITATIONS, **_ISSUE_467_BATCH_C_CITATIONS}:
        assert n in ISSUE_467_DISPOSITION_ROWS, f"#{n} 이 disposition 표에 없다."
    for citations in (_ISSUE_467_BATCH_A_CITATIONS, _ISSUE_467_BATCH_C_CITATIONS):
        for n, path in citations.items():
            if not path.is_file():
                missing_citation.append((n, path))
    assert not missing_citation, (
        f"배치 행이 인용하는 파일이 없다: {missing_citation}"
    )
    assert len(ISSUE_467_DISPOSITION_ROWS) == 13, (
        "issue-467 disposition 표는 13개 행이어야 한다."
    )


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    import importlib.util as _ilu

    _mig_spec = _ilu.spec_from_file_location(
        "test_boundary_workflow_migration",
        Path(__file__).resolve().parent / "test_boundary_workflow_migration.py",
    )
    _migration = _ilu.module_from_spec(_mig_spec)
    _mig_spec.loader.exec_module(_migration)

    tests = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    tests += [(n, f) for n, f in sorted(vars(_migration).items())
              if n.startswith("t_") and callable(f)]
    _run(tests)
    sys.exit(0)
