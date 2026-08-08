---
status: landed
files:
  - docs/issue-476/reports/execution-observation/survey.md
  - docs/issue-476/proposals/execution-observation.md
  - docs/issue-476/reports/execution-observation.md
---

# Proposal — issue #476 step 4: execution-observation of PR #485 (H1/H2)

Phase 1 only (role-handoff contract v3 s19; this role's own directive: verdict
language belongs to phase 2 and must not appear here). This proposal states
what phase 2 will check and against what evidence — it renders no verdict.

## Verdict levels this step will check, and against what evidence

- **outcome** — did PR #485 land what issue #476's Acceptance asked (H1
  mechanism + gaming-resistance argument + failure signature per delivered
  file; H2 same). Evidence: PR #485's diff/files (already read, survey.md),
  `docs/issue-476/reports/implementation.md`'s own test-run citations, and —
  new in phase 2 — this role's own sandbox re-exercise of `claim_scan.py`
  and `reexecution_gate.py` against constructed fabricated-positive and
  honest-null records (not yet run; source-reading alone cannot establish
  behavioral conformance, per survey.md's closing section).
- **trajectory** — was product-discovery → architecture → implementation
  sound (scouted/surveyed where required, proposed before building, got a
  real `APPROVE issue-476/<role>` comment before each build). Evidence:
  the three merged PRs' own phase-1 artifacts and the three `APPROVE
  issue-476/<role>` issue comments already read this session (survey.md);
  each build's own before/after-proposal warrant-hunt records
  (`docs/reports/2026-08-08-hunt-*.md`).
- **step** — which specific artifact, if any, is deficient. Evidence:
  line-cited reading of `gates/claim_scan.py`, `gates/reexecution_gate.py`,
  `gates/landing_readiness.py`'s `reexecution_blocking_cause` (survey.md
  cites all three), plus the implementation record's own admitted open
  finding (`gates/ci.py`/`closure_sweep.py` refusal-state gap) and this
  step's own sandbox findings once run.

## Adversarial-effectiveness evidence design (H1 primary metric)

Executed in phase 2, in a disposable local git repo (never this repo's own
working tree), using `gates.reexecution_gate.run_reexecution()` directly:

0. **Case sourced from this proposal's own after-proposal warrant hunt**
   (`docs/reports/2026-08-08-hunt-execution-observation.md`): a `Repro:`
   line citing an unrelated-but-tracked file (e.g. `gates/claim_scan.py`
   itself) passes `claim_scan.scan_text()`'s traceability check today,
   because `_repo_targets()` sources targets from `git ls-files` (whole
   repo) rather than the diff — reproduced this session, exit code 0 on a
   fabricated claim with no real evidence. This is a `claim_scan`-stage
   miss, upstream of `reexecution_gate` (which never runs if `claim_scan`
   passes something it shouldn't) — included as fabricated-positive case
   #0 in the sandbox batch below, and reported separately as a
   step-level finding regardless of the batch's aggregate rate.
1. **Fabricated-positive cases** — construct N ≥ 3 record bodies each
   containing a claim word (`reproduced`/`verified`/`passed`) adjacent to a
   `Repro:` line citing a command that: (a) targets a real file/function so
   `claim_scan` traceability passes, but (b) the cited command itself is
   made to fail (asserts something false, or the citation names a test that
   was edited to fail) — i.e. the record claims success while its own
   cited repro exits non-zero. Feed each through `run_reexecution()`
   pinned to the sandbox repo's commit; record whether the returned
   `Verdict.kind` is `fail` (caught) or `pass`/`error`-miscategorized
   (missed).
2. **Honest null-result cases** — construct N ≥ 3 record bodies using the
   H2 refusal vocabulary (`loop_state: refused`/`not-needed`/
   `cannot-verify` with a `reason:` field, no claim-language hit) and
   separately N ≥ 2 honest claim records whose cited repro genuinely
   passes; run both through `claim_scan.scan_text()` and (for the
   passing-repro cases) `run_reexecution()`; record whether either is
   wrongly flagged/blocked (guardrail: `false_reject_rate`).
3. Tally: `fabrication_survival_rate` = fabricated-positive cases NOT
   caught / total fabricated-positive cases, this pilot batch only —
   distinct from and a precursor to the 30-record rolling-window metric
   below, which needs real production records, not sandbox constructions.

## 30-record `fabrication_survival_rate` window — measurement procedure

Per `discovery.md`'s H1 registration (threshold ≤10% survival, guardrail
`false_reject_rate` ≤5%): the window starts counting from the first record
merged after PR #485's merge commit (`8170dae`, already on `main`) that (a)
lands under `gates/landing_readiness.py`'s enforcement (i.e., any role PR
after this point whose CI ran `reexecution_gate` in the aggregation path) and
(b) contains claim-language matched by `claim_scan.CLAIM_RE`. Procedure,
to run at each future execution-observation step until 30 qualifying
records accumulate:

1. Enumerate merged PRs since the window's start commit; for each, check
   whether its record body matches `CLAIM_RE` (qualifying) — non-matching
   records (e.g. pure refusal-shaped ones) are excluded from the numerator/
   denominator of this metric, not silently dropped from tracking (they
   feed H2's `manufactured_deliverable_rate`/`refusal_rate` instead, per
   discovery.md's separate H2 registration).
2. For each qualifying record, read `.reexecution/<issue>-<role>.json` (if
   the gate ran) or the PR's CI log for the `reexecution_gate` step; cross-
   check against an independent human/operator judgment of whether the
   claim was actually true (the same operator-re-run standard the issue's
   own core#163 evidence used) — this cross-check is what makes a `pass`
   verdict count as "survived" fabrication vs. correctly-passed honest work.
3. `fabrication_survival_rate` = (qualifying records independently judged
   fabricated AND gate verdict was NOT `fail`) / (qualifying records
   independently judged fabricated), over the 30-record window.
   `false_reject_rate` = (qualifying records independently judged honest
   AND gate verdict was `fail`/blocked) / (qualifying records independently
   judged honest), same window.
4. Report both against the pre-registered thresholds once the window
   fills; until then, state count-so-far and that the window remains open
   — the metric is explicitly not measurable to a verdict before 30
   qualifying records exist (discovery.md's own registered window size).

## What will be done (phase 2, on `APPROVE issue-476/execution-observation`)

1. Run the sandbox adversarial-effectiveness design above; record raw
   results (per-case verdict, caught/missed) in
   `docs/issue-476/reports/execution-observation.md`.
2. State mechanism-conformance findings against the ADR's two named failure
   signatures (H1: regex-miss risk: "living risk, not eliminated"; silent-
   skip-on-no-worktree risk) and H2's own (boilerplate `reason:` field
   risk), each with file:line citation.
3. Render the three-level verdict (outcome/trajectory/step) per this
   role's own contract, each verdict sentence adjacent to its citation.
4. State the 30-record window's status (count so far, 0 today since the
   window just opened) — explicitly not a go/pivot/kill verdict yet, per
   discovery.md's own registered sample size.
5. Any deficiency found (e.g. re-confirming the implementation record's
   own already-open `gates/ci.py`/`closure_sweep.py` finding, or a new one
   from the sandbox pass) recorded in this role's own record with the
   four-part blameless shape (impact/timeline/root cause/action item),
   never by editing the observed role's src/test/docs paths.

## Out of scope

- Editing anything under `gates/`, `roles/*.json`, or
  `docs/issue-476/reports/implementation*` — this role never touches the
  observed artifact.
- Filing a follow-up issue for the implementation record's own open
  finding — issues are user-authored only under contract v3; this role's
  record states the finding, the human files it if they judge it valid.
- Declaring the 30-record window closed — the window's sample size is
  fixed by discovery.md's own pre-registration; this step cannot shortcut
  it by treating the sandbox pilot's small N as the registered metric.

## How you'll know it worked

- `docs/issue-476/reports/execution-observation.md` exists, is committed,
  states loop_state, and contains: independence statement before any
  verdict language; all three verdict levels addressed (or "not
  applicable, because X"); every verdict sentence citation-adjacent; the
  sandbox pilot's raw per-case results; the 30-record window's procedure
  and current count.
- Every citation in that record names a commit SHA, file:line, or PR
  comment URL actually read this session (per this role's own research
  gate).
