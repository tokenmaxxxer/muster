#!/usr/bin/env python3
"""issue #398 — 중복 테스트 모듈 베이스네임 게이트(`duplicate_test_basenames`)
단위 테스트.

네트워크 없이, 임시 디렉터리에 만든 파일트리 위에서 돈다 —
`test_closes_gate_ci.py`와 같은 오프라인 관례.

파일명 참고: proposal(docs/issue-398/proposals/2026-08-07-...md)은 이 파일을
`gates/test_gates.py`로 두라고 적었으나, 그 이름 자체가 루트 `test_gates.py`와
바로 이 파일이 검사하는 충돌 모양(패키지 경계 없는 동일 베이스네임)을
재현한다 — 게이트를 추가하면서 게이트가 막으려는 상태를 저장소에 만드는
꼴이라 `test_duplicate_test_basenames.py`로 바꿔 붙였다. 자세한 내용은
docs/issue-398/reports/implementation.md "Rationale for deviations" 참조.

  python3 gates/test_duplicate_test_basenames.py
"""
from __future__ import annotations
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates


def _tree(files: dict[str, str]) -> Path:
    d = Path(tempfile.mkdtemp())
    for path, content in files.items():
        f = d / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
    return d


def t_duplicate_test_basenames_catches_reintroduced_collision():
    # #330/#337 의 실물 사고를 그대로 재현한다: gates/test_gates.py 와 루트
    # test_gates.py, 둘 다 __init__.py 없는 디렉터리 아래.
    d = _tree({
        "test_gates.py": "def t_x(): pass\n",
        "gates/test_gates.py": "def t_y(): pass\n",
        "gates/gates.py": "\n",
    })
    try:
        bad = gates.duplicate_test_basenames(d)
        assert bad and "test_gates.py" in bad[0], bad
        assert "test_gates.py" in bad[0] and "gates/test_gates.py" in bad[0], bad
    finally:
        shutil.rmtree(d)


def t_duplicate_test_basenames_passes_on_current_tree():
    # 회귀 가드: 지금 저장소 자체(리네임 후)에서는 걸리지 않아야 한다.
    root = Path(__file__).parent.parent
    bad = gates.duplicate_test_basenames(root)
    assert bad == [], bad


def t_duplicate_test_basenames_ignores_directories_with_init_py():
    # __init__.py 가 있는 디렉터리는 pytest 가 패키지로 취급해 이름공간이
    # 안 겹친다 — 검사 대상에서 빠져야 한다.
    d = _tree({
        "a/__init__.py": "",
        "a/test_x.py": "def t_a(): pass\n",
        "b/test_x.py": "def t_b(): pass\n",
    })
    try:
        bad = gates.duplicate_test_basenames(d)
        assert bad == [], bad
    finally:
        shutil.rmtree(d)


def t_duplicate_test_basenames_passes_with_no_collision():
    d = _tree({
        "test_a.py": "def t_a(): pass\n",
        "gates/test_b.py": "def t_b(): pass\n",
    })
    try:
        assert gates.duplicate_test_basenames(d) == []
    finally:
        shutil.rmtree(d)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
