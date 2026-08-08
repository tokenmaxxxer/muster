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
