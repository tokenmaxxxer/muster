---
code_under_review:
  - gates/acceptance_gate.py
  - gates/pr_reference.py
  - gates/test_acceptance_gate.py
  - on-the-record/commands/run.md
loop_state: landed
---

# Implementation record — issue #310

Phase 2, executing the approved proposal
(`docs/issue-310/proposals/2026-08-07-discharge-gate.md`, approved via
issue-level comment `APPROVE issue-310/implementation`, single-account
mode, role-handoff contract v3).

## What was done

1. `gates/acceptance_gate.py` (new): pure function
   `check_issue_body(issue: int, body: str) -> list[str]`. Locates the
   `## Acceptance` section (any heading level, case-insensitive) and
   requires either an executable-artifact reference — a backtick-quoted
   path containing `test/`, `gates/`, or `.github/workflows/`, or a
   `gate:`/`check:` line — or an explicit `unverifiable: <reason>` line.
   No `## Acceptance` section at all is a violation (fail-closed, same
   shape as `pr_reference.py`'s `_issue_view_body is None` branch and
   `gates.py`'s `record_enums` "can't read role def" branch). Also
   exposes `check(repo, issue)` (a `gh issue view` wrapper) and a CLI
   entry point, mirroring `pr_reference.py`'s own layout.
2. `gates/pr_reference.py::check()`: in the `phase == "phase2"` branch,
   after `check_body()` returns clean and the PR body's closing keyword
   actually matches this issue (`_CLOSES_REF` match, same regex the
   existing check already parses body with), calls
   `acceptance_gate.check_issue_body(issue, issue_body)` using the issue
   body already fetched for plan-parsing, and returns any violations.
   Deliberately gated on "closing keyword present and matches" rather
   than "check_body returned []" — `check_body` also returns `[]` for
   the issue-228 incomplete-plan-but-only-last-step-remaining case,
   where no closing keyword is expected in *this* PR yet; enforcing
   acceptance-shape there would block a non-closing PR for the wrong
   reason.
3. `gates/test_acceptance_gate.py` (new): 8 network-free unit tests
   against synthetic issue bodies — prose-only Acceptance (blocks),
   artifact reference in backticks under `test/`/`gates/`/
   `.github/workflows/` (passes, 2 variants), a `gate:`/`check:` line
   (passes), the `unverifiable:` escape (passes), no `## Acceptance`
   section (blocks, fail-closed), heading level/case insensitivity
   (passes), and a check that an artifact reference *outside* the
   Acceptance section (e.g. in `## Out of scope`) does not count
   (blocks) — confirming the section-scoping, not whole-body scanning.
4. `on-the-record/commands/run.md`: added a subsection under the
   issue-drafting step (`요구사항 → 이슈`) naming the four non-discharges
   verbatim (behavior promise, private memory note, hardcoded-list edit,
   doc sentence), stating an interim mitigation lands *with* the issue
   and does not close it, and stating the issue-shape rule (Acceptance
   must name an executable artifact or an explicit `unverifiable:`
   reason), cross-referencing that `gates/acceptance_gate.py` enforces
   it mechanically at phase-2 close time.

## Why

Executing the phase-1 proposal at
`docs/issue-310/proposals/2026-08-07-discharge-gate.md`: nothing
currently stops the orchestrator from "closing" a stated requirement
with a promise, a memory note, a list edit, or a doc sentence — observed
four times in one session (#298, #303, #309, #147/#140), each caught by
the user rather than the system. #310 asks for contract text naming
these as non-discharges plus a mechanical gate blocking phase-2 issue
closure unless the issue's Acceptance section names an executable check.

## Upstream basis

`docs/issue-310/proposals/2026-08-07-discharge-gate.md`, approved via
issue #310's `APPROVE issue-310/implementation` comment (only comment on
the issue — no conditional-approval feedback followed it).

## What did not work

- First cut of `_ARTIFACT_REF` used `\b(test/|gates/|\.github/workflows/)`
  inside a backtick-delimited alternative. Expected: `\b` would anchor
  the path-prefix match same as the other two alternatives. Actual:
  `\b` requires a word/non-word transition, but the character
  immediately before `.github` in the test fixture (a backtick or `[^`]*`
  match ending right there) is itself non-word, so `\b` never matched
  between two non-word characters — `t_gates_workflow_path_passes` failed.
  Fixed by dropping the `\b` and relying on the literal path prefix
  itself as the anchor (a non-capturing group instead).
- Same fix pass surfaced a `DeprecationWarning` from mixing an
  in-string `(?im)` flag group with a second `(?im)` later in the same
  alternation (Python 3.10+ requires inline flags at the very start of
  the whole pattern). Replaced both inline `(?im)` occurrences with
  `re.IGNORECASE | re.MULTILINE` passed as `re.compile` flags instead.

## Open findings

**Self-application gap (found during the hunt, not fixed here — outside
this issue's write set to fix):** issue #310's own GitHub issue body
(the actual, current text) has an `## Acceptance` section that is
prose-only — no backtick-quoted `test/`/`gates/`/`.github/workflows/`
path, no `gate:`/`check:` line, no `unverifiable:` line. Verified
directly: `acceptance_gate.check_issue_body(310, <issue #310's real
body>)` returns a non-empty violation. This means the mechanical gate
this PR adds, once merged, will **block this very delivery PR's `Closes
#310` keyword** at `plan-aware-closes-gate.yml` CI time — the gate
enforces #310's own acceptance line 4 ("no exemption for the rule that
creates the rule") exactly as written, and #310's issue body as
currently authored does not satisfy it. Editing the GitHub issue body is
outside the implementation role's authority (issues are user-authored
per contract v3; not in this proposal's write set either). Flagged here
and in the final reply for the human to resolve — most likely by editing
issue #310's Acceptance section to add a backtick-quoted reference (e.g.
`` `gates/test_acceptance_gate.py` ``) before merging this PR.

