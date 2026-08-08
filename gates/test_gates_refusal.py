#!/usr/bin/env python3
"""issue #476 H2 — `gates/gates.py`의 `record_refusal_reasoned` 및
확장된 `loop_state` enum(record_enums) 단위 테스트.

네트워크 없이, 실제 git 저장소(임시 디렉터리에 초기화) 위에서 돈다 —
`test_orphaned_references.py`와 같은 오프라인 관례.

파일명은 제안서의 `gates/test_gates.py`가 아니라 `test_gates_refusal.py`다 —
빌드 중 발견: 저장소 루트에 이미 `test_gates.py`(gates.py 전체 자체점검)가
있어 베이스네임이 충돌한다(`duplicate_test_basenames` 게이트가 바로 이
충돌 모양을 막는 것). 같은 이름은 `__init__.py` 경계 없이 pytest 수집을
깨뜨린다.

  python3 gates/test_gates_refusal.py
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gates


def _run(*args, cwd):
    p = subprocess.run(["git", "-C", str(cwd), *args],
                        capture_output=True, text=True)
    assert p.returncode == 0, (args, p.stdout, p.stderr)
    return p.stdout


def _repo_with_record(record_body: str, role: str = "implementation"):
    """origin/main 에 빈 상태를 커밋하고, HEAD 에서
    docs/issue-476/reports/<role>.md 를 record_body 로 추가한 임시
    git repo. 정리는 호출자 책임(tempfile.TemporaryDirectory 를 쓰지 않는
    이유는 `test_orphaned_references.py`와 같은 관례를 따르기 위해서)."""
    d = Path(tempfile.mkdtemp())
    _run("init", "-q", "-b", "main", cwd=d)
    _run("config", "user.email", "t@example.com", cwd=d)
    _run("config", "user.name", "t", cwd=d)
    (d / "README.md").write_text("base")
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "base", cwd=d)
    _run("update-ref", "refs/remotes/origin/main", "HEAD", cwd=d)
    _run("checkout", "-q", "-b", "issue-476/implementation", cwd=d)
    record = d / f"docs/issue-476/reports/{role}.md"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(record_body)
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "head", cwd=d)
    return d


def t_refused_state_without_reason_is_blocked():
    d = _repo_with_record("---\nloop_state: refused\n---\nbody\n")
    bad = gates.record_refusal_reasoned(d, {})
    assert len(bad) == 1, bad
    assert "reason" in bad[0], bad


def t_refused_state_with_reason_is_clean():
    d = _repo_with_record(
        "---\nloop_state: refused\nreason: no expert need found\n---\nbody\n")
    bad = gates.record_refusal_reasoned(d, {})
    assert bad == [], bad


def t_not_needed_state_without_reason_is_blocked():
    d = _repo_with_record("---\nloop_state: not-needed\n---\nbody\n")
    bad = gates.record_refusal_reasoned(d, {})
    assert len(bad) == 1, bad


def t_cannot_verify_state_without_reason_is_blocked():
    d = _repo_with_record("---\nloop_state: cannot-verify\n---\nbody\n")
    bad = gates.record_refusal_reasoned(d, {})
    assert len(bad) == 1, bad


def t_positive_path_state_is_unaffected_by_reason_absence():
    d = _repo_with_record("---\nloop_state: landed\n---\nbody\n")
    bad = gates.record_refusal_reasoned(d, {})
    assert bad == [], bad


def t_empty_reason_field_still_blocks():
    d = _repo_with_record("---\nloop_state: refused\nreason:\n---\nbody\n")
    bad = gates.record_refusal_reasoned(d, {})
    assert len(bad) == 1, bad


def t_record_enums_accepts_new_refusal_values():
    d = _repo_with_record(
        "---\nloop_state: cannot-verify\nreason: environment unreachable\n"
        "---\nbody\n")
    bad = gates.record_enums(d, {})
    assert bad == [], bad


def t_record_enums_still_rejects_unknown_value():
    d = _repo_with_record("---\nloop_state: made-up-value\n---\nbody\n")
    bad = gates.record_enums(d, {})
    assert len(bad) == 1, bad
    assert "enum" in bad[0], bad


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
