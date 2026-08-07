# Survey — issue-310

## Scope of the survey

issue-310 is about this repo (`on-the-record`, the orchestrator) itself:
how a user-stated requirement gets discharged. No product-shaped UI/UX
surface exists here, so the scout protocol's product-scouting branch does
not apply; the comparable "best-in-class" is this repo's own existing
mechanical gates — they are the prior art for "a rule that isn't just a
sentence." Scouting = reading those gates, not a web sweep.

## What already exists

- `on-the-record/commands/run.md` — the orchestrator's operating
  instructions. Line ~18 already says the orchestrator is a "대필자"
  (ghostwriter) who registers only user-confirmed issues via
  `gh issue create`; line ~306 says `gh issue close` runs only after
  explicit user confirmation, and `closure_sweep.py` "여전히 감지만
  한다" (still only detects). Nowhere does it require an issue's
  acceptance criteria to name an executable artifact — the four
  non-discharges named in #310 are not named anywhere here as
  non-discharges.
- `gates/pr_reference.py` — `check_body()` gates PR *wording*: phase-1
  PRs must plainly reference `#<issue>` (no Closes/Fixes/Resolves,
  contract v3 s19); phase-2 PRs must carry `Closes/Fixes/Resolves #n`,
  and additionally, per issue-228, refuses that keyword if the issue's
  own checklist plan (`flows._plan_from_body`) still has incomplete
  non-final steps. This is the closest existing precedent to what #310
  asks for — a merge-time text gate keyed off issue/PR body content —
  but it checks *presence of a closing keyword*, never *what the issue's
  acceptance criteria actually say*.
- `gates/closure_sweep.py` — board-wide sweep comparing issue state vs.
  PR state (`OPEN_PR_ON_CLOSED_ISSUE`, `MERGED_DELIVERY_ISSUE_OPEN`).
  Report-only, "위반이 있는 이슈마다... 코멘트" — never blocks, never
  reads issue *content* beyond state.
- `gates/gates.py::record_enums()` — the direct precedent named in the
  issue's item 3 ("mirroring how record-fields-gate gates record
  writes"): it reads a changed `docs/issue-<n>/reports/<role>.md`
  record's frontmatter, and blocks when a declared field's value isn't
  in the role's declared enum (`roles/<role>.json`'s `record_fields`).
  Same shape needed here: read a record/issue field, check it against a
  declared requirement, block if absent or non-conforming — "unreadable
  is not the same as passing" is the standing principle
  (`record_wellformed_in`, `writeset`, `parse_new_deps` all fail closed
  on unparseable input, never silently pass).
- `on-the-record/hooks/deliverable-guard.sh` — blocks the orchestrator
  session itself from writing to a target repo's `src/`, `test/`,
  `docs/` trees directly; the enforced discharge path is already
  "draft the issue, spawn the role" for *code*. #310 is the same rule
  applied to *closing* the issue that resulted.
- No file in this repo currently enumerates "promise / memory note /
  hardcoded-list edit / doc sentence" as non-discharges, and no gate
  reads an issue's Acceptance section at all.

## Gap

1. **Contract text gap**: nothing in `on-the-record/commands/run.md` (or
   any doc this repo ships) names the four non-discharges from #310's
   observed instances, or states that an interim mitigation lands *with*
   the issue rather than closing it.
2. **Issue-shape gap**: nothing requires an issue's Acceptance section to
   name an executable artifact (test path, gate name, CI job) rather
   than prose.
3. **Mechanical gap**: no gate reads issue Acceptance content at
   phase-2-close time. `pr_reference.check_body()` is the natural splice
   point — it already gates the phase-2 closing keyword and already
   fetches the issue body (`_issue_view_body`) for plan-parsing
   (issue-228's precedent for reading issue content, not just PR
   content).

## Alternatives visible in the existing code

- Extend `closure_sweep.py` (board-wide, post-hoc, comment-only) vs.
  extend `pr_reference.check_body()` (merge-time, blocking, PR-scoped).
  `closure_sweep` fits *detecting* drift across the whole board;
  `pr_reference` fits *blocking* a specific phase-2 close before it
  happens, which is what #310 item 3 asks for ("gate issue closure").
- A new standalone `gates/acceptance_gate.py` module (mirroring
  `record_enums`'s standalone-function shape in `gates.py`) vs. inlining
  the check into `pr_reference.py` directly. A separate module keeps the
  pure/network-free logic unit-testable the same way `classify()` in
  `closure_sweep.py` and `dep_names()` in `gates.py` are — network-free
  functions with `_pr_view`/`_issue_view` thin wrappers around them.

These are recorded in the proposal's Rationale, not decided here.
