# Survey — issue-294

Scope: on-the-record/commands/run.md, step 6 ("결과 수용" / acceptance branch).

## Current state

Line 229 of `on-the-record/commands/run.md`:

```
- 결과 수용 → `gh pr merge <n> --merge --delete-branch` — 머지된
  브랜치는 반드시 함께 지운다. 역할별 이슈 브랜치는 PR 이 생명주기다
```

Acceptance is a single command. Nothing upstream of it in step 6 reads
`gh pr checks <n>` or branches on the result. No other line in run.md
references `gh pr checks` (grepped, no hits).

## Overlap with named issues

- **#290** (test suite decorative, no CI runs it) and **#291** (no branch
  protection on core/rulebooks) are the *substrate* half named in #294's
  own body — they are about there being something to check at all. Both
  are still OPEN. #294's acceptance criteria explicitly scope those two
  out: "Cross-referenced from #290 and #291 so the three land as one
  working system, not three partial fixes" — i.e. #294 only needs to
  reference them, not fix them.
- **#284** (closes-gate phase-flip false red) is CLOSED. #294's body
  cites it only as context for why a missing/red check must not be
  treated as equivalent to a passing one — no code changes needed here
  beyond the run.md text.
- **#298** and #298's 2026-08-07 Stop-hook comment, cited in this
  session's invocation, concerns whether the orchestrator itself can be
  blocked mechanically — orthogonal to this issue's scope (run.md
  procedure text), not touched here.

## Write set

- `on-the-record/commands/run.md` — add a required precondition to the
  acceptance branch (step 6, "결과 수용"): read `gh pr checks <n>`
  before merging; refuse to merge on a failing or missing required
  check; name the "no checks configured" branch explicitly (escalate,
  do not treat absence as pass).

No other file needs to change: this is procedure/instruction text, not
code with a test suite of its own (run.md has no associated unit tests
in this repo).

## Design space

The acceptance criteria in #294 are specific enough to leave no open
design decision: (1) name check verification as a required precondition
of merge, (2) give an explicit branch for "no checks exist" (escalate).
Scout-directive skip condition applies: "the spec leaves no design
decision open." No exemplar sweep needed — this is a rewrite of an
existing internal procedure paragraph, not a product-shaped surface.
