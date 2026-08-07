# Survey — issue #328 (issue bundling)

## Scope of the defect

Issue content (title/body) is authored as prose by the orchestrator LLM
during `run.md`'s "요구사항 → 이슈" step (`on-the-record/commands/run.md:14-32`,
`:266-273`). There is no function in `spawn.py` that constructs an issue
title or body — `spawn.py` only posts *comments* to already-open issues
(`_post_crash_comment` and similar) and gates only read issue/PR metadata
after the fact (`gates/pr_reference.py`, `gates/closure_sweep.py`). This
means the defect cannot be fixed by patching a single call site; the only
enforceable mechanism is a **post-hoc mechanical check** run against an
issue's title/body text, mirroring how `gates/pr_reference.py` checks PR
bodies after the fact rather than how the PR was written.

## Existing gate pattern (what to reuse)

`gates/pr_reference.py` establishes the house pattern for this kind of
check: a pure `check_body(text, ...) -> list[str]` function that takes
already-fetched text and returns human-readable violation strings (empty
list = pass), independently unit-testable with no network
(`test_gates.py` imports `pr_reference` directly and calls `check_body`
with literal strings). A thin CLI wrapper (`gates/pr_reference.py`'s
`__main__` block, not shown above but present per its docstring) calls
`gh issue view`/`gh pr view` to fetch the live text, then calls the pure
function. `gates/gates.py`'s stated philosophy applies directly: "불확실하면
막는다" (uncertain → block) — a check that can't confidently classify an
issue should fail closed, not silently pass.

`.github/workflows/plan-aware-closes-gate.yml` shows the wiring pattern
for turning a gate script into an enforced CI check: checkout `main` only
(never the PR's own diff, so a PR can't rewrite the gate that judges it),
run the gate script with `GH_TOKEN`, exit-code gates the job. That
workflow triggers on `pull_request`; this issue's check needs to trigger
on `issues: opened` instead, since bundling is a property of the issue
itself, filed before any PR exists.

## What's missing (gap confirmed)

- No file in the repo mentions issue #310 ("acceptance must name an
  executable artifact") verbatim — that constraint exists only in GitHub
  issue history, not yet codified in-repo.
- No `docs/decisions/` or `docs/specs/` entry on issue sizing or
  bundling — the sibling "issue-sizing" issue's concept is not yet
  documented anywhere in-repo either. This issue and its sibling are
  genuinely new ground, not a case of missed existing tooling.
- No `.github/ISSUE_TEMPLATE/`, no `CONTRIBUTING.md`, no `scripts/`
  directory — issue authorship has zero structural guardrails today.

## Mechanically checkable vs. not

The issue itself names three tells: (1) title needs "and", (2) acceptance
items touch unrelated code paths, (3) the issue would be worked by
different roles. Of these:

- (1) is directly checkable from title text alone (regex on coordinating
  conjunctions), no network beyond fetching the title.
- (2) is checkable if acceptance items name concrete paths in inline code
  spans (the existing repo convention — issues in this project routinely
  reference file paths like `` `spawn.py:2199` `` in backtick spans); if
  two or more top-level path roots with no common ancestor appear across
  distinct acceptance bullets, that's a mechanical signal.
- (3) is not mechanically checkable without a role-assignment field that
  doesn't exist in issue text today (issues don't declare "role: X" as
  structured data) — flagging this honestly as unchecked, per issue
  #310's own requirement that an unchecked rule must say so rather than
  pass as enforced.

## Write set for the proposal

- `gates/issue_bundling.py` — new pure-function gate (title/body →
  violations), CLI entry fetching via `gh issue view`.
- `test_issue_bundling.py` — unit tests, no network, following
  `test_gates.py`'s existing style.
- `.github/workflows/issue-bundling-gate.yml` — CI wiring on
  `issues: opened`.
- `docs/issue-328/reports/implementation.md` — phase-2 record.
