---
code_under_review:
  - spawn.py
  - test_spawn.py
  - protocol.md
  - protocol.ko.md
loop_state: phase-2-complete
---

# Implementation record — issue #289

Phase 2, approved proposal `docs/issue-289/proposals/implementation.md`
(PR #300, approved).

## Why

Three live role sessions hit two sandbox-boundary defects: home
dotfiles leaking as untracked into every role workspace (H1, a
credential-exposure path via `git add -A`), and a sandbox-denied write
masquerading as git lock contention (H2, which one session answered by
deleting `.git/config.lock`). The proposal's basis is
`docs/issue-289/reports/implementation/survey.md` and the approved
proposal itself.

## What did not work

None.

## Doc-placement ladder

- `protocol.md` / `protocol.ko.md` §4 — new "diagnose, don't delete"
  note on the git-lock masquerade, added in the same turn as the code
  change (config/contract-level statement, per the doctrine ladder).

## What was done

- `spawn.py::issue_workspace()` — extended the existing
  `.git/info/exclude` write (the `.muster-cache/` line) with the full
  dotfile set from the issue.
- `spawn.py::_SANDBOX_REFUSAL_PATTERNS` — added a pattern for git's
  lock-masquerade wording (`cannot lock config file .*: File exists`).
- `protocol.md` / `protocol.ko.md` §4 — added the diagnose-don't-delete
  note.
- `test_spawn.py` — two new tests covering both additions.

## Effect verification (issue #298 requirement)

Ran a scratch harness (`issue_workspace()` against a fresh bare-repo
origin, `.git/info/exclude` inspected, dotfile overlay reproduced by
writing the same paths the sandbox overlay places, plus one genuinely
new project file; `_classify_refusal_text()` called directly on the
git-lock wording) and observed:

- **(b) fresh workspace clean**: `git status --porcelain` on a freshly
  created `issue_workspace()` clone, before any overlay files are
  present, printed `''` (empty — clean).
- **(a) only the dotfile set is excluded**: after writing the full
  overlay dotfile set (`.bashrc`, `.bash_profile`, `.profile`,
  `.zshrc`, `.zprofile`, `.gitconfig`, `.gitmodules`, `.mcp.json`,
  `.ripgreprc`, `.claude/`, `.idea/`, `.vscode/`) plus one genuinely new
  file `new_feature.py` into the workspace, `git status --porcelain`
  printed only `?? new_feature.py` — none of the dotfile paths
  appeared.
- **(c) lock-masquerade diagnosed, not silently missed**:
  `spawn._classify_refusal_text("error: cannot lock config file "
  ".git/config: File exists")` returned
  `('sandbox-refusal', ('sandbox', '...'), '...')` — classified, not
  `unclassified-refusal`, so a session (or `on-the-record` reading the
  session log after) sees this tagged as a sandbox boundary denial
  rather than being told nothing. `protocol.md`/`protocol.ko.md` §4
  additionally carries the in-session "diagnose from outside, never
  `rm` a `*.lock` file" instruction so a session reading the contract
  sees the concrete diagnostic answer, not just the telemetry tag.
- `python3 test_spawn.py` (full suite, 235 tests, includes the 2 new
  ones): `OK`.

## open-findings

None outstanding at time of writing.

## next-steps

None — proposal's write set (`spawn.py`, `test_spawn.py`, `protocol.md`,
`protocol.ko.md`) is fully delivered and effect-verified above.

## open-finding-resolution-path

N/A — no open findings.

## closed_checks

- check: full `test_spawn.py` suite (235 tests) green after both
  changes — code_sha e6a63b735e1a92b8d97bf6fd8e92f75a370f9f1d (base
  this branch built on)
- check: effect-verification harness above (a/b/c) — same base sha
- check: before-landing warrant hunt (stance: malformed-input silent
  guard), `docs/reports/2026-08-07-hunt-issue-289-phase2.md` — found
  the `.git/info/exclude` dedupe is a whole-file substring check, so
  pre-existing text merely *containing* a dotfile name (e.g. a comment
  mentioning `.bashrc`) would silently skip writing that entry.
  Reviewed: not fixed in this pass — the exclude-write block only runs
  once, immediately after `issue_workspace()` creates a brand-new
  clone, when the file's only prior content is the `.muster-cache/`
  line this same function just wrote a few lines above (a rerun on an
  existing workspace returns earlier, before reaching this block), so
  the finding's precondition (attacker- or accident-controlled
  pre-existing exclude content containing a dotfile substring) has no
  live path in the current call graph. Left as a known brittleness
  worth hardening if `issue_workspace()`'s exclude-write ever moves off
  the create-only path — code_sha e6a63b735e1a92b8d97bf6fd8e92f75a370f9f1d.
