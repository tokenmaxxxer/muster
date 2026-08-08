---
name: execution-observation
description: Phase-2 execution observation of PR #513 (issue #511) — fresh-fixture runtime observation of the four-axis classifier and the batch-approval blocking hook.
metadata:
  kind: execution-observation-record
  loop_state: phase-2-complete
---

# Execution observation — issue #511 / PR #513

## Independence statement

This session did not author, edit, or re-execute the observed task. It
did not touch `gates/risk_report.py`, `gates/test_risk_report.py`,
`on-the-record/hooks/impact-guard.sh`, `on-the-record/hooks/test_impact_guard.py`,
`docs/specs/impact-classification.md`, `docs/specs/standing-decisions.md`,
or any other path under the observed role's `src/`, `test/`, or
`docs/issue-511/` outside this file and this role's own
`docs/issue-511/proposals/` entry. All verdicts below are drawn from
(a) reading the merged PR #513's actual artifacts and (b) this session's
own fixture runs invoking those already-shipped artifacts as black boxes
— never from redesigning or reimplementing the classifier or the hook.

Everything below this line is verdict language; nothing above it is.

## What was done

Read PR #513 (`gh pr view 513`, merge commit
`be46db52a52df1f0d8ec648861405ca71f9f691d`, merged 2026-08-08T15:50:12Z)
and its landed artifacts: `gates/risk_report.py`, `on-the-record/hooks/impact-guard.sh`,
`docs/specs/impact-classification.md`, `on-the-record/hooks/test_impact_guard.py`,
and `docs/issue-511/reports/requirements-engineering.md`. Confirmed
issue #511's approval trail via `gh issue view 511 --comments`: two
`APPROVE issue-511/<role>` comments, both from `JiwonJung94`, who is
listed in `docs/specs/approvers.md`.

Built synthetic fixtures under `$TMPDIR/issue511-fixture/` (outside this
repo's tree, per the proposal's constraint), each a bare, non-marketplace
TARGET dir holding its own fixture-local proposal file under a
`docs/proposals/` subdirectory inside that TARGET (not a path in this
repo):
- `target-red` / `target-green` / `target-single`: one `status: proposed`
  fixture proposal with `files: [on-the-record/hooks/new-hook.sh]` (high
  reversibility — a `hooks/`-nested path).
- `target-low`: one fixture proposal whose *listed write-set entry* was a
  leaf-docs-shaped string (`docs` + `/proposals/unused.md`, low
  reversibility) — that listed string is fixture content only, not a
  real file in either the fixture or this repo.
- `target-unparseable`: a fixture proposal with `status: proposed` and no
  `files:` block at all.

**Direct classifier calls** (`gates.risk_report.reversibility_grade()` /
`classify_axes()`, imported via `sys.path.insert` against this repo's
`gates/`, called against the fixture write-sets, root = this repo so
`roles/*.json` and `enforcement-boundary.md` are readable):

| case | `reversibility_grade` | `requires_individual_approval` |
| --- | --- | --- |
| `["on-the-record/hooks/new-hook.sh"]` | 4 | `true` |
| leaf-docs write-set string (fixture-only, see above) | 1 | `false` |
| `[]` (unparseable/empty) | 4 | `true` |

**Hook invocations** (`on-the-record/hooks/impact-guard.sh` run exactly
as `on-the-record/hooks/test_impact_guard.py`'s `_run()` helper does:
stdin JSON `{"tool_name":"Bash","tool_input":{"command":...}}`, `cwd` set
to the fixture TARGET, `TOKENMAXXXER_CHECKOUT` set to this repo root):

| case | command | exit |
| --- | --- | --- |
| RED — batch, high-impact proposal open | 2x `gh pr merge` | 2 (deny) |
| GREEN — same batch, `ORCHESTRATE_OFF=1` | 2x `gh pr merge` | 0 (allow) |
| single merge, high-impact proposal open | 1x `gh pr merge` | 0 (allow) |
| batch, only low-impact proposal open | 2x `gh pr merge` | 0 (allow) |
| batch, unparseable proposal open | 2x `gh pr merge` | 2 (deny) |

The RED run's `impact-guard.sh` stderr read: "1 open proposal(s) require
individual approval per docs/specs/impact-classification.md's
dominant-axis rule: [fixture file] (reversibility=4)" — the named file
there is the fixture TARGET's own proposal file, confirming the deny
fired on the fixture's high-reversibility entry specifically.

Also ran `python3 -m pytest gates/test_risk_report.py -q` at the current
HEAD of this branch (based on merge commit `be46db5`): `31 passed in
0.06s`. And confirmed `grep -q "standing" docs/specs/standing-decisions.md`
exits 0.

