---
proposal: docs/issue-476/proposals/execution-observation.md
---

# Hunt record — execution-observation

## after-proposal — stance 1: assume the gate/mechanism just touched is bypassable — find the bypass

Verdict: FINDING — claim_scan.py's "target traceability" check accepts any evidence citing a path that exists anywhere in the repo, not one that is actually part of the diff/claim's referenced change, so a fabricated Repro: line naming an unrelated existing file passes the gate.
Kind: silent-failure
Seed: docs/issue-476/reports/execution-observation/survey.md, docs/issue-476/proposals/execution-observation.md (proposes sandbox-testing gates/claim_scan.py + gates/reexecution_gate.py from PR #485 for fabrication-catching effectiveness)
cap_seconds: 60
tier: default
diff_stat_lines: ~250 (docs only)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:01:00Z

### Reproduce
Write a file `fake_claim.md` containing:
```
I claim the fix is verified.
Repro: see gates/claim_scan.py for details, totally unrelated to this change
```
Then run:
```
python3 gates/claim_scan.py fake_claim.md --repo .
```

### Observed
```
claim_scan: fake_claim.md — 주장 근거/추적성 이상 없음
```
Exit code 0 — the claim scanner reports "no issues" even though the cited evidence (`gates/claim_scan.py`) has nothing to do with the actual claim and no command was ever run.

### Expected
`_repo_targets()` builds its traceability set from `git ls-files` (the entire tracked repo), not from `git diff` targets, despite the module docstring explicitly promising "그 근거가 실제 diff/repo 안의 대상... 가리키는지를... 검사". Because any tracked file name satisfies the check, an author can fabricate a "Repro:" line pointing at an arbitrary existing file (e.g. the gate script itself, or README.md) and the traceability check will always pass — the exact "인접 커맨드 없는 주장" bypass the gate claims to close is still open whenever the cited target merely exists in the repo rather than being the actual object of the diff.
