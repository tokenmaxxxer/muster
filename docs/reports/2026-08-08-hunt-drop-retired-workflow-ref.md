---
proposal: docs/issue-499/proposals/2026-08-08-drop-retired-workflow-ref.md
---

# Hunt record — drop-retired-workflow-ref

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `_ARTIFACT_REF` only pattern-matches a backtick-quoted path string; it never checks the referenced artifact actually exists on disk, so any fabricated path under `test/`, `gates/`, or `.github/workflows/` satisfies the gate. The proposed fix (dropping the `.github/workflows/` alternative) does not close this — the same bypass survives via `test/` or `gates/` prefixes.
Kind: silent-failure
Seed: gates/acceptance_gate.py `_ARTIFACT_REF` regex (lines 21-25), proposal docs/issue-499/proposals/2026-08-08-drop-retired-workflow-ref.md
cap_seconds: 60
tier: default
diff_stat_lines: 0 (docs-only survey/proposal, no code diff yet)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:02:00Z

### Reproduce
```
python3 - << 'PYEOF'
from gates.acceptance_gate import check_issue_body
body = """## Acceptance
See `test/does_not_exist_anywhere.py` for verification.
empty state: n/a
provenance: read
"""
print(check_issue_body(999, body))
PYEOF
```

### Observed
`[]` (gate passes) even though `test/does_not_exist_anywhere.py` does not exist anywhere in the repo.

### Expected
The gate should fail closed (or at least warn) when the referenced artifact path does not exist in the repo, since its stated purpose is to require a reference to an "실행가능한 산출물" (executable artifact) — a phantom path is functionally identical to prose-only acceptance text, which the gate exists to reject.
</content>

## before-landing — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: NO FINDING
Seed: HEAD commit "fix(issue-499): drop retired .github/workflows/ ref from acceptance_gate" — drops `\.github/workflows/` from `_ARTIFACT_REF` in gates/acceptance_gate.py; flips test/test_side_effect_round.py and gates/test_acceptance_gate.py (the latter outside the frozen write set, documented in docs/issue-499/reports/implementation.md).
cap_seconds: 120
tier: default
diff_stat_lines: ~90 across 5 files
started_at: 2026-08-08T00:00:00
ended_at: 2026-08-08T00:05:00

Searched the whole repo (`grep -rln "github/workflows"`) for any other file that asserts/depends on `_ARTIFACT_REF` accepting a `.github/workflows/...` reference. Only two code sites match: `test/test_side_effect_round.py` and `gates/test_acceptance_gate.py`, both already flipped in this commit. Other `.github/workflows/` hits in the repo (`test_risk_report.py::t_protected_path_is_high_regardless_of_size`, `gates/test_boundary.py`, `test_gates.py::t_protected_paths`, `gates/gates.py::ci_reachable_gates` docstring) test unrelated behavior (path-protection/risk classification, CI reachability prose) and do not touch `_ARTIFACT_REF` or the acceptance-gate accept/reject decision. Ran `python3 -m pytest -q`: 703 passed, 1 failed (`test_spawn.py::WatcherAutoArm::test_watchdog_flags_pid_reused_by_unrelated_process`) — unrelated to acceptance_gate/_ARTIFACT_REF, a pre-existing watchdog-timing test. No file outside the commit's write set still assumes the old accept-`.github/workflows/` behavior.
