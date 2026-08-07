---
proposal: docs/issue-412/proposals/2026-08-07-shallow-checkout-detection.md
---

# Hunt record — shallow-checkout-detection

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the marker file's "before trusting history" claim is unenforced: the proposal specifies writing the marker but names no reader, and grep across the repo (on-the-record/, docs/issue-412/) shows nothing outside this proposal even mentions the marker path.
Kind: design-error
Seed: docs/issue-412/proposals/2026-08-07-shallow-checkout-detection.md (What will be done, item 1)
cap_seconds: 60
tier: size:small
diff_stat_lines: 2 files added (proposal + survey), docs-only
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:01:00Z

### Reproduce
grep -rn "ON_THE_RECORD_SHALLOW\|is-shallow\|marker" on-the-record/ docs/issue-412/

### Observed
Every hit for the marker/detection mechanism is inside the proposal itself
(and the survey noting the same `is-shallow-repository` check as a *searched
target*, not a consumer). No existing script, hook, or "orchestrator" in
`on-the-record/` reads `.git/ON_THE_RECORD_SHALLOW` or any file under the
checkout before running `git log`/`rev-list`. The proposal's own "What will
be done" text asserts "so any later history-dependent check can look for
that marker before trusting git log/rev-list output" as though this
consultation already happens or will automatically follow from the marker
existing — but no such consulting code is proposed, scoped, or shown to
exist anywhere. The "Out of scope" section explicitly excludes touching any
site other than self-update.sh's clone path, which means the history-
dependent checks that produced the original 29 false "not merged" results
are never wired to check the marker. The write has no reader by
construction of this proposal's own scope boundaries.

### Expected
For the stated acceptance bar ("a check that fails when the checkout is
shallow... before a history-dependent conclusion is about to be drawn") to
actually hold, either (a) the proposal must identify and modify the actual
history-dependent check sites to consult the marker, or (b) explicitly
scope that wiring into phase-2 as a required, tracked follow-up rather than
implying (via "so any later history-dependent check can look for that
marker") that the mechanism is self-enforcing once the file exists.
