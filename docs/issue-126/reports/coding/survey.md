---
subject: issue-126
role: coding
phase: 1
---

# Current-state survey — issue-126

## Scout skip record

Skipped. This is an internal protocol/gate fix with no design decision open
against an external product category — the relevant field is the repo's own
contract text and gate code, which this survey covers directly.

## Where approval strings are read/written today

1. **Core protocol text (session-start directive, contract v3 s19)** — not a
   file in this repo (lives in the coding-rulebook plugin outside
   on-the-record). As relayed to role sessions, it already states
   issue-comment-first: PR review Approve for two-account hardening, or an
   issue-level `APPROVE issue-<n>/<role>` comment in single-account mode.
   This is the target canon the issue asks to converge on.

2. **`on-the-record/commands/run.md`** (the orchestrator's `/orchestrate:run`
   relay script, step 6, lines 183-186) — instructs the orchestrator to post
   the approval string to the **PR**, not the issue:
   `gh pr comment <n> --body "APPROVE issue-<n>/<역할>"`. This contradicts
   the issue-primary canon above and is the exact drift the issue's ops-agent
   rulebook incident (issue-24) hit: the role session checked issue comments
   and PR reviews, not PR comments, and found nothing.

3. **`spawn.py::approve_scope()`** (lines 859-914) — a *different* approval
   kind (`APPROVE issue-<n>/scope`, issue #115), not the phase-2-open
   approval this issue is about. It already reads issue comments first, then
   unions in PR comments (`_issue_comments` called on both the issue number
   and the PR number for the front role's branch) with no stated priority.
   Functionally closer to "issue is canonical, PR is a fallback" already,
   but the code doesn't say so — it just merges both lists.

4. **No scripted gate exists** for the phase-2-open `APPROVE issue-<n>/<role>`
   check itself. Each role session performs this check ad hoc via its own
   `gh` calls, guided only by the prose contract description relayed at
   session start. There is no shared library function role sessions call
   (unlike `approve_scope` for the scope-approval kind), so drift in the
   *prose* (run.md) directly becomes drift in *behavior* with nothing to
   catch it.

## Issue-timeline completeness (point 3 of the issue)

`gates/gates.py` has no check requiring a PR body to reference its subject
issue (`#n` or `Closes #n`). Grepped for `Closes #`, `issue_ref`, `#n` —
no matches. `PROTECTED_ROOT_FILES`/`PROTECTED_ROOT_DIRS` (lines 24-29) cover
unrelated protections (secrets, CI config, role definitions), not issue
linkage. This is a genuine gap, not drift — nothing today blocks a PR that
never mentions its issue.

## Write set implied by the issue's four asks

- `on-the-record/commands/run.md` — fix step 6 relay instructions: canonical
  approval comment target is the **issue** (`gh issue comment <issue-n>`),
  PR review Approve stays documented only as the two-account hardened
  alternative path.
- `spawn.py` — `approve_scope()`: no behavior change needed (already
  issue-first-then-PR), but its docstring/comment should say so explicitly
  so future edits don't accidentally invert the priority silently.
- `gates/gates.py` (+ `test_gates.py`) — new gate: every PR opened by a role
  must carry an issue reference in its body (`#<n>` for phase-1 proposal
  PRs, `Closes #<n>` for phase-2 delivery PRs); missing reference blocks.
- `protocol.md` / `protocol.ko.md`, `README.md` / `README.ko.md` — state the
  single canonical approval location plainly, so this repo's own docs match
  what role sessions are told at session start, closing the "contract text
  lives outside this repo" gap as far as this repo's own docs can.

No `.env`, dependency, or schema/migration surface is touched — pure
docs/gate-code change.
