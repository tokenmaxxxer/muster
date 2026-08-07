Subject: issue-322

# Current-state survey

## Where operator decisions currently live
- PR reviews: Approve / non-APPROVE review comments on role PRs (`gh pr view --json reviews`, `gh api repos/.../pulls/<n>/reviews`). Per contract v3 s19, single-account approval is the literal string `APPROVE issue-<n>/<role>` as an issue comment; everything else is prose feedback — this prose is exactly the "노하우" the issue names.
- Issue comments on filed issues (`gh issue view <n> --comments`).
- `docs/decisions/*.md` — but these are role-authored ADRs about *technical* choices, not a log of the operator's approve/refuse judgments. Two exist today (`2026-07-29-headless-cli-measured-facts.md`, `2026-07-29-permanently-closed-alternatives.md`); neither is structured for pattern mining (free prose, no per-decision fields).
- `ledger/collect.py` reads `docs/**/reports/review.md` verdict fields (Present/Surface/Absent/Incorrect) — this is a *reviewer* verdict ledger, not an operator-decision ledger. Nothing analogous exists for the operator's own approve/refuse/feedback history.
- Nothing today parses PR review bodies or issue comments for recurring corrective language. No file, script, or gate in `gates/`, `ledger/`, or `on-the-record/` touches PR review *text* — `gates/*.py` are all deterministic diff/path checks, not content-of-feedback checks.

## The #310 evidence cited by the issue
`docs/issue-310` only exists on the unmerged branch `origin/issue-310/implementation` (phase-1 proposal only, not landed on main). Its proposal (`docs/issue-310/proposals/2026-08-07-discharge-gate.md`) addresses a *different* recurring correction (patch-instead-of-structure) by proposing a mechanical discharge gate for *that specific* rule. It does not build any general mining/surfacing mechanism — confirming the gap #322 describes: each recurring correction to date has been hand-turned into an artifact by a human noticing the repetition, not by the system.

## What "recoverable" concretely means here
The raw corpus is: (a) issue-comment bodies on `JiwonJung94`/`jjongkwann`-authored comments across issues, (b) PR review bodies from `docs/specs/approvers.md` accounts, (c) the `## What did not work` / `## Rationale for deviations` sections role sessions already write into their own records when a correction forced a change. (c) is the highest-signal source: it is already the record of "something the operator's implicit judgment invalidated," authored by the role that got corrected, one entry per event — but nothing currently aggregates it across issues/sessions to find repeats.

## Constraints observed
- Per contract v3 s19, the operator is the sole author of requirements/approvals; no role may fabricate or restate their judgment as a rule on their behalf (this issue's own body: "the operator is the author of their own judgment, and a mined pattern is a *proposal* to them, never a fact about them").
- Per #310 (this session's directive), acceptance must name an executable artifact that fails on regression; a memory note, doc sentence, or promise does not discharge it.
- Per #330 (this session's directive), a change must state what it invalidates on disk / reaches beyond its own acceptance criteria.
- gh CLI is available and authenticated in this environment (used above for issue/PR reads) — a mining script can shell out to `gh api`/`gh issue`/`gh pr` without a new dependency.

## Write set this proposal will project
- `docs/issue-322/proposals/<date>-decision-mining.md` (this proposal)
- `docs/issue-322/reports/implementation/survey.md` (this file)
- (phase 2, pending approval) a script under a new top-level location analogous to `ledger/` — the repo's existing convention for "read the record, compute something objective" tools — plus its test file, since `ledger/collect.py` and `gates/*.py` both ship paired `test_*.py`.

## Scout brief
See `docs/issue-322/reports/implementation/scout-brief.md`.
