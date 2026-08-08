#!/usr/bin/env python3
"""issue-460 — `.github/workflows/` retirement migration gate.

Checks: (a) `.github/workflows/` is absent or empty; (b) every deleted
workflow filename has a migration-table row in
`docs/specs/enforcement-boundary.md` with a non-empty `replacement`
column, and any row naming a `CI-supplement`/`out of scope` drop is
cross-referenced by name in `on-the-record/UNENFORCED-CLAUSES.md`.

  python3 gates/test_boundary_workflow_migration.py
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
SPEC = ROOT / "docs" / "specs" / "enforcement-boundary.md"
UNENFORCED = ROOT / "on-the-record" / "UNENFORCED-CLAUSES.md"

DELETED_WORKFLOWS = [
    "on-the-record-tests.yml",
    "plan-aware-closes-gate.yml",
    "closure-sweep.yml",
    "issue-bundling-gate.yml",
]

_MIGRATION_ROW_RE = re.compile(
    r"^\|\s*`([^`|]+\.yml)`\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|$", re.MULTILINE
)


def _migration_rows(spec_text: str) -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for line in spec_text.splitlines():
        m = _MIGRATION_ROW_RE.match(line)
        if not m:
            continue
        name, verdict, replacement = m.group(1), m.group(2).strip(), m.group(3).strip()
        out[name] = (verdict, replacement)
    return out


def t_workflows_dir_absent_or_empty():
    assert not WORKFLOWS_DIR.is_dir() or not any(WORKFLOWS_DIR.iterdir()), (
        f"{WORKFLOWS_DIR} 가 아직 남아 있다 — issue-460 은 전부 삭제를 요구한다."
    )


def t_every_deleted_workflow_has_migration_row():
    rows = _migration_rows(SPEC.read_text(encoding="utf-8"))
    missing = [name for name in DELETED_WORKFLOWS if name not in rows]
    assert not missing, (
        f"{SPEC.relative_to(ROOT)} 에 마이그레이션 행이 없다: {missing}"
    )
    empty_replacement = [name for name in DELETED_WORKFLOWS if not rows[name][1]]
    assert not empty_replacement, (
        f"replacement 컬럼이 비어 있다: {empty_replacement}"
    )


def t_ci_supplement_or_out_of_scope_rows_are_cross_referenced():
    rows = _migration_rows(SPEC.read_text(encoding="utf-8"))
    unenforced_text = UNENFORCED.read_text(encoding="utf-8") if UNENFORCED.is_file() else ""
    for name in DELETED_WORKFLOWS:
        verdict, replacement = rows[name]
        if "CI-supplement" in verdict or "out of scope" in verdict:
            continue
        if "CI-supplement" in replacement or "out of scope" in replacement:
            referenced_mechanism = re.search(r"`([a-zA-Z_]+\.py)`", replacement)
            if referenced_mechanism:
                assert referenced_mechanism.group(1) in unenforced_text, (
                    f"{name} 의 replacement 가 CI-supplement/out-of-scope 를 "
                    f"언급하지만 {UNENFORCED.relative_to(ROOT)} 에 그 메커니즘이 "
                    f"없다."
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
