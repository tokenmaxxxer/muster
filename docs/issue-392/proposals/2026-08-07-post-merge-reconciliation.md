---
status: proposed
files:
  - on-the-record/commands/run.md
  - gates/closure_sweep.py
  - gates/flows.py
  - docs/specs/flows-schema.md
  - test_gates.py
---

## Request

Two symptoms with one cause: after a merge, nothing reconciles the
orchestrator's local checkout or the remote's branch list against
reality. Symptom 1 — the orchestrator's own clone goes stale after a
`gh`-side merge, and a stale read is stated with full confidence.
Symptom 2 — branches survive their PRs on paths that don't go through
`gh pr merge --delete-branch` (merges outside the orchestrator's relay,
partial failures, branches pushed with no PR ever opened). Deciding
what a no-PR branch means (abandoned vs. never-submitted) is a hard
precondition before anything is proposed for deletion.

## Constraints

- Nothing may auto-delete a branch without first distinguishing
  abandoned work from never-submitted work (issue's explicit
  precondition; losing unsubmitted work is a worse defect than #392
  itself).
- `closure_sweep.py`'s existing contract is detect-only — it reports,
  it does not act (`gates/closure_sweep.py:5-6`, reaffirmed by #383).
  The new check must not break that contract by introducing the first
  automatic delete.
- The fix must not be "a rule the orchestrator remembers" (#392 item 1,
  stated explicitly) — a doc note saying "remember to `git pull`" does
  not satisfy this.
- No new standing checker: #392's boundary section requires checking
  whether this belongs in #383's existing sweep first.

## Rationale

**Chosen approach**: (a) fold the post-merge local-checkout refresh
into the single merge command the orchestrator already always runs,
rather than adding a separate reminder step; (b) add a
branch-reconciliation check to `gates/closure_sweep.py`
(`git ls-remote` vs. open PRs vs. PR history), reported through the
same `hygiene` surface `flows --json` already exposes, rather than a
new command or script.

**Alternative considered and rejected — a new `spawn.py sync` command
the orchestrator calls after every merge**: this repeats exactly the
shape #392 diagnoses for symptom 1 itself — a step that exists only if
someone remembers to invoke it is a habit, not a mechanism. Chaining
the refresh onto the merge command the protocol already names as a
single mandatory action (`gh pr merge <n> --merge --delete-branch`)
removes the "remember to also run X" failure mode entirely: there is
no second command to forget.

**Alternative considered and rejected — a new standalone branch-sweep
script (e.g. `gates/branch_sweep.py`)**: #392's own boundary section
asks whether this belongs in #383's sweep rather than a new one.
#383 already establishes that an unwired-but-correct checker is
equivalent to no checker (`grep -rn closure_sweep .github/` is empty
today). A second new script has the same wiring risk and duplicates
the `gh`/`git` plumbing `closure_sweep.py` already owns for reading
issue and PR state per subject. Extending the existing sweep reuses
its call path and its one already-read surface (`flows --json`
`hygiene`) instead of adding a second surface the operator has to
learn to check.

**Alternative considered and rejected — deriving all orchestrator
reads from `gh` instead of local files (symptom 1's "legitimate answer"
per the issue text)**: this would touch every place the orchestrator
reads repo state, not just the post-merge moment — a much larger
change than this issue's measured trigger (one merge, one stale read)
justifies, and the issue's own text frames it as one option to
"consider rather than assume away," not a mandate. The smaller fix
(refresh at the one point staleness is introduced — right after a
merge) closes the actual reproduced failure without redesigning how
the orchestrator reads state everywhere else.

## What will be done

1. `on-the-record/commands/run.md:229` — change the documented merge
   step from `gh pr merge <n> --merge --delete-branch` to that command
   chained with a local refresh of the orchestrator's own checkout
   (fetch + fast-forward main), written as one line so it is the merge
   action's definition, not a separate step to remember.
2. `gates/closure_sweep.py` — add a branch-reconciliation check:
   `git ls-remote --heads origin` minus branches backing an open PR
   minus `main`, cross-referenced per branch against `gh pr list
   --state all --head <branch>`:
   - a closed or merged PR exists for the branch → classified as a
     leftover (safe-delete candidate), reported by name.
   - no PR was ever opened for the branch → classified separately as
     unsubmitted, reported by name, explicitly never proposed for
     deletion.
   Detect-only, matching the existing contract: this reports both
   classes, deletes neither.
3. `gates/flows.py` / `docs/specs/flows-schema.md` — surface the new
   check's two classified lists under `hygiene` (new field, verbatim
   passthrough of `closure_sweep`'s output, same pattern as the
   existing `hygiene.closure_sweep` field), so the operator sees branch
   counts through the surface `flows --json` already provides (#392
   item 4), reusing #374's demonstrated pattern of surfacing existing
   computed data rather than building a new notifier.
4. `test_gates.py` — cases for: a branch with a merged PR (leftover), a
   branch with a closed-unmerged PR (leftover), a branch with no PR
   ever opened (unsubmitted, distinct classification), and a branch
   backing an open PR (excluded entirely).

## Out of scope

- Any automatic deletion, of either classified branch type. Deletion
  stays a human act (`gh` command by hand), same as `closure_sweep`'s
  existing issue-closing contract.
- Wiring `closure_sweep`/`flows` into CI — that gap is #383's own scope
  item 3, already filed, not duplicated here.
- `spawn.py clean`'s own defects (#288) — different resource (local
  work directories), confirmed in the survey.
- Redesigning the orchestrator's reads to derive fully from `gh`
  instead of local files — considered and rejected above as
  disproportionate to the measured trigger.

## How you'll know it worked

- `git ls-remote --heads origin` compared by hand against the new
  check's output on this repository's real branch state (5 known
  no-PR-open branches per #392's own measurement) — the check names
  each one and its classification (leftover vs. unsubmitted).
  Symptom 2: caught, reported, nothing deleted.
- The merge-relay doc change is read back to confirm the refresh is
  syntactically part of the same command line, not a separate
  bullet — grep `run.md` for the chained command.
  Symptom 1: the reproduction path from the issue (merge via `gh`,
  then read a file the merge changed) is closed by definition once the
  refresh is inseparable from the merge step; this is a process/doc
  fix, not something a unit test executes.
- `python3 test_gates.py` — new cases pass, existing cases unaffected.
