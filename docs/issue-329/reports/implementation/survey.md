# Survey — issue #329 (issue sizing has no effort axis)

## Where issue drafting currently happens

`on-the-record/commands/run.md` step 1 ("요구사항 → 이슈", lines 17-32) is
the only place an issue draft is produced. It already carries a mandatory
skill-evaluation sub-step and (step 2, lines 33-47) a mandatory lead-role
classification. Neither step mentions size or effort. Nothing in this file,
or anywhere else in the repo, asks the orchestrator to estimate how big the
resulting session will be, or to split before filing.

The only body-syntax the orchestrator writes into an issue today is the
`## 실행 계획` block (lines 236-284), parsed by `ledger/collect.py` /
`gates/closure_sweep.py`. That block records *step ordering across roles*,
not size of any one step. It is optional for single-role issues — exactly
the case #329 is about (one coherent, correctly-scoped unit that is still
too large for one session).

## Where mechanical gates live today

`gates/` holds deterministic, LLM-free checks wired into CI:
`gates/ci.py` is the entry point, dispatching to `gates/gates.py`
(write-scope/protected-path/deps/record checks) and `gates/pr_reference.py`
(issue-reference / Closes-keyword checks). `gates/closure_sweep.py` parses
the `## 실행 계획` block. Precedent: `gates/pr_reference.py` and
`gates/ci.py`'s `--pr`/`--autodetect` path both call `gh pr view --json ...`
to pull PR-level facts (head branch, body) that only exist on GitHub, not in
the local checkout — the same shape needed to read a PR's diff stats.
`gates/test_closes_gate_ci.py` is the existing pattern for a pytest file
that exercises a gate's logic against fixtures, without hitting the network.

There is no gate today that reads PR/session size (additions+deletions,
files changed, or `spawn.py` session duration) at all. `ledger/collect.py`
aggregates board state but does not compute or report diff size per PR.

## What proxy for "session size" already exists

- `gh pr view <n> --json additions,deletions,changedFiles` — GitHub-computed
  diff stat per PR, free, no LLM, same call shape `pr_reference.py` already
  uses.
- `spawn.py` writes a per-session log (referenced in `docs/handbooks/on-the-record.md`
  and issue #192's fix) that could time a session, but issue #192's fix
  already addresses log-overwrite, not session-length measurement — that is
  a heavier, less direct proxy than PR diff size for catching *this*
  defect, since a long session that produces a small diff (heavy
  exploration) is a different problem than a small session producing a
  huge diff (correctly-scoped-but-oversized issue, #329's exact complaint).

## Adjacent, already-filed issues (no overlap, but shared root)

- **#328** (bundling): title needs "and" / unrelated code paths in one
  issue. Different fault — a single-mechanism issue can be correctly
  bundled (or not bundled at all) and still be oversized; #329 is about
  effort magnitude on one coherent unit, independent of whether topics were
  merged. No shared fix surface: #328's tell is topic-relatedness, #329's
  is line/session-time magnitude.
- **#310** (acceptance discharge): sets the constraint this proposal must
  satisfy — an executable artifact, not prose.
- **#325** (issues filed then dropped) and **#298** (orchestrator is the
  only unenforced actor): both point at the same structural gap this issue
  sits in — orchestrator-side procedural steps (step 1's issue drafting
  among them) currently have no CI-checkable trace. #329 is scoped to the
  sizing sub-problem only; it does not attempt the general orchestrator
  enforcement surface #298 asks for.

## Skip-condition check (scout directive)

This issue is process/prose-plus-gate work with a real design decision open
(where to draw the size threshold, and what mechanical proxy to check) —
neither scout skip condition (pure bugfix / no design decision open)
applies. Scouting was still skipped: this is an internal process-tooling
change to `on-the-record` itself (no product-shaped or externally-comparable
surface — there is no "category" of competing issue trackers whose sizing
heuristics are a meaningful bar for an internal orchestrator directive).
The written record of that judgment is this line.
