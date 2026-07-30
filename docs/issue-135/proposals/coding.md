# Build proposal — issue #135

files:
- `gates/closure_sweep.py` (new)
- `spawn.py` (new subcommand wiring only — no change to existing functions)
- `test_gates.py` (new cases, same file the issue-126 gate tests live in)

## Request (paraphrased)

Define, in code, what "the board's issues and PRs are closed
consistently" means, and add a sweep that finds violations of that
definition across the whole board and reports them as an idempotent
issue comment — without auto-closing anything (closing stays a
human/orchestrator decision).

## Constraints

- Report only. Never call `gh issue close` / `gh pr close` from this
  code path (contract v3: GitHub acts are human decisions).
- Must not misflag a phase-1 proposal PR (merged, issue still open by
  design — role-handoff contract v3 s19) as a violation. Only a PR
  whose body actually carries `Closes/Fixes/Resolves #n` obligates the
  issue to be closed; a plain `#n` reference never does, merged or not.
- Reuse `gates/pr_reference.py`'s existing `_CLOSES_REF` classification
  instead of re-deriving "is this a delivery PR" with a second regex —
  two independent parsers of the same convention drifting apart is
  exactly the kind of inconsistency this issue is about.
- Idempotent comment: reuse the `_post_crash_comment`-style
  marker-check-before-post pattern (`spawn.py:1486`,
  `_issue_comments()`), not a new posting mechanism.
- No new dependency, no new env var.

## What will be done

1. `gates/closure_sweep.py`:
   - `find_violations(root, subjects) -> list[dict]` — pure-ish
     orchestration function (network via `gh`, no writes). For each
     subject (`issue-<n>`, from `spawn.py::board()`'s keys) and each
     role branch `issue-<n>/<role>`:
     - Resolve the branch's PR via the existing `_pr_for_branch`
       helper (state `all`, so both open and merged/closed are seen).
     - Fetch issue state (`gh issue view <n> --json state`) and PR
       state + body (`gh pr view <pr> --json state,body`).
     - Classify the PR body with `pr_reference._CLOSES_REF` (delivery
       reference) vs `pr_reference._PLAIN_REF` (proposal reference) —
       import and reuse, do not reimplement.
     - **Invariant 1** (closed issue, PR still open): issue state
       `CLOSED` and PR state `OPEN` and the PR references this issue
       (plain or Closes) → violation `open-pr-on-closed-issue`.
     - **Invariant 2** (delivery merged, issue still open): PR state
       `MERGED`, body matches `_CLOSES_REF` for this issue number, and
       issue state is `OPEN` → violation `merged-delivery-issue-open`.
     - A merged PR with only a plain `#n` reference and an open issue
       is explicitly **not** a violation (phase-1 shape, by design) —
       this is the side-effect case the proposal's constraint calls
       out; it must appear as a negative test case.
   - `format_report(violations) -> str` — one line per violation,
     `issue #n / PR #m: <kind>`.
   - `_post_sweep_comment(root, violations)` — marker-guarded
     (`_SWEEP_COMMENT_MARKER`), posts once per distinct violation set
     (marker includes a hash of the sorted violation list so a changed
     violation set posts a fresh comment instead of going silent
     forever) via the existing `_issue_comments`/`gh api ... comments`
     call shape. Posted to... open question resolved as: post to a
     fixed meta-issue is out of scope (no such issue exists); instead
     post one comment per *violating* issue, on that issue itself —
     matches the existing `_post_crash_comment` precedent of commenting
     on the subject issue directly.

2. `spawn.py`: add `closure-sweep` as a new CLI subcommand (parallel to
   existing `watchdog`), calling `gates.closure_sweep.find_violations`
   over `board(root)`'s subjects and printing/posting the result. Not
   wired into the watchdog's per-tick loop automatically in this
   phase — it's an explicit, human/orchestrator-invoked subcommand
   (`spawn.py closure-sweep`), matching how `approve_scope` is
   explicit-invoke rather than automatic. (Auto-scheduling it inside
   `roster_watchdog`'s tick is a separate decision an approver may ask
   for later — out of scope here per the scope-exceeded rule: the
   watchdog loop is not in this write set.)

3. `test_gates.py`: cases against `closure_sweep.find_violations` (or
   a lower-level pure classifier extracted for testability) covering:
   closed issue + open PR referencing it (violation), merged delivery
   PR + open issue (violation), merged phase-1 PR (plain ref) + open
   issue (NOT a violation — the side-effect case), closed issue with no
   PR (no violation, nothing to report), everything consistent (no
   violation).

## Out of scope

- Auto-closing issues or PRs.
- Scheduling the sweep automatically inside the watchdog tick.
- Sweeping PRs outside the `issue-<n>/<role>` branch-naming convention
  (a bugfix PR with an unconventional branch name referencing an issue
  by chance) — the board's subjects are the sweep's universe, matching
  the issue text's "보드의 이슈-PR 쌍."
- Cross-repo sweeps (tokenmaxxxer-core case C) — this repo's `gh`
  context only; a separate sweep per repo if ever needed.

## How it'll be known to work

`python3 test_gates.py` run once, new `closure_sweep` cases passing,
including the negative (non-violation) phase-1 case. Manually run
`spawn.py closure-sweep` against this repo's real board once and show
its output in the record (real GitHub calls, not mocked — matches the
no-mock directive: this is a real `gh` integration, not a fixture).
