---
proposal: docs/issue-284/proposals/2026-08-07-closes-gate-record-evidence-and-fork-fallback.md
---

# Hunt record — closes-gate-record-evidence-and-fork-fallback

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the planned fork/branch-mismatch fallback (extract issue number from a plain "#N" in the PR body, role=None) discards the current fail-closed rejection of PRs not connected via the issue-<n>/<role> branch convention, letting any PR from an arbitrary/unrelated branch pass the closes-gate as phase1 merely by mentioning the issue number once anywhere in the body.
Kind: design-error
Seed: docs/issue-284/proposals/2026-08-07-closes-gate-record-evidence-and-fork-fallback.md item 2 (branch-mismatch fallback), read against current gates/ci.py `_autodetect_issue_phase` and gates/pr_reference.py `check_body`
cap_seconds: 60
tier: default
diff_stat_lines: 245 (docs-only, survey.md + proposal.md)
started_at: 2026-08-07T14:30:06+09:00
ended_at: 2026-08-07T14:37:00+09:00

### Reproduce
Current `gates/ci.py:_autodetect_issue_phase` docstring explicitly justifies fail-closed for branches not matching `issue-<n>/<role>`:
"브랜치가 그 형태가 아니면(...) 이슈 번호를 알 방법이 없다 — 통과가 아니라 차단한다(fail closed): 조용히 건너뛰면 #245 가 고치려는 '강제 지점 없음' 구멍이 이 경로로 그대로 되살아난다."

The proposal's item 2 replaces that block with: on branch mismatch, extract `#N` from the PR body via `pr_reference._PLAIN_REF` and proceed with `role=None`. That routes the PR into the existing phase1 check, which already exists today and was run to confirm it accepts a bare mention:

```
cd gates && python3 -c "
import pr_reference
print(pr_reference.check_body(284, 'random PR from a fork, unrelated branch name, just chatting about #284', 'phase1'))
"
```

### Observed
`[]` — phase1 check passes with nothing more than the substring `#284` anywhere in the PR body, no branch naming discipline, no relation to any real issue-284 work.

Also checked `flows._pr_approved`: with `role=None` the single-account comment path needs literal `"APPROVE issue-284/None"` (unreachable in practice), but the PR-review approval path (`rv.get("state")=="APPROVED"` from any approvers.md login) does not reference `subject`/`role` at all, so an unrelated fork PR could even reach phase2-approved status via a stray Approve review, independent of role.

### Expected
A PR whose branch does not follow `issue-<n>/<role>` should stay fail-closed (as today, and as the surrounding docstring in the same function argues for), not silently downgrade to a weaker "any plain #N reference passes phase1" path — the proposal as described reopens exactly the "no enforcement point" hole issue #245's fail-closed branch-parsing was built to close, this time for fork/mismatched-branch PRs.
