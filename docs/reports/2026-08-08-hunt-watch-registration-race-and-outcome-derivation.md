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

## before-landing — stance 2: assume this guard goes silent when its own input is malformed — make it go silent

Verdict: NO FINDING
Seed: spawn.py `_pr_open_or_merged_for_branch`, `_watch` roster-poll grace-wait, `fail_closed_downgrade` silent-failure-upgrade branch (commit 45473c8)
cap_seconds: 120
tier: size:default
diff_stat_lines: ~260 (3 files)
started_at: 2026-08-08T10:05:00Z
ended_at: 2026-08-08T10:24:00Z

Tested three angles directly:

1. `_pr_open_or_merged_for_branch(root, branch)` with a monkeypatched
   `subprocess.run`:
   - non-JSON stdout, rc=0 -> returns `None` (fail-closed, correct).
   - rc != 0 with well-formed JSON stdout -> returns `None` (rc check runs
     before parsing, correct — no false positive from stray output).
   - one edge case *did* crash: valid JSON but wrong shape (a dict instead
     of a list, e.g. `{"number":42,"state":"OPEN"}`) raises
     `AttributeError: 'str' object has no attribute 'get'` because the
     `try/except ValueError` around `json.loads` only catches decode
     failure, not shape mismatch. This is a real gap, but it is not
     realistically reachable: `gh pr list --json number,state` always
     returns a JSON array by contract of the `--json` flag; there is no
     `gh` failure mode that emits a bare JSON object for a list query. Not
     pursuing as the finding — no plausible caller/attacker gets this
     shape from `gh` itself, so it doesn't clear the "reproduction that
     matters" bar even though the crash itself reproduces.

2. `_watch`'s new grace-wait loop against a corrupted `WORKSPACE_INDEX` on
   disk (mid-write JSON): `_workspace_index_load()` catches `(OSError,
   ValueError)` and returns `{}`. Confirmed by reading the loop: each poll
   iteration re-reads via `_workspace_index_load()`, so a corrupt file
   during the grace window just yields `{}` -> `entry=None` -> loop keeps
   spinning until `stall_timeout_min*60` elapses -> falls through to the
   existing "기록 없음" stderr message and `return 1`. The full grace
   window is consumed, not skipped; nothing hangs or exits early. No
   defect here.

3. `fail_closed_downgrade`'s new branch has a single call site
   (`_spawn_one`) that always passes real `bool`s for `already_delivered`/
   `new_commit`/`push_succeeded` computed from concrete git/gh state — no
   other caller exists in the repo (`grep -rn fail_closed_downgrade`
   confirms). "malformed types from a future caller" has no current
   reproduction; it's speculation about code that doesn't exist yet, which
   the rules explicitly disqualify.

No finding clears the reproduction bar for this stance.
