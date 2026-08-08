---
loop_state: phase-1-survey
---

# Current-state survey: issue #511 execution observation

Subject: #511. Observed role/session: the session that authored PR #513
(branch `issue-511/requirements-engineering`, merged into `main` as
`be46db5`, top implementation commit `e9b2435`). Observed artifacts read
this session: `gh issue view 511` (full body + comment thread), `gh pr
view 513 --json ...,commits`, `git show e9b2435 --stat`, and the observed
role's own phase-2 record at
`docs/issue-511/reports/requirements-engineering.md` (all sections, in
full), plus the shipped code itself: `gates/risk_report.py`,
`on-the-record/hooks/impact-guard.sh`,
`on-the-record/hooks/test_impact_guard.py`,
`docs/specs/impact-classification.md`, `docs/specs/standing-decisions.md`.

## Scope named

This survey covers exactly one observation target: whether the runtime
claims about `gates/risk_report.py`'s four-axis classifier and
`on-the-record/hooks/impact-guard.sh`'s batch-approval blocking path —
as landed in PR #513 and described in
`docs/issue-511/reports/requirements-engineering.md` — actually hold when
independently exercised against fresh fixtures this session builds
itself: a high-impact (worst-reversibility) proposal is blocked from
batch approval, a low-impact one passes, unparseable input classifies to
the highest grade, and the classification values used match the anchored
conditions stated in `docs/specs/impact-classification.md` and
`docs/specs/standing-decisions.md`, not undocumented code-only constants.

## What the record already claims (read, not yet verified)

`docs/issue-511/reports/requirements-engineering.md` claims (quoted/
summarized from that file): `pytest gates/test_risk_report.py -q` → "31
passed"; `python3 on-the-record/hooks/test_impact_guard.py` → "4 passed"
covering `t_batch_of_only_low_impact_proposals_is_allowed`,
`t_batch_with_high_impact_proposal_is_denied`,
`t_kill_switch_reverts_the_wiring_and_allows_the_same_batch`,
`t_single_merge_is_not_treated_as_a_batch`; and a full-suite run of "272
passed". These are read as claims to independently reproduce this
session, on my own fixtures, not accepted as given.

An open finding already recorded by the observed session itself
(`docs/issue-511/reports/requirements-engineering.md`, "Open findings"):
`scan_open_proposals()` trusts each proposal's `status: proposed`
frontmatter with nothing flipping it on merge, so in *this actual repo*
`impact-guard.sh` denies nearly every real batch merge today —
independent of this session's own fixture runs, which must therefore use
a synthetic TARGET repo (per requirement 7 / `test_impact_guard.py`'s own
pattern), not this repo's own working tree, to observe intended
red/green behavior cleanly.

## Write surfaces this session touches (thin/unknown before execution)

- `on-the-record/hooks/impact-guard.sh` — read in full (109 lines).
  Invocation contract: payload JSON on stdin
  (`{"tool_name": "Bash", "tool_input": {"command": ...}}`), script reads
  it, sets `IG_PAYLOAD`/`IG_CHECKOUT`/`IG_TARGET` env vars for an inline
  `python3 -c` block, `cwd` at invocation time is read via `pwd -P` as
  `IG_TARGET` (the classified TARGET repo). Confirmed from
  `on-the-record/hooks/test_impact_guard.py`'s own `_run()` helper
  (subprocess with `input=payload`, `cwd=target`,
  `TOKENMAXXXER_CHECKOUT=ROOT`) — not yet confirmed from a live run this
  session.
- `gates/risk_report.py` — read in full (314 lines): `classify_axes()`,
  `reversibility_grade()`, `batch_blocked()`, `scan_open_proposals()`.
  Fail-closed default (`AXIS_MAX=4`) on empty/unparseable write-set
  confirmed by reading each `*_grade` function's `if not paths: return
  AXIS_MAX` branch; not yet confirmed by an actual unparseable-proposal
  fixture run.
- `docs/specs/impact-classification.md`,
  `docs/specs/standing-decisions.md` — read in full; the grade bands and
  the `AXIS_MAX`/`requires_individual_approval` wording quoted there is
  the anchor this session's fixture values must be checked against
  (issue #511 acceptance: "classification values match the anchored
  conditions in the spec files, not code-only constants").
- No file under the observed role's `src/`, `test/`,
  `gates/risk_report.py`, `on-the-record/hooks/`, or any
  `docs/issue-511/` path other than this role's own report/proposal path
  will be edited by this observation — independence per the role
  directive.

## Scout skip record

Scouting is skipped: this is a verification-shaped task with no open
design decision (independently re-invoking an already-designed,
already-shipped classifier and hook against fixtures this session
builds) — skip condition "pure bugfix / no design decision left open"
applies, same as the precedent observation for issue #512
(`docs/issue-512/reports/execution-observation/survey.md`).
