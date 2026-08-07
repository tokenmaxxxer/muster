---
status: proposed
files:
  - gates/ci.py
  - gates/test_closes_gate_ci.py
  - .github/workflows/plan-aware-closes-gate.yml
  - docs/issue-369/decisions/record-evidence-via-gh-api-contents.md
  - docs/issue-369/reports/implementation.md
---

Pure bugfix (scout-directive skip condition 1) — see
`docs/issue-369/reports/implementation/survey.md` for the current-state
survey this proposal is drafted from.

## Request

`gates/ci.py::_phase2_record_evidence` reads the phase-2 record off the
local working tree, but the gate workflow always checks out `main` — so
the record, which exists only on the PR branch, can never be found in CI.
Fix the lookup to read the record from the PR's own ref via `gh api`
(data only, no code execution) instead of the local filesystem, re-run the
six affected PRs' `closes-gate` check in CI and report each result
individually, and audit what else in `--closes-only` mode now depends on
the working tree versus reading only metadata as the workflow's comment
claims.

## Constraints

- Must not weaken the trust boundary the `main`-pinned checkout exists
  for: PR code must never be checked out or executed by the gate.
- Existing local-filesystem unit tests for `_phase2_record_evidence`
  (`gates/test_closes_gate_ci.py:413-444`) must keep working — they test
  real, still-needed behavior (frontmatter parsing), just not the whole
  path end to end against a PR ref.
- Acceptance is binding: six PRs (#337 #340 #343 #350 #352 #353) verified
  green in CI, not locally, no PR body edited; a test that fails if a
  filesystem read of PR-branch content is reintroduced; the item-3 audit
  as a list.

## Rationale

Two ways to get the record's content without checking out the PR branch
were considered:

1. **`gh api repos/<slug>/contents/<path>?ref=<branch>`** (chosen) — a
   single authenticated GET that returns the file's content (base64) as
   JSON data at a given ref. No PR code is fetched into a working tree, no
   script from the PR is imported or run. This is the same trust shape
   `gates/ci.py` already relies on elsewhere (`_pr_commit_messages` at
   `gates/ci.py:85-113` calls `gh api repos/<slug>/pulls/<pr>/commits` the
   same way) — reusing an established, already-reviewed pattern rather
   than inventing a new one.
2. **Fetch a tarball/checkout of the PR ref in a scratch directory,
   read the file from disk** (rejected) — this is exactly the shape the
   workflow's `main`-pinned checkout was written to prevent (workflow
   comment, `.yml:17-20`): once the PR's tree is materialized anywhere in
   the gate's execution, a PR can put arbitrary content at
   `docs/issue-<n>/reports/<role>.md` *and* arbitrary code elsewhere in
   its own tree that the gate might be induced to import or execute later
   (even if this specific read doesn't exec it, the pattern normalizes
   "check out PR content into the gate's process" for future changes).
   Rejected because it reintroduces the exact risk the design comment
   warns about, for no benefit over the contents API — the contents API
   gets the same data with a strictly narrower capability.

## What will be done

- `_phase2_record_evidence` gains a `pr: int` parameter (available at its
  only call site, `gates/ci.py:319-320`, since `check()` already has
  `pr`). It still resolves `role` from the branch name (pure, unchanged),
  then fetches the record's raw text via
  `gh api repos/<slug>/contents/docs/issue-<issue>/reports/<role>.md?ref=<branch>`
  (base64-decoded), instead of `Path.exists()` / `Path.read_text()`. A
  missing file (404) or API failure returns `False`, same as today's
  "file doesn't exist" branch.
- The frontmatter-parsing step (`gates.record_frontmatter`) is unchanged
  and kept callable on plain text, so the four existing unit tests are
  updated only to inject fetched text instead of writing files into a
  `repo` fixture — they keep testing the same logic (does a fetched text
  blob with/without `loop_state` parse right), now decoupled from local
  file I/O to match what production actually does.
- One new unit test pins that `_phase2_record_evidence` does not call
  `Path.exists`/`Path.read_text`/any local-filesystem read for the
  record path — it patches the `gh api` call to return controlled JSON
  and asserts no filesystem access happens for that path, so a regression
  back to local-tree reads fails this test (acceptance item 2's pinning
  test).
- A short decision record,
  `docs/issue-369/decisions/record-evidence-via-gh-api-contents.md`,
  states explicitly why a `gh api` content read does not check out or
  execute PR code and so preserves the workflow's trust boundary (the
  confirmation #369 asks for, not just an assumption).
- The workflow comment's claim ("closes-only 모드는 ... 메타데이터만
  읽으므로") is corrected in `.github/workflows/plan-aware-closes-gate.yml`
  to name the one now-true exception (record content, fetched via `gh
  api`, still not a local-tree read) — a one-line comment edit, no
  behavior change to the workflow itself.
- Item 3's audit (what else in `--closes-only` mode reads the working
  tree vs. only metadata) is carried out by reading every function on the
  `--closes-only` call path (`pr_reference.check`, `_phase_from_approval`
  and its callees, `_autodetect_issue_phase`, `_pr_head_ref`,
  `_pr_is_cross_repo`) and is reported as a list in the phase-2 record,
  per the acceptance criterion ("as a list, or a statement of what was
  searched if empty").
- Once the fix lands, the six PRs (#337 #340 #343 #350 #352 #353) are
  re-run through the actual CI `closes-gate` check (not a local worktree)
  and each result is reported individually in the phase-2 record and the
  PR body.

## Out of scope

- Any change to `--closes-only`'s Closes-keyword detection logic itself
  (`gates/pr_reference.py`) beyond the item-3 audit — unless the audit
  finds an actual working-tree dependency there, in which case that
  finding is reported, not silently fixed under this proposal's frozen
  write set.
- Re-litigating whether existence-only `loop_state` evidence is the right
  policy (#284's decision, `docs/issue-284/decisions/`) — unaffected by
  this fix.
- Editing any of the six PRs' bodies (explicitly disallowed by
  acceptance).

## How you'll know it worked

- `pytest gates/test_closes_gate_ci.py` passes, including the new pinning
  test.
- Each of #337, #340, #343, #350, #352, #353 shows `closes-gate` passing
  in its GitHub Checks tab (CI-run, not a local worktree run), with no
  body edit on any of them — reported individually.
- The decision record states and justifies why the `gh api` contents read
  preserves the `main`-pinned checkout's trust boundary.
- The phase-2 record lists item 3's audit result.
