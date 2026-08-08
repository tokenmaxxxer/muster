#!/usr/bin/env python3
"""issue #517 — `record-scaffold.sh` 테스트.

`gates/test_record_lint.py`와 같은 오프라인 관례: 임시 git 저장소 위에서
스캐폴더를 실행하고, 그 산출물을 `record_lint`로 검사한다.

  python3 on-the-record/hooks/test_record_scaffold.py
  python3 -m pytest on-the-record/hooks/test_record_scaffold.py -q
"""
from __future__ import annotations
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).parent
PLUGIN_ROOT = HOOKS_DIR.parent
REPO_ROOT = PLUGIN_ROOT.parent
GATES_DIR = REPO_ROOT / "gates"
SCAFFOLD_SH = HOOKS_DIR / "record-scaffold.sh"

sys.path.insert(0, str(GATES_DIR))
import record_lint


def _run(*args, cwd):
    p = subprocess.run(["git", "-C", str(cwd), *args],
                        capture_output=True, text=True)
    assert p.returncode == 0, (args, p.stdout, p.stderr)
    return p.stdout


def _empty_repo():
    d = Path(tempfile.mkdtemp())
    _run("init", "-q", "-b", "main", cwd=d)
    _run("config", "user.email", "t@example.com", cwd=d)
    _run("config", "user.name", "t", cwd=d)
    (d / "README.md").write_text("base")
    _run("add", "-A", cwd=d)
    _run("commit", "-q", "-m", "base", cwd=d)
    _run("update-ref", "refs/remotes/origin/main", "HEAD", cwd=d)
    _run("checkout", "-q", "-b", "issue-517/implementation", cwd=d)
    return d


def _scaffold(root: Path, role: str, issue: str):
    p = subprocess.run([str(SCAFFOLD_SH), role, issue, str(root)],
                        capture_output=True, text=True)
    assert p.returncode == 0, (p.stdout, p.stderr)
    return root / "docs" / f"issue-{issue}" / "reports" / f"{role}.md"


def t_raw_output_fails_only_on_placeholder_violations():
    d = _empty_repo()
    record = _scaffold(d, "implementation", "999")
    assert record.exists()
    bad = record_lint.lint_record(record)
    assert bad, "scaffold placeholders should still trip record_lint"
    for b in bad:
        assert "PLACEHOLDER" in b or "loop_state" in b, b


def t_refuses_to_overwrite_existing_record():
    d = _empty_repo()
    _scaffold(d, "implementation", "999")
    p = subprocess.run([str(SCAFFOLD_SH), "implementation", "999", str(d)],
                        capture_output=True, text=True)
    assert p.returncode != 0, p.stdout


def t_filled_in_copy_passes_clean():
    d = _empty_repo()
    record = _scaffold(d, "implementation", "999")
    text = record.read_text()
    text = text.replace("PLACEHOLDER: loop_state", "in-progress")
    text = re.sub(r"PLACEHOLDER: [^\n]*", "filled in.", text)
    record.write_text(text)
    bad = record_lint.lint_record(record)
    assert bad == [], bad


def t_declares_every_role_record_field_as_placeholder():
    d = _empty_repo()
    record = _scaffold(d, "technical-feasibility", "999")
    text = record.read_text()
    assert "verdict: PLACEHOLDER: verdict" in text, text
    assert "loop_state: PLACEHOLDER: loop_state" in text, text


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
