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

## Re-verification against current main (2026-08-07)

Per #390 a green run against the branch's original base attests to a
state that no longer exists once ~13 PRs have landed on `main` since.
Rebased `issue-289/implementation` onto `origin/main`
(`0f3151a`, PR #423 merged) and re-ran the suite from that base:

- `python3 -m pytest -q --ignore=gates`: **407 passed** (14.41s) — the
  `gates/` subtree is excluded per instruction (reported module-name
  collision, #398); on this run `gates/` in fact collected (see below),
  so that collision was not reproduced here — reported as observed,
  not assumed still-open.
- `python3 -m pytest -q gates` (informational, outside the requested
  scope): 68 passed, 1 pre-existing failure
  (`test_closes_gate_ci.py::t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`,
  a fixture for issue #304 missing an `## Acceptance` section) —
  unrelated to this issue's write set (`spawn.py`, `test_spawn.py`,
  `protocol.md`, `protocol.ko.md`); left untouched, out of scope.
- `python3 test_spawn.py` (full unittest suite, superset check): 235
  passed, `OK`.

## Acceptance-gate blocker (issue #289, addressed to the issue author)

`gates/acceptance_gate.py` (landed today via #310) now blocks this PR:
issue #289's own `## Acceptance` section is prose only — three bullets
naming no executable artifact. Rewriting the GitHub issue body is
correctly out of reach for a role session: `gh issue edit` is refused
by `gh-guard.sh` (contract v3 s9 — issues are the user's requirement
backlog, user-authored only). The following rewrite is proposed for the
issue author to apply directly; it was validated locally against
`acceptance_gate.check_issue_body()` before being proposed here (empty
violation list):

```
## Acceptance
- check: python3 -m pytest -q test_spawn.py -k test_fresh_workspace_excludes_dotfile_set — a fresh `issue_workspace()` clone excludes the full home-dotfile set via `.git/info/exclude`, so `git add -A`/`git status` cannot surface them.
- check: python3 -m pytest -q test_spawn.py -k test_git_lock_masquerade_is_classified_as_sandbox_refusal — the lock-masquerade wording is classified as a sandbox refusal, not left unclassified/silent, so the denial is legible to the session and to `on-the-record` reading the log.
- unverifiable: whether a session actually refrains from deleting a lock file is a behavioral/procedural outcome, not something a repo-local test can observe. The mitigation is the `protocol.md`/`protocol.ko.md` §4 diagnose-don't-delete instruction, backed by the check above making the denial legible in the first place; compliance with that instruction happens in a session this repo cannot execute or inspect.
```

Both named checks were run and pass on this branch (see above and
`closed_checks` below). Until the issue author applies this text (or an
equivalent), `acceptance_gate.py` will keep blocking this PR — that
block is correct per its own design and is not something this role
session may bypass or route around.

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
- check: re-verification against current `main` after rebase (#390) —
  `python3 -m pytest -q --ignore=gates` 407 passed,
  `python3 test_spawn.py` 235 passed OK — code_sha
  fa496e71eed2dd23e2b5a774a868eeccdd8d77db (rebased onto
  `origin/main@0f3151a`).
- check: second re-verification (2026-08-07, ~60 more PRs landed on
  `main` since the previous rebase, up to #429) — rebased onto
  `origin/main@23d90ea`. `python3 -m pytest -q --ignore=gates`: 407
  passed (19.18s). `python3 -m pytest -q gates` (informational): 68
  passed, the same pre-existing unrelated failure as before
  (`t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`,
  issue #304's fixture missing `## Acceptance`) — untouched, out of
  this issue's write set. `python3 gates/acceptance_gate.py 289`: still
  exits 1 (issue #289's own `## Acceptance` section is still prose-only
  on GitHub) — expected, since applying the rewrite below requires the
  issue author; a role session's `gh issue edit 289` is refused by
  `gh-guard.sh` (contract v3 s9). code_sha ab7b132 (this commit).

## Acceptance-gate rewrite, validated (2026-08-07 re-check)

The rewrite proposed in the previous section was re-validated against
`gates.acceptance_gate.check_issue_body()` on this run: empty violation
list (`[]`). It is unchanged from what a prior pass proposed and still
matches the delivered artifacts — `test_spawn.py::test_fresh_workspace_excludes_dotfile_set`
and `test_spawn.py::test_git_lock_masquerade_is_classified_as_sandbox_refusal`
both still exist and still pass (see `python3 -m pytest -q --ignore=gates`
above). Still blocked on the issue author applying it — this role
session cannot edit the issue itself.

## Third re-verification (2026-08-07, rebase onto main@2395573, full suite no --ignore)

Roughly 80 more PRs landed on `main` today; rebased
`issue-289/implementation` onto `origin/main` again (rebase was
conflict-free — `git rebase origin/main` applied cleanly, no manual
resolution needed). Re-ran acceptance evidence against this rebased
tree, not the original base:

- `python3 -m pytest -q` (full suite, **no** `--ignore`, per current
  instruction — `gates/` collision from #398 was not observed on this
  run): **508 passed** (15.76s) — matches `main`'s reported 508.
- `python3 test_spawn.py` (full unittest suite): 263 passed, `OK`.
- `python3 -m pytest -q test_spec_index.py -k t_baseline_repo_passes`:
  1 passed — this is the third acceptance-check artifact now named in
  the issue body (spec-index hash), not present in earlier re-checks
  above; it passes on this branch.

The GitHub issue body was found rewritten (per the orchestrator, to
name executable artifacts under #310's closes-gate). Read the current
body directly rather than relying on memory of the earlier prose
version. Its `## Acceptance` now names:

- `test_spawn.py` (dotfile-exclusion criterion)
- `test_spawn.py` (sandbox-denial-legibility criterion)
- `test_spec_index.py::t_baseline_repo_passes` (spec-index hash
  criterion)
- one `unverifiable:` line (no session needs to delete a lock file)

All three named executable artifacts exist in this branch and pass, as
run above — `test_spawn.py::test_fresh_workspace_excludes_dotfile_set`,
`test_spawn.py::test_git_lock_masquerade_is_classified_as_sandbox_refusal`,
`test_spec_index.py::t_baseline_repo_passes`. No mismatch found between
the artifacts the issue names and what this branch actually produces.

Re-ran `gates.acceptance_gate.check_issue_body(289, <current body>)`
directly against the live issue body fetched via `gh issue view 289`:
returned `[]` (no violations) — the acceptance gate that blocked
earlier re-checks now clears, because the issue body itself was
rewritten to name these artifacts, not because anything on this branch
changed. code_sha 6dc8768 (this commit, rebased onto
`origin/main@2395573`).
