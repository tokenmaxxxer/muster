# Current-state survey — issue #135

## What exists today

- `spawn.py` `roster_watchdog()` (line 1393) scans the live session roster
  for anomalies (`normal`/`stalled`/`crashed`/`in-progress`) — no
  issue↔PR closure cross-check anywhere in it.
- `gates/pr_reference.py` (issue-126): `check_body(issue, body, phase)`
  gates a *single PR at open time* — phase1 PRs must carry a plain `#n`
  (Closes/Fixes/Resolves forbidden), phase2 PRs must carry
  `Closes|Fixes|Resolves #n`. Wired into `gates/ci.py` via optional
  `--pr/--issue/--phase` flags. This is a pre-merge gate on wording, not
  a post-merge consistency sweep — it cannot see what happens after the
  PR closes.
- Idempotent-comment pattern already exists:
  `spawn.py::_post_crash_comment` (line 1486) — build a fixed marker
  string, check `_issue_comments()` (line 804, `gh api
  repos/<slug>/issues/<n>/comments`) for it before posting, so repeat
  watchdog runs never double-comment. Reusable as-is for a sweep report
  comment.
- `board(root)` (spawn.py line 955) enumerates local subjects
  (`docs/issue-<n>/`) → role → frontmatter, but that is *local repo
  state*, not GitHub issue/PR state — it cannot tell open vs. closed.

## GitHub API surface (tested empirically, this session)

`gh pr view <n> --json closingIssuesReferences` returns the issues a PR
will close on merge — GitHub computes this from `Closes/Fixes/Resolves
#n` in the body, whether the PR is open or merged:

```
$ gh pr view 136 --json number,closingIssuesReferences
{"closingIssuesReferences":[{"number":73,...}],"number":136}
```

This is the load-bearing primitive: it is exactly GitHub's own
understanding of "which issue does this PR close," so the sweep can
reuse it instead of re-parsing PR bodies with regex (`pr_reference.py`'s
`_CLOSES_REF`/`_PLAIN_REF` remain useful for the open-PR pre-merge gate,
but a closed-loop sweep should ask GitHub directly rather than duplicate
the parse).

## The three measured leak cases (issue body)

| case | issue | PR | what happened |
|---|---|---|---|
| A | on-the-record #97 (CLOSED now) | #98, body `Refs #97` (plain, no Closes), MERGED | phase-1-shaped reference on a PR that carried real changes — merge did not auto-close #97; someone closed it by hand later. Leak point: a PR that isn't a phase-1 proposal still used a plain `#n` instead of `Closes #n`, so GitHub had nothing to auto-close on merge. |
| B | on-the-record #44 (CLOSED now) | #50, body `Relates to #44` (plain) | same shape as A — phase-1-style plain reference on a merged PR whose companion delivery PR (or later manual close) eventually closed the issue. |
| C | tokenmaxxxer-core #16 (CLOSED, `closedAt` 2026-07-30T10:06:37Z) | #17, body `Part of #16`, MERGED at 09:52:50Z | ~14 min gap between merge and manual close in this snapshot — the issue text describes this pair as observed open+merged for over a day at filing time; it has since been closed by hand, i.e. it self-healed only because a human noticed and intervened, not because any automation caught it. |

All three share one shape: a merged PR whose body plainly references
its issue but does not carry `Closes/Fixes/Resolves`, so GitHub's
auto-close never fires, and the issue is left open until a human
notices and closes it by hand. `pr_reference.py`'s phase1/phase2 gate
(issue-126) only fires at PR-open time and only on the *shape* of the
reference for a role-handoff PR; it does not (and structurally cannot,
being pre-merge and single-PR) catch this after the fact, and it has no
opinion about PRs opened outside the two-phase role-handoff flow (a bare
bugfix PR, e.g.) which is exactly the shape of cases A/B/C.

## Where none of the three leaked from "missing permission" or "missing gate entirely"

- Session did not fail to close: none of the three PRs were phase-2
  delivery PRs under the role-handoff contract (no `Closes #n`
  requirement applied to them at write time) — cases A/B predate or sit
  outside the phase1/phase2 convention on that branch's PR (a plain
  `Refs`/`Relates to` reference was never wrong for a *non-role-handoff*
  PR, since the convention only binds role-handoff coding sessions).
  Case C is a cross-repo-adjacent situation (core repo) where "Part of
  #16" was chosen deliberately to avoid a premature auto-close.
- So the leak is not a broken gate — `pr_reference.py` did what it was
  built for. It's an absent invariant *sweep*: nothing periodically asks
  "is there a closed issue with an open PR" or "is there a merged PR
  that closes an issue that's still open" across the whole board,
  regardless of whether the PR went through the two-phase convention.

## Existing test coverage

- `test_gates.py`: 4 cases for `pr_reference.check_body` (phase1/phase2
  pass/fail) — pre-merge only.
- `test_spawn.py`: watchdog/respawn tests including
  `test_cap_reached_posts_comment_instead_of_respawning` (idempotent
  comment marker pattern) — no test touches issue/PR closure state.
