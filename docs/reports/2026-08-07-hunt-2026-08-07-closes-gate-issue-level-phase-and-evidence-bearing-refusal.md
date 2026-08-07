---
proposal: docs/issue-312/proposals/2026-08-07-closes-gate-issue-level-phase-and-evidence-bearing-refusal.md
---

# Hunt record — closes-gate-issue-level-phase-and-evidence-bearing-refusal

## before-landing — stance: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — a malformed/empty-role `APPROVE issue-<n>/` comment (no role token after the trailing slash) is treated as a valid issue-level approval and permanently flips the whole issue to phase2.
Kind: design-error
Seed: gates/ci.py diff 5e9aeab..0f93836 — `_approved_roles_on_issue` (new) and `_phase_from_approval`'s `if (approved_roles or review_approved)` check
cap_seconds: 120
tier: default
diff_stat_lines: gates/ci.py +52/-16 (per git diff 5e9aeab..0f93836 -- gates/ci.py)
started_at: 2026-08-07T14:21:09+09:00
ended_at: 2026-08-07T14:35:00+09:00

### Reproduce
```python
import sys; sys.path.insert(0, '.')
from pathlib import Path
import gates.ci as ci
import spawn

spawn._approvers = lambda repo: {'jjongkwann'}
spawn._issue_comments = lambda repo, n: [{'login': 'jjongkwann', 'body': 'APPROVE issue-245/'}]
ci._pr_reviews = lambda repo, pr: []

print('approved_roles:', ci._approved_roles_on_issue(Path('.'), 245))
print('phase:', ci._phase_from_approval(Path('.'), 1, 245, 'implementation'))
```
Run with `python3 <script>` from repo root.

### Observed
```
approved_roles: {''}
phase: phase2
```
An allowlisted-login comment whose body is exactly `APPROVE issue-245/` (trailing slash, no role text — e.g. a typo, or copy-paste truncation) produces `roles.add(body[len(prefix):])` = `roles.add('')`, giving `approved_roles == {''}`. This is a non-empty Python set, so `_phase_from_approval`'s `approved_roles or review_approved` is truthy and the function returns `"phase2"`. Because phase is a property of the whole issue now, this one malformed comment permanently disables the phase1 closing-keyword gate (`_phase1_surface_mismatch`, only invoked `if phase == "phase1"`) for every future PR against the issue, with no comment maintaining or able to retract the state — there is no revocation path once the (malformed) approval sits in the issue's comment history.

### Expected
`_approved_roles_on_issue` should only ever place non-empty, genuine role tokens (e.g. matching the `[^/]+` branch-role vocabulary) into its result set, and/or `_phase_from_approval` should check for a non-empty *role name*, not truthiness of a Python set that can legitimately contain the empty string. The pre-diff code (`flows._pr_approved`) is immune to this because it does exact-string comparison against a concrete `needle = f"APPROVE {subject}/{role}"` built from a real role extracted by `_ISSUE_ROLE_BRANCH` (`[^/]+`, at least one character) — it can never match a comment with an empty role suffix.
