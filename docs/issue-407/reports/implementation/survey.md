# Survey — issue-407

## Where the batch-rhythm behaviour actually lives

`spawn.py` (repo root, the orchestrator engine) contains no merge/land/batch
function — grep for `merge|land|batch` returns nothing. Merging is not code;
it is a `gh pr merge <n> --merge --delete-branch` call the orchestrator issues
itself, per `on-the-record/commands/run.md` (the slash-command prompt loaded
each turn). Step 6 of that file (lines 189-234) is where the behaviour #407
describes is written down:

- Lines 189-193 ("하지 않는 것"): the *board* (a separate rendering step)
  never acts — it only aggregates. Actual accept/merge/reject stays "항목별로"
  (per item) in step 6. So the protocol's own text already claims per-item
  landing.
- Lines 196-208: when 2+ items are waiting **on a human decision**, they are
  rendered as one globally-numbered queue in that turn's reply. This is a
  batched *render* of a decision list, not a batched merge — line 229 shows
  merge itself firing per accepted item (`gh pr merge <n> ...`).
- Nothing in run.md computes readiness (checks green + record present +
  approval recorded) as a standalone, callable check. Readiness is implicit
  in whatever the orchestrator notices when it re-reads `gh` state at the
  top of a turn — i.e., readiness is only ever evaluated turn-locally, never
  between turns and never per-PR on demand.
- Nothing in run.md or gates/ requires a "block" to name what it blocks or
  which items it covers when the stop is not about a specific PR (the #341
  requirement). The #398 incident (blanket halt of 19 merges over a suite
  collection failure that only 관련 있는 PRs could have caused) is exactly
  the gap: no script exists that could have told the orchestrator "only PRs
  touching gates/ are actually implicated."

## gates/ — existing machine-gate pattern to build on

`gates/closure_sweep.py:35` (`classify(issue_state, pr_state, pr_body,
issue)`) is the precedent for what a landing-readiness check should look
like: a pure, network-free function taking already-fetched `gh` state and
returning a classification, wrapped by a thin `main()` that does the `gh`
calls (see `_issue_view`/`_pr_view_state_body` at lines 49-60). No
equivalent exists for "is this PR ready to land" — `gates/pr_reference.py`
checks issue/PR body cross-references only, `gates/spawn_coverage.py`
checks which open issues lack a spawned session, `gates/flows.py` reports
stage-per-flow for display, `gates/skip_gate.py` is unrelated (skip-record
enforcement).

## #398 (module-name collision) — confirmed, boundary set

`gates/test_gates.py` and root `test_gates.py` share a bare module name
with no `__init__.py`/package marker under `gates/`, so pytest's default
rootdir-relative import breaks collection when both are gathered in one
run. Reproduced today:

```
$ python3 -m pytest -q --ignore=gates
........................................................................ [ 74%]
........................................................................ [ 93%]
.....................F.                                                  [100%]
1 failed, 385 passed in 19.34s
```

The one failure (`test_spec_index.py::t_baseline_repo_passes`, a stale
`docs/specs/reconciled-index.md` hash for `docs/handbooks/operations.md`)
is pre-existing on `origin/main` (branch is clean, at `origin/main` tip,
before any change in this session) and unrelated to #407 or #398. #398 is
open and explicitly in flight (per this session's invocation prompt) —
fixing the collision itself (e.g. renaming/packaging `gates/test_gates.py`)
is #398's write set, not this issue's. What #407 needs from #398 is only
the fact that it demonstrates the failure mode: a real defect scoped to
`gates/` collection, wrongly generalized into a stop on all 19 pending
merges regardless of whether they touched `gates/`.

## Boundary check (searched, recorded)

- **#324** (`docs/specs/parallel-conflict-methodology.md:77`, listed
  out-of-scope there): serialization at *spawn* time — independent role
  sessions not started concurrently. #407 is serialization at *landing*
  time, after sessions already finished. No overlap in write set found by
  grepping `docs/decisions/`, `docs/specs/` for "324".
- **#341**: `docs/issue-341/` exists (proposal + implementation report) but
  is not cross-referenced from any other decisions/specs file (grep found
  no other hits). #407 draws on #341's principle (a block must name its
  enforcer/scope) as a requirement on the landing mechanism, not a
  duplicate of #341's own delivery.
- **#390**, **#374**: no `docs/decisions/` or `docs/specs/` file references
  either number (grep over both directories, zero hits beyond incidental
  numeric-line matches in unrelated survey docs). Both are cited in #407's
  own issue text as adjacent-not-overlapping; nothing on disk contradicts
  that.
- No Stop hook exists yet. `on-the-record/hooks/hooks.json` wires exactly
  three events: `SessionStart` → `self-update.sh`, `UserPromptSubmit` →
  `directive.sh`, `PreToolUse` (Write|Edit|MultiEdit|NotebookEdit) →
  `deliverable-guard.sh`. The 2026-08-07 comment on #298 (cited in this
  session's invocation) describes a Stop hook capability that is not yet
  wired here — it does not exist in this repo today.

## What this rules in for the write set

- `gates/landing_readiness.py` (new): pure per-PR readiness classifier
  (checks green / record present / approval recorded → READY, or BLOCKED
  with a named reason and the exact scope it covers), following the
  `closure_sweep.classify` shape so it is unit-testable without `gh`.
- `gates/test_landing_readiness.py` (new): tests the classifier, including
  a scenario modeled on the measured #398 incident (a suite-collection
  failure scoped to `gates/`-touching PRs blocks only those, not the
  whole open set).
- `on-the-record/commands/run.md` (edit, step 6 and its surrounding
  prose): require any stop that is not about one specific PR's own checks
  to cite `gates/landing_readiness.py`'s scope output, and make explicit
  that merge relay per accepted item is not deferred behind the
  decision-queue render.

No new dependency, no new env var, no migration.
