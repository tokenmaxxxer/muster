---
proposal: docs/issue-484/proposals/2026-08-08-watch-registration-race-and-outcome-derivation.md
---

# Hunt record — watch-registration-race-and-outcome-derivation

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — dropping the `outcome == "progressed"` gate reuses `_pr_for_branch`'s `--state all` check unchanged, so a genuinely-failed session on a branch with a previously *closed/rejected* (never-merged) PR will be upgraded from `silent-failure` to `progressed`, exactly the "relabel a genuine failure away" gap the stance asks about.
Kind: design-error
Seed: docs/issue-484/proposals/2026-08-08-watch-registration-race-and-outcome-derivation.md, docs/issue-484/reports/implementation/survey.md (HEAD af131f3)
cap_seconds: 60
tier: default
diff_stat_lines: 182 insertions (2 new files)
started_at: 2026-08-08T19:20:00+09:00
ended_at: 2026-08-08T19:23:00+09:00

### Reproduce
```
grep -n "_pr_for_branch" spawn.py
# 994: def _pr_for_branch(root, branch):
#   r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all", ...])
#   returns int(out) if r.returncode==0 and out.isdigit() else None
```
Proposal item 2 says: "compute `already_delivered` (existing `_pr_for_branch` check) ... independent of `classify()`'s raw verdict — i.e. drop the `outcome == "progressed"` gate ... Extend `fail_closed_downgrade`'s logic ... so a raw `"silent-failure"` verdict is upgraded to `"progressed"` ... when `already_delivered` is true." It reuses `_pr_for_branch` as-is; no state filter (e.g. `--state merged`/open-or-merged only) is proposed.

`--state all` in `gh pr list` matches OPEN, CLOSED, and MERGED PRs alike — `_pr_for_branch` returns a PR number for a branch with a *closed-without-merging* PR just as readily as for a merged one.

### Observed (design-level)
Scenario once implemented as specified: branch `issue-58/impl` has an earlier PR that was opened, reviewed, and closed as rejected (bad approach, never merged). A later session on that same branch does no useful work this run — `classify()` correctly returns `"silent-failure"` (no board delta, no commit). Under the proposed change, `already_delivered = _pr_for_branch(...) is not None` is now computed unconditionally (gate dropped) and is `True` (closed PR still matches `--state all`), and the extended `fail_closed_downgrade` upgrades `"silent-failure"` → `"progressed"`. The session is silently relabeled as successful even though nothing landed and the branch's only history is a rejected PR.

### Expected
`already_delivered` should only be true for a PR state that actually represents delivered work (open-not-yet-merged or merged), not any historical PR on the branch — e.g. `--state all` combined with checking the returned PR's actual state (`OPEN`/`MERGED`, not `CLOSED`), or restricting to `--state merged` plus a live-open check. The proposal as written carries this gap into the "drop the gate" change without amending `_pr_for_branch`'s state filter, so implementing it verbatim reproduces the exact silent-failure-masking bug class issue-484 is trying to fix.
