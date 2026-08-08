#!/usr/bin/env python3
"""issue #517 — `gates.record_lint` 단일 패스 집계 테스트.

`test_gates_refusal.py`와 같은 오프라인 관례: 임시 디렉터리에 실제 git
저장소를 만들고 그 위에서 돈다. 네트워크 없음.

  python3 gates/test_record_lint.py
  python3 -m pytest gates/test_record_lint.py -q
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import record_lint


def _run(*args, cwd):
    p = subprocess.run(["git", "-C", str(cwd), *args],
                        capture_output=True, text=True)
    assert p.returncode == 0, (args, p.stdout, p.stderr)
    return p.stdout


def _repo_with_record(record_body: str, role: str = "implementation",
                       rel: str | None = None):
    """`test_gates_refusal.py::_repo_with_record`와 같은 관례: origin/main 에
    빈 상태를 커밋하고, HEAD 에서 레코드 하나를 추가한 임시 git repo. 정리는
    호출자 책임이 아니다(임시 디렉터리, 프로세스 종료 시 OS 가 회수)."""
    d = Path(tempfile.mkdtemp())
    _run("init", "-q", "-b", "main", cwd=d)
    _run("config", "user.email", "t@example.com", cwd=d)
    _run("config", "user.name", "t", cwd=d)
    (d / "README.md").write_text("base")
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "base", cwd=d)
    _run("update-ref", "refs/remotes/origin/main", "HEAD", cwd=d)
    _run("checkout", "-q", "-b", "issue-517/implementation", cwd=d)
    rel = rel or f"docs/issue-517/reports/{role}.md"
    record = d / rel
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(record_body)
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "head", cwd=d)
    return d, record


def t_one_invocation_reports_all_distinct_violations():
    """네 종류 이상의 서로 다른 체커가 같은 레코드 하나에서 동시에 위반을
    내고, `lint_record` 한 번 호출이 전부를 보고한다 — 첫 실패에서 멈추지
    않는다(issue #517 Acceptance)."""
    body = (
        "---\n"
        "loop_state: landed\n"
        "---\n\n"
        "# record\n\n"
        "body references `gates/does-not-exist-xyz.py`.\n\n"
        "We completed 5 of 10 checks without derivation.\n\n"
        "- claim — checked: some::test — result: unverifiable\n"
        "- unverifiable:\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)

    assert any("Acceptance verification" in b for b in bad), bad   # missing required heading
    assert any("#330" in b for b in bad), bad                      # broken code reference
    assert any("#333" in b for b in bad), bad                      # bare count claim
    assert any("#310" in b for b in bad), bad                      # unverifiable, no reason
    assert any("#331" in b for b in bad), bad                      # checked-claim, no reason
    assert len(bad) >= 4, bad


def t_clean_record_yields_no_violations():
    body = (
        "---\n"
        "loop_state: in-progress\n"
        "---\n\n"
        "# record\n\nbody, no claims.\n")
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert bad == [], bad


def t_invalid_enum_value_is_reported():
    body = "---\nloop_state: bogus-state\n---\n\nbody\n"
    d, record = _repo_with_record(body)
    bad = record_lint.lint_record(record)
    assert any("enum" in b for b in bad), bad


def t_repo_with_no_records_yields_explicit_empty_state():
    d = Path(tempfile.mkdtemp())
    _run("init", "-q", "-b", "main", cwd=d)
    _run("config", "user.email", "t@example.com", cwd=d)
    _run("config", "user.name", "t", cwd=d)
    (d / "README.md").write_text("base")
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "base", cwd=d)

    assert record_lint.find_records(d) == []
    rc = record_lint.main([str(d)])
    assert rc == 0


def t_non_record_path_is_reported_not_silently_skipped():
    d = Path(tempfile.mkdtemp())
    _run("init", "-q", "-b", "main", cwd=d)
    off_path = d / "docs" / "notes.md"
    off_path.parent.mkdir(parents=True, exist_ok=True)
    off_path.write_text("not a record")
    bad = record_lint.lint_record(off_path)
    assert bad and "레코드 경로 형태" in bad[0], bad


def _run_all():
    tests = [(n, f) for n, f in globals().items()
             if n.startswith("t_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except AssertionError as e:
            failed += 1
            print(f"FAIL {name}: {e}")
        else:
            print(f"ok {name}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
