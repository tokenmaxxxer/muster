# Risk-classified approval report

`gates/risk_report.py` gives a human triaging a batch of open phase-1
proposals a single view of which ones are low-stake and which are not,
instead of deciding on each proposal cold and one at a time (issue #319).

## Running it

```
python3 gates/risk_report.py [repo-root]
```

Scans `docs/issue-*/proposals/*.md` and `docs/proposals/*.md` for entries
with `status: proposed`, classifies each `high`/`low`, and prints one
Markdown table with `high` rows first.

## Classification

- `high`: any path in the proposal's `files:` list is protected
  (`gates.py:is_protected` — `.github`, `migrations`, `auth`, root config,
  credential-shaped globs, etc.), OR total changed lines exceed 30, OR the
  `files:` list is missing/unparseable.
- `low`: everything else.

An unparseable write-set is fail-closed into `high` — an unknown write-set
is never presented as safe.

## What this is not

This report is **advisory only**. It never grants approval, never changes
what counts as a valid phase-2 approval act, and is not wired into any
blocking gate (`gates.py:check()`, CI, `gh-guard`). Contract v3 s19 still
requires, for every phase-2 transition, either a PR review `Approve` from
an `approvers.md` account distinct from the PR author, or an issue comment
whose entire body is exactly `APPROVE issue-<n>/<role>` from an
`approvers.md` account. Reading a `low` classification does not excuse
skipping that check — it only tells the reviewer where to look first.
