files:
- gates/pr_reference.py
- gates/test_closes_gate_ci.py
- test_gates.py

Skip condition: scouting skipped — pure bugfix (regex keyword-set correction
to match GitHub's own documented closing-keyword behavior; the target set of
9 keywords is fixed externally, not a design choice this session makes). See
`docs/issue-280/reports/implementation/survey.md`.

## Request

`gates/ci.py --closes-only`'s closing-keyword detection matches only
`closes|fixes|resolves`, three of GitHub's nine keyword inflections. A
phase-1 PR body reading "Fixed #19" passes the required check with zero
approval, and GitHub auto-closes the issue on merge — defeating the
contract's phase-1/phase-2 approval gate with ordinary commit English, no
adversary needed. Match GitHub's full closing-keyword set
(close/closes/closed, fix/fixes/fixed, resolve/resolves/resolved)
case-insensitively in both the phase-1 `--closes-only` path and the phase-2
`check_body` path, and add regression tests for every spelling.

## Constraints

- Single source of truth: both gate surfaces (`gates/ci.py`'s
  `_closes_ref_for_issue`, `gates/pr_reference.py`'s `check_body`) already
  share one regex (`pr_reference._CLOSES_REF`) — the fix must stay a single
  edit to that regex, not two parallel keyword lists that can drift apart
  again.
- No behavior change to anything the current tests already pin: existing
  `closes`/`fixes`/`resolves` matches, the fenced-quote case, and the
  multi-issue `.finditer()` case must keep passing unmodified.
- Case-insensitivity, word-boundary discipline (`\b`), and the `#(\d+)`
  capture group shape must be preserved — downstream code reads
  `m.group(1)` (keyword) and `m.group(2)` (issue number) positionally.

## Rationale

Considered keeping the three-keyword regex and adding a second explicit
regex for the six missing forms (`close|closed|fix|fixed|resolve|resolved`),
run as an additional check. Rejected: two regexes checked independently
would require both call sites to combine two match objects instead of one,
doubles the surface for the two regexes to drift out of sync on a future
edit (the exact failure this issue reports — an incomplete list silently
diverging from GitHub's actual behavior), and gains nothing over one regex
whose alternation already expresses all nine forms compactly via optional
suffixes (`close[sd]?`, `fix(?:e[sd])?`, `resolve[sd]?`).

## What will be done

- Widen `pr_reference._CLOSES_REF` to match all nine GitHub closing-keyword
  inflections, case-insensitively, keeping the existing two capture groups.
- Verify the widened regex against all 9 spellings x 3 case variants, plus
  the existing negative cases (`unclosed #19`, `prefixes #19` — word-boundary
  false positives) manually before committing, since this is the phase-2
  confirmation run no-mock requires.
- Add regression tests: `gates/test_closes_gate_ci.py` gets a 9-keyword sweep
  through `ci._phase1_mismatch` (the `--closes-only` path this issue's live
  probe found silent); `test_gates.py` gets the matching sweep through
  `pr_reference.check_body(..., "phase2")`, plus one test documenting that
  `check_body`'s phase-1 branch does not itself gate closing keywords (that
  responsibility lives in `gates/ci.py`, confirmed by reading — the sweep
  belongs on the `ci.py` side).
- Run the full existing test suites (`gates/test_closes_gate_ci.py`,
  `test_gates.py`) once and fix anything the widened regex breaks before the
  PR.

## Out of scope

- Any change to `.github/workflows/plan-aware-closes-gate.yml` — it invokes
  `ci.py --closes-only` and carries no keyword list of its own (verified in
  the survey).
- Any change to `gates/gates.py`'s unrelated write-scope/protected-path
  checks, or to `closure_sweep.py` beyond its existing indirect use of
  `check_body`.
- Re-litigating the `--closes-only` mode's existing scope-narrowing
  rationale (documented in `docs/issue-245/reports/implementation.md`) —
  unaffected by this fix.

## How you'll know it worked

- `python3 gates/pr_reference.py` regex, exercised directly, matches all 9
  keyword forms (close/closes/closed/fix/fixes/fixed/resolve/resolves/resolved)
  in both cases, and does not match near-miss words (`unclosed`, `prefixes`).
- `gates/test_closes_gate_ci.py` and `test_gates.py` both pass in full,
  including new tests covering all 9 spellings in phase-1 (`ci._phase1_mismatch`)
  and phase-2 (`pr_reference.check_body`) paths.
- A synthetic phase-1 body of `"Fixed #280 stuff"` fed through
  `ci._phase1_mismatch(body, 280)` returns a non-empty block list (the exact
  scenario the issue's live probe found passing silently before this fix).
