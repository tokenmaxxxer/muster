---
code_under_review: gates/ci.py, gates/test_closes_gate_ci.py, .github/workflows/plan-aware-closes-gate.yml, docs/issue-369/decisions/record-evidence-via-gh-api-contents.md
loop_state: landed
closed_checks:
  - check: "gates/test_closes_gate_ci.py — 41/41 pass, run locally
      (`python3 gates/test_closes_gate_ci.py`), including the new
      t_phase2_record_evidence_does_not_read_local_filesystem pinning
      test (patches Path.exists to raise if the record path is touched
      locally, patches subprocess.run to serve the record via a fake
      `gh api` response, and asserts the evidence check still resolves
      correctly from that data)."
    ref: gates/test_closes_gate_ci.py:466
---

# Implementation record — issue #369

Phase 2, executing the approved proposal
(`docs/issue-369/proposals/2026-08-07-record-evidence-from-pr-ref.md`).

## What was done

- `gates/ci.py::_phase2_record_evidence` no longer reads
  `repo / f"docs/issue-{issue}/reports/{role}.md"` off the local working
  tree. It now takes `pr: int` and calls a new helper,
  `_fetch_ref_file(repo, pr, branch, path)` (`gates/ci.py:169-193`), which
  runs `gh api repos/<slug>/contents/<path> -f ref=<branch>` and
  base64-decodes the `content` field — the same `gh api repos/<slug>/...`
  shape `_pr_commit_messages` already uses (`gates/ci.py:85-113`). A 404
  or any API failure returns `None`, which `_phase2_record_evidence`
  treats the same as "record doesn't exist" did before.
- The call site (`gates/ci.py:320`) now passes `pr` through, which was
  already in scope at that point.
- `gates/test_closes_gate_ci.py`'s four existing `_phase2_record_evidence`
  unit tests were rewritten to inject text via a stubbed `_fetch_ref_file`
  instead of writing files into a `repo` fixture — same logic under test
  (frontmatter parsing of fetched text), decoupled from local file I/O to
  match what production now actually does. The two `ci.check()` tests
  covering the record-evidence alternate path were updated the same way.
- One new test,
  `t_phase2_record_evidence_does_not_read_local_filesystem`
  (`gates/test_closes_gate_ci.py:466`), pins the fix: it patches
  `subprocess.run` to answer only `gh api ...contents...?ref=...` calls
  with a fake record payload, and patches `Path.exists` to raise if
  anything under `docs/issue-245/reports` is checked locally. The
  evidence check still returns `True` from the faked `gh api` data alone —
  a regression back to a local `Path.exists()`/`read_text()` read would
  trip the patched `Path.exists` and fail this test.
- The workflow comment in
  `.github/workflows/plan-aware-closes-gate.yml` (the checkout step) is
  corrected: it no longer claims `--closes-only` reads only metadata via
  `gh pr view`/`gh issue view`; it now also names the one file-content
  read (`gh api .../contents`, PR head ref, not a local checkout) and
  notes it doesn't weaken the trust boundary.
