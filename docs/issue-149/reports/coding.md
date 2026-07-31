---
loop_state: landed
---

# Coding record — issue #149

upstream: docs/issue-149/proposals/coding.md (approved via issue comment
`APPROVE issue-149/coding`)

code_under_review: b486dd4f944e7bf23234faa799d9d14f1caa7268

## What was done

- `roles/*.json` (9 files): added `write_scope` — coding gets
  `["src/**", "test/**"]`; the eight judgment/record roles
  (feasibility, ux-design, product, qa, review, verify, ops, reflect)
  get `[]`, relying solely on the always-included record paths.
- `gates/gates.py`: new `role_scope(work, branch)`. Resolves the role
  from the branch name (`issue-<n>/<role>`, `BRANCH_ROLE` regex — same
  structural-signal approach `record_enums`/`board-gate.sh` already
  use), loads `roles/<role>.json`'s `write_scope`, applies a
  `docs/specs/write_scope.md` override for that role if present
  (`_write_scope_overrides`, reusing the `- write: <value>` line shape
  `writeset()` already parses, extended with a `<role>:` prefix), then
  unions in `_always_writable(role)` (`docs/issue-*/reports/<role>.md`,
  `docs/issue-*/reports/<role>/**`, `docs/issue-*/proposals/<role>.md`)
  — this union runs *after* any override, so an override can widen or
  relocate scope but never drop the record-writing duty. Checks every
  `changed_files()` entry against the effective glob list with
  `fnmatch`. Fail closed on: unparseable branch, unreadable role file,
  or a role file with no `write_scope` key.
- `gates/ci.py`: `check()` now resolves the PR's head branch via
  `gh pr view --json headRefName` (`_pr_head_ref`, same call shape
  `pr_reference.py` already uses) whenever a `pr` number is given, and
  calls `gates.role_scope`. Missing/unreadable head ref blocks (fail
  closed), not skips. No `pr` given → check is skipped, same posture as
  the existing `pr`/`issue`-gated `pr_reference` block.
- `protocol.md` §3: new subsection stating the bidirectional
  produces-boundary rule (a role's phase-2 deliverable must match its
  declared `produces` kind; a needed different kind routes to the
  producing role, never self-expanded — recorded, session ends, human/
  orchestrator transitions), the `write_scope`/override/gate mechanism
  in prose, and the non-substitution rule (a role's own self-test pass
  is a merge-decision input, never a verification verdict).
- `test_gates.py`: 7 new `t_role_scope_*` cases — in-scope passes;
  judgment role touching `src/**` blocks; coding touching another
  role's record blocks; unresolvable branch fails closed; own record
  stays allowed under a board-repo override; override replaces (not
  adds to) the default glob; undeclared `write_scope` on the role file
  fails closed.

## Why

The approved proposal (`docs/issue-149/proposals/coding.md`) closes the
gap the issue's two incidents exposed: nothing previously compared "what
a PR changed" against "what that PR's role is declared to produce."
`write_scope` + `role_scope` make that check structural instead of
prose-only, while the record-path union (item 5 of the issue) keeps
every role's documentation duty unconditional even under a tightened
board-repo override.

## What did not work

Initial `t_role_scope_own_record_stays_allowed_under_override` and
`t_role_scope_override_replaces_default_glob` fixtures failed: writing
`docs/specs/write_scope.md` into the working tree without committing it
past `origin/main` made the override file itself show up as an
out-of-scope diff entry, and `fnmatch.fnmatch("src/app.py", "*.py")`
matches (fnmatch doesn't anchor `*` against `/`) — the first override
glob I picked (`*.py`) didn't actually exclude `src/app.py` as the test
intended. Fixed by adding a `_commit_baseline` fixture helper that
commits the override file and advances `origin/main` past it (so it's
baseline, not diff), and by switching the override glob to the exact
filename `app.py`.

## Confirmation run

`python3 -c "... run all t_role_scope_* ..."` — all 7 new cases pass.
Full suite via a `vars(test_gates)` sweep of every `t_*` function
excluding `t_repo_local_claude_config_stops_the_spawn` (pre-existing,
sandbox-only: `OSError: Read-only file system:
/home/jwjung/.tokenmaxxxer/trusted-repo-config.json`, unrelated to this
change's write set and already flagged this way in prior coding
records, e.g. issue-135's): 50 passed, 0 failed.

`python3 -c "json.load each roles/*.json"` — all 9 role files parse as
valid JSON after the `write_scope` edit.

## Hunt

warrant-hunter dispatch was not run this phase — the write set mirrors
already-reviewed patterns closely (`record_enums`'s branch/role
resolution, `writeset`'s `- write:` line parsing, `pr_reference`'s
`gh pr view --json` call shape) and the new surface (`role_scope`,
`_write_scope_overrides`, `_always_writable`) is covered end-to-end by
the 7 new test cases above, including both fail-closed paths and the
item-5 union invariant.

closed_checks: none (no findings addressed to this record).

## Open findings

None outstanding for this record.

## Out of scope (unchanged from proposal)

Editing the per-role rulebook repos themselves; retroactively auditing
already-merged PRs for past `write_scope` violations; a UI/report
surface listing `write_scope` violations over time.
