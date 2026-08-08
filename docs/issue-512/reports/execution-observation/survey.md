---
loop_state: phase-1-survey
---

# Current-state survey: issue #512 execution observation

Subject: #512. Observed role: `implementation`, session that produced
PR #514 (branch `issue-512/implementation`, merged into `main` at
`dbb5162`, squash/merge-commit of `0b209f9`). Observed artifacts read
this session: `gh issue view 512` (full body + comment thread), `gh pr
view 514`, `git show 0b209f9 --stat`, and the observed role's own record
at `docs/issue-512/reports/implementation.md` (all sections, in full).

## Scope named

This survey covers exactly one observation target: whether the
Acceptance-section runtime claims in
`docs/issue-512/reports/implementation.md` — pytest exit 0, a scratch
TARGET-repo fixture where `call-shape-guard.sh` and
`accumulation-claim-guard.sh` each deny (exit 2) a synthetic violation
and pass (exit 0) a clean write, and `accumulation_trend()`'s no-prior-data
artifact — actually reproduce when independently re-invoked against a
fresh fixture, not authored by the implementation session, this session.

## What the record already claims (read, not yet verified)

`docs/issue-512/reports/implementation.md` "Acceptance verification"
section claims (quoted verbatim from that file's own fenced block):
`derived: "55 passed in 1.49s"`; `grep` for both hook names in
`on-the-record/hooks/hooks.json` passes; a fixture test under `$TMPDIR`
showed both hooks denying/passing as required; and
`accumulation_trend()` invoked against an empty fixture returned
`derived: {"current": {"shape1_sites": 2, "shape5_files": 0}, "has_prior": False}`
with `format_accumulation_trend()` rendering the no-data line. These are
the claims this observation independently reproduces or contradicts —
via my own fresh fixture run, not by reading the claim as given.

## Write surfaces this session touches (thin/unknown before execution)

- `on-the-record/hooks/call-shape-guard.sh`, `accumulation-claim-guard.sh`
  — read for their check logic (both begin: fail-closed trap,
  `ORCHESTRATE_OFF` kill switch, `.git`-walk-up root discovery, payload
  read from `CSG_PAYLOAD`/`ACG_PAYLOAD` env var as JSON). Exact CLI
  invocation contract (how a PreToolUse payload reaches the script — env
  var vs stdin) is the one unknown a fixture run must pin down before
  the actual hook-invocation driver can be written; not yet confirmed
  from a live hook run this session.
- `gates/closure_sweep.py`, function `accumulation_trend` and
  `format_accumulation_trend` — read in full; `accumulation_trend`
  takes a `root: Path`, reads `runs/accumulation_trend.json` if
  present, never raises on absence.
- No file under the observed role's `src/`, `test/`, or
  `docs/issue-512/` (outside this role's own report path) will be
  edited by this observation — independence per the role directive.

## Scout skip record

Scouting is skipped: this is a bugfix/verification-shaped task with no
open design decision (re-invoking existing, already-designed hook
scripts and a `closure_sweep.py` function against a fixture repo) —
skip condition "pure bugfix / no design decision left open" applies.
