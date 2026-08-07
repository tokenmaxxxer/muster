#!/usr/bin/env python3
"""issue #336 — spec 문서 드리프트 게이트(gates/spec_index.py) 단위 테스트.

네트워크·GitHub 없이 도는 것만(`test_gates.py`와 같은 관례).

  python3 test_spec_index.py
"""
from __future__ import annotations
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "gates"))
sys.path.insert(0, str(Path(__file__).parent))
import spec_index

REPO_ROOT = Path(__file__).parent


def _copy_tracked_docs(dst: Path) -> None:
    """dotfile/무관 디렉터리를 건드리지 않고 인덱스가 참조하는 문서만 복사한다."""
    rows = spec_index.parse_index(REPO_ROOT / spec_index._INDEX_PATH)
    paths = {spec_index._INDEX_PATH} | {p for p, _ in rows}
    for rel in paths:
        src = REPO_ROOT / rel
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)


def t_baseline_repo_passes():
    """현재 저장소 상태에서 인덱스와 실제 파일이 일치해야 한다."""
    bad = spec_index.check(REPO_ROOT)
    assert bad == [], bad


def t_mutated_tracked_file_fails():
    """인덱스에 기록된 문서 중 하나를 고치면 게이트가 차단해야 한다."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        _copy_tracked_docs(repo)
        rows = spec_index.parse_index(repo / spec_index._INDEX_PATH)
        assert rows, "인덱스에 추적 문서가 없다 — 테스트가 성립하지 않는다"
        target = repo / rows[0][0]
        target.write_text(target.read_text(encoding="utf-8") + "\nDRIFTED\n",
                           encoding="utf-8")
        bad = spec_index.check(repo)
        assert bad, "변경된 문서가 있는데 게이트가 통과했다"
        assert rows[0][0] in bad[0]


def t_missing_index_fails():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        _copy_tracked_docs(repo)
        (repo / spec_index._INDEX_PATH).unlink()
        bad = spec_index.check(repo)
        assert bad and "없음" in bad[0]


def t_update_resyncs_hash():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        _copy_tracked_docs(repo)
        rows = spec_index.parse_index(repo / spec_index._INDEX_PATH)
        target = repo / rows[0][0]
        target.write_text(target.read_text(encoding="utf-8") + "\nDRIFTED\n",
                           encoding="utf-8")
        assert spec_index.check(repo)
        spec_index.update(repo)
        assert spec_index.check(repo) == []


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"ok  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
