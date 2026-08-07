# issue-384 current-state survey

## Scope of the survey

Write surfaces expected for the eventual fix, and the mechanism each already carries.

### `.github/workflows/plan-aware-closes-gate.yml`
- Triggers on `pull_request` (not `pull_request_target`), `branches: [main]`.
- The `checkout` step is hard-pinned: `uses: actions/checkout@v4` with `ref: main` —
  never the PR ref. Comment at lines 30-35 states this exists specifically so a PR
  cannot edit `gates/ci.py` to make itself pass.
- Only one job, one required check name (`closes-gate`). No second job, no
  alternate check name exists today.
- Runs `python3 gates/ci.py . --pr "$PR_NUMBER" --autodetect --closes-only`.

### `gates/ci.py`
- `check(repo, pr, issue, phase, closes_only=True)` runs only the plan-aware
  Closes gate + phase1-surface-mismatch check; skips write_scope/protected-path/
  deps/record checks (`closes_only` branch, lines 291-347).
- All PR-specific data (`_pr_head_ref`, `_pr_title`, `_pr_commit_messages`,
  `_pr_reviews`, `_pr_is_cross_repo`, `pr_reference._pr_view`) is fetched via
  `gh pr view` / `gh api` — metadata only. Nothing in `ci.py`'s executed path
  reads or executes code from the PR's own worktree; the only code executed is
  whatever `checkout` put on disk, which is always `main` per the workflow step
  above. This is the trust boundary the issue names, and it is a property of
  the **workflow file's checkout step**, not of `ci.py` — `ci.py` has no
  awareness of which ref it was checked out from.
- `_autodetect_issue_phase` derives issue+role from the head branch name
  (`issue-<n>/<role>`), and phase from approval evidence
  (`_phase_from_approval`, reusing `flows._pr_approved` — same
  metadata-only reads).
- `_phase2_record_evidence` (added for #284) already establishes precedent for
  "accept an alternate signal, read from `gh`/repo metadata, in place of a
  body edit" — the record file's existence + non-empty `loop_state` substitutes
  for a body-level `Closes #N` when phase flipped after the body was written.
  This is the closest existing analog to a bootstrap escape hatch, and it is
  scoped narrowly (existence + one non-empty field, not content-checked) for a
  documented reason (`docs/issue-284/decisions/record-evidence-as-closing-intent.md`).

### `gates/gates.py`, `gates/pr_reference.py`, `gates/flows.py`
- Owned by other issues (#228, #172) per existing docstrings; `ci.py`'s own
  docstring already treats them as reuse targets, not files to duplicate logic
  into. `pr_reference._CLOSES_REF` (closing-keyword regex) and
  `flows._pr_approved` (two-path approval check) are the two functions any
  bootstrap eligibility check would need to reuse, both already metadata-only.

### `gates/test_closes_gate_ci.py`
- Existing test file for `gates/ci.py`; this is the location a bootstrap-path
  test would live, per this repo's convention of one test file per gate
  module rather than a separate `tests/` tree.

### `docs/issue-245/decisions/2026-08-04-closes-gate-wiring-tradeoffs.md`,
### `docs/issue-284/decisions/record-evidence-as-closing-intent.md`
- Prior decisions this proposal must not silently re-litigate: fail-closed on
  extraction failure (#245), and the record-existence alternate-evidence
  precedent (#284) reused above.

## What does not exist (searched, not assumed)

- No second required check / second workflow file exists under
  `.github/workflows/` — `ls .github/workflows/` returns only
  `plan-aware-closes-gate.yml`. Confirmed by directory listing, not inferred.
- No `gates/bootstrap.py` or any function/string matching `bootstrap` exists
  anywhere in `gates/` or `.github/workflows/` — confirmed via
  `grep -ri bootstrap gates/ .github/workflows/` (see below), zero hits.
- No repo-level branch-protection config is version-controlled in this repo
  (GitHub's ruleset config is a GitHub-side setting, not a file) — the only
  branch-protection-adjacent artifact in the tree is the comment in
  `plan-aware-closes-gate.yml` (lines 6-10) noting that check registration
  happens in Settings > Branches and is *not* done from this PR (issue #245
  precedent: infra registration is explicitly out of write-set for a gate PR).

```
$ grep -ri bootstrap gates/ .github/workflows/
(no output)
$ ls .github/workflows/
plan-aware-closes-gate.yml
```

## Scout (ran; not skipped)

Design decision is open (how to shape the escape hatch), so scouting applies —
not a pure bugfix, not a fully-specified spec. One research agent, one round
(the question is narrow enough that a single deepened pass reached saturation
— a second round would not have changed the two structural conclusions
below), searching GitHub's own docs/changelog and prior-art for "self-modifying
CI gate" patterns.

**Findings** (full findings + sources in the agent's report, condensed here):
1. GitHub branch protection / rulesets have **no native OR-across-required-checks**
   — required checks are a strict AND over the configured list. A second,
   separate "bootstrap" workflow/check cannot substitute for the primary check
   when it's red; the escape hatch must be folded into the *same* required
   check's own script.
2. GitHub's documented mitigation for the identical `pull_request_target`
   self-referential problem (a workflow can't test its own edit to itself,
   by design, hardened further in the actions/checkout v7 changes) is:
   admin/human bypass for the PR that edits the trust-sensitive file, not an
   automated "the gate approves its own patch" mechanism. No public source
   describes the latter as solved automatically anywhere.

Sources: docs.github.com "About protected branches", "Troubleshooting required
status checks", "Managing a branch protection rule", "Securely using
pull_request_target"; github.blog changelog 2026-06-18 and 2025-11-07.

**Gap line**: current state has zero escape-hatch surface (must-be #1, "the
check itself must contain any bootstrap logic," is unmet — nothing here does
that yet) and zero admin-bypass documentation surface (must-be #2 is partially
met: humans already *can* merge past a red required check via repo-admin
override outside this codebase, but that path today produces the undocumented
Closes-#N-body-edit workaround the issue describes, not a recorded bootstrap).
The design gap is: fold eligibility logic into `gates/ci.py` (adopt finding 1)
and require an explicit, recorded justification the moment the escape hatch is
used, rather than relying on silent admin override (adopts finding 2's
"human decides" while rejecting its "and nothing records it").

Stages used: 1 sweep + 0 deepening (saturated after round 1 — both structural
conclusions were already load-bearing and unambiguous; a second search
round would only have added more citations to the same two points, not
changed the design). Mode: single foreground agent (background dispatch
would violate contract v3 s22's headless single-consumption rule for this
session), not a parallel multi-angle fan-out — the question decomposed
cleanly into one research agent's scope (GitHub's own mechanism docs), so a
wider fan-out was not warranted; documented here rather than silently
narrowed.
