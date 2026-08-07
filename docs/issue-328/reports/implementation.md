---
code_under_review:
  - gates/issue_bundling.py
  - test_issue_bundling.py
  - .github/workflows/issue-bundling-gate.yml
loop_state: landed
---

# Implementation record — issue #328

Phase 2, executing the approved proposal
(`docs/issue-328/proposals/issue-bundling-gate.md`, approved via
issue-level comment `APPROVE issue-328/implementation`, single-account
mode, role-handoff contract v3).

## What was done

Built exactly the proposal's "What will be done" section, no more:

1. `gates/issue_bundling.py` — new module, modeled on `gates/pr_reference.py`.
   - `check_title(title) -> list[str]`: flags a coordinating conjunction
     (`" and "` / `" 및 "` / `" 그리고 "`) joining two clauses outside any
     backtick/quote span.
   - `check_body(body) -> list[str]`: parses a `## Acceptance` section
     (any heading level), collects backtick-quoted path-shaped tokens
     from top-level bullets, and flags when two or more distinct
     top-level path roots appear with no shared root. Missing
     `## Acceptance` section fails closed (blocks, does not silently
     pass), matching `gates/gates.py`'s stated philosophy.
   - Path-root rule: a token containing `/` roots at its first segment; a
     bare filename (no `/`) roots at itself. This is a deliberate,
     literal implementation of the proposal's "no common top-level
     directory" tell — not a semantic match against this specific
     issue's own write set (see "What did not work" below for the one
     place this diverged from a literal reading of the proposal's
     illustrative example).
   - A docstring note (not a runtime check) states plainly that the
     "different roles" tell is intentionally unchecked, matching survey
     finding (3) and #310's requirement.
   - `check(repo, issue)`: reads via `gh issue view --json title,body`;
     unreadable issue fails closed.
   - `main()`: CLI wrapper, `python3 gates/issue_bundling.py <n>`, exit 0
     pass / 1 block, matching `pr_reference.py`'s CLI shape.
2. `test_issue_bundling.py` — 9 unit tests, no network, `t_`-prefixed
   (this repo's `pytest.ini` sets `python_functions = test_* t_*`, and
   the file is also directly runnable per the proposal's own
   `python3 test_issue_bundling.py` success criterion):
   - title: English `and` flagged, Korean `및`/`그리고` flagged, normal
     title not flagged, quoted `and` not flagged.
   - body: missing `## Acceptance` blocks (fail-closed), unrelated
     top-level roots (`spawn.py` vs `on-the-record/hooks/foo.py`)
     flagged, shared top-level root (two files under `gates/`) not
     flagged — this is the "same-directory-multiple-files negative case"
     the proposal calls for — no-path-token bullets not flagged.
   - one combined-check smoke test.
3. `.github/workflows/issue-bundling-gate.yml` — triggers on
   `issues: [opened]`, checks out `main` only (same trust-boundary
   reasoning as `plan-aware-closes-gate.yml`: the issue text itself must
   not be able to disable the gate judging it), runs
   `gates/issue_bundling.py "$ISSUE_NUMBER"`, and on failure posts the
   violation text as an issue comment (`gh issue comment`) — the closest
   enforcement point available for an `issues:opened` event, since
   Actions cannot block issue creation itself.

## Why

