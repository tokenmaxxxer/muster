---
subject: issue-126
role: coding
phase: 2
loop_state: landed
code_under_review: e78afcd
---

# Coding record — issue-126

Approved via `APPROVE issue-126/coding` (issue comment, single-account mode).

## What was done

1. `on-the-record/commands/run.md` step 6: relay instruction changed from
   `gh pr comment <n>` to `gh issue comment <issue-n>` for scope/proposal
   approval, with the two-account PR-review-Approve alternative kept as a
   documented fallback only.
2. `spawn.py::approve_scope()`: added a comment above the issue-comment-first
   read stating the priority explicitly (no logic change — it already read
   issue comments before PR comments).
3. `gates/pr_reference.py` (new): `check_body(issue, body, phase)` — pure,
   network-free function deciding pass/block from a PR body string; `check()`
   wraps it with a `gh pr view` fetch. Phase-1 (proposal) PRs require a
   plain `#<issue>` reference; phase-2 (delivery) PRs require
   `Closes/Fixes/Resolves #<issue>`. Given no existing gate entry point
   threads a PR number (both `gates.check()` and `ci.py`'s `check(repo)` are
   local-checkout-only — confirmed by the phase-1 warrant-hunter finding),
   this is its own entry point, wired into `gates/ci.py` as optional
   `--pr <n> --issue <n> [--phase phase1|phase2]` flags — skipped when not
   given, so callers without PR context are unaffected.
4. `test_gates.py`: 4 new cases against `pr_reference.check_body` — phase-1
   pass/fail, wrong-issue-number fail, phase-2 Closes-required pass/fail.
5. `protocol.md`/`protocol.ko.md`, `README.md`/`README.ko.md`: each gained a
   short passage naming the issue comment as canonical, PR review Approve as
   the two-account alternative — matching text across the four files.

## Why

Contract v3 s19's `APPROVE issue-<n>/<role>` string was read from different
locations across surfaces (this repo's own relay text told orchestrators to
post it as a PR comment, while the core protocol and role sessions already
treat the issue comment as canonical) — that drift already caused a missed
approval elsewhere (ops-agent-rulebook issue-24, per the phase-1 survey).
Unifying on one canonical location, and gating that every PR names its
issue, closes both the drift and the traceability gap it left.

## Upstream basis

`docs/issue-126/proposals/coding.md` (phase-1 build proposal, items 1-4),
approved by issue comment `APPROVE issue-126/coding`; design constraint for
item 3 sourced from the phase-1 warrant-hunter finding recorded in
`docs/reports/2026-07-30-hunt-issue-126-coding.md`.

## How it was confirmed

`python3 test_gates.py` run once: all `t_pr_reference_*` cases pass (4/4).
One pre-existing failure (`t_repo_local_claude_config_stops_the_spawn`,
`OSError: Read-only file system` writing outside the repo tree) reproduces
identically on the pre-change commit (`git stash` + rerun) — unrelated to
this change, sandbox environment artifact.

## What did not work

- Initially considered folding the PR-reference check into `gates.py`'s
  `ALL`/`check(names, d, cfg)` dispatch table to match the existing gate
  shape. Reverted: that signature is `(Path, dict) -> list[str]` with no PR
  number, and every other gate in it is local-diff-only by design (see
  `ci.py`'s docstring on why spec-based checks stay out of the CI entry
  point) — forcing a PR number through it would break that invariant for
  every other gate function sharing the table.

## Out of scope (per proposal, unchanged)

- Contract v3 s19 text itself (lives outside this repo).
- Retrofitting historical PRs lacking an issue reference.
- Any change to `APPROVE issue-<n>/scope` semantics beyond the clarifying
  comment.

## Open findings

None outstanding. No blocking finding from verify/qa is pending against this
record as of writing.
