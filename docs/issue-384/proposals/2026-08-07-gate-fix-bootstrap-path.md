---
status: proposed
files:
  - gates/ci.py
  - gates/test_closes_gate_ci.py
  - docs/issue-384/decisions/2026-08-07-bootstrap-eligibility-shape.md
  - docs/issue-384/reports/implementation.md
---

## Request

A PR that fixes `gates/` or `.github/workflows/` is judged by the version of
the gate it is replacing, because `plan-aware-closes-gate.yml` always
checks out `gates/ci.py` from `main` (trust boundary, must not change). Three
times in one afternoon (#360, #284, #369) this forced a manual, unfiled
workaround — a throwaway session editing the PR body to add a closing keyword
so the pre-fix gate would judge it as compliant. Decide and build a defined,
mechanically detectable bootstrap path for this specific case, that a PR
outside `gates/`/`.github/workflows/` cannot use, and that leaves a record
so the workaround does not read as precedent.

## Constraints

- The `checkout: ref: main` pin in `plan-aware-closes-gate.yml` must not
  change — any bootstrap logic must run as code already on `main`, evaluated
  against the incoming PR's *metadata* (via `gh`), never against code checked
  out from the PR's own ref.
- No dependency on GitHub-side config as part of this fix: scout confirmed
  branch protection / rulesets have no OR-across-required-checks, so a
  second parallel "bootstrap" check cannot substitute when the primary
  required check is red — the escape hatch has to live inside `gates/ci.py`,
  the single script the one required check already runs.
- Must not weaken the check for any PR outside `gates/`/`.github/workflows/`.
- Must not retroactively bless the three already-merged workarounds as
  acceptable practice; the record must say what was actually done.

## Rationale

**Chosen approach**: fold a narrow, self-contained eligibility check into
`gates/ci.py`'s `closes_only` path — call it `_gate_bootstrap_eligible()`.
It fires only when all of: (a) the PR's full changed-file set (read via
`gh api ... pulls/<n>/files`, metadata, not checkout) is a non-empty subset
of `{gates/, .github/workflows/}`; (b) the PR body carries a
`## Bootstrap justification` section naming the specific defect being fixed;
(c) the existing phase2 approval signal (`_phase_from_approval`, already
metadata-only, already reused from #172/#271) is present. When eligible, the
closing-keyword mismatch that would otherwise block is waived and the CI
output prints a distinguishable line (`게이트 통과 (bootstrap: gate-self-fix)`)
so the event is greppable in Actions logs — this is what makes it "counted"
rather than invisible, per the issue's second listed cost.

**Rejected alternative 1 — a second required-check workflow file** (e.g.
`gate-bootstrap.yml`) that passes independently and is registered as an
*additional* required check, so either check passing is enough. Rejected
because scout's finding is unambiguous: GitHub required status checks are a
strict AND over the configured list, not an OR — adding a second required
check makes both mandatory, which is strictly worse (a legitimate gate-fix PR
would now need both the still-broken primary check AND the new one to pass).
A second *non-required* check would work today only via a GitHub Settings
change (repo-admin action outside this repo's write set, and reversible by
anyone with settings access without this PR's constraints traveling with
it) — the eligibility logic would live outside version control entirely,
which the issue's "must be identifiable mechanically" criterion rules out.

**Rejected alternative 2 — repo-admin merge override, undocumented** (the
status quo: an admin merges past the red check by hand). Rejected because
this is literally the mechanism that produced three unfiled, invisible
workarounds today — it satisfies nothing in the issue's acceptance section
(no test, no mechanical detection, no record) and scout confirms it is
GitHub's own documented mitigation for the identical `pull_request_target`
self-referential problem, i.e. the field has not solved this better; we are
not leaving a known gap unaddressed, we are choosing to record and gate what
that unavoidable human decision actually is (constraint (b) and (c) above),
rather than leave it as silent admin discretion.

## What will be done

- Add `_gate_bootstrap_eligible(repo, pr, issue)` to `gates/ci.py`,
  implementing the three-part test above, reusing
  `_pr_head_ref`/`gh api pulls/<n>/files`/`_phase_from_approval` (no new
  network-call helpers beyond one `gh api ... /files` call for changed
  paths).
- Wire it into `check()`'s `closes_only` branch: when the closes-keyword
  mismatch (`closes_msg`) would otherwise block AND
  `_gate_bootstrap_eligible()` is true, drop that reason (same pattern as the
  existing `_phase2_record_evidence` waiver at ci.py:318-330) and record which
  waiver fired so the two are distinguishable in output.
- Extend `gates/test_closes_gate_ci.py`:
  1. PR confined to `gates/**`/`.github/workflows/**`, with justification
     section and phase2-approval evidence → bootstrap fires, PR passes.
  2. Same PR but touching one file outside those two prefixes → bootstrap
     does not fire (falls through to normal, still-blocked behavior).
  3. Same PR but missing the justification section, or missing approval
     evidence → bootstrap does not fire.
  4. A non-gate PR (e.g. touching only `src/`) can never reach the
     eligibility branch regardless of body content — asserted directly, not
     just implied by (2).
  5. Trust-boundary regression test: assert every subprocess/network call
     added for bootstrap eligibility goes through `gh` (metadata) and that no
     new code path in `ci.py` reads or imports anything from a
     PR-ref checkout — plus a static assertion over
     `.github/workflows/plan-aware-closes-gate.yml` that the `checkout` step's
     `ref:` is still literally `main` and no second checkout step exists in
     the file (grep-based, so a future edit to the YAML that reintroduces a
     PR-ref checkout fails this test immediately rather than silently).
- Write `docs/issue-384/decisions/2026-08-07-bootstrap-eligibility-shape.md`
  recording the three-part eligibility shape and the two rejected
  alternatives above (ADR-shaped, per doctrine ladder: this is a
  library/pattern choice over a named alternative).
- Record, in the phase-2 implementation record, exactly how many of the three
  named sessions (#360, #284, #369) this bootstrap path would have replaced
  had it existed at the time, and confirm whether this PR's own landing still
  needed a human bypass (expected: yes, once — `_gate_bootstrap_eligible`
  only exists once merged to `main`; this PR cannot benefit from its own
  logic, which is inherent to the trust-boundary constraint, not a defect in
  the design) or state what alternative applied.

## Out of scope

- Registering any check name in GitHub branch protection settings (already
  established as out of write-set precedent from #245).
- Any change to `.github/workflows/plan-aware-closes-gate.yml` itself — the
  fix is entirely inside `gates/ci.py`, which the workflow already checks out
  from `main` and executes; the workflow file needs no edit for this proposal
  and is listed in the added trust-boundary regression test specifically so
  it stays that way.
- Retroactively re-labeling #360/#284/#369's merged PRs or history.
- General write_scope/protected-path/deps/record checks — this proposal only
  touches the `closes_only` path, which is the one that actually blocked the
  three named cases.

## How you'll know it worked

- `gates/test_closes_gate_ci.py`'s five new cases run and pass, including the
  trust-boundary regression test — this is the "test over the actual
  situation" the issue's acceptance section requires, not prose.
- The trust-boundary regression test passing, plus the unchanged
  `plan-aware-closes-gate.yml` diff (or its absence, since this proposal's
  write set excludes it), is the verification-not-assertion the issue asks
  for regarding "a PR still cannot edit `gates/ci.py` to make itself pass" —
  stated as a result of running that test, in the phase-2 record, not
  asserted independently of it.
- The phase-2 record states the count from "What will be done"'s last bullet
  as a measured number, not an estimate.