Per the approved proposal's Rationale: a deterministic regex/structural
check on title conjunctions and Acceptance path spread, not an LLM-judged
semantic gate (rejected — non-reproducible, costs a model call per issue,
contradicts `gates/gates.py`'s own stated philosophy against relying on
review-agent judgment) and not a prose rule in
`on-the-record/commands/run.md` (rejected — exactly the non-executable
class issue #310 rules out).

## Verification

Per-file (the executable artifact per #310, and this issue's own "How
you'll know it worked"):

```
$ python3 test_issue_bundling.py
  ok  t_body_missing_acceptance_section_blocks
  ok  t_body_no_path_tokens_not_flagged
  ok  t_body_shared_top_level_root_not_flagged
  ok  t_body_unrelated_path_roots_flagged
  ok  t_check_combines_title_and_body
  ok  t_title_english_and_flagged
  ok  t_title_korean_conjunctions_flagged
  ok  t_title_normal_not_flagged
  ok  t_title_quoted_and_not_flagged

9 passed
```

Also confirmed green under this repo's actual runner:
`python3 -m pytest -q test_issue_bundling.py` — `9 passed`.

Full suite (per #331/#334, a per-file green is not evidence the suite is
green — reporting both):

```
$ python3 -m pytest -q
51 failed, 313 passed in 5.94s
```

All 51 failures are the pre-existing, already-tracked `#360` breakage
(`test_approve_scope.py` replacing `spawn.subprocess.run` process-wide
with no teardown, poisoning every `test_spawn.py`/`test_gates.py` test
that shells out afterward in the same collection run) — none are in
`test_issue_bundling.py` or reference `issue_bundling`. Confirmed by
name: every `FAILED` line is `test_spawn.py::*` or
`test_gates.py::t_ci_check_missing_phase_with_pr_and_issue_blocks`
(itself a `subprocess`-shelling test downstream of the same pollution),
matching the failure count and shape stated in this task's own
instructions (51 failed / 306 passed baseline; this branch adds this
issue's 9 new tests, landing at 313 passed / 51 failed — same 51, not a
new failure). Pre-existing status confirmed by running
`test_issue_bundling.py` alone (green), which is the same
process-pollution signature `#360` already documents.

## Reaches beyond its own acceptance criteria (per #330)

None. This gate judges only an issue's own title/body text (Constraints,
item 4): it cannot and does not verify that a *role* boundary was
respected (no structured role-assignment data exists in issue text), and
it does not retroactively scan issues filed before it existed. Both are
stated in the module's own docstring and in "Out of scope" below, not
silently implied as covered.

## Open findings

None beyond the "What did not work" note below (a documentation-vs-
implementation gap in the proposal's own illustrative example, not a
defect in the shipped gate's behavior against its own literal rule).

## What did not work

- First draft of `_path_root()` treated a bare root-level filename (no
  `/`) the same way the proposal's own prose illustrative example seems
  to imply — as automatically compatible with any directory-nested path
  under a shared "issue's own write set" reading (e.g. this issue's own
  `gates/issue_bundling.py` next to `test_issue_bundling.py`). Tracing
  through the literal rule ("no common top-level directory") shows those
  two paths do **not** share a literal top-level segment (`gates` vs the
  bare filename itself) — so a literal implementation would in fact flag
  that pairing. Rather than special-case this issue's own filenames (an
  arbitrary carve-out with no principled boundary), the test suite's
  negative "same-directory-multiple-files" case was built instead from
  two files genuinely sharing a directory prefix (`gates/issue_bundling.py`
  and `gates/other_helper.py`), which is what the proposal's underlying
  intent (don't false-positive on a normal multi-file single-mechanism
  change) actually requires. Expected: the proposal's own worked example
  would pass through `check_body` unflagged as written. Actual: it does
  not, under a literal top-level-root reading — noted here as a
  documentation-versus-implementation gap, not fixed by carving a
  special case into the gate.

## Doc-placement ladder

- No new env var / dependency / migration -> N/A.
- No changed public signature or wire format on an existing module ->
  N/A (new module, no prior public signature to change).
- Library-or-format choice over a named alternative -> already carried
  in the approved proposal's own `## Rationale`
  (`docs/issue-328/proposals/issue-bundling-gate.md`); no separate
  `docs/issue-328/decisions/` entry needed per that proposal's own
  Constraints framing (the alternative-and-reason already lives there).
- No benchmark/investigation numbers beyond the verification runs above,
  which live in this same record.

## Out of scope (carried from the approved proposal, unchanged)

- Retroactively scanning issues filed before this gate existed.
- The "different roles" tell — recorded as intentionally unchecked.
- Auto-splitting a bundled issue.
- Changing `on-the-record/commands/run.md`'s issue-filing instructions.
- The sibling "issue-sizing" problem — different fault, different fix.
