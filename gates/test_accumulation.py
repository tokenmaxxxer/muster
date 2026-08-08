#!/usr/bin/env python3
"""issue #424 — `accumulation.check_accumulation_claim` 단위테스트.

네트워크 없이, 임시 git 저장소 위에서 돈다.

  python3 gates/test_accumulation.py
"""
from __future__ import annotations
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import accumulation

_CI_PY_WITH_6_CALLS = "\n".join(
    f"subprocess.run(['gh', 'api', 'x{i}'])" for i in range(6))
_CI_PY_WITH_7TH_CALL = _CI_PY_WITH_6_CALLS + "\nsubprocess.run(['gh', 'api', 'x7'])\n"


def _repo(files: dict[str, str]) -> Path:
    d = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    for path, content in files.items():
        f = d / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    subprocess.run(["git", "-c", "user.email=t@t.com", "-c", "user.name=t",
                    "commit", "-q", "-m", "init"], cwd=d, check=True)
    return d


def t_shape1_seventh_gh_call_without_accumulation_line_flags():
    d = _repo({"gates/ci.py": "import subprocess\n" + _CI_PY_WITH_7TH_CALL})
    try:
        bad = accumulation.check_accumulation_claim(d, "## Request\nfoo\n")
        assert bad, "a 7th unguarded inline gh call with no ## Accumulation must flag"
    finally:
        shutil.rmtree(d)


def t_shape1_seventh_gh_call_with_accumulation_line_passes():
    d = _repo({"gates/ci.py": "import subprocess\n" + _CI_PY_WITH_7TH_CALL})
    try:
        body = "## Accumulation\nAfter N more, ci.py grows one gh call per row.\n"
        assert accumulation.check_accumulation_claim(d, body) == []
    finally:
        shutil.rmtree(d)


def t_change_touching_neither_shape_returns_empty_regardless_of_body():
    d = _repo({"README.md": "hello\n"})
    try:
        assert accumulation.check_accumulation_claim(d, "## Request\nfoo\n") == []
        assert accumulation.check_accumulation_claim(d, "no heading at all") == []
    finally:
        shutil.rmtree(d)


def t_shape5_roles_json_touch_without_accumulation_line_flags():
    d = _repo({"roles/product.json": "{}\n"})
    try:
        bad = accumulation.check_accumulation_claim(d, "## Request\nfoo\n")
        assert bad, "touching roles/*.json with no ## Accumulation must flag"
    finally:
        shutil.rmtree(d)


def t_shape1_heading_only_no_body_still_flags():
    # issue #512 requirement 3: heading-existence used to be enough to
    # pass; after the field-presence strengthening, an empty body must
    # still flag.
    d = _repo({"gates/ci.py": "import subprocess\n" + _CI_PY_WITH_7TH_CALL})
    try:
        bad = accumulation.check_accumulation_claim(d, "## Accumulation\n\n## Out of scope\nx\n")
        assert bad, "an empty ## Accumulation body must still flag (issue #512)"
    finally:
        shutil.rmtree(d)


def t_shape1_heading_with_body_passes():
    d = _repo({"gates/ci.py": "import subprocess\n" + _CI_PY_WITH_7TH_CALL})
    try:
        body = "## Accumulation\nAfter N more, ci.py grows one gh call per row.\n## Out of scope\nx\n"
        assert accumulation.check_accumulation_claim(d, body) == []
    finally:
        shutil.rmtree(d)


def t_non_git_directory_fails_closed_not_silently_empty():
    # before-landing warrant hunt (stance: malformed-input-goes-silent):
    # a non-git `work` directory must not silently return [] — that would
    # hide a real shape-1/5 violation behind a git-call failure.
    d = Path(tempfile.mkdtemp())
    (d / "roles").mkdir()
    (d / "roles" / "product.json").write_text("{}\n")
    try:
        bad = accumulation.check_accumulation_claim(d, "## Request\nfoo\n")
        assert bad, "non-git work dir must fail closed, not return [] silently"
    finally:
        shutil.rmtree(d)


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
