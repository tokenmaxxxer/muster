# Parallel role-session conflict methodology

Adapted from the `agent-coordination`/`merge-gates` skill methodology to this
repo's role-handoff contract (v3): role sessions land only through a PR plus a
human `Approve` (contract v3 s19) — they never self-merge and never watch each
other's liveness in real time. This spec answers #323: what a role session
does the moment it detects an overlapping write set with another open PR.

## Claim source

The claim is the `files:` frontmatter already frozen on a phase-1 proposal
(`docs/issue-<n>/proposals/*.md`) once that issue has a currently-open PR. No
new claim file is introduced — the existing artifact is the record.

`files:` frontmatter is this repo's one authoritative write-set-claim format;
any other role or issue that needs to read a write-set claim consumes this
same parser (see `scripts/check-write-set-conflicts.sh`) rather than
inventing a second one. (Binding on this decision: a sibling proposal for
issue #324 chose a `spec.md` `write:` glob as an alternative source and had
that choice rejected — measured 0 files matching that glob anywhere in this
repo, so it named no real claims. `files:` frontmatter is the format that
actually appears on disk.)

## Liveness signal

A write-set claim is "in flight" exactly when its issue has a currently-open
PR (`gh pr list`). No heartbeat file, no claims.json, no polling loop: role
sessions are short-lived and do not watch each other, so PR open/closed state
on GitHub is the only signal with an actual process behind it.

## Overlap detection

For every pair of distinct issues each with a currently-open PR, compute the
intersection of their proposals' `files:` path lists. Any non-empty
intersection is a conflict candidate.

## What counts as a conflict

Any path present in both issues' frozen `files:` lists while both PRs remain
open, and no resolution record exists for that pair (see below). A resolution
record present for the pair means the conflict is settled, not absent — the
checker treats it as resolved, not as never-having-existed.

## Where a resolution is recorded

- If the resolution fits naturally inside one of the two subjects' own
  record, it goes in that subject's `docs/issue-<n>/reports/implementation.md`,
  under the existing `## Rationale for deviations` section.
- Otherwise (the resolution doesn't belong to either subject alone — e.g. it
  changes a shared contract both issues depend on), it goes in a new
  `docs/issue-<n>/reports/conflict-<other-issue>.md`, written under whichever
  of the two issues detected the overlap later (see resolution rule below).

## Resolution rule

Cheapest-to-revert yields, adapted from `agent-coordination`. Applied by
whichever session's write-set overlap is *detected later* — that session
still has the choice available (it has not yet committed against the
now-claimed path), so it is the one that adapts: waits, narrows its own write
set, or coordinates a shared contract change, and records which it did and
why.

## Known limitation — proposals with no `files:` claim

Measured against this branch's `docs/issue-*/proposals/*.md` (all issue
trees): 111 total proposal files, 75 (67.6%) carry `files:` frontmatter, 36
(32.4%) do not. A proposal with no `files:` frontmatter makes no write-set
claim this checker can see — its issue's overlaps are `unknown`, not
"resolved" and not silently treated as "no possible conflict." This
methodology does not retroactively correct or backfill those 36 proposals;
that is out of scope here and left as a known gap for whichever future work
wires this checker into an actual merge gate.

## Out of scope (see issue #323's approved proposal)

- Running this checker automatically in CI or as a `PreToolUse` gate hook.
- Orchestrator scheduling changes to increase parallelism (#324).
- Orchestrator-side enforcement of its own procedural obligations (#298).
- Any change to the existing worktree-per-role isolation mechanism.
- A live, real-time coordination bus (heartbeats, `claims.json`) — this
  repo's PR open/closed state is the liveness signal used instead.
