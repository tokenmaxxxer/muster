---
proposal: docs/issue-371/proposals/2026-08-07-status-state-vocabulary.md
---

# Hunt record — status-state-vocabulary

## after-proposal — stance 0: assume the gate/mechanism just proposed is bypassable — find the bypass

Verdict: FINDING — `merged-verified`'s condition ("review record with no Absent/Incorrect verdicts") silently admits `Surface` verdicts as if they were `Present`, letting a shallow/incomplete review masquerade as an independently-verified merge.
Kind: design-error
Seed: docs/issue-371/proposals/2026-08-07-status-state-vocabulary.md (step 1, `merged-verified` bullet: "PR MERGED with Closes-ref, no `review` role record for the subject shows a `Present`-only verdict set post-merge" / decision text: "review record with no Absent/Incorrect verdicts")
cap_seconds: 60
tier: size:docs-only
diff_stat_lines: 255
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:01:00Z

### Reproduce
`ledger/collect.py` defines `VERDICTS = ("Present", "Surface", "Absent", "Incorrect")` — four values, not two. `Surface` is used elsewhere in this repo as a non-passing verdict distinct from `Present` (e.g. a clean review report is described as having "No Surface, Absent, Incorrect, or Unverifiable findings" in an existing conformance-review record).

```
$ grep -n "VERDICTS" ledger/collect.py
VERDICTS = ("Present", "Surface", "Absent", "Incorrect")
```

The proposal's positive gate for `merged-verified` is only defined as *absence* of Absent/Incorrect — it never requires *presence* of only `Present`. A review record consisting entirely of `Surface` verdicts (present but shallow/questionable — exactly the middle verdict this repo's own ledger vocabulary reserves for that case) satisfies "no Absent/Incorrect verdicts."

### Observed
As specified, a role record with e.g. `verdict: Surface` on every requirement line contains zero `Absent`/`Incorrect` occurrences, so `compute()` per the proposal's own rule reaches `merged-verified` — the state whose entire purpose (per the Rationale section) is to distinguish "independently re-run and confirmed" from cases where verification was weak or incomplete.

### Expected
`merged-verified` should require the review record's verdict set to be `Present`-only (as the step-1 bullet's negative-case wording for `merged-unverified` actually implies — "shows a `Present`-only verdict set" — but which the positive definition of `merged-verified` never restates), so an all-`Surface` review record is excluded rather than silently passing the negative "no Absent/Incorrect" test.