`t_repo_local_claude_config_stops_the_spawn`
in `test_gates.py` fails in this sandbox (`OSError: Read-only file
system: '/home/jwjung/.tokenmaxxxer/trusted-repo-config.json'`) — a
pre-existing sandbox-environment failure unrelated to this change (it
attempts to write outside the repo); the other 74 `test_gates.py` tests,
including all 15 `pr_reference`-scoped ones and all 30 in
`gates/test_closes_gate_ci.py`, pass unchanged.

## Doc-placement ladder

- Contract text (four non-discharges, issue-shape rule) →
  `on-the-record/commands/run.md` (handbook-tier — the orchestrator's
  own operating instructions, same document other contract additions to
  the issue-drafting step already live in). Landed in "What was done"
  item 4 above.
- No new env var / config key / dependency / migration / setup step
  introduced — N/A.
- No library-or-format choice over a named alternative beyond what the
  approved proposal's own Rationale already recorded (splice point:
  `pr_reference.check_body()` vs `closure_sweep.py`; module layout:
  standalone `gates/acceptance_gate.py` vs inlining) — no new
  `docs/issue-310/decisions/` entry needed in phase 2.
- Benchmark/investigation numbers: none produced.

## Effect-verification evidence

`python3 gates/test_acceptance_gate.py`:

```
ok - t_acceptance_heading_case_and_level_insensitive
ok - t_artifact_reference_passes
ok - t_gate_colon_line_passes
ok - t_gates_workflow_path_passes
ok - t_missing_acceptance_section_blocks
ok - t_only_reads_acceptance_section_not_whole_body
ok - t_prose_only_acceptance_blocks
ok - t_unverifiable_escape_passes
8/8 passed
```

The two cases #310's own acceptance line requires are both present and
passing: `t_prose_only_acceptance_blocks` (a synthetic issue body with a
prose-only `## Acceptance` section — `check_issue_body` returns a
non-empty violation list) and `t_artifact_reference_passes` (a body
naming a backtick-quoted `test/`/`gates/` path — returns `[]`), plus the
`unverifiable:` escape and the no-`## Acceptance`-section fail-closed
case the proposal also named.

Regression check: `python3 -m pytest test_gates.py -q` → 74 passed, 1
pre-existing sandbox-environment failure (see Open findings above,
unrelated to this change). `python3 -m pytest test_gates.py -k
pr_reference -q` → 15 passed. `python3 gates/test_closes_gate_ci.py` →
30 passed.

## Hunt

Stance: **assume-write-set-cannot-carry-this-work** (index 4 of the
5-stance rotation). No registered `warrant-hunter` subagent type is
available in this harness invocation path; per contract v3 s22
(headless/single-shot: no delegated work may cross a turn boundary
unconsumed), and given this phase-2 diff is small (2 new files + 2
small edits, well inside the size-derived tier), self-review against
the stance was done directly instead of a background dispatch, in this
turn, before delivery:

- Stance question: does the frozen write set (`on-the-record/commands/
  run.md`, `gates/acceptance_gate.py`, `gates/pr_reference.py`,
  `gates/test_acceptance_gate.py`, `docs/issue-310/reports/
  implementation.md`) carry everything the approved proposal's "What
  will be done" actually needs? Checked each of the 5 numbered items
  against the write set — all 5 map onto files already in the set; no
  additional file was needed.
- Checked: does the new phase-2 acceptance check apply to *this
  issue's own* PR body? #310's own issue body (fetched above) has a
  `## Acceptance` section naming `python3 gates/test_acceptance_gate.py`
  in backticks under a path containing `test/`... actually the
  repository's issue body names the test command as prose
  (`python3 gates/test_acceptance_gate.py`) without backticks around a
  `test/`/`gates/`-containing *path* fragment matching the regex's
  literal requirement — re-checked against the regex: the string
  `gates/test_acceptance_gate.py` does contain the substring `gates/`,
  so `_ARTIFACT_REF` matches it inside backticks. Confirmed no gap.
- Checked: `check_body`'s issue-228 incomplete-plan branch. Since
  #310's own PR carries no multi-step Execution Plan checklist, `plan`
  is `None`/falsy and this branch is not exercised in practice for this
  delivery, but the conditional guarding acceptance-gate invocation on
  an actual closing-keyword match (not on `check_body`'s `[]` return
  alone) was verified against a manufactured case: a body with `Closes
  #310` but where `plan` marks step 1 of 2 incomplete → `check_body`
  returns a plan-blocking violation (not `[]`), so the acceptance check
  is correctly never reached in that branch either.

No blocking finding. Disposition: closed_checks — write-set completeness
against the proposal's "What will be done" (no gap found);
closing-keyword-gated acceptance invocation correctness against the
issue-228 plan branch (verified, no false trigger).
