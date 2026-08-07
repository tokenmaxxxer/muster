---
proposal: docs/issue-332/proposals/2026-08-07-claim-evidence-at-write-time.md
---

# Hunt record — claim-evidence-at-write-time

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: FINDING — the only workflow that runs `gates/ci.py` as a required PR check invokes it with `--closes-only`, which returns before ever calling `record_fulfils_diff` — so the proposal's new `count` gate (extending `record_fulfils_diff`) would never actually execute in enforced CI, and the write set omits the file that would need to change to fix that (`.github/workflows/plan-aware-closes-gate.yml`, or a new workflow invoking `ci.py` without `--closes-only`).
Kind: design-error
Seed: docs/issue-332/proposals/2026-08-07-claim-evidence-at-write-time.md (frozen write set: gates/gates.py, gates/ci.py, test_gates.py, docs/decisions/2026-08-07-measured-claim-line.md)
cap_seconds: 60
tier: default
diff_stat_lines: docs-only (survey.md + proposal.md added under docs/issue-332/)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:05:00Z

### Reproduce
```
grep -n "closes-only" .github/workflows/plan-aware-closes-gate.yml
# run: python3 gates/ci.py . --pr "$PR_NUMBER" --autodetect --closes-only

python3 - <<'PY'
import ast
tree = ast.parse(open("gates/ci.py").read())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "check":
        print(ast.unparse(node))
PY
# shows: `if closes_only: return bad` occurs before the block containing
# `bad += gates.record_fulfils_diff(repo, {})`
```

### Observed
`gates/ci.py::check()`, when called with `closes_only=True` (the mode the
repo's only required-status-check workflow, `.github/workflows/plan-aware-closes-gate.yml`,
actually uses via `--closes-only`), returns `bad` at the `if closes_only: return bad`
line — several lines before `record_fulfils_diff` is ever invoked. This is
also stated directly in `check()`'s own docstring: "`closes_only=True`: ...
write_scope/protected-path/deps/record 검사는 전부 건너뛴다" (record checks
are all skipped). So today, issue #155's existing `fulfils: delete|create|move`
gate already does not run on real PRs through the enforced CI path — it only
runs when someone calls `gates/ci.py` with a bare `--pr --issue --phase`
(non-closes-only) invocation, which no workflow in `.github/` does.

### Expected
The proposal's "How you'll know it worked" section claims `gates/ci.py`'s
check list "runs it on a PR touching a phase-2 record the same way
`record_fulfils_diff` already runs today" — but `record_fulfils_diff` does
not run on the real enforced PR check today. Wiring a new `count` kind into
`record_fulfils_diff` (proposal step 3) does nothing for actual claim
enforcement unless the write set also includes whatever makes the enforced
workflow invoke `ci.py` without `--closes-only` (e.g. a new/modified
`.github/workflows/*.yml`, plus registering that new check name as required
in GitHub branch protection settings) — none of which is in the proposal's
frozen file list.