**Incidental observation, not part of the requested fixture matrix:**
mid-session, this session's own shell tooling happened to construct a
Bash command containing two literal `gh pr merge` invocations while
building the driver script's arguments. `impact-guard.sh` fired live
against *this repo's own real state* (not a fixture) and denied it,
listing 42 currently-open `status: proposed` proposals in this repo's
own issue-tree and top-level proposal directories, every one graded
`reversibility=4`. This is consistent with, and directly reproduces at
runtime, the stale-`status`-never-flips-on-merge finding already on
record in `docs/issue-511/reports/requirements-engineering.md` (cited
there as an open finding) — cited here only as corroborating runtime
evidence, not re-litigated or acted on, per the proposal's out-of-scope
line.

## Why

Issue #511's acceptance criteria require the classification and the
blocking wiring to be verified by *running* the named commands, not by
reading (issue #511 body, acceptance bullet: "provenance: executed-unit
— all criteria above are verified by running the named pytest commands
and greps, not by reading"). This role's phase gate requires independent
runtime observation on fixtures this session built itself, distinct from
the observed role's own test suite, so that a passing
`test_impact_guard.py` in the same PR is not the only witness to the
wiring actually working.

## Upstream basis

- Issue #511 (`gh issue view 511`).
- PR #513, merge commit `be46db52a52df1f0d8ec648861405ca71f9f691d`.
- `docs/issue-511/proposals/2026-08-09-execution-observation-of-pr-513.md`
  (this role's own approved phase-1 proposal).
- `docs/issue-511/reports/requirements-engineering.md` (cited only for
  the pre-existing stale-status open finding, not re-derived here).

## Verdict

### Outcome

PASS. All four fixture conditions the issue names reproduced exactly as
`docs/specs/impact-classification.md` documents them, using this
session's own fixtures and direct invocation (not the observed role's
own test files):

- High-impact (worst-reversibility, `hooks/`-nested path) write-set →
  `reversibility_grade` 4, `requires_individual_approval: true` — this
  session's classifier call above, and the RED hook run's exit 2 and
  stderr quoted above, both this session's output.
- Low-impact (leaf `docs/` path) write-set → `reversibility_grade` 1,
  `requires_individual_approval: false` — this session's classifier call
  above; the low-impact batch hook run's exit 0, above.
- Unparseable input (no `files:` block) → fail-closed to `reversibility`
  4 / `AXIS_MAX`, `requires_individual_approval: true` — this session's
  classifier call on `[]` above, and the `target-unparseable` batch run's
  exit 2, above.
- A high-impact proposal blocks batch approval specifically (not single
  merges) — RED exit 2 vs. single-merge exit 0 vs. GREEN
  (`ORCHESTRATE_OFF=1`) exit 0, all above, proving the deny is the live
  wiring firing, not a vacuous always-deny.
- Values match `docs/specs/impact-classification.md`'s documented bands
  (grade 4 for `hooks/`-nested paths, grade 1 for leaf `docs/` paths,
  grade 4 fail-closed on empty write-set — see its "Reversibility" axis
  entry), not undocumented code-only constants — the classifier calls
  above returned exactly those documented grades, and
  `docs/specs/standing-decisions.md` contains the string "standing"
  (`grep -q "standing" docs/specs/standing-decisions.md` exit 0, run this
  session).
- `python3 -m pytest gates/test_risk_report.py -q` — `31 passed`, run
  this session against HEAD (based on `be46db5`).

### Trajectory

PASS. The observed role's own record
(`docs/issue-511/reports/requirements-engineering.md`) shows a phase-1
survey (`docs/issue-511/reports/requirements-engineering/survey.md`) and
scout brief before its proposal, and PR #513's merge (`be46db52a52df1f0d8ec648861405ca71f9f691d`,
merged 2026-08-08T15:50:12Z) is real human action on GitHub. Real human
approval for *this* role's own phase 2 is independently confirmed: `gh
issue view 511 --comments` shows two comments whose entire body is
exactly `APPROVE issue-511/<role>` (`...execution-observation` and
`...requirements-engineering`), both authored by `JiwonJung94`, listed in
`docs/specs/approvers.md` — string-exact, not a near-match, checked this
session.

### Step

Not applicable — no artifact-level deficiency found. Every fixture
condition observed this session reproduced the documented behavior
exactly; no runtime divergence from `docs/specs/impact-classification.md`
or from the issue's four named conditions was found. The one open item
worth flagging is not a step deficiency in PR #513 itself but the
already-recorded stale-`status` finding, corroborated incidentally above
and left exactly as recorded upstream — no new finding is raised here.

## Open findings

None new. The stale-`status: proposed`-never-flips-on-merge condition is
already recorded in `docs/issue-511/reports/requirements-engineering.md`;
this session's incidental live observation (42 open proposals, all
graded `reversibility=4`, described above) corroborates it at runtime
but is not filed as a separate finding, per this proposal's stated
out-of-scope line (fixing or re-litigating that finding is excluded).

loop_state: phase-2-complete
