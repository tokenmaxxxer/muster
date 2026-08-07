# issue-369 current-state survey

Pure bugfix per scout-directive skip condition 1: the defect and its fix are
fully specified by #369 itself (mismatched trust-boundary assumption between
`gates/ci.py::_phase2_record_evidence` and the `main`-pinned checkout in
`.github/workflows/plan-aware-closes-gate.yml`). No product-shaped design
decision is open — scouting is skipped; this is the mandatory skip record.

## Write surfaces

- `gates/ci.py:169-188` — `_phase2_record_evidence(repo, branch, issue)`
  reads `record_path = repo / f"docs/issue-{issue}/reports/{role}.md"` off
  the **local working tree**. Called from `check()` at `gates/ci.py:319-320`
  with `pr` already in scope (`check(repo, pr, issue, phase, closes_only)`),
  so a `pr` argument is trivially threadable into
  `_phase2_record_evidence` without changing its call site's available data.
- `.github/workflows/plan-aware-closes-gate.yml:23-31` — checkout step pins
  `ref: main`, by design, with an explicit trust-boundary comment (lines
  17-22): PR code must never run gate logic against itself. The step's
  comment (line 21-22) also currently asserts `--closes-only` "PR의 파일
  diff를 전혀 보지 않고 `gh pr view`/`gh issue view`로 메타데이터만
  읽으므로" — this is the assertion #369 says is now false.
- Existing helper pattern for reading GitHub data without local checkout:
  `gates/ci.py:85-113` (`_pr_commit_messages`) already calls
  `gh api repos/<slug>/pulls/<pr>/commits` via `subprocess.run` (no shell,
  argv list — matches no-footgun's subprocess rule) and
  `spawn._repo_slug(repo)` (`gates/ci.py:100`) is the established way to get
  `owner/repo` for such calls. `gh api repos/<slug>/contents/<path>?ref=<sha>`
  is the equivalent read-only endpoint for a single file's content at a
  given ref — it returns base64-encoded content as JSON data; GitHub does
  not execute anything to serve it, and `gh api` itself only performs an
  HTTP GET-with-auth, no local execution of PR content.
  `_pr_head_ref(repo, pr)` (`gates/ci.py:53-62`) returns `headRefName`, i.e.
  a branch name — sufficient as the `ref` query param for the contents API
  (GitHub resolves branch names to their current head commit server-side).
- `gates/test_closes_gate_ci.py:413-444` — four existing tests call
  `ci._phase2_record_evidence(repo, "issue-245/implementation", 245)`
  directly against a local `repo` fixture (tmp dir tree, no network). These
  assert local-filesystem behavior that the fix must not silently break for
  local/offline callers — but per item 2's acceptance criterion ("fails if
  someone reintroduces a filesystem read for PR-branch content"), the
  *production* code path (as called from `check()`) must no longer read the
  PR's tree from disk. This means either the signature changes (adding
  `pr`) and existing direct-unit tests get updated to the new signature, or
  the function is split into a pure frontmatter-parsing core (tree-agnostic,
  keeps existing unit-test shape) plus a new caller that fetches content via
  `gh api` and passes text in — the latter avoids rewriting working local
  tests and cleanly separates "parse frontmatter" (pure, already covered)
  from "fetch record text for this PR" (network, needs a new pinning test
  per acceptance item 2).
- `docs/issue-284/decisions/record-evidence-as-closing-intent.md` — records
  why existence-only (not value) of `loop_state` was chosen as evidence;
  unaffected by *where* the text comes from, only relevant as prior context.

## Six acceptance PRs (#337 #340 #343 #350 #352 #353)

Current state (per #369's own report) is uniform: all six fail
`closes-gate` in CI with the "대안: ... 통과한다" message, meaning the
alternative evidence path is being reached but returning false in CI
specifically because the checked-out tree is `main`, not the PR branch.
No PR-specific handling needed — the fix is generic to the function.

## Trust boundary property to preserve

The checkout-main step exists so PR code cannot edit `gates/ci.py` to pass
itself (workflow comment, `.yml:17-20`). Reading file *content* from the
PR's ref via `gh api repos/<slug>/contents/<path>?ref=<branch>` fetches
data only — no PR code is checked out, invoked, imported, or executed by
this call, so the property survives unchanged. This must be verified
explicitly in the proposal/decision record, not merely asserted.

## Item 3 (audit scope)

Everything else `--closes-only` mode touches needs enumeration against
"reads only metadata, never the working tree" — `gates/pr_reference.py`
(the plan-aware Closes check itself), `gates/ci.py::_phase_from_approval`
and its callees (`spawn._approvers`, `spawn._issue_comments`,
`flows._pr_approved`, `_pr_reviews`), and `_autodetect_issue_phase` /
`_pr_head_ref` / `_pr_is_cross_repo`. This audit is scope item 3's
deliverable and belongs in the phase-2 record, not duplicated here.
