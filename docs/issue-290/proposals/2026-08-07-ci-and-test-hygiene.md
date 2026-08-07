---
status: proposed
files:
  - .github/workflows/on-the-record-tests.yml
  - test_approve_scope.py
  - test_gates.py
  - on-the-record/commands/run.md
  - docs/issue-290/reports/implementation/survey.md
  - docs/issue-290/proposals/2026-08-07-ci-and-test-hygiene.md
---

Scout skip condition: spec leaves no design decision open (see
`docs/issue-290/reports/implementation/survey.md`) — both issues name the
exact defect and the exact fix pattern already present in this repo.

## Request

Issues #290 and #294 describe one working system with no CI actually
verifying PRs. #290: no workflow runs the pytest suite on a PR head;
`test_approve_scope.py` monkeypatches `subprocess.run` process-globally
with no teardown, breaking 46/336 tests in a full-directory run; and
`test_gates.py:99` has a tautological `assert ... or True`. #294: the
acceptance step in `run.md` merges via a bare `gh pr merge` with no
requirement to read the PR's checks first, so real merges have landed
with zero automated verification.

## Constraints

- Fix stays inside the on-the-record repo checked out in this workspace;
  core and the 43 rulebook repos (also named in #290/#291) are separate
  repos, out of this write set.
- The restore pattern must match `test_spawn.py`'s existing
  `unittest.mock.patch` usage, not invent a new teardown style.
- The CI workflow must check out the PR head (not `main`, unlike
  `plan-aware-closes-gate.yml`, whose `ref: main` pin is deliberate for a
  different trust reason specific to that gate) since it needs to run the
  PR's own code.

## Rationale

Considered wrapping the monkeypatched tests in a manual
try/finally that reassigns `spawn.subprocess.run = subprocess.run`
afterward, instead of `mock.patch`. Rejected: `test_spawn.py` already
established `mock.patch("spawn.subprocess.run", ...)` as the house
pattern in this same repo (lines 267, 293), and a hand-rolled
try/finally is one exception path away from leaking the same bug this
issue reports — `mock.patch` restores on exception unconditionally,
which a bare reassignment does not.

Considered registering the new workflow as a required check via the
GitHub API/branch-protection settings inside this PR, to directly close
#294's "no checks to look at" branch. Rejected for this write set: this
session has no repo-admin scope to touch branch protection, and
`plan-aware-closes-gate.yml`'s own header comment documents that even
for the existing gate, required-check registration was deliberately left
to a manual Settings step outside the PR that adds the workflow (see
`docs/issue-245/reports/implementation.md`, referenced in that file's
header). The proposal instead names it explicitly in Out of scope so it
is not silently dropped.

## What will be done

- Add `.github/workflows/on-the-record-tests.yml`: triggers on
  `pull_request` against `main`, checks out the PR head (default
  `actions/checkout@v4` ref, no `ref: main` override), sets up Python
  3.11, installs no extra deps (repo has none beyond stdlib per
  `pytest.ini`), and runs `pytest -q`.
- In `test_approve_scope.py`, replace both process-global
  `spawn.subprocess.run = fake_run` assignments (currently at the lines
  the issue calls out as :57 and :98) with
  `with mock.patch("spawn.subprocess.run", fake_run):` wrapping the
  assertions that follow, so the patch is scoped to the test and restored
  on exit — matching `test_spawn.py`'s existing pattern. Add the
  `from unittest import mock` import.
- In `test_gates.py:99`, delete the `or True` so the assertion can
  actually fail: `assert "커밋안됨" not in v`.
- In `on-the-record/commands/run.md`, amend the "결과 수용" bullet
  (lines 229-230) to require reading `gh pr checks <n>` before merging,
  refuse merge on any failing or missing required check, and state the
  explicit branch for "no checks exist" (escalate rather than merge on
  the PR body's self-report alone), per #294's Acceptance criteria.

## Out of scope

- Core repo and the 43 rulebook repos' missing CI (#290's cross-repo
  half, #291) — not checked out here, separate repositories.
- Registering the new workflow as a required check in GitHub branch
  protection settings — needs a manual Settings step outside PR scope
  (see Rationale).
- T3 (core's harnesses collapsing "denied for the wrong reason" into exit
  2) and T5 (technical-feasibility suites skip-passing) from #290 — those
  live in core/rulebook repos, out of this write set.
- `approve-scope`'s `/scope`-vs-`/role` mismatch and comment pagination,
  explicitly called out in `run.md` as issue #224's scope, not touched
  here.

## How you'll know it worked

- `pytest -q` over the whole on-the-record directory passes (no
  cross-file monkeypatch bleed).
- `test_gates.py`'s `t_rulebook_version_is_recorded` can actually fail if
  `커밋안됨` leaks into a clean version string.
- The new workflow file is present and its `on: pull_request` step
  checks out the PR head, confirmed by reading the YAML (no live PR
  needed to confirm this structurally).
- `run.md`'s acceptance bullet names `gh pr checks` as a required
  precondition and states the no-checks branch explicitly.
