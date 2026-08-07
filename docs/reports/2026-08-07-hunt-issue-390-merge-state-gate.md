
## after-proposal — stance 0: assume the gate/mechanism just proposed is bypassable — find the bypass

Verdict: FINDING — proposal never states the merge-state-gate check must be registered as a required status check in branch protection, unlike its sibling closes-gate, which explicitly documents this dependency; without that registration (an out-of-repo, out-of-PR admin step) the gate is advisory-only and never blocks a merge.
Kind: design-error
Seed: docs/issue-390/proposals/2026-08-07-merge-state-gate.md
cap_seconds: 180
tier: size:>200-lines
diff_stat_lines: N/A (docs-only proposal, no code diff yet)
started_at: 2026-08-07T15:57:06+09:00
ended_at: 2026-08-07T16:00:00+09:00

### Reproduce
```
grep -n -i "branch protection\|required check\|register" docs/issue-390/proposals/2026-08-07-merge-state-gate.md
# only hit: line 73 "The job fails the required check when any script exits non-zero."
grep -n "branch protection" .github/workflows/plan-aware-closes-gate.yml
# sibling gate's comment explicitly states (translated): the check name must be registered
# as required in the main branch protection rules, or before registration it only reports
# status and blocks nothing.
```

### Observed
The proposal's "What will be done" section describes `merge-state-gate.yml` and calls its
outcome "the required check" as an established fact, but the proposal contains zero mention
of branch-protection registration, no decision to register it, and no note deferring that
step (contrast with the sibling gate's inline comment, which points to a separate
implementation-notes doc for the exact registration procedure). As written, once merged the
workflow runs and reports a check status but -- exactly like closes-gate before its own
registration step landed -- does not block any merge until a human separately adds it to
branch protection in Settings > Branches. Nothing in the proposal's "How you'll know it
worked" acceptance test (a synthetic git-repo unit test) exercises or asserts this either,
so the gap is invisible to the proposal's own acceptance criteria.

### Expected
The proposal should explicitly state (as the sibling gate does) that the new check name must
be added to branch protection's required-status-checks list for main, and either include that
as an action item or explicitly defer it with a stated reason -- otherwise the mechanism is a
no-op gate identical in kind to the pre-registration closes-gate the sibling comment describes.
