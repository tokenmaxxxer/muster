---
code_under_review: gates/ci.py, gates/test_closes_gate_ci.py
loop_state: phase-2-complete
open_findings: none
closed_checks:
  - check: "gates/test_closes_gate_ci.py — 43/43 pass locally
      (`python3 gates/test_closes_gate_ci.py`), including two new tests:
      t_fetch_ref_file_issues_gh_api_with_dash_x_get (drives the real
      `_fetch_ref_file`, not a mock of itself, and asserts the exact
      argv `subprocess.run` receives — confirmed red by temporarily
      reverting the `-X GET` argv and re-running, then restored) and
      t_fetch_ref_file_distinguishes_404_from_api_failure (404 -> (None,
      None), other failure -> (None, stderr))."
    ref: gates/test_closes_gate_ci.py:502-563
  - check: "closes-gate re-run against the six live PRs named in #284's
      acceptance test, using the same `gates/ci.py --pr <n> --autodetect
      --closes-only` entrypoint CI invokes, with no body edits: #337
      pass, #340 pass, #343 pass, #350 pass, #352 pass, #353 pass."
    ref: "manual run, this session"
---

# Implementation record — issue #388

## Why

`_fetch_ref_file` built its `gh api` call as `-f ref=<branch>` with no
`-X GET`. `gh api` switches the request method to POST as soon as any
`-f`/`-F` is supplied and no `-X` is given explicitly, so every record
lookup 404s regardless of whether the record exists. That silently made
`_phase2_record_evidence` return `False` unconditionally, killing #284's
whole alternative path (the six named PRs stayed red on `closes-gate`)
in exactly the way #369 was filed to fix, because #369's own test mocked
`subprocess.run` and so could not see a defect that lives entirely in
the argv handed to it.

## What was done

1. **Fix the call** (`gates/ci.py::_fetch_ref_file`, line ~189). Added
   `"-X", "GET"` to the argv. Chose `-X GET` over `?ref=` in the URL
   path because it is the smaller diff and keeps the existing
   `-f ref=<branch>` idiom `_pr_commit_messages` (`gates/ci.py:85-113`)
   already establishes for this codebase's `gh api` calls.

2. **Make the test able to fail on this.** The existing pinning test
   (`t_phase2_record_evidence_does_not_read_local_filesystem`) mocks
   `subprocess.run` itself and only asserts `cmd[:2] == ["gh", "api"]`
   plus that `ref=issue-245/implementation` appears somewhere in the
   argv — it does not check `-X GET`, so it passed against both the
   broken and the fixed call and could never catch this defect. Added
   `t_fetch_ref_file_issues_gh_api_with_dash_x_get`
   (`gates/test_closes_gate_ci.py:502`), which drives the real
   `_fetch_ref_file` (not `_phase2_record_evidence` mocking
   `_fetch_ref_file` out from under itself) and asserts `"-X" in cmd and
   cmd[cmd.index("-X") + 1] == "GET"`. Demonstrated red: reverted the
   `-X GET` argv in `gates/ci.py`, re-ran
   `python3 gates/test_closes_gate_ci.py`, watched this test fail with
   the exact "missing an explicit -X GET" assertion message, then
   restored the fix and re-ran to confirm all 43 pass. What it still
   does not cover: whether `gh` itself, given a well-formed argv,
   actually performs a GET against GitHub's API — that is `gh`'s own
   contract, outside this test's reach (a live `gh api` call against a
   real PR ref was also run manually this session and returned real
   record content, covering that gap for this run but not asserted in
   the suite).

3. **Distinguish file-absent from API-failed.** `_fetch_ref_file` now
   returns `(text, err)` instead of bare `text | None`: a 404
   (`returncode != 0` with `"404"` or `"Not Found"` in stderr) returns
   `(None, None)` — file genuinely absent; any other failure returns
   `(None, r.stderr)` — the caller can tell "not found" from "the API
   call itself broke". `_phase2_record_evidence` was updated to unpack
   the tuple; it still treats both as "no evidence" for gate purposes —
   the issue asked only that the two be distinguishable at the fetch
   layer, not that the gate change behavior on API failure. All five
   existing mocks of `ci._fetch_ref_file` across
   `gates/test_closes_gate_ci.py` were updated to return 2-tuples to
   match the new signature. Added
   `t_fetch_ref_file_distinguishes_404_from_api_failure`
   (`gates/test_closes_gate_ci.py:539`) covering both branches directly.

4. **Audit other `gh api` call sites.** Searched the whole tree
   (`grep -rn '"gh", "api"'`) and found three other sites:
   `gates/ci.py::_pr_commit_messages` (`--paginate --slurp`, no `-f`,
   already a plain GET — fine), `gates/closure_sweep.py:138` and
   `spawn.py:1814` (both `-f body=<...>` against `.../comments` — `-f`
   here is intentional: these calls *create* a comment and want POST,
   which is exactly what `-f` without `-X GET` produces). None of the
   other three share this defect's shape.

## Acceptance — what was actually run, and its scope

Ran, this session, from the branch with the fix applied locally (not
yet merged to `main`):
`python3 gates/ci.py . --pr <n> --autodetect --closes-only` for
`<n>` in 337, 340, 343, 350, 352, 353 — the same entrypoint and same
`--closes-only` mode the `.github/workflows` required check invokes,
making real `gh api`/`gh pr view` calls against the live PRs, no PR
body edited. All six: `게이트 통과` (gate passed).

**What this does and does not establish:** this exercises the exact
fixed logic against live GitHub data for all six PRs, and each one now
resolves via the record-evidence path with no body edit — the acceptance
property #284 asked for. It is a local run, not a GitHub Actions run;
the GitHub Actions `closes-gate` check itself will re-run this same
`gates/ci.py` only once this PR merges to `main` (the workflow checks
out the gate script from `main`, same structural gap #369's record
"CI acceptance — PENDING MERGE" section already documented for the
prior fix). If a discrepancy exists between this local Python
environment and the CI runner's, it would not surface here — not
claimed as checked. Once merged, re-running the `closes-gate` required
status check on each of the six PRs in GitHub Actions is what would
close that remaining gap.

## What did not work

None.

## Doc placement

- No new env var, config key, dependency, or migration — nothing
  belongs in a handbook.
- No library-or-format choice over a named alternative and no changed
  public wire format beyond `_fetch_ref_file`'s return shape, which is
  internal to `gates/ci.py` and covered above, not a cross-module
  contract — no `docs/issue-388/decisions/` entry.
- Benchmark/investigation numbers: the six-PR re-run results are
  recorded above under `closed_checks` and restated in the PR/issue
  reply, not duplicated into a separate `docs/issue-388/reports/`
  entry.