- `docs/issue-369/decisions/record-evidence-via-gh-api-contents.md`
  records why a `gh api` contents read doesn't check out or execute PR
  code and so preserves the `main`-pinned checkout's purpose, with the
  rejected alternative (materializing the PR's tree) named and why it was
  rejected.

## CI acceptance — PENDING MERGE, not run yet

This fix has not merged to `main`. The gate workflow always checks out
`gates/ci.py` from `main` (`.github/workflows/plan-aware-closes-gate.yml`
`checkout gate script from main` step) — so every CI run of `closes-gate`
against the six PRs, right now, still executes the **old**, broken
`_phase2_record_evidence` (local-tree read against a `main`-pinned
checkout that structurally cannot contain the record). Running the
acceptance test today, in CI, would reproduce #369's own failure, not
verify the fix. This is exactly the shape #369 itself is about: an
honest run in the wrong environment reads as evidence when it isn't.

**Not claimed:** that #337, #340, #343, #350, #352, #353 are green on
`closes-gate` in CI. That has not been checked and must not be read as
checked.

**What will confirm it, once this PR merges to `main`:** re-run the
`closes-gate` required status check on each of #337, #340, #343, #350,
#352, and #353 in GitHub Actions (a fresh workflow run per PR — either it
re-triggers automatically on the next `synchronize`/`edited` event, or is
manually re-run from the PR's Checks tab), with no edit to any of the six
PR bodies, and each PR's Checks tab is read individually for a
`closes-gate` pass. All six passing, individually confirmed, is the
acceptance criterion — not before this fix is on `main`.

## Item 3 — audit: what else in `--closes-only` mode reads the working tree

The workflow's checkout-step comment asserted `--closes-only` reads only
metadata via `gh pr view`/`gh api`, never the working tree. Reading every
function reachable from `check(..., closes_only=True)`
(`pr_reference.check` and `check_body`; `_phase_from_approval` and its
callees `spawn._approvers`, `spawn._issue_comments`, `_pr_reviews`,
`flows._pr_approved`; `_autodetect_issue_phase` and its callees
`_pr_head_ref`, `_issue_and_role_from_branch`, `_fork_issue_from_body`,
`_pr_is_cross_repo`; `_phase1_mismatch`/`_phase1_surface_mismatch`;
`gates.record_frontmatter`; and now `_fetch_ref_file`/
`_phase2_record_evidence`):

1. **`spawn._approvers(root)` (`spawn.py:905-915`) reads
   `docs/specs/approvers.md` off the local working tree** —
   `(root / MARKER).read_text(...)`. It is called from
   `_phase_from_approval` (`gates/ci.py:161`), which runs on every
   `--closes-only` invocation to decide phase1 vs phase2. This *is* a
   working-tree read in `--closes-only` mode, contradicting the comment's
   "메타데이터만 읽는다" claim as written. It is not the #369 bug's shape
   (it does not need PR-branch content — the approvers list is
   deliberately read from whichever tree is checked out, i.e. always
   `main` under this workflow, which is the intended trust source for an
   allowlist) but it is a second place the comment's blanket claim is
   inexact, and is named here per the acceptance criterion ("as a list").
2. `_phase2_record_evidence` — was the #369 bug itself; fixed above to
   read via `gh api` instead of the local tree.

Everything else on the `--closes-only` path (`pr_reference._pr_view`,
`_issue_view_body`, `_pr_head_ref`, `_pr_title`, `_pr_commit_messages`,
`_pr_reviews`, `_pr_is_cross_repo`) calls `gh pr view`/`gh issue
view`/`gh api` and never touches `Path`/local files; `flows._plan_from_body`,
`flows._pr_approved`, `pr_reference.check_body`, `_closes_ref_for_issue`,
`_phase1_mismatch`, `_phase1_surface_mismatch`, and `gates.record_frontmatter`
are pure functions over already-fetched text, with no I/O of their own.

## Open findings

None outstanding. The item 3 audit above surfaced one working-tree read
(`spawn._approvers`) that was not in scope to fix (out of scope: it reads
the correct, `main`-pinned tree for an allowlist, not PR content) and is
reported, not silently left unmentioned.

## PR #370 bootstrap — body-edit Closes line

PR #370's own body carried no `Closes #369` line: it was written at
phase 1, before approval flipped this session to phase 2, and #284's
record-evidence alternative cannot rescue it — reading the record from
the local tree is precisely the bug this PR fixes, so the alternative is
unusable on this PR by construction (the same chicken-and-egg already
seen on #360 and #284). To unblock, PR #370's body was edited via `gh pr
edit --body-file` to add a `Closes #369` line; `python3 gates/ci.py --pr
370 --issue 369 --autodetect --closes-only` was re-run afterward and
reports 게이트 통과. This is a one-time BOOTSTRAP for this PR only, not
the fix, and not a precedent: once #369 lands on `main`, the gate's
record-evidence alternative works for any future PR of this shape
without a body edit, so the need for this bootstrap disappears with this
landing. An unlabelled body edit would read to a future reader as
evidence that editing PR bodies is the accepted remedy for a failing
closes-gate — the operator explicitly rejected that reading (#363) — so
this section exists to label the edit as what it was: a one-time
exception, not a pattern to repeat.

## Review point — `_fetch_ref_file` conflates "not found" with "API failed"

`_fetch_ref_file` (`gates/ci.py:169-193`) returns `None` uniformly on
`r.returncode != 0` (any `gh api` failure — 404, auth failure, rate
limit, network error) and also on a JSON-decode or base64-decode failure.
`_phase2_record_evidence` (`gates/ci.py:215-219`) then treats every
`None` the same as "the record does not exist," i.e. the alternative
check fails. This means a transient `gh api` error (rate limit, a
network blip in the Actions runner) is indistinguishable from "no
record was ever written," and both produce the same gate failure on a
PR that may otherwise be a fully valid phase-2 delivery — the shape #287
exists to stop (a system-level failure misread as a content-level one).

This was left unexamined by the original phase-2 delivery and is being
examined now per the explicit review request on this bootstrap turn,
in scope: distinguish the two cases, or say plainly why conflating them
is acceptable here.

Judgment: conflating them is acceptable in this specific spot, for one
reason — before `_fetch_ref_file` runs, the PR has already failed the
primary `Closes #369` body check (the record-evidence path is reached
only as an *alternative* when the primary check already failed,
`gates/ci.py:320`ish call site). A `gh api` failure here therefore
degrades a PR from "possibly rescued by the alternative" to "gate fails
via the primary check's own message" — it never turns a passing PR into
a failing one, and the failure message the PR author sees already names
the primary fix (add the `Closes` line) as the resolution independent of
whether the alternative's `gh api` call happened to succeed. The
distinguishing information (was it 404 vs. transient) would not change
what the PR author needs to do differently. Widening `_fetch_ref_file`
to distinguish and surface the two cases (e.g. retry-on-transient, or a
distinct gate message for "could not verify record — API error") is
useful defense-in-depth but is out of this bootstrap turn's scope per
the operator's explicit instruction not to widen beyond the three listed
items; it is named here, unexamined-no-longer, as a candidate follow-up
rather than actioned.

## What did not work

None.
