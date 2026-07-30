# Scout brief — issue #135

Mode: single session, no parallel subagent dispatch available for this
probe (one technical question, not a multi-angle field survey) —
falling back to direct, sequential API testing in-session rather than
fan-out. 1 stage, ~2min wall-clock.

## Finding: GitHub already computes the exact invariant we need

`gh pr view <n> --json closingIssuesReferences` returns the issues a
given PR will close on merge, derived by GitHub itself from
`Closes/Fixes/Resolves #n` text — for both open and merged PRs. Tested
live against this repo:
`gh pr view 136 --json number,closingIssuesReferences` →
`{"closingIssuesReferences":[{"number":73,...}]}`.
Source: GitHub CLI / GraphQL API, verified empirically this session
(no external doc fetch available in this environment; behavior
confirmed by direct call, not assumed).

## Must-be (adopt)

- Ask GitHub for the closing relationship (`closingIssuesReferences`),
  don't re-derive it by regex-parsing PR bodies a second time —
  `gates/pr_reference.py`'s regex is for pre-merge wording validation
  only; a post-hoc sweep should trust GitHub's own linkage so the two
  checks can never disagree about what counts as "closes."
- Idempotent reporting via a fixed marker comment (already the pattern
  in `spawn.py::_post_crash_comment`) — adopt the same shape rather than
  inventing a new one.

## Pattern to skip

- Auto-closing or auto-reopening anything. The issue text is explicit
  that a sweep reports, it does not act — closing is a human/
  orchestrator decision (contract v3: humans decide via GitHub acts).
  Bots that silently reopen/close issues (seen in some CI-bot designs)
  are exactly the footgun to avoid here.

## Gap line

Current state already has: idempotent-comment posting, a pre-merge
reference-shape gate, a local board reader. Missing: any code that asks
GitHub for issue/PR *state* (open/closed/merged) and cross-checks it —
that's the entire gap this issue closes.

Sources:
- `gh pr view 136 --json closingIssuesReferences` (this session, live test)
- `gh issue view 97/44 --repo tokenmaxxxer/on-the-record`,
  `gh pr view 98/50` (this session, live test)
- `gh issue view 16 --repo tokenmaxxxer/tokenmaxxxer-core`, `gh pr view 17` (this session, live test)
