---
proposal: docs/issue-443/proposals/2026-08-08-execution-observation-of-pr-447.md
---

# Hunt record — execution-observation-of-pr-447

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the phase-1/phase-2 approval gate (`gates/ci.py._phase_from_approval`, contract v3 s19) is role-blind on approved issues that already carry ANY role's APPROVE comment: an execution-observation PR on issue #443 would be graded phase2-approved off the pre-existing `APPROVE issue-443/implementation` comment, without any human ever approving execution-observation's own phase-1 proposal.
Kind: composition
Seed: docs/issue-443/proposals/2026-08-08-execution-observation-of-pr-447.md, docs/issue-443/reports/execution-observation/survey.md
cap_seconds: 120
tier: default
diff_stat_lines: 187 (2 new files)
started_at: 2026-08-08T00:00:00Z
ended_at: 2026-08-08T00:02:00Z

### Reproduce
```
gh issue view 443 --json comments -q '.comments[] | select(.body | startswith("APPROVE")) | .body + " | " + .author.login'

python3 - <<'PY'
import sys; sys.path.insert(0, "gates")
import ci
from pathlib import Path
roles = ci._approved_roles_on_issue(Path("."), 443)
print("approved_roles for issue 443:", roles)
phase = "phase2" if roles else "phase1"
print("phase determination for ANY role PR on issue 443:", phase)
PY
```

### Observed
```
APPROVE issue-443/implementation | JiwonJung94
approved_roles for issue 443: {'implementation'}
phase determination for ANY role PR on issue 443: phase2
```
`_approved_roles_on_issue` and `_phase_from_approval` (gates/ci.py:179-218) key phase entirely off the ISSUE, not the (issue, role) pair — an approval comment naming `implementation` is enough to make `_phase_from_approval` return `"phase2"` for a hypothetical `execution-observation` PR on the same issue, even though no human has posted `APPROVE issue-443/execution-observation`. The proposal under hunt explicitly claims its trajectory verdict will check for "a real human approval under contract v3 s19 before phase-2 work began" (per-role, by its own framing) — but the actual gate mechanism it implicitly relies on for that check cannot distinguish "this role was approved" from "some other role on this issue was approved once." This is documented in `gates/ci.py` as deliberate (issue #312: "phase is a property of the issue, not the role" — enabling architect→implementation cross-role handoff), so it is a genuine composition regression rather than an oversight: a rule correct for the architect→implementation handoff case, and wrong when a later, unrelated role (execution-observation) reuses the same issue number and inherits an approval it was never granted.

### Expected
`gates/ci.py` phase-2 admission for a role's own record/PR should require an APPROVE comment naming that role specifically (or an explicit, separately-approved cross-role handoff), not any prior APPROVE on the issue — otherwise any role that later attaches itself to an already-approved issue number gets phase-2 write privileges for free.
