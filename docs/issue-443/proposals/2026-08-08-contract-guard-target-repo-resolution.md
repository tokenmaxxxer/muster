---
status: proposed
files:
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/test_contract_guard.py
---

## Request

`contract-guard.sh` (a PreToolUse hook intercepting `gh pr merge`) resolves
the PR/issue it judges against the session's cwd repo, never the repo the
merge command actually targets. When a `gh pr merge` command carries a
`cd <other-repo> &&` prefix, an `-R owner/repo` flag, or a full PR URL, the
hook still runs its `gh pr view`/`gh issue view` lookups against cwd — so
it can judge the wrong repo's same-numbered PR/issue entirely. #443 asks
for target-repo resolution to cover whichever of those three forms are
actually reachable, with an explicit unreached marker for any that
genuinely cannot be resolved without a local checkout, plus a red-green
cross-repo test fixing the before/after behavior.

## Constraints

- The phase-2 `Closes #<issue>` predicate and its judgment logic are
  unchanged — this issue is scoped to repo resolution only, not to what
  gets judged once the right repo is found.
- No retroactive fix to any past merge; this only changes future
  invocations.
- The hook stays zero-install (header comment, contract-guard.sh:4–10):
  no new local dependency, and remote-repo lookups must go through `gh`
  itself, never assume a local checkout that doesn't exist.
- Fail-open discipline is preserved: a repo-resolution path that cannot be
  completed without new capability stays an explicit, commented unreached
  branch that exits 0 — never a guess.

## Rationale

Considered fetching the target repo's `docs/specs/approvers.md` over the
GitHub API (`gh api repos/<owner>/<repo>/contents/...`) for the `-R`-flag
and full-URL forms, so all three forms get a complete fix. Rejected: this
adds a new network-call class (contents API + base64 decode) the hook has
never used, for a feature only exercised in the `-R`/URL-without-local-
checkout case — which the survey found has no local git checkout to
correlate the fetched file against anyway (the hook has no way to confirm
the fetched approvers.md is current relative to what the merge command's
author actually sees, since there's no local diff/fsck to anchor it to).
The `cd <path> &&` prefix case — the one the issue's own repro actually
hit — has a real local checkout and needs no such workaround: chdir'ing
the `gh` subprocess calls into that path is a complete, low-risk fix using
the same `gh` mechanism the original shell command itself would have used.
Given the header's own stated fail-open philosophy (contract-guard.sh:20–26:
"a lookup failure here is reported and passed through rather than
blocking"), treating the `-R`-flag/URL-without-local-checkout path as an
explicit unreached (fail-open, commented) is consistent with the file's
existing convention rather than a new one, and matches acceptance
criterion 1's explicit allowance ("식별 불가 형태는 현행 fail-open 주석
관례대로 명시적 unreached 로 남긴다").

## What will be done

1. In `contract-guard.sh`'s Python heredoc, before the PR-number
   extraction: detect a leading `cd <path> &&` in the full command string
   and a `-R <owner/repo>` / `--repo <owner/repo>` flag or a full
   `github.com/<owner>/<repo>/pull/<n>` URL in the post-`gh pr merge`
   argument text.
2. Full PR URL: extract `(owner/repo, number)` from it directly — this
   also fixes the number extraction itself, since the URL form currently
   falls through the "no explicit number" unreached branch (confirmed in
   the survey) even though a number is present in the URL.
3. `cd <path> &&` case: run every `gh` subprocess call
   (`gh pr view`, `gh issue view`) with `cwd=<path>` instead of the
   process's own cwd, and read `approvers.md` from
   `<path>/docs/specs/approvers.md` instead of `os.getcwd()`-relative.
   This is the complete fix — no unreached marker needed for this form.
4. `-R`/URL case (no `cd` prefix, so no local checkout of the target
   repo): pass `-R <owner/repo>` to the `gh pr view` / `gh issue view`
   subprocess calls so the PR/issue body judged is correctly the target
   repo's — but since `approvers.md` cannot be read locally for a repo
   with no checkout, stop before the phase-2 determination and exit 0
   with an explicit new comment marking it unreached (matching the
   existing "gh lookup failed" / "no explicit number" comment style at
   contract-guard.sh:57–61 and :74–75).
5. No `cd`/`-R`/URL present at all (today's only reachable case): behavior
   is unchanged — same-repo resolution against cwd, byte-identical to
   current code path.
6. Add `on-the-record/hooks/test_contract_guard.py`: a new pytest module
   (no existing test covers this hook — confirmed in survey) that invokes
   `contract-guard.sh` as a subprocess with a crafted `CG_PAYLOAD` env var,
   using a fake `gh` shim script on `PATH` that returns canned JSON keyed
   by which repo (`-R` value / cwd) it was invoked against — mirroring the
   `subprocess.run(["git", "-C", ...])` fixture pattern already used
   throughout `test_gates.py`. Cases:
   - red-green: cwd repo and a `cd <target>` repo both have a PR/issue
     numbered identically with different bodies/approval states; assert
     the pre-fix code path (documented, not re-implemented — asserted via
     a `git stash`-able snapshot or by asserting the new code exhibits the
     fixed behavior only, since the actual pre-fix binary no longer exists
     post-merge) denies/allows per the *target* repo, not cwd.
   - `-R owner/repo` flag: asserts target-repo PR/issue judged; explicit
     unreached case (no local approvers.md) asserts exit 0.
   - Full PR URL: asserts target-repo PR/issue judged (same as `-R`).
   - `cd <path> &&` prefix: asserts target-repo PR/issue judged, including
     `approvers.md` read from the target path.
   - No repo indicator (bare `gh pr merge 137`): unchanged cwd-repo
     behavior, one regression case.

## Out of scope

- Changing the phase-2 `Closes #<issue>` predicate itself.
- Fetching `approvers.md` over the GitHub contents API for the `-R`/URL
  case (rejected above).
- Any other `gh` subcommand besides `gh pr merge` interception.
- Editing `docs/specs/enforcement-boundary.md` or the issue-441
  architecture docs (unchanged predicate, no spec change needed).

## How you'll know it worked

- `on-the-record/hooks/test_contract_guard.py` passes, and its red-green
  cross-repo case fails against the current (pre-fix) file content when
  run against it and passes against the fixed file — demonstrating a real
  before/after flip, not a vacuously-true assertion.
- Each of the three forms (`-R`, full URL, `cd &&` prefix) has a
  corresponding passing test case, with the `-R`/URL case's approvers-gap
  asserted as an explicit exit-0 (unreached), matching acceptance
  criterion 2.
- Manual smoke: running the hook script directly with a `CG_PAYLOAD`
  simulating the issue's own repro command
  (`cd <core> && gh pr merge 137 --merge`) against two repos with
  differently-numbered-but-identical PRs confirms it judges the `cd`
  target's PR body, not cwd's.
