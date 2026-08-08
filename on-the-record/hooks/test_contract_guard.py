"""Tests for contract-guard.sh target-repo resolution (issue #443).

Invokes contract-guard.sh as a subprocess with CG_PAYLOAD set, and a fake
`gh` shim on PATH that resolves canned fixtures by repo — either from a
`-R owner/repo` flag on the argv, or from the subprocess's own cwd (mirrors
how the real hook now calls `gh` with cwd=<target> for the `cd &&` form).
"""
import json
import os
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "contract-guard.sh"

FAKE_GH = """#!/usr/bin/env python3
import json, os, sys

fixtures = json.load(open(os.environ["GH_FIXTURES"]))
cwd_map = fixtures.get("cwd_map", {})
argv = sys.argv[1:]

repo = None
for i, a in enumerate(argv):
    if a in ("-R", "--repo") and i + 1 < len(argv):
        repo = argv[i + 1]
    elif a.startswith("--repo="):
        repo = a.split("=", 1)[1]
if repo is None:
    repo = cwd_map.get(os.getcwd(), cwd_map.get("__default__"))

data = fixtures.get("repos", {}).get(repo)
if data is None:
    sys.exit(1)

if argv[:2] == ["pr", "view"]:
    print(json.dumps({"body": data["pr_body"], "number": int(argv[2])}))
elif argv[:2] == ["issue", "view"]:
    print(json.dumps(data.get("issue_comments", [])))
else:
    sys.exit(1)
"""


def _write_fake_gh(bin_dir: Path):
    p = bin_dir / "gh"
    p.write_text(FAKE_GH)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def _approve_comment(issue, login):
    return {"body": f"APPROVE issue-{issue}/implementation", "author": {"login": login}}


def _run_guard(cmd, fixtures, tmp_path, cwd=None):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    _write_fake_gh(bin_dir)
    fixtures_path = tmp_path / "fixtures.json"
    fixtures_path.write_text(json.dumps(fixtures))

    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["GH_FIXTURES"] = str(fixtures_path)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True,
        env=env, cwd=str(cwd) if cwd else None, timeout=20,
    )


def _repo_dir(tmp_path, name, approvers):
    d = tmp_path / name
    (d / "docs" / "specs").mkdir(parents=True)
    (d / "docs" / "specs" / "approvers.md").write_text(
        "\n".join(f"- {a}" for a in approvers) + "\n"
    )
    return d


def test_cross_repo_same_number_judges_target_not_cwd(tmp_path):
    """Red-green: cwd repo and `cd <target>` repo both have PR #7 / issue
    #9, different bodies/approval — the fixed hook must judge the target
    repo, not cwd."""
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    target_dir = _repo_dir(tmp_path, "targetrepo", ["bob"])

    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd", str(target_dir): "target"},
        "repos": {
            "cwd": {
                "pr_body": "Closes #9",  # would PASS if judged (wrong repo)
                "issue_comments": [_approve_comment(9, "alice")],
            },
            "target": {
                "pr_body": "no closing keyword here, just #9",  # must FAIL
                "issue_comments": [_approve_comment(9, "bob")],
            },
        },
    }
    r = _run_guard(f"cd {target_dir} && gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir)
    assert r.returncode == 2, r.stderr
    assert "phase-2 issue (#9)" in r.stderr


def test_repo_flag_targets_repo_but_no_local_approvers_is_unreached(tmp_path):
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "owner/target": {
                "pr_body": "no closing keyword, just #9",
                "issue_comments": [_approve_comment(9, "bob")],
            },
        },
    }
    r = _run_guard("gh pr merge 7 -R owner/target --merge", fixtures, tmp_path, cwd=cwd_dir)
    assert r.returncode == 0, r.stderr  # explicit unreached: no local approvers.md for target


def test_full_pr_url_targets_repo_but_no_local_approvers_is_unreached(tmp_path):
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "owner/target": {
                "pr_body": "no closing keyword, just #9",
                "issue_comments": [_approve_comment(9, "bob")],
            },
        },
    }
    r = _run_guard(
        "gh pr merge https://github.com/owner/target/pull/7 --merge",
        fixtures, tmp_path, cwd=cwd_dir,
    )
    assert r.returncode == 0, r.stderr


def test_cd_prefix_reads_target_approvers_and_denies(tmp_path):
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    target_dir = _repo_dir(tmp_path, "targetrepo", ["bob"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd", str(target_dir): "target"},
        "repos": {
            "target": {
                "pr_body": "no closing keyword, just #9",
                "issue_comments": [_approve_comment(9, "bob")],
            },
        },
    }
    r = _run_guard(f"cd {target_dir} && gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir)
    assert r.returncode == 2, r.stderr
    assert "phase-2 issue (#9)" in r.stderr


def test_cd_prefix_allows_when_target_pr_closes_issue(tmp_path):
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    target_dir = _repo_dir(tmp_path, "targetrepo", ["bob"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd", str(target_dir): "target"},
        "repos": {
            "target": {
                "pr_body": "Closes #9",
                "issue_comments": [_approve_comment(9, "bob")],
            },
        },
    }
    r = _run_guard(f"cd {target_dir} && gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir)
    assert r.returncode == 0, r.stderr


def test_repo_flag_overrides_cd_prefix_when_they_disagree(tmp_path):
    """Regression for before-landing hunt finding: `cd <path> &&` combined
    with an explicit `-R other/repo` naming a *different* repo must not
    silently judge the `cd`-target repo and drop the flag — the flag wins
    (matching real `gh` semantics) and, with no local checkout of the
    flagged repo, falls into the explicit unreached/fail-open path rather
    than a false "compliant" verdict."""
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    target_dir = _repo_dir(tmp_path, "targetrepo", ["bob"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd", str(target_dir): "target"},
        "repos": {
            "target": {  # cd-target repo: looks compliant
                "pr_body": "Closes #9",
                "issue_comments": [_approve_comment(9, "bob")],
            },
            "other/repo": {  # -R-named repo: actually violates phase-2
                "pr_body": "no closing keyword, just #9",
                "issue_comments": [_approve_comment(9, "eve")],
            },
        },
    }
    cmd = f"cd {target_dir} && gh pr merge 7 -R other/repo --merge"
    r = _run_guard(cmd, fixtures, tmp_path, cwd=cwd_dir)
    assert r.returncode == 0, r.stderr  # explicit unreached, not a false-compliant allow


def test_no_repo_indicator_unchanged_cwd_behavior(tmp_path):
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd"},
        "repos": {
            "cwd": {
                "pr_body": "no closing keyword, just #9",
                "issue_comments": [_approve_comment(9, "alice")],
            },
        },
    }
    r = _run_guard("gh pr merge 7 --merge", fixtures, tmp_path, cwd=cwd_dir)
    assert r.returncode == 2, r.stderr
    assert "phase-2 issue (#9)" in r.stderr
