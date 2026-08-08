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
