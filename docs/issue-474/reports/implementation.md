---
code_under_review:
  - gates/repo_scope.py
  - test_repo_scope_gate.py
  - docs/specs/survey-conventions.md
  - gates/acceptance_gate.py
  - gates/test_acceptance_gate.py
  - gates/test_setup_failure_propagates.py
  - docs/issue-474/decisions/416-provenance-and-empty-state.md
  - gates/gates.py
  - gates/ci.py
  - gates/test_recurrence.py
  - spawn.py
  - gates/accumulation.py
  - gates/test_accumulation.py
  - docs/specs/enforcement-boundary.md
  - on-the-record/commands/run.md
loop_state: landed
---

# implementation — issue-474 (Batch D: provenance/recurrence gates)

Phase-1 proposal approved via `APPROVE issue-474/implementation` (single-account
mode, exact-string issue comment by JiwonJung94, an approvers.md account),
posted on issue #474.

Upstream basis: `docs/issue-474/proposals/2026-08-08-batch-d-provenance-and-recurrence-gates.md`.

## What was done

- **#415** — `gates/repo_scope.py::check_repo_scope(text: str) -> list[Violation]`:
  flags a capability/contract absence sentence (fixed English/Korean
  phrase list) with no adjacent repo-scope phrase (`as of <sha>`, `in
  <repo>`, `checked <repo path>`), skipping sentences that already carry
  a file-path anchor. `test_repo_scope_gate.py` (repo root, per #415's own
  approved proposal) — three fixtures: unscoped flags, scoped passes,
  file-anchored passes. `docs/specs/survey-conventions.md` created with
  the "Capability and contract claims are repo-scoped" section.
  **Ceiling, restated per the survey's requirement**: this mechanism does
  not verify cross-repo truth — it only flags a missing scope statement,
  never judges whether the claim itself is correct. **Narrower gap
  (warrant-hunt-found, #415's own record)**: the absence-phrase list is
  fixed and closed; a synonym/contraction outside it ("isn't
  implemented") never reaches the scope check at all and passes silently
  — not because it is scoped, but because it was never recognized as an
  absence claim.
- **#416** — extended `gates/acceptance_gate.py::check_issue_body`: any
  `## Acceptance` section with an executable-artifact reference (and not
  exempted by `unverifiable:`) now additionally requires an `empty
  state:` line and a `provenance: executed-live|executed-unit|read` line.
  `gates/test_acceptance_gate.py` — added 4 new cases and updated 4
  pre-existing pass-fixtures to carry the new required fields (they
  tested other axes and would otherwise now fail on the new checks).
  `gates/test_setup_failure_propagates.py` — builds a synthetic harness
  shaped like `tests/run-orchestrate-tests.sh`'s setup step, breaks it,
  and asserts the harness's own exit code goes nonzero.
  `docs/issue-474/decisions/416-provenance-and-empty-state.md` (path
  deviation, see below) states the presence-not-truth ceiling and which
  of #416's four "what needs deciding" items this answers (1 partially,
  2 yes, 3 yes, 4 deferred).
- **#419** — `gates/gates.py`: added `subprocess_call_shape_divergence`
  (whole-tree `ast`-based scan for same-command `subprocess`/`gh` calls
  whose semantic flag sets diverge, e.g. `-f` vs `-X GET`) and
  `sibling_mention_check` (a `# sibling: <name>` comment above a
  def/class requires the changed record's `## Siblings` section to name
  it), both registered in `ALL`. `gates/ci.py::check()`: wired both into
  the same non-`--closes-only` chain — `subprocess_call_shape_divergence`
  runs unconditionally, `sibling_mention_check` runs when `pr` is given
  (fetches the PR's own record text via `_fetch_ref_file`, mirroring
  `role_scope`'s `pr is not None` gating). `gates/test_recurrence.py`
  (path deviation, see below): fixtures per the proposal's item 4 — #388
  shape flags, identical flag sets pass; marked-and-mentioned pair
  passes, marked-and-unmentioned fails, unmarked returns `[]`.
  `spawn.py`: applied `# sibling: core_version` above `core_root` and `#
  sibling: core_root` above `core_version` — the real pair the issue
  names.
  **Ceiling, restated as a count against #419's four named instances**:
  this mechanism would catch instance 1 (#388's argument-shape
  divergence) outright, and instance 2 (#313's `core_root`/`core_version`
  miss) only *after* the marker is applied (now applied to the real
  pair, demonstrated above, not a synthetic-only fixture). Instances 3
  (rule re-derived in three trigger shapes) and 4 (migrated format, stale
  readers) are not caught and are named as such.
- **#424** — new `gates/accumulation.py::check_accumulation_claim(work:
  Path, body: str) -> list[str]` (signature deviation, see below):
  requires a `## Accumulation` line in a proposal body when the working
  tree touches either of two named recurrence-prone shapes — shape 1 (a
  changed `.py` file already carrying 3+ inline `subprocess`/`gh` calls,
  modeling `gates/ci.py`'s real 6-call-site instance) or shape 5 (a
  changed `roles/*.json` file, modeling the 43-file instance).
  `gates/accumulation.py::check_accumulation_claim` — presence-only
  check, same ceiling style as #416's `provenance:`. `gates/test_accumulation.py`:
  fixture reproducing shape 1 (a 7th inline `gh` call with no heading
  must flag; the same fixture with the heading present must not; a
  change touching neither shape returns `[]` regardless of body text) —
  plus a shape-5 fixture and a fail-closed regression test added after
  the before-landing hunt (see Open findings).
- `docs/specs/enforcement-boundary.md`: added rows for `repo_scope.py`
  and `accumulation.py` (both `repo-local` — neither is wired into any
  zero-install preflight or `contract-guard.sh`), required by
  `gates/test_boundary.py::t_all_gates_modules_recorded` (#441) for any
  new `gates/*.py` module.
- `docs/specs/reconciled-index.md`: regenerated via `python3
  gates/spec_index.py --update` after editing `on-the-record/commands/run.md`
  (required by `gates/spec_index.py`'s own hash-drift check).
- `on-the-record/commands/run.md`: four new subsections before "## 하지
  않는 것" (following Batch A's placement precedent, `git show 9554c53`)
  — one per row (#415 repo-scope convention, #416 provenance/empty-state
  fields, #419 recurrence-check conventions including `# sibling:`
  syntax, #424 the `## Accumulation` line convention).

## Rationale for deviations

- **`docs/issue-474/decisions/416-provenance-and-empty-state.md` instead
  of the proposal's literal `docs/issue-416/decisions/provenance-and-empty-state.md`.**
  `board-gate.sh` (contract v3 s10) mechanically refuses any
  `docs/issue-416/**` write from a branch other than `issue-416/<role>` —
  this delivery runs on `issue-474/implementation`. The decision content
  is unchanged; only the path moved to this batch's own issue tree, with
  the #416 issue number kept in the filename and body for discoverability.
- **`accumulation.check_accumulation_claim(work: Path, body: str)` instead
  of the proposal's literal `check_accumulation_claim(body: str)`.** The
  proposal's own item 4 text requires detecting whether a change touches
  either named recurrence-prone shape (inline subprocess/gh call-site
  accumulation, or a `roles/*.json`-style repeated one-line edit) — that
  detection needs the working tree, not just the proposal text. A
  `body`-only signature cannot see the diff it is meant to judge, so
  `work: Path` was added as the first parameter.
- **`gates/test_recurrence.py` instead of the proposal's literal
  `gates/test_gates.py`.** The proposal text (and #419's own adopted design)
  names `gates/test_gates.py` for the new fixtures, but this repo already
  has `gates/test_duplicate_test_basenames.py`, whose own docstring records
  that `gates/test_gates.py` is exactly the collision shape (#398) the
  `duplicate_test_basenames` gate exists to catch — landing a file with that
  literal name would make this batch's own delivery fail the already-shipped
  `duplicate_test_basenames_gate` check. Followed #398's own precedent
  (`test_duplicate_test_basenames.py` naming) and used `gates/test_recurrence.py`
  instead — same content/fixtures the proposal specifies, different
  filename only.

## What did not work

- Wrote `gates/accumulation.py`'s `changed`-file detection to fall back
  silently to `[]` whenever its `git diff`/`git ls-files` subprocess
  calls failed (e.g. `work` not a git repo) — expected this to only ever
  hit the "no changes" case in practice; the before-landing warrant hunt
  reproduced that a non-git `work` directory makes the check silently
  report no violations even when a real shape-1/shape-5 pattern is
  present. Replaced with an explicit fail-closed branch when both `git
  diff` calls return nonzero, and again when the `git ls-files` fallback
  fails.

## Open findings

- **Resolved.** Before-landing warrant hunt (stance 2 of the rotation,
  `docs/reports/2026-08-08-hunt-issue-474-implementation.md`): found
  `check_accumulation_claim` fails open (silently returns `[]`) when its
  `git` subprocess calls fail rather than failing closed. Fixed in
  `gates/accumulation.py` (see "What did not work" above) and covered by
  a new regression test,
  `gates/test_accumulation.py::t_non_git_directory_fails_closed_not_silently_empty`.
  resolved_findings: hunt dated 2026-08-08, stance 2 (malformed-input
  goes silent), fix committed in this same delivery — finder re-clears on
  next hunt if it disagrees.

## Resolution path

N/A — the one open finding above is resolved and closed in this same
delivery; no unresolved findings remain.

## closed_checks

- `python3 test_repo_scope_gate.py` — 3/3 passed.
- `python3 gates/test_acceptance_gate.py` — 12/12 passed.
- `python3 gates/test_setup_failure_propagates.py` — 2/2 passed.
- `python3 gates/test_accumulation.py` — 5/5 passed (includes the
  post-hunt fail-closed regression test).
- `python3 -m pytest gates/test_recurrence.py -k "subprocess_call_shape_divergence or sibling_mention" -v` — 5 passed.
- `python3 -m pytest -q --ignore=gates` (repo root) — 473 passed, 1 failed
  (`test_gates.py::t_rulebook_version_is_recorded`, asserts the local
  checkout is not dirty — fails only because this delivery's changes were
  staged-but-uncommitted at test time; confirmed via `git stash` that it
  passes on a clean tree, and will pass once this record's commit lands).
- `python3 -m pytest -q` run from inside `gates/` — 123 passed (0
  failed), including `gates/test_boundary.py::t_class_b_disposition_rows_cited`
  (unmodified, stays green) and `gates/test_boundary.py::t_all_gates_modules_recorded`
  (green after the `enforcement-boundary.md` rows were added).
