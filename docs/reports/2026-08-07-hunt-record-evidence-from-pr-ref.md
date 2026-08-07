---
proposal: docs/issue-369/proposals/2026-08-07-record-evidence-from-pr-ref.md
---

# Hunt record — record-evidence-from-pr-ref

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: NO FINDING
Seed: docs/issue-369/proposals/2026-08-07-record-evidence-from-pr-ref.md; gates/ci.py (_phase2_record_evidence ~L169-188, caller ~L319-320, _pr_commit_messages ~L85-113 pattern); .github/workflows/plan-aware-closes-gate.yml
cap_seconds: 120
tier: default
diff_stat_lines: ~size:21-200 (docs-only proposal + survey)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:03:00Z

Checked candidates for a needed-but-unlisted path:
- Auth/permission scope: workflow already grants `contents: read` (plus
  `pull-requests: read`, `issues: read`); `gh api repos/<slug>/contents/...`
  needs nothing beyond `contents: read`, matching the existing
  `_pr_commit_messages` gh-api call under the same permissions block — no
  workflow permissions change needed beyond what's already in the write
  set (.github/workflows/plan-aware-closes-gate.yml is already listed).
- `spawn._repo_slug`: already used unmodified by `_pr_commit_messages`
  (gates/ci.py:100) for the identical gh-api-repos-slug pattern; no
  evidence it needs changing for this reuse. spawn.py is not in the write
  set and grep found no other call site requiring a change there.
- Test mocking layer: grepped for `conftest.py` — only the root one
  exists, and existing gh-api-backed helpers (`_pr_commit_messages`,
  `_pr_title`, etc.) are already monkey-patched directly in
  gates/test_closes_gate_ci.py without any shared fixture/mock file
  outside it (e.g. t_ci_check_phase2_passes_via_record_evidence... block
  monkeypatches ci._pr_head_ref, pr_reference._pr_view,
  ci._pr_title/_pr_commit_messages, spawn._approvers/_issue_comments,
  ci._pr_reviews directly). No indication a new file is needed for
  mocking the new gh-api call.
- Considered whether a fork-originated PR would need the fork's own
  repo slug (headRepositoryOwner/headRepository) rather than the base
  slug for `ref=<branch>` to resolve — `_pr_is_cross_repo` already exists
  in gates/ci.py and gates a separate fork-issue-in-body fallback path;
  `_phase2_record_evidence` is gated on `_issue_and_role_from_branch`
  matching `issue-<n>/<role>`, a convention this path is meant to cover.
  This looked like a live gap but I could not get gh network access in
  this sandbox (Bash denied mid-session for `gh pr view` on the six
  target PRs) to confirm any of #337/#340/#343/#350/#352/#353 is actually
  a fork PR that would hit this path with a mismatched slug. Without a
  reproduction this stays a hypothesis, not a finding.

No file outside the frozen write set (gates/ci.py,
gates/test_closes_gate_ci.py, .github/workflows/plan-aware-closes-gate.yml,
docs/issue-369/decisions/record-evidence-via-gh-api-contents.md,
docs/issue-369/reports/implementation.md) was found to be structurally
required by the described fix.
