# Decision: phase-2 record evidence is fetched via `gh api .../contents`, not a local checkout

Context: `gates/ci.py::_phase2_record_evidence` needs the phase-2 record
file's text. It runs inside `.github/workflows/plan-aware-closes-gate.yml`,
whose checkout step is deliberately pinned to `ref: main` (never the PR's
own ref) so that a PR cannot edit `gates/ci.py` to make itself pass. The
record, however, lives only on the PR branch — a `main`-pinned local tree
structurally cannot contain it (issue #369).

## Decision

Fetch the record's content with
`gh api repos/<slug>/contents/docs/issue-<issue>/reports/<role>.md -f ref=<pr-head-branch>`
(`gates/ci.py::_fetch_ref_file`), base64-decode the `content` field, and
hand the decoded text to the existing pure `gates.record_frontmatter`
parser. No local filesystem read of the record path remains.

## Why this preserves the trust boundary

The workflow's checkout step exists to stop one specific thing: PR-authored
code executing as part of the gate. Two properties hold for the chosen
approach:

- **No code from the PR is fetched or executed.** `gh api .../contents`
  returns one file's bytes as JSON data over the GitHub API — it does not
  clone, check out, `git fetch`, or materialize the PR's tree anywhere on
  disk. The gate's own process never imports, execs, or sources anything
  from that response; it only base64-decodes it and hands it to a
  frontmatter *parser* (regex/YAML-shaped key extraction over text), the
  same as before.
- **The data path already exists at this trust level.** `_pr_commit_messages`
  (`gates/ci.py:85-113`) already calls `gh api repos/<slug>/pulls/<pr>/commits`
  from inside this same `main`-pinned gate to read PR-authored commit
  message *text* and pattern-match it for closing keywords — text authored
  by the PR, read as data, never executed. Reading one more PR-authored
  file's text the same way adds no new capability the gate didn't already
  have; it only reuses the established shape (`gh api` over `subprocess.run`
  with an argv list, no shell).

Contrast with the rejected alternative (checking out or otherwise
materializing the PR's tree to read the file from disk): that would put
the PR's *entire* tree — including arbitrary code elsewhere in it — on
disk inside the gate's execution environment, which is exactly what the
`main`-pinned checkout was written to prevent, even if this one read
wouldn't itself execute anything. `gh api .../contents` gets the same
single file's data with a strictly narrower capability (one named path,
declared read-only), so it was chosen instead.

## Consequence

`_phase2_record_evidence` now takes `pr: int` (needed for the `gh api`
call's repo/PR context) in addition to `branch`/`issue`. A missing file
(404) or any `gh api` failure returns `False`, same behavior as the old
"file doesn't exist" branch.
