---
code_under_review:
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
  - on-the-record/hooks/spec-index-preflight.sh
  - on-the-record/hooks/test_spec_index_preflight.py
  - on-the-record/hooks/hooks.json
  - docs/specs/enforcement-boundary.md
loop_state: phase-2-complete
resolved_findings:
  - finding: docs/reports/2026-08-08-hunt-issue-459-pr-and-spec-index-preflight-hooks.md (before-landing) — pr-preflight.sh/spec-index-preflight.sh shipped without the executable bit, so hooks.json's direct command invocation would fail with Permission denied (exit 126) on every Bash call.
    resolution: chmod 775 both scripts to match every sibling hook (contract-guard.sh etc.); re-ran the hunter's exact repro (`echo hi` payload through pr-preflight.sh) and confirmed exit 0.
---

# Implementation record — issue-459

Subject: issue-459. Approved via issue-level comment `APPROVE
issue-459/implementation` by JiwonJung94 (approvers.md, single-account
mode — PR #461 author is also JiwonJung94).

## Why

run.md's PR/commit authoring flow repeated two CI-caught mistakes today
(#447/#448/#458 closes-trailer shape, #455 spec-index-drift shape); the
fix is to catch both in-session, before the act, per the approved
phase-1 proposal.

## Plan / what was done

Built per `docs/issue-459/proposals/2026-08-08-pr-and-spec-index-preflight-hooks.md`,
exactly the frozen write set, no widening:
- `on-the-record/hooks/pr-preflight.sh` — `PreToolUse`/`Bash`, intercepts
  `gh pr create`/`gh pr edit`; ports `gates/pr_reference.py::check_body`
  and `gates/flows.py::_plan_from_body` inline (zero-install, no
  `gates/` import); resolves subject issue + phase from the current
  branch name and the `APPROVE issue-<n>/<role>` comment convention;
  extracts PR body from `--body`/`--body-file` on the command line
  itself; denies (exit 2) with the exact expected trailer; fail-open on
  any lookup/parse gap.
- `on-the-record/hooks/test_pr_preflight.py` — 8 cases (red: #447/#458
  premature-Closes shape, #448 missing-Closes shape; green: phase-1
  plain-`#n`, phase-2 Closes with no/complete/only-last-incomplete
  plan) plus 2 `_plan_from_body`-port cases.
- `on-the-record/hooks/spec-index-preflight.sh` — `PreToolUse`/`Bash`,
  intercepts `git commit`; ports `gates/spec_index.py::parse_index`'s
  row regex inline; hashes staged (not working-tree) content via
  `git show :<path>`; prefers the staged index version when
  `reconciled-index.md` is itself staged (same-commit regen detection);
  denies (exit 2) naming the file and `python3 gates/spec_index.py
  --update`; fail-open when the index is unreadable or `git diff
  --cached` fails.
- `on-the-record/hooks/test_spec_index_preflight.py` — 6 cases: 2 red
  (drift not regenerated / staged index still has old hash), 2 green
  (staged index matches new hash / unrelated file / unchanged content),
  1 skip case (staged deletion).
- `on-the-record/hooks/hooks.json` — added `pr-preflight.sh` and
  `spec-index-preflight.sh` as two more `command` entries in the
  existing `Bash` matcher block, after `contract-guard.sh`.
- `docs/specs/enforcement-boundary.md` — added two `contract` rows for
  the new `.sh` files.

Confirmation run (this session, once): `python3
on-the-record/hooks/test_pr_preflight.py` exit 0 (8/8 pass); `python3
on-the-record/hooks/test_spec_index_preflight.py` exit 0 (6/6 pass);
`python3 gates/test_boundary.py` exit 0 (5/5 pass, both new `.sh` files
recognized). Manual end-to-end check: staged an edit to
`protocol.md` (an actual `reconciled-index.md`-tracked file) without
regenerating the index, piped a synthetic `git commit` PreToolUse
payload into `spec-index-preflight.sh` directly — denied (exit 2) with
the exact regen command named; reverted the test edit with `git
checkout --`, working tree confirmed clean of the probe afterward.

## What did not work

None.

## Doc-placement ladder

- [x] `on-the-record/hooks/hooks.json` — new dep-free wiring entries added same commit as the new hooks (config/setup-step doctrine).
- [x] `docs/specs/enforcement-boundary.md` — two new rows recorded same commit as the two new `.sh` files (mechanical `test_boundary.py` requirement, doctrine ladder: new mechanism -> boundary spec).
- No new env var, dependency, or migration introduced.

## Hunt cadence

- After-proposal hunt already recorded (commit cc64173 / b311bac).
- Before-landing hunt: dispatched (stance 4, cap 180s per >5 files
  touched), recorded in
  `docs/reports/2026-08-08-hunt-issue-459-pr-and-spec-index-preflight-hooks.md`.
  Returned one finding (see resolved_findings above) — resolved same
  session, hunter's exact repro re-run and confirmed fixed.

## Open findings

None — the one before-landing finding is resolved (see
`resolved_findings:` in frontmatter).

## Open finding resolution path

N/A — no open findings remain.

## Next steps

None for this issue — commit, push, and PR #461 update land this
turn. Follow-ups explicitly out of scope per the proposal: CI-supplement
workflow twins, extending `pr_reference.check_body`'s underlying rule,
`closure_sweep.py` board-wide case, folding `landing_readiness.py` into
a hook.
