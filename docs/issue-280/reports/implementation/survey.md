# Current-state survey — issue #280

Scout: skipped. Skip condition = pure bugfix (regex keyword-set correction against
GitHub's own documented closing-keyword list; no design decision is open — the
target set of 9 keywords is fixed by GitHub's behavior, not a choice this
session makes).

## Write set (verified by reading, not assumed)

- `gates/pr_reference.py` — `_CLOSES_REF` (line 25) is the single regex:
  `r"(?i)\b(closes|fixes|resolves)\s+#(\d+)"`. It backs two call sites:
  - `check_body()` (line 28) — phase-2 gate: blocks a phase-2 delivery PR
    body unless it matches `_CLOSES_REF` for the target issue.
  - `gates/ci.py:_closes_ref_for_issue()` (line 128) — phase-1 gate: scans
    every closing-keyword match via `.finditer()` (not `.search()`, to
    survive an earlier unrelated-issue reference) and blocks a phase-1
    body/title/commit-message surface that matches it. This is the
    `--closes-only` required check `.github/workflows/plan-aware-closes-gate.yml`
    runs, and the one the issue's live probe found silent on `Fixed #19`.
  - Both call sites `import re` on the same module-level `_CLOSES_REF` —
    fixing the regex in one place fixes both surfaces. No duplicate regex
    exists elsewhere (`grep -rn "_CLOSES_REF\|closes|fixes|resolves" *.py
    gates/*.py` — only `pr_reference.py`, `gates/ci.py`, `closure_sweep.py`
    (which imports `check_body`, not the regex directly), and `test_gates.py`
    reference it).
- `gates/test_closes_gate_ci.py` — existing unit tests for `ci._phase1_mismatch`
  already probe `"Closes #245"`/fenced-quote/cross-issue cases against the
  old three-keyword regex; they need the full 9-keyword sweep added
  (issue's acceptance criterion: "regression tests cover all 9 keyword
  spellings, case variants, and the in-code-fence case" — the fenced-quote
  case is already covered by `t_phase1_mismatch_matches_inside_fenced_quote`
  and needs no new fixture, just the wider regex to keep passing it).
- `test_gates.py` — existing `t_pr_reference_phase2_requires_closes` covers
  `Closes`/`closes`/`Fixes` only; needs the same 9-keyword sweep for the
  phase-2 `check_body` path, plus a phase-1 case documenting that
  `check_body`'s phase-1 branch checks only `#N` presence (closing-keyword
  blocking for phase-1 lives in `gates/ci.py`, not `pr_reference.check_body`
  — confirmed by reading `check_body`'s phase-1 branch, which never touches
  `_CLOSES_REF`).

## GitHub's actual keyword set (verified against issue text + code, not invented)

9 forms across 3 verbs x 3 inflections: `close/closes/closed`,
`fix/fixes/fixed`, `resolve/resolves/resolved`. Case-insensitive (`_CLOSES_REF`
already carries `(?i)`, unaffected by this fix).

## No other write surfaces found

- `.github/workflows/plan-aware-closes-gate.yml` invokes `ci.py --closes-only`
  — no keyword list duplicated in the workflow file itself (confirmed by
  reading it); no change needed there.
- `docs/issue-245/**` and `docs/issue-271/**` (prior related work) are
  read-only history for this issue, not part of the write set.
