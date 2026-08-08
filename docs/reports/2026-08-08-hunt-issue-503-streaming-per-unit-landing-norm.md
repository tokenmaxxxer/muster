---
proposal: docs/issue-503/proposals/2026-08-08-streaming-per-unit-landing-norm.md
---

# Hunt record — issue-503-streaming-per-unit-landing-norm

## after-proposal — stance 0: assume the gate just touched is bypassable: find the bypass

Verdict: FINDING — the proposed run.md-section-presence gate is a bare substring check (modeled on `t_run_md_references_unenforced_clauses`), so it is satisfied by the marker phrase appearing anywhere in run.md (e.g. inside a rejected-alternative note or a quoted counter-example), not just inside an actually-enforced streaming-landing section.
Kind: design-error
Seed: docs/issue-503/proposals/2026-08-08-streaming-per-unit-landing-norm.md — step 2 ("Add one assertion function to gates/test_boundary.py ... parallel in style to t_run_md_references_unenforced_clauses ... asserting the new section's marker text is present in run.md")
cap_seconds: 60
tier: default
diff_stat_lines: ~270 (docs-only, two new files)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:01:00Z

### Reproduce
```
grep -n "t_run_md_references_unenforced_clauses" -A 5 gates/test_boundary.py
```
gives:
```python
def t_run_md_references_unenforced_clauses():
    assert RUN_MD.is_file(), f"{RUN_MD} 가 없다."
    assert "UNENFORCED-CLAUSES.md" in RUN_MD.read_text(encoding="utf-8"), (
        "run.md 가 UNENFORCED-CLAUSES.md 를 참조하는 줄이 없다(#452)."
    )
```
i.e. a plain `marker in full_file_text` substring test with no locality/section-scoping. The proposal (step 2) explicitly says the new assertion will be "parallel in style" to this function. Simulating what such a check accepts:
```python
import re
text = "스트리밍 랜딩이 기본이다 -- 이 문구는 사실 반려된 대안 섹션 안에 있다. 실제 정책은 배치 배리어를 유지한다."
print(bool(re.search("스트리밍 랜딩이 기본이다", text)))
```

### Observed
`True` — the marker text passes the presence check even when it appears inside a rejected-alternative aside or negated prose that states the opposite of the intended policy (batch barriers still apply). The gate cannot distinguish "the streaming-landing norm is stated as the enforced default" from "the phrase is quoted somewhere in run.md for any reason." The code comment at gates/test_boundary.py:146-151 already documents that this exact bare-substring / section-title-fallback shape was a confirmed bypass for a sibling gate in issue-464 (docs/reports/2026-08-08-hunt-class-a-orchestrator-loop-wiring.md), and the fix there was to require the line itself to carry disposition vocabulary, not just live under the right heading. The new proposal does not carry that constraint forward — step 2 names only "the new section's marker text is present," with no requirement that the marker sentence itself state the streaming-is-default/barrier-exception disposition, or that it appear outside any "Alternative considered and rejected" context.

### Expected
A presence gate for a normative rule should assert that the operative marker text appears in a context that actually states the rule as enforced policy (e.g. anchored to the correct heading and excluding text inside "반려/rejected" subsections), mirroring the disposition-vocabulary fix issue-464 already forced onto the sibling `justified`-clause gate — otherwise any future run.md edit that merely mentions the phrase (positively or negatively, in any section) keeps the gate green while the actual streaming-landing default silently reverts to batch-barrier behavior.
