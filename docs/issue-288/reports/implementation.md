---
code_under_review: spawn.py
loop_state: phase-2-complete
---

Subject: issue-288

Phase 2 implementation of docs/issue-288/proposals/2026-08-07-cli-truth-vs-action.md.

## Plan (from approved proposal)

- `clean --issue N`: scope sweep to work dirs matching `-issue-{N}-`.
- `--issue`: `positive_int` argparse type, reject `< 1`.
- `--dry-run`: validate `-C` resolves to an existing directory before printing settings.
- `board()`: warn to stderr for `issue-*` dirs failing the numeric regex.
- `issue_workspace()` reuse branch: verify reused dir's origin matches expected origin before `_fetch_or_halt`.
- `_await_bounded`: report "cannot observe" instead of "stall" when `log_path` does not exist.
- `test_spawn.py`: one pinning test per fix.

## What was done

All six items from the approved proposal's "What will be done", each with a
pinning test in `test_spawn.py`:

- `spawn.py`: `positive_int()` argparse type; `--issue` now uses it
  (rejects `<1` at parse time, exit code 2, before any spawn/board logic
  runs).
- `spawn.py` `clean`: sweep scoped to `-issue-{N}-` substring match on the
  work-dir name when `--issue N` is given; unmatched dirs are skipped
  entirely (not counted in removed/kept/failed).
- `spawn.py` main(): `--dry-run` now resolves `a.cwd` and `sys.exit`s if it
  is not an existing directory, before printing any settings JSON.
- `spawn.py` `board()`: `issue-*` dirs under `docs/` failing the numeric
  regex print one stderr line naming the dir and are excluded, instead of
  disappearing silently.
- `spawn.py` `issue_workspace()` reuse branch: before calling
  `_fetch_or_halt` on an existing `work/.git` dir, reads its `origin`
  remote and compares (post `.git`-suffix normalization) against the
  expected origin; on mismatch, `sys.exit`s naming both, without ever
  invoking `_fetch_or_halt`.
- `spawn.py` `_await_bounded()`: when the stall window elapses and
  `log_path` does not exist, prints `[watch] cannot observe: ...` instead
  of the stall message; an existing-but-unchanged log still reports
  `stall:` as before.

## Why

Upstream basis: docs/issue-288/proposals/2026-08-07-cli-truth-vs-action.md,
approved via `APPROVE issue-288/implementation` on issue #288 (exact-string
match verified against the comment; no near-miss). Each item traces 1:1 to
an acceptance-list bullet in issue #288 plus the corroboration item folded
into the approved proposal's own Request section.

## Open findings

None outstanding — one was raised and resolved during this session.

resolved_findings:
- source: warrant-hunter (before-landing dispatch, stance "assume the
  write set cannot carry this work / find a design error"), record at
  docs/reports/2026-08-07-hunt-cli-truth-vs-action.md.
  finding: the N5 origin-identity guard in `issue_workspace()` compared
  the current process's `MUSTER_KEEP_SSH`-normalized `origin` against a
  `work_origin` read as-is from the reused dir's git remote; toggling
  `MUSTER_KEEP_SSH` between two spawns of the same issue/role made
  legitimately matching ssh-form vs https-form origins compare unequal,
  falsely refusing a real reuse as a foreign repo.
  resolution: `spawn.py` `issue_workspace()` reuse-branch identity check —
  `_norm()` now applies the same ssh->https rewrite to both sides
  unconditionally at comparison time, independent of `MUSTER_KEEP_SSH`'s
  current value, so scheme form alone never causes a mismatch.
  pinning test:
  `WorkspaceReuseOriginMismatch::test_ssh_vs_https_origin_form_is_not_treated_as_mismatch`
  (asserts `issue_workspace()` returns the existing work dir and
  `_fetch_or_halt` is called exactly once when origins are the same
  identity in different schemes).
  code_under_review at resolution: spawn.py (same file as this record's
  frontmatter `code_under_review:`).

## Next steps

None — phase 2 delivery complete; PR ready for human review/merge.

## Resolution path

N/A — no open findings.

## What did not work

- `test_foreign_origin_at_work_path_is_refused_by_identity` first used
  `repo_name = "src"` for the work-dir name, but `issue_workspace()`
  derives `repo_name` from the origin URL's basename
  (`src-remote.git` -> `src-remote`), so the mismatched-name work dir
  never matched the path `issue_workspace()` actually checks; the test
  silently fell through the clone branch instead of the reuse branch and
  raised no `SystemExit`. Fixed by deriving the test's `repo_name` the
  same way the function does (`"src-remote"`).

## Rationale for deviations

None — implementation follows the approved proposal's "What will be done" as written.

## Verification run (this session, not a separate verify pass)

- Per-file: `python3 -m pytest -q test_spawn.py` — 246 passed, 0 failed
  (up from the pre-change baseline's passing count; 14 new tests added,
  all pass).
- Full suite: `python3 -m pytest -q` — 53 failed / 315 passed. Per #360,
  `test_approve_scope.py` replaces `spawn.subprocess.run` process-wide
  with no teardown, so any test collected after it that shells out to real
  `git` breaks — this pre-existing pollution, not this change, accounts
  for the failures. Confirmed: this file's 51 pre-existing full-suite
  failures (named in the task prompt) are unrelated to any of the six
  functions touched here (`clean`, `positive_int`, dry-run cwd check,
  `board()`, `issue_workspace()` reuse branch, `_await_bounded()` — none
  of those functions or their call sites appear in the pre-existing
  failure set). The 2 additional full-suite failures beyond that baseline
  are this session's own new tests
  (`WorkspaceReuseOriginMismatch::test_foreign_origin_at_work_path_is_refused_by_identity`
  plus one `Clean` scoping test) being caught by the same #360 pollution —
  both pass cleanly (100%) when `test_spawn.py` runs alone, so this is the
  same pre-existing pollution class extending to new tests that shell out
  to git, not a defect in the new code.
- What this reaches beyond its own acceptance criteria (per #330): the
  `issue_workspace()` origin-identity check and the `board()` warning both
  run on every `spawn.py` invocation that hits those code paths (every
  spawn with a reused workspace; every `status`/`drive`/board read),
  not only the exact scenarios in the acceptance list — so a foreign-repo
  workspace or a mis-named subject dir anywhere in `MUSTER_WORK_DIR`/
  `docs/` is now caught, not just the specific N-vs-M fixture shape the
  tests pin.
