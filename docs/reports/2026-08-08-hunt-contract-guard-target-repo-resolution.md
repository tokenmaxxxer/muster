---
proposal: docs/issue-443/proposals/2026-08-08-contract-guard-target-repo-resolution.md
---

# Hunt record — contract-guard-target-repo-resolution

## after-proposal — stance 1: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: NO FINDING
Seed: git show 8e7d1b4 --stat (docs-only, 2 files, 223 lines) — proposal docs/issue-443/proposals/2026-08-08-contract-guard-target-repo-resolution.md, survey docs/issue-443/reports/implementation/survey.md
cap_seconds: 60
tier: default
diff_stat_lines: 223
started_at: 2026-08-08T00:00:00Z (approx, not captured precisely)
ended_at: 2026-08-08T00:03:00Z (approx)

Checked candidates for a build-time path missing from the frozen write set
{contract-guard.sh, test_contract_guard.py}:

- hooks.json (on-the-record/hooks/hooks.json) wires contract-guard.sh by
  path only, with no args/CG_PAYLOAD reference that the proposal's changes
  would invalidate — no edit needed there.
- No docs/specs/enforcement-boundary.md or similar file exists in the repo
  (`find on-the-record -iname "*enforcement-boundary*"` — empty), and no
  markdown anywhere references contract-guard.sh
  (`grep -rln "contract-guard" on-the-record --include="*.md"` — empty), so
  there's no doc that would go stale.
- Root-level pytest.ini has no testpaths/norecursedirs restriction, and
  conftest.py's autouse fixture only asserts subprocess.run/spawn
  attributes are unpatched at session end — it does not scope test
  collection to test_gates.py, so
  on-the-record/hooks/test_contract_guard.py will be collected by the
  existing `pytest -q` CI step
  (.github/workflows/on-the-record-tests.yml) without config changes.
- No existing test infra file (no conftest.py under on-the-record/hooks/,
  no tests/fixtures/ tree used elsewhere for a comparable "target repo"
  checkout) is referenced by the proposal's "mirror the git -C fixture
  pattern" language as a shared file the new test would import from
  test_gates.py tests other tools (gates/spawn/ci/flows) and its git
  fixtures are private to that module — the proposal's test file is
  self-contained (invokes contract-guard.sh as a subprocess with its own
  crafted CG_PAYLOAD/fake-gh-shim/target-repo tmp dirs), so no shared
  fixture file is actually needed as a write target.
- contract-guard.sh is already executable (100755) so no chmod/permission
  file is needed.

Nothing found that phase-2 execution mechanically requires touching
outside the frozen write set. Did not chase this further (e.g. whether
GitHub Actions' ubuntu-latest runner has `gh` preinstalled) since it isn't
reproducible from this sandbox and isn't a write-set gap either way.

## before-landing — stance: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — when a command has both a leading `cd <path> &&` prefix and an explicit `-R`/`--repo owner/repo` flag naming a *different* repo, contract-guard.sh silently judges the `cd`-target repo's PR/issue and drops the `-R` flag entirely from its own subprocess calls, so a phase-2 contract violation in the repo the merge would actually run against (the `-R` repo) goes undetected and the merge is silently allowed (exit 0).
Kind: silent-failure
Seed: on-the-record/hooks/contract-guard.sh (uncommitted working tree), on-the-record/hooks/test_contract_guard.py (new, 193 lines) — issue #443 phase-2 target-repo-resolution fix
cap_seconds: 180
tier: default
diff_stat_lines: >200 (contract-guard.sh changes + new 193-line test file)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:07:00Z

### Root cause
In `contract-guard.sh`'s embedded Python: `target_repo_flag` is only ever set when `target_cwd is None` (see the `if target_cwd is None:` guards after both the URL-match and repo-flag-match branches). Once a leading `cd <path> &&` prefix sets `target_cwd`, `target_repo_flag` stays `None` even if the command also carries an explicit repo-selector flag (or a full PR URL for a different repo) after the intercepted subcommand. The lookup helper then calls the CLI with `cwd=target_cwd` and no repo-selector flag at all, so every lookup resolves against whatever repo the `cd`-target checkout happens to be, not the repo the invocation would actually operate on via the explicit flag. `approvers.md` is likewise read from `target_cwd`, not the flagged repo. There is no state tracking "the repo flag disagrees with the cd target" — the regexes for `cd`, URL, and repo-flag are evaluated independently with no cross-check, and precedence silently favors `cd` while discarding the flag.

### Reproduce
Ad-hoc script using the test module's existing harness (`_repo_dir`, `_approve_comment`, `_run_guard` from `on-the-record/hooks/test_contract_guard.py`):

```python
import sys
sys.path.insert(0, "on-the-record/hooks")
from test_contract_guard import _repo_dir, _approve_comment, _run_guard
import tempfile, pathlib

with tempfile.TemporaryDirectory() as td:
    tmp_path = pathlib.Path(td)
    cwd_dir = _repo_dir(tmp_path, "cwdrepo", ["alice"])
    target_dir = _repo_dir(tmp_path, "targetrepo", ["bob"])  # the cd checkout
    fixtures = {
        "cwd_map": {str(cwd_dir): "cwd", str(target_dir): "target"},
        "repos": {
            "target": {  # the cd-target repo: looks compliant
                "pr_body": "Closes #9",
                "issue_comments": [_approve_comment(9, "bob")],
            },
            "other/repo": {  # the repo the command's flag actually names: violates phase-2
                "pr_body": "no closing keyword, just #9",
                "issue_comments": [_approve_comment(9, "eve")],
            },
        },
    }
    flag = "-" + "R"
    cmd = "cd " + str(target_dir) + " && gh pr merge 7 " + flag + " other/repo --merge"
    r = _run_guard(cmd, fixtures, tmp_path, cwd=cwd_dir)
    print("returncode:", r.returncode)
    print("stderr:", r.stderr)
```

### Observed
```
returncode: 0
stderr:
```
The hook exits 0 (allow) with no stderr, even though the intercepted command names `other/repo` via the repo flag (which real CLI semantics would honor over the process cwd), and that repo's PR #7 body ("no closing keyword, just #9") does not close phase-2 issue #9 there.

### Expected
The hook should either judge the flag-named repo (pass the same repo flag through regardless of any `cd` prefix, since an explicit repo selector on the invocation itself overrides the process cwd) and deny the merge, or — if it cannot safely resolve conflicting `cd`/flag signals — treat this as an explicit unreached/fail-open case with a comment, the same honest treatment given to the "flag present but no local checkout" and "no explicit PR number" cases elsewhere in the same file. Instead it silently substitutes the wrong repo's data and returns a false "no violation" verdict.
