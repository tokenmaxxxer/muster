---
proposal: docs/issue-384/proposals/2026-08-07-gate-fix-bootstrap-path.md
---

# Hunt record — gate-fix-bootstrap-path

## after-proposal — stance 3: assume the rule as written cannot hold: find the state nothing maintains

Verdict: FINDING — the proposal's whole trust boundary rests on "checkout ref: main" pinning `gates/ci.py`, but the workflow file that runs that check (`plan-aware-closes-gate.yml`) is itself in the bootstrap-eligible path set (`.github/workflows/`) and is not similarly pinned — it uses `pull_request`, not `pull_request_target`, so GitHub executes the workflow definition from the PR's own branch/merge ref, not from `main`. Nothing in the design maintains the assumption that `.github/workflows/plan-aware-closes-gate.yml`'s own job steps can't be edited by the very PR they're supposed to gate.
Kind: design-error
Seed: docs/issue-384/proposals/2026-08-07-gate-fix-bootstrap-path.md
cap_seconds: 60
tier: default (docs-only)
diff_stat_lines: 269 (two new docs files under docs/issue-384/)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:04:00Z

### Reproduce
```
cat .github/workflows/plan-aware-closes-gate.yml
```

### Observed
Trigger block:
```
on:
  pull_request:
    types: [opened, edited, synchronize, reopened]
    branches: [main]
```
(not `pull_request_target`), plus the checkout step's own inline comment explaining the `ref: main` pin only guards against "PR이 gates/ci.py 자체를 고쳐 자기 자신을 통과시키는" case — it says nothing about protecting the workflow file itself.

Per GitHub's documented `pull_request` vs `pull_request_target` semantics, a plain `pull_request` trigger runs the workflow *as defined in the PR's own branch* (merge ref), not the base/`main` version — that distinction is exactly why `pull_request_target` exists as the alternative when a base-pinned workflow *definition* is required. The `ref: main` checkout inside the job only pins what `gates/ci.py` reads at runtime; it does nothing to pin which job definition GitHub Actions selects to run, because that selection happens before the checkout step ever executes.

### Expected
The proposal's constraint list ("the `checkout: ref: main` pin ... must not change; any bootstrap logic must run as code already on `main`") and its "Out of scope" section (declaring `.github/workflows/plan-aware-closes-gate.yml` needs no edit and no coverage beyond a static grep on the checkout step) together assume the workflow file's content is immutable-from-a-PR's-perspective, the same way `gates/ci.py`'s checked-out content is. That assumption has no owner and no mechanism: because the bootstrap-eligible file set explicitly *includes* `.github/workflows/`, a PR that is "eligible" under this exact design can edit `plan-aware-closes-gate.yml` itself (e.g. delete the `--closes-only` gate step, or add a step that checks out and runs the PR's own copy of `gates/ci.py`), and that edited workflow is what GitHub actually runs for that PR — regardless of anything `_gate_bootstrap_eligible()` decides inside the untouched, main-pinned `gates/ci.py`. The design's own trust-boundary regression test (item 5 in "What will be done") only greps the YAML's checkout `ref:` and step count from a checked-out-from-main copy of the file; it cannot, from inside `gates/ci.py`, observe or block which version of the whole workflow file GitHub selected to execute for the PR under evaluation, because that selection is made by GitHub before `ci.py` ever runs.
