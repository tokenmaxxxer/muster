# Survey — issue #371 (status reports collapse "delivered" and "working")

## Where the report the operator saw comes from

`spawn.status(cwd)` (spawn.py:1123-1161) is the status-report generator. For
each subject (`docs/issue-<n>/`) and role it prints, per role record:

```
[{role}] loop_state: {fm.get('loop_state')}   verdict: {fm.get('verdict')}
```

(spawn.py:1140-1147). `fm` comes straight from `frontmatter()` (spawn.py:1084),
which reads the `loop_state:`/`verdict:` keys written by the role session
itself into its own `docs/issue-<n>/reports/<role>.md`. This is an **asserted**
label — the session that writes `loop_state: approved` or `landed` is grading
its own work, and nothing cross-checks it against GitHub. This is exactly the
"asserted vs derived" gap #333 names generally, applied to the field the
operator actually reads.

`status()`'s own docstring (spawn.py:1126-1128) states the design principle
explicitly: "상태는 에이전트의 것이다... 그 파일을 밖에서 고치면 문지기를
안 거친다" (state belongs to the agent; on-the-record must not patch that file
itself, or it bypasses the rulebook's transition gates). That principle is
sound for *writing* — but the issue's ask is to *read* additional signal
alongside the asserted frontmatter, not to overwrite it. Nothing in that
docstring blocks adding a second, derived column next to the asserted one.

## What derivation infrastructure already exists

- `spawn._pr_for_branch(root, branch)` (spawn.py:935) — PR number for a
  subject/role branch, via `gh pr list`.
- `gates/closure_sweep.py:_pr_view_state_body` (closure_sweep.py:59-68) and
  `_issue_view` (closure_sweep.py:53-56) — `gh pr view --json state,body` /
  `gh issue view --json state`, i.e. exactly "merge status" and "issue state"
  per #371 item 2's derivation list. `closure_sweep.classify()`
  (closure_sweep.py:38-50) already distinguishes MERGED-with-Closes-ref vs
  OPEN-with-Closes-ref vs plain-ref-only (phase-1 shape, not a violation) —
  the has_plain/has_closes split from `pr_reference.py`
  (`_CLOSES_REF`/`_PLAIN_REF`).
- `ledger/collect.py:parse()` (ledger/collect.py:37-45) — reads a
  `review.md` record's `verdict:` lines (Present/Surface/Absent/Incorrect).
  This is the closest existing proxy for "was the acceptance independently
  re-run": a `review` role record with `Present` verdicts for a subject means
  a session other than the builder re-checked it. No review record at all, or
  one still showing Absent/Incorrect, means it was not.
- **No check-status (CI) reader exists yet.** `gh pr checks` /
  `statusCheckRollup` is not queried anywhere in `spawn.py` or `gates/`.
  `gates/ci.py:check()` (referenced from `spawn.gate_report`, spawn.py:1177-1198)
  inspects the local working tree's diff against a base ref — a different
  thing from a PR's remote CI check status.

## Nothing in-repo currently distinguishes the states the issue names

Searched `spawn.py`, `gates/*.py`, `docs/handbooks/on-the-record.md` for any
enum/vocabulary of delivery states: only `loop_state: proposed,approved,landed`
(the *role's own* three-value state machine, documented per-role in
`docs/handbooks/on-the-record.md:69,94`) exists, and it is self-asserted, not
merge/check-derived, and has no "blocked" or "rejected-reworking" value at
all — a role that stalls at `approved` with a PR sitting unmergeable looks
identical, from `status()`'s output, to one whose PR merged five minutes ago.

## Adjacent/overlapping in-flight work (do not duplicate)

- PR #355 (issue-333, "derived record counts gate") — general asserted-vs-
  derived counting; not specific to the operator-facing status report or to
  merge/check state.
- PR #354 (issue-341, "no-concurrency-limit regression test + enforceability
  verdict") — different subsystem (concurrency), same enforceability-verdict
  spirit.
- PR #343 (issue-331, "mechanically check completion claims") — closest
  cousin: checks that a role *ran its own check* before claiming done. #371 is
  the orchestrator-level report failing to say the work never reached the
  operator at all — different actor (orchestrator's aggregate report vs a
  single role's completion claim), same direction of error, per the issue's
  own Boundary section. Building on #343's eventual mechanism (once merged)
  is a natural fit for a later increment; nothing to import today since #343
  is itself still open/pre-merge.
- PR #342 (issue-320, "semantic effect reporting") and PR #338 (issue-318,
  "approval-request content shape") — the issue's own Boundary section says
  these are related but distinct: #320 is PRs-vs-effects, #318 is what an
  approval request must contain. This work must not widen into either.
- issue #298 comment (2026-08-07) — establishes that a `Stop` hook can
  inspect and block the orchestrator's own report text. Not yet located as a
  concrete hook in this tree (`on-the-record/hooks/` has no `Stop` matcher in
  `hooks.json` today — only `SessionStart`, `UserPromptSubmit`, `PreToolUse`).
  Confirms the issue's framing that report-text inspection is mechanically
  reachable, but the hook itself is future work, not something this proposal
  can lean on as already-existing enforcement.

## Skip condition check (scout directive)

This is not a pure bugfix (new state vocabulary + derivation logic is a
design decision) and the spec leaves real design open (which states, how many,
what "blocked-on" detail, how deep the mechanical check on item 3 can honestly
go). Scouting therefore applies in principle — but this is an internal
governance/reporting mechanism for a single-operator agent-orchestration tool,
not a product-shaped surface with an external market of comparable products to
benchmark (no "category" of competing agent-status-report tools to sweep).
Per scout-directive, non-product roles scout "the best of their own
deliverable's kind" — for this deliverable that kind is: how does this same
repo's own prior art solve analogous derived-state problems? That search *is*
the "existing infrastructure" section above (closure_sweep, ledger, pr_reference)
and is the applicable substitute for an external sweep here. No external
web-facing scout brief is written; this section documents why.
