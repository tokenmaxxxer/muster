---
proposal: docs/issue-321/proposals/2026-08-07-requirements-registry.md
---

# Hunt record — requirements-registry

## after-proposal — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING — the frozen write set omits .github/workflows/plan-aware-closes-gate.yml, and that workflow only ever invokes gates/ci.py with --closes-only, which returns from check() before reaching the block where record_enums/record_wellformed_in/record_no_tool_residue_in/record_fulfils_diff run — so a new gates.requirement_registry check wired in the same style would never execute in the actual required CI check.
Kind: design-error
Seed: docs/issue-321/proposals/2026-08-07-requirements-registry.md (files: docs/specs/requirements.md, gates/gates.py, gates/ci.py, test_gates.py, docs/issue-321/decisions/2026-08-07-registry-placement.md)
cap_seconds: 60
tier: default
diff_stat_lines: 0 (proposal-stage, docs only)
started_at: 2026-08-07T00:00:00Z
ended_at: 2026-08-07T00:03:00Z

### Reproduce
grep -n "run: python3 gates/ci.py" .github/workflows/plan-aware-closes-gate.yml
# => run: python3 gates/ci.py . --pr "$PR_NUMBER" --autodetect --closes-only
sed -n '229,295p' gates/ci.py | grep -n "closes_only\|return bad\|record_enums"
# => "if closes_only: return bad" appears BEFORE "bad += gates.record_enums(repo, {})"

### Observed
The only .github Actions job that runs gates/ci.py as a required status check
always passes --closes-only. Inside check(), the closes_only branch returns
`bad` immediately after the protected-path + pr_reference checks, skipping
every line below it (record_enums, record_wellformed_in,
record_no_tool_residue_in, record_fulfils_diff). Any new check appended the
same way the proposal describes ("wiring it into gates/ci.py's check()
dispatch") — i.e. as another `bad += gates.requirement_registry(...)` line
alongside the existing record_* calls — lands after that early return and so
never runs when CI invokes the gate for real PRs.

### Expected
The write set should either include .github/workflows/plan-aware-closes-gate.yml
(to drop --closes-only or add a second required check that isn't
closes-only), or the proposal should explicitly say the new gate is
enforced only in local/non-CI invocations of gates/ci.py — otherwise the
registry check silently never blocks a real PR.
