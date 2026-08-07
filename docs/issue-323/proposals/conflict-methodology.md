---
status: proposed
files:
  - docs/specs/parallel-conflict-methodology.md
  - scripts/check-write-set-conflicts.sh
  - test/check-write-set-conflicts.test.sh
  - docs/handbooks/operations.md
---

## Request

The operator observed that parallel role sessions have no methodology for
resolving conflicts gracefully: isolation (per-role worktrees) defers
collisions to merge time instead of resolving them, and by merge time the
context needed to resolve them well is gone. Named failure modes: two
sessions editing the same file, two sessions changing the same contract
incompatibly, a session building on an assumption a concurrent merge
invalidates, or verification passing against a state that no longer
exists by merge time. This is scoped as research-before-implementation:
produce a methodology, then something the system enforces — not
recurring ad-hoc fixes.

## Constraints

- Per #310: prose alone does not discharge this — the acceptance artifact
  must be executable and must fail on regression.
- Per #330: state what the change reaches beyond its own acceptance
  criteria, including already-on-disk state it invalidates (see below).
- Per contract v3: role sessions land through PR + human Approve, not
  self-merge; any mechanism must fit that landing model, not assume
  agents merge themselves.
- Per operator item 7 (sibling issue framing): stay inside this issue's
  boundary — define and mechanically check the methodology. Do not absorb
  #324 (parallelism scheduling) or #298 (orchestrator enforcement gap);
  both are named only as boundary markers in the survey.
- Documents land only under `docs/` per contract v3's output-layout rule;
  no new top-level coordination directory (ruling out a literal `.agents/`
  copy of the `agent-coordination` skill's bus).

## Rationale

Chosen approach: adapt the `agent-coordination`/`merge-gates` skills'
write-set-overlap detection to this repo's existing artifacts — each
phase-1 proposal already freezes a `files:` list, so overlap detection is
a diff over proposals already on disk, backed by a script that fails
(non-zero exit) when two *currently open* PRs' frozen write sets overlap
without a recorded resolution.

Alternative considered and rejected: copy `agent-coordination`'s `.agents/`
claims/conflicts/heartbeat bus verbatim (claims.json, heartbeat staleness,
self-merge). Rejected because it assumes a coordination model this repo
does not have — role sessions are short-lived, do not loop watching each
other's heartbeats in real time, and never self-merge (contract v3 s19
requires PR + human Approve). Building a heartbeat-liveness mechanism here
would be machinery with nothing to drive it; the PR's open/closed state on
GitHub already is this repo's liveness signal, so a parallel liveness
system would be pure duplication with no operational signal feeding it.

A second alternative considered and rejected: a purely reactive check that
only inspects merge conflicts *after* they occur (git's own conflict
markers). Rejected per `merge-gates` Step 5 — textual mergeability is the
wrong variable; a clean git merge does not mean the write sets didn't
collide in intent, and inspecting only post-hoc would put the check after
the point the operator said context is already lost.

## What will be done

1. Write `docs/specs/parallel-conflict-methodology.md`: the adapted
   methodology — how a write-set claim is recorded (the existing
   `files:` frontmatter of an open phase-1/phase-2 PR's proposal is the
   claim; no new claim file), how overlap is detected (diff open PRs'
   frozen write sets against each other), what counts as a conflict
   (any shared path between two PRs both still open), where a resolution
   is recorded (`docs/issue-<n>/reports/implementation.md`'s existing
   `## Rationale for deviations` section, or a new
   `docs/issue-<n>/reports/conflict-<other-issue>.md` when the resolution
   doesn't fit either subject's own record), and the resolution rule
   (cheapest-to-revert yields, adapted from `agent-coordination`, applied
   by whichever session's write-set overlap is detected later since it is
   the one that can still choose a different path before committing).
2. Write `scripts/check-write-set-conflicts.sh`: reads `files:` frontmatter
   from every proposal under `docs/issue-*/proposals/*.md` whose issue has
   a currently-open PR (via `gh pr list`), computes pairwise path
   intersections across distinct issues, and exits non-zero listing the
   overlapping paths and issue numbers when an intersection exists with no
   matching resolution record on disk.
3. Write `test/check-write-set-conflicts.test.sh`: fixtures two proposal
   files with an overlapping path and no resolution record, runs the
   script against the fixture directory, and asserts non-zero exit and
   that the offending path appears in output; a second fixture with a
   resolution record present asserts exit 0.
4. Cross-reference the script in `docs/handbooks/operations.md` as a
   pre-merge check, one line, pointing at the spec for the full
   methodology.

## Out of scope

- Actually running the checker in CI/as a gate hook (a `PreToolUse`/CI
  wiring decision belongs to whichever role owns gate infrastructure —
  this proposal delivers the spec, the script, and its test, not a new
  gate hook).
- Orchestrator scheduling changes to run more work in parallel (#324).
- Orchestrator-side enforcement of its own procedural obligations (#298).
- Any change to the existing worktree-per-role isolation mechanism itself.
- A live, real-time coordination bus (heartbeats, claims.json) — rejected
  above; this repo's PR state is the liveness signal used instead.

## How you'll know it worked

- `test/check-write-set-conflicts.test.sh` passes: it demonstrably fails
  the run when an unresolved write-set overlap exists between two open
  proposals, and passes when a resolution record is present — this is the
  executable, regression-failing artifact #310 requires.
- `docs/specs/parallel-conflict-methodology.md` exists and a role session
  reading it can name, without inference, what to do the moment it
  detects an overlapping write set with another open PR.

## Reach beyond this issue's own acceptance (per #330)

This phase-1 change writes only new files (the two survey/brief documents
and this proposal) — nothing already on disk is invalidated by phase 1.
Phase 2, once approved, will add a new script and spec but will not modify
any existing gate, hook, or role behavior; it introduces a checker that
does not run automatically anywhere yet (see Out of scope #1), so no
in-flight session's current behavior is invalidated by this issue's
delivery. The one piece of already-recorded state this proposal's
methodology *would* eventually make load-bearing, once wired into a gate
by a future issue: any phase-1 proposal on disk today that never listed an
accurate `files:` write set. This proposal does not audit or correct past
proposals — flagged here as a known limitation, not fixed in scope.
