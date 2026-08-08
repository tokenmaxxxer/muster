#!/usr/bin/env python3
"""issue #415 — `gates.repo_scope.check_repo_scope` 단위테스트.

네트워크 없이 도는, 다른 게이트 테스트와 같은 관례. 저장소 루트에 두는
이유는 #415 의 자체 승인된 proposal(`docs/issue-415/proposals/implementation.md`
item 2)이 이 경로를 그대로 지정했다 — `gates/` 아래가 아니다.

  python3 test_repo_scope_gate.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "gates"))
import repo_scope


def t_unscoped_absence_claim_flags():
    text = "Capability X does not exist in this codebase."
    bad = repo_scope.check_repo_scope(text)
    assert bad, "unscoped absence claim must be flagged"


def t_scoped_absence_claim_passes():
    text = ("Capability X does not exist as of a1b2c3d in the "
            "thaki-agent-security-controller checkout.")
    assert repo_scope.check_repo_scope(text) == []


def t_file_anchored_claim_passes():
    text = "Function Z does not exist in `foo.py:12`."
    assert repo_scope.check_repo_scope(text) == []


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
