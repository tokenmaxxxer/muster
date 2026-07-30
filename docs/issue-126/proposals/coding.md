---
subject: issue-126
role: coding
phase: 1
---

# Build proposal — issue-126

files:
- `on-the-record/commands/run.md`
- `spawn.py`
- `gates/gates.py`
- `test_gates.py`
- `protocol.md`, `protocol.ko.md`
- `README.md`, `README.ko.md`

## Request (paraphrased intent)

Same `APPROVE issue-<n>/<role>` string, but sessions look for it in
different places (issue comment vs PR comment vs PR review), and that drift
already caused a missed approval (ops-agent-rulebook issue-24). Fix: (1)
make the issue comment the one canonical approval location, PR review
Approve documented only as the two-account hardened alternative; (2) align
this repo's own relay instructions and docs to that canon; (3) require
every PR opened in the flow (proposal, delivery, respawn) to reference its
issue in the body, so the issue timeline shows the full decision + delivery
history.

## Constraints

- Approval semantics stay unchanged (contract v3 s19: an actor cannot mint
  its own approval, approvers.md allowlist, exact-string match). This is a
  *location* fix, not a new approval mechanism.
- `spawn.py::approve_scope()` already checks issue comments first — no
  functional change there, only a clarifying comment so the priority is
  explicit and future edits can't silently flip it.
- No PROTECTED_ROOT_FILES bypass: `protocol.md`/`protocol.ko.md` edits go
  through the normal gate path like any other change.

## What will be done

1. `on-the-record/commands/run.md` step 6 (lines ~183-186): change the
   relay instruction from `gh pr comment <n> --body "APPROVE issue-<n>/<역할>"`
   to `gh issue comment <issue-n> --body "APPROVE issue-<n>/<역할>"`, with a
   one-line note that PR review Approve is the alternative only under
   account-separated (two-account) hardening.
2. `spawn.py`: add a short comment on `approve_scope()` stating issue
   comments are canonical and the PR-comment union is a fallback, matching
   the fixed relay instruction — no logic change.
3. `gates/gates.py`: new gate function checking the PR body (via
   `gh pr view --json body` or the diff context already available to the
   gate) contains `#<issue-n>` — `Closes #<issue-n>` required specifically
   for phase-2 delivery PRs (detected the same way existing gates detect
   phase, e.g. via the record's `loop_state`), plain `#<issue-n>` sufficient
   for phase-1 proposal PRs. Missing reference fails closed with a message
   naming the expected string. Add corresponding cases to `test_gates.py`.
4. `protocol.md`/`protocol.ko.md` and `README.md`/`README.ko.md`: add or
   correct a short passage naming the issue comment as the single canonical
   approval-signal location, PR review Approve as the two-account hardened
   alternative — matching what role sessions are already told at session
   start, so this repo's own docs stop being the odd one out.

## Out of scope

- Editing the contract v3 s19 text itself (lives in the coding-rulebook
  plugin, outside this repo) — only this repo's relay script and docs are
  touched.
- Retrofitting historical PRs that lack an issue reference.
- Any change to the scope-approval (`APPROVE issue-<n>/scope`) mechanism
  beyond the clarifying comment.

## How it'll be known to work

- `run.md`'s step 6 text, read cold, sends the orchestrator to `gh issue
  comment`, not `gh pr comment`, for the default (single-account) case.
- `test_gates.py` gains passing cases (PR body has `#126`/`Closes #126`)
  and failing cases (body has neither) exercising the new gate function,
  run via `python3 -m pytest test_gates.py` (or however the suite is
  invoked) and shown green before the phase-2 PR.
- `protocol.md`/`protocol.ko.md` and `README.md`/`README.ko.md` state the
  same canonical location in matching terms across the English/Korean
  pairs.
