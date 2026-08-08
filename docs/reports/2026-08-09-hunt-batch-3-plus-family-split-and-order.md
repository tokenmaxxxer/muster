---
proposal: docs/issue-525/proposals/2026-08-09-batch-3-plus-family-split-and-order.md
---

# Hunt record — batch-3-plus-family-split-and-order

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the proposal's own "How you'll know it worked" verification step ("grep -o for each role name across the three scout-briefs' must-bes sections returns exactly one match per role") is false when run: multiple role names occur 2-4 times each in the scout-briefs (e.g. brand-design x4, finance-unit-economics x3, growth-analytics x3, ux-engineering x3, content-design x2, devrel x2, implementation x2, knowledge-management x2, risk-management x2, sales x2), because roles are legitimately discussed in multiple sections (must-be entry, gap notes, shared-lineage cross-references) rather than appearing exactly once. The "exactly one match" acceptance criterion names a check that cannot pass against the very files this PR ships, i.e. state (a single, un-deduped mention count) that nothing in the scout-briefs' structure maintains.
Kind: design-error
Seed: docs/issue-525/proposals/2026-08-09-batch-3-plus-family-split-and-order.md, docs/issue-525/reports/implementation/survey.md, docs/issue-525/reports/implementation/scout-brief-{build,ops-knowledge,commercial-risk}.md (5 new files, ~430 lines)
cap_seconds: 120
tier: default
diff_stat_lines: ~430 (5 new files)
started_at: 2026-08-09T02:40:00+09:00
ended_at: 2026-08-09T02:47:00+09:00

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-525-implementation
grep -o "brand-design" docs/issue-525/reports/implementation/scout-brief-*.md | wc -l
grep -o "finance-unit-economics" docs/issue-525/reports/implementation/scout-brief-*.md | wc -l
```

### Observed
`brand-design` matches 4 times, `finance-unit-economics` matches 3 times (also content-design, devrel, growth-analytics, implementation, knowledge-management, risk-management, sales, ux-engineering all match more than once) — not "exactly one match per role" as the proposal's acceptance criterion asserts.

### Expected
The acceptance criterion should either scope the grep to a single, uniquely-identifiable line per role (e.g. the "Sources:"-adjacent must-be bullet, not a bare `grep -o` over the whole brief) or state a different, actually-checkable invariant — as written it names a check a reviewer running it verbatim will see fail even though the underlying 33-role accounting (verified separately: survey's 33 names and the proposal's family-split union are set-identical) is in fact correct.
