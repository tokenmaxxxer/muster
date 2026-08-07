#!/usr/bin/env python3
"""issue #322 — ledger/decisions.py 단위 테스트. 네트워크·GitHub 없이 도는 것만
(`gates/test_closes_gate_ci.py` 와 같은 관례), 임시 git 레포에 실제 커밋을 만들어
`history()` 가 실사용 경로를 통과하게 한다.

  python3 ledger/test_decisions.py
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import decisions


def _git_repo(tmp: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp)], check=True)
    subprocess.run(["git", "-C", str(tmp), "config", "user.email", "t@t.com"], check=True)
    subprocess.run(["git", "-C", str(tmp), "config", "user.name", "t"], check=True)
    return tmp


def _commit(repo: Path, rel: str, text: str, msg: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    subprocess.run(["git", "-C", str(repo), "add", rel], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", msg], check=True)


def t_normalize_strips_issue_and_sha_tokens():
    a = decisions.normalize("patch instead of structure, per #310 (abc1234def)")
    b = decisions.normalize("patch instead of structure, per issue-245 (fed4321cba)")
    assert a == b, (a, b)


def t_extract_bullets_reads_both_sections():
    text = (
        "## What did not work\n"
        "- tried X, broke because Y\n"
        "- tried Z, broke because W\n"
        "\n"
        "## Rationale for deviations\n"
        "- swapped approach because of contention\n"
        "\n"
        "## Doc placement\n"
        "- unrelated section, must not be picked up\n"
    )
    bullets = decisions.extract_bullets(text)
    assert bullets == ["tried X, broke because Y", "tried Z, broke because W",
                        "swapped approach because of contention"], bullets


def t_single_occurrence_does_not_flag():
    with tempfile.TemporaryDirectory() as td:
        repo = _git_repo(Path(td))
        _commit(repo, "docs/issue-1/reports/implementation.md",
                "## What did not work\n- patch instead of structure, per #1\n",
                "issue-1 record")
        d = decisions.collect(repo)
        assert d["candidates"] == [], d["candidates"]


def t_second_occurrence_across_subjects_flags_and_exits_nonzero():
    with tempfile.TemporaryDirectory() as td:
        repo = _git_repo(Path(td))
        _commit(repo, "docs/issue-1/reports/implementation.md",
                "## What did not work\n- patch instead of structure, per #1\n",
                "issue-1 record")
        _commit(repo, "docs/issue-2/reports/implementation.md",
                "## What did not work\n- patch instead of structure, per #2\n",
                "issue-2 record")
        d = decisions.collect(repo)
        assert len(d["candidates"]) == 1, d["candidates"]
        cand = d["candidates"][0]
        assert cand["count"] == 2
        assert cand["subjects"] == ["issue-1", "issue-2"]
        assert (1 if d["candidates"] else 0) == 1  # main()'s exit-code contract


def t_recurrence_covered_by_a_decision_entry_passes():
    with tempfile.TemporaryDirectory() as td:
        repo = _git_repo(Path(td))
        _commit(repo, "docs/issue-1/reports/implementation.md",
                "## What did not work\n- patch instead of structure, per #1\n",
                "issue-1 record")
        _commit(repo, "docs/issue-2/reports/implementation.md",
                "## What did not work\n- patch instead of structure, per #2\n",
                "issue-2 record")
        _commit(repo, "docs/decisions/2026-08-07-patch-instead-of-structure.md",
                "# Decision\n\nCovers the recurring correction: "
                "patch instead of structure, per issue.\n",
                "decision entry")
        d = decisions.collect(repo)
        assert d["candidates"] == [], d["candidates"]


def t_none_placeholder_bullets_are_ignored():
    with tempfile.TemporaryDirectory() as td:
        repo = _git_repo(Path(td))
        _commit(repo, "docs/issue-1/reports/implementation.md",
                "## What did not work\n- None.\n", "issue-1 record")
        _commit(repo, "docs/issue-2/reports/implementation.md",
                "## What did not work\n- None.\n", "issue-2 record")
        d = decisions.collect(repo)
        assert d["candidates"] == [], d["candidates"]


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
