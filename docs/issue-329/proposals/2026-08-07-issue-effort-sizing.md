---
status: proposed
files:
  - on-the-record/commands/run.md
  - gates/issue_size.py
  - gates/test_issue_size_gate.py
  - gates/ci.py
  - docs/handbooks/on-the-record.md
---

## Request

The operator observed that on-the-record sizes an issue by dependency
alone — related work goes in one issue regardless of how much work it is —
and some spawned-role sessions run 40-50 minutes as a result. Effort is
never considered at filing time. The fix needs a second sizing axis
(effort) alongside dependency, applied when an issue is drafted, plus a
mechanical check per #310 (prose does not discharge a requirement).

## Constraints

- Per #310: acceptance must name an executable artifact that fails on
  regression; a doc sentence or memory note does not count.
- Per #328 (filed alongside, different fault): do not fold bundling
  (unrelated topics in one issue) into this fix — #329 is about effort
  magnitude on a single, correctly-scoped unit, independent of topic
  relatedness.
- Per role-handoff contract v3 s19 (this session): phase 1 only —
  survey + proposal, no code, until a human Approve lands.
- No pre-filing prediction is available: `gh issue create` happens before
  any code exists, so there is no diff to measure yet. A gate that only
  fires post-hoc (on the merged PR) is the honest ceiling of what is
  mechanically checkable here — the fix's preventive half has to be a
  drafting-time estimate the orchestrator commits to in the issue body,
  not something a script can verify before the fact.

## Rationale

**Chosen approach:** two parts. (1) `on-the-record/commands/run.md` step 1
gains a mandatory effort-estimate sub-step, structurally identical to the
existing mandatory skill-evaluation and lead-role-classification sub-steps
already in that file — the orchestrator states a rough size band (S/M/L,
anchored to diff-lines-changed bands) in the issue draft before
`gh issue create`, and an L estimate must be split into multiple issues
before filing, the same way step 2 already forces an explicit classification
instead of a silent default. (2) A new deterministic gate,
`gates/issue_size.py`, reads a merged PR's `gh pr view --json
additions,deletions,changedFiles` (same call shape `gates/pr_reference.py`
already uses) and fails when a PR's total changed lines exceed the declared
band by a wide margin — catching the case where the drafting-time estimate
was wrong or skipped, which is the actual, checkable "regression" for a
sizing defect that by nature cannot be verified before the work exists.

**Alternative considered and rejected — session wall-clock time as the
metric:** `spawn.py` already writes a per-session log (see issue #192), so
elapsed session time looked like a more direct proxy for "a 40-50 minute
session" than diff size. Rejected because wall-clock time conflates two
different defects: a long session that produces a small diff is a
research/exploration problem, not a sizing problem, while #329's own
complaint (large PR, single merge-conflict surface, one approval covering
many decisions) is specifically about *artifact* size, not time-on-task.
Diff size is also free (GitHub already computes it) and matches the
existing `gates/pr_reference.py` precedent; timing would need a new
log-parsing path with no existing gate analog.

**Alternative considered and rejected — a hard `gh issue create` wrapper
that blocks filing:** would require intercepting the `Bash(gh issue
create:*)` call itself (a PreToolUse hook matcher change), giving a true
filing-time block. Rejected for this proposal: the hook has no way to
estimate the *future* diff size of unwritten work, so a hard block could
only ever check for the presence of the size-band field the orchestrator
itself just typed — i.e., it would enforce that the field exists, not that
the estimate is honest. That is worth doing but is a distinct, smaller
follow-up (a PreToolUse addition to `deliverable-guard.sh` or a sibling
hook checking the drafted body for a `size:` line) — bundling it here would
widen this proposal's write set into the hooks directory for a check that
adds format-compliance, not effort-accuracy. Left out of scope below.

## What will be done

- `on-the-record/commands/run.md` step 1: add a mandatory effort-estimate
  sub-step (same enforcement shape as the existing skill-evaluation and
  lead-role-classification sub-steps — explicit statement in conversation,
  no silent default). Bands: S (~<150 changed lines), M (~150-400), L
  (~400+). An L estimate must be split into multiple issues before
  `gh issue create` runs; the split issues get filed instead of the
  original. The chosen band is written into the issue body as a one-line
  `size: S|M|L` marker (parseable, same spirit as the existing `## 실행
  계획` block's fixed grammar).
- `gates/issue_size.py`: new deterministic gate. Given `--pr <n>` (and repo
  path), calls `gh pr view <n> --json additions,deletions,changedFiles`,
  resolves the source issue via the existing `issue-<n>/<role>` branch-name
  convention (`gates.BRANCH_ROLE`-style, same as `gates/ci.py`), reads that
  issue's `size:` marker via `gh issue view`, and fails (exit 1) when
  changed-lines exceeds the declared band by a defined margin (documented
  in the module) — the mechanical "fails when this regresses" artifact
  #310 requires. Missing `size:` marker on an issue with a linked PR also
  fails, so an issue drafted without going through the new step 1 sub-step
  is itself a detectable regression.
- `gates/test_issue_size_gate.py`: pytest fixtures (no network — same
  pattern as `gates/test_closes_gate_ci.py`) exercising the band-margin
  logic and the missing-marker failure path deterministically.
- `gates/ci.py`: wire `issue_size` in alongside the existing `--pr
  --issue` optional path (same opt-in shape `pr_reference.py` uses — skips
  cleanly when no PR context, per `ci.py`'s own documented fail-open
  rationale for PR-only checks).
- `docs/handbooks/on-the-record.md`: document the `size:` marker and band
  thresholds next to the existing `## 실행 계획` block documentation, so
  the mechanical grammar has one home.

## Out of scope

- A hard PreToolUse block on `gh issue create` that checks the drafted
  body for the `size:` field before the call is allowed to run (the
  rejected-alternative note above) — worth a follow-up issue, not bundled
  here.
- #328's bundling fix (unrelated-topics-in-one-issue) — different fault,
  different tell, filed separately by the operator on purpose.
- Retroactively re-sizing or splitting any of the 336 issues already filed.
- Session wall-clock enforcement (rejected alternative above).

## How you'll know it worked

- `pytest gates/test_issue_size_gate.py` passes today and fails when the
  band-margin or missing-marker logic in `gates/issue_size.py` is reverted
  or weakened — the executable regression artifact #310 requires.
- `python3 gates/ci.py <repo> --pr <n> --issue <n>` exits 1 on a real PR
  whose merged diff exceeds its issue's declared `size:` band by the
  documented margin, and exits 0 otherwise — verified against at least one
  fixture PR in the test file plus a dry run against this proposal's own
  eventual delivery PR (which must itself declare and stay inside a
  truthful band).
- `on-the-record/commands/run.md` step 1 visibly requires and `run.md`'s
  reviewer can point at the effort-estimate sub-step the same way step 2's
  lead-role classification is already pointed at in review — an issue
  drafted after this change either carries a `size:` line and (if L) is
  split, or the omission is itself what `gates/issue_size.py` catches on
  the resulting PR.
