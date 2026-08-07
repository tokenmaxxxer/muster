# Scout brief — issue #358

Non-product, process-methodology issue: the deliverable is an in-repo
convention plus a checker, not a market-facing surface. Best-in-class here is
this project's own prior solution to the identical shape of problem, one
layer down — #287, already landed as the governing precedent (see survey.md).

Sweep angle used (single round, in-repo — no external web search available
this session, stated per scout-directive's fallback for unavailable search):
read the corrected records of the three cited proposals (#318/#320, #324,
#341/#327) and the existing #287 issue text.

## Findings

- **Must-be**: a failed/incomplete lookup must yield a distinctly-labeled
  outcome, never one that reads the same as a verified negative. #287 states
  this for gates; #358 is the same must-be for survey prose.
- **Performance axis chosen**: mechanical checkability of the *shape* of an
  absence claim (evidence-adjacency), not semantic correctness of the claim
  itself — the same ceiling #341's own survey already accepted for
  orchestrator-constraint claims ("classifying ... is a natural-language
  judgment call ... a mechanical gate must refuse to attempt").
- **Pattern to adopt**: #318's approach of (a) a pure, unit-testable content-
  check function plus (b) two exact regression fixtures for facts already
  proven wrong (`runs/active.json`, the `Stop` hook's existence) — cheap,
  precise, and does not attempt to grade prose quality.
- **Pattern to skip**: a full NLP/semantic classifier for "was this absence
  claim well-researched" — #341 already rejected the adjacent case
  ("keyword/regex gate over ... prose ... is exactly the kind of check
  gates.py's own docstring says a mechanical gate must refuse to attempt")
  and the same reasoning applies here.
- **Gap line**: the project already has the *concept* (#287) but no
  *artifact* for the prose/survey instance of it — no checker, no convention
  doc, no regression fixture pinning either corrected fact from #358's own
  three cited cases.

Stage count: 1 (in-repo precedent read only). Mode: sequential single-session
read (no parallel dispatch — the three source documents were on different
branches and needed to be read in sequence to build the "same shape as #287"
argument). This is stated explicitly per scout-directive's fallback-mode
disclosure requirement.

Sources: `origin/issue-318/implementation:docs/issue-318/reports/implementation/survey.md`,
`origin/issue-324/implementation:docs/issue-324/reports/implementation/survey.md`,
`origin/issue-341/implementation:docs/issue-341/reports/implementation/survey.md`,
issue #287 (`gh issue view 287`), `.gitignore`, `spawn.py:1393`.
