---
status: proposed
files:
  - docs/issue-511/reports/execution-observation.md
---

## Request

Independently observe, on fresh fixtures built outside this repository's
own tree, the runtime behavior of the artifacts PR #513 (merged `be46db5`,
issue #511) landed — `gates/risk_report.py`'s four-axis classifier and
`on-the-record/hooks/impact-guard.sh`'s batch-approval blocking path —
against the four conditions issue #511 itself names: a high-impact
(worst-reversibility) proposal is blocked from batch approval; a
low-impact one passes; unparseable input classifies to the highest grade
(fail-closed); and the classification values used match the anchored
conditions in `docs/specs/impact-classification.md` /
`docs/specs/standing-decisions.md`, not undocumented code-only constants.
Render the three-level verdict (outcome / trajectory / step) in
`docs/issue-511/reports/execution-observation.md`.

## Constraints

- Verdict claims require citation adjacent to the claim (commit SHA,
  file:line, or PR comment URL) — no bare assertion.
- Independence: never edit the observed role's `src/`, `test/`, or
  `docs/issue-511/` paths outside this role's own report/proposal path.
- Never re-run the observed *task* (do not redesign or rebuild the
  classifier or the hook); invoking the already-shipped
  `gates/risk_report.py` functions and `impact-guard.sh` script against
  fixtures built by this session, to observe their runtime behavior, is
  the acceptance criterion the issue itself names ("Observe runtime
  behavior on fresh fixtures") — distinct from re-executing the
  implementation work.
- Record must state the independence statement before any verdict
  language.
- Fixtures are synthetic (built in `$TMPDIR`, outside this repo's own
  tree), not this repo's own `docs/proposals/`/`docs/issue-*/proposals/`
  set — the observed session's own record already flags that this repo's
  real proposal set is stale (`status: proposed` never flips on merge),
  which would make an in-repo run non-representative of the intended
  red/green behavior.

## What will be done

1. Build a scratch git-less fixture directory tree under `$TMPDIR`
   (mirroring `on-the-record/hooks/test_impact_guard.py`'s own pattern:
   a bare TARGET dir with `docs/proposals/*.md`), outside this repo.
2. Call `gates.risk_report.reversibility_grade()` /
   `classify_axes()` directly (Python import, `sys.path.insert` to this
   repo's `gates/`) against: (a) a high-reversibility write-set (a
   `hooks/`-nested path, per `impact-classification.md`'s Axis 2), (b) a
   low-reversibility write-set (a leaf `docs/` path), (c) an empty/
   unparseable write-set — and check each returned grade against the
   band stated in `docs/specs/impact-classification.md`, not just
   against the code's own constant.
3. Invoke `on-the-record/hooks/impact-guard.sh` exactly as
   `test_impact_guard.py`'s `_run()` helper does (stdin JSON payload,
   `cwd` set to the fixture TARGET, `TOKENMAXXXER_CHECKOUT` set to this
   repo root) against: a batch (2+ `gh pr merge`) with a high-impact
   proposal open → expect exit 2; the same batch with only low-impact
   proposals open → expect exit 0; a single `gh pr merge` (not a batch)
   with the high-impact proposal still open → expect exit 0 (per the
   hook's own documented batch-only scope).
4. Write `docs/issue-511/reports/execution-observation.md` — outcome /
   trajectory / step verdict, each claim cited to what this session's own
   fixture runs actually produced, or to the read PR artifacts.

## Out of scope

Fixing anything found (including the already-recorded stale-`status`
open finding); filing issues; editing the observed role's classifier,
hook, tests, or specs; re-litigating findings already recorded in
`docs/issue-511/reports/requirements-engineering.md` beyond citing them.

## How you'll know it worked

`docs/issue-511/reports/execution-observation.md` exists, committed,
with `loop_state` at a terminal value for this record kind, every
verdict-bearing sentence carrying an adjacent citation, and the
independence statement preceding all verdict language.

## Hunt record

docs-only, no before-landing dispatch — the only file this transition
touches (`docs/issue-511/reports/execution-observation.md`) is under
`docs/`.
