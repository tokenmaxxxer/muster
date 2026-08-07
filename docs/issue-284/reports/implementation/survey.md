# issue-284 survey — closes-gate phase flip + fork PRs

## Live evidence (2026-08-07)

Six delivery PRs red on closes-gate for the exact F1 mechanism: #337, #340,
#343, #350, #352, #353. Checked #337 (`issue-330/implementation`) directly:
body still reads "Phase 1 (proposal only, contract v3 s19) for #330." with no
`Closes`/`Fixes`/`Resolves` anywhere in body or either commit message, even
though the phase-2 commit landed real code and the phase-2 record
(`docs/issue-330/reports/implementation.md`, fetched from
`origin/issue-330/implementation`) exists with `loop_state: phase-2-complete`
in its frontmatter. That record is exactly the kind of artifact
`record-shape-directive` mandates every phase-2 session write — so a
phase-2 delivery always leaves a locatable, committed trace independent of
the PR body text.

## Gate code (`gates/ci.py`, `gates/pr_reference.py`)

- `ci.py::_phase_from_approval` (ci.py:144) derives phase1/phase2 from
  approval evidence (issue comment or PR review), reusing
  `flows._pr_approved` (`gates/flows.py:130`). Unrelated to the body text —
  this is what "flips" once approval lands.
- `pr_reference.py::check_body` (pr_reference.py:24) is the actual Closes
  requirement: phase2 requires a `Closes/Fixes/Resolves #<issue>` match in
  the PR body (`_CLOSES_REF`), full stop. `check_body`'s own docstring in
  `ci.py::_phase1_surface_mismatch` (ci.py:186) notes it is **owned by
  #228** — other code supplements it rather than editing it (that function
  is itself an example: it re-implements a wider phase1 check over
  body+title+commits without touching `check_body`).
- `ci.py::check()` (ci.py:243) composes `pr_reference.check(...)` results
  with everything else; this is where a phase2-specific supplement can sit
  without touching `pr_reference.py`.
- `gates.record_frontmatter(text)` (gates/gates.py:279) is the existing
  shallow `---` frontmatter parser already used by `record_enums` — reusable
  to read `loop_state` from a record file without a new parser.
- `_ISSUE_ROLE_BRANCH` / `_issue_and_role_from_branch` (ci.py:34, ci.py:56)
  is the sole issue-number extraction path today; it fails closed (blocks)
  the instant the branch isn't `issue-<n>/<role>` — this is F2, confirmed
  against the issue's #278/#279 xtmono fork-PR incident (enforce_admins had
  to be lifted to land those).
- `pr_reference._PLAIN_REF` (pr_reference.py:22) already matches a bare
  `#N` in body text and is exactly what phase1 already requires from every
  PR — reusable as the fork fallback's extraction pattern instead of a new
  regex.

## roles/*.json loop_state vocabulary (unreliable as a hard enum)

`roles/implementation.json` declares `loop_state` enum
`["scope-proposed", "scope-approved", "in-progress", "landed"]`
(roles/implementation.json:20), but the observed real record on #337 used
`phase-2-complete` — outside that enum. This is not a bug hit by
`record_enums` because the required CI check runs `ci.py` in
`--closes-only` mode (ci.py:243's docstring, ci.py main() `--closes-only`
flag), which skips `record_enums` entirely. **Consequence for this issue's
fix**: loop_state's *value* is not a trustworthy enum to gate on today —
only the record file's *existence* with a non-empty `loop_state` field is a
safe signal (mere presence, not a specific string), matching what
`record-shape-directive` actually mandates ("carries `loop_state:`
frontmatter", not a fixed vocabulary).

## #312 overlap (PR #314, `issue-312/implementation`, open, phase2)

`_phase_from_approval` is #312's write set (PR #314 body: "`ci.py`'s
`_phase_from_approval` no longer requires an exact role match... phase is
now a property of the issue"). Its landing loosens the role match to "any
approvers.md-authored `APPROVE issue-<n>/<any role>`" — it does not touch
`_autodetect_issue_phase`'s branch-name extraction, `check()`'s phase2
composition, or `pr_reference.py`. Confirmed by reading `flows._pr_approved`
(flows.py:130): the PR-review Approve path (two-account mode) never
consults `role` at all — only the single-account `APPROVE <subject>/<role>`
issue-comment path does. That means a fork PR calling
`_phase_from_approval(repo, pr, issue, role=None)` is already safe today,
independent of whether #312 has landed: the two-account path still works,
and the single-account path degrades to "never matches" rather than
crashing or misclassifying. No coordination is needed on that call site's
behavior, only on *which function* touches it (see proposal Rationale).

## Alternatives considered here (see proposal Rationale for the rejected ones)

- Making phase derivation issue-level (what #312 already does) — does not
  address this issue's premise per the issue text itself: the Closes
  *requirement* still flips under an unchanged PR once its issue becomes
  phase2, and #312 admits this ("phase2 판정" 결함이지 "요구사항 뒤집힘" 결함은
  아니다). Confirmed by reading #314's own PR body: it explicitly punts the
  "phase determination gap" feedback to an open finding, not this issue's
  concern.
- Auto-editing the six stuck PRs' bodies via `gh pr edit` from this
  session — rejected: this session is issue-284/implementation, not
  issue-330/implementation etc.; contract v3 forbids the orchestrator (and,
  by the same logic, an unrelated role session) from editing another role's
  PR. The fix must be gate-side so those PRs go green on their own, or via
  their own role session choosing to add Closes — not edited out-of-band
  here.
