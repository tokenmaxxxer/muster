# Proposal — issue #189 execution-observation, phase-2 verification method

Status: proposal (phase 1). No verdict is rendered anywhere in this document —
this section states which of the three verdict levels will be checked and
against what evidence, per this role's phase-1 facet requirement.

## What phase 2 will check, and against what evidence

**Outcome** — did PR #193 (commits `b60843f`, `8d2c96a`) land what
`execution-plan.md`'s acceptance criteria 4.4 items 1-2 asked, specifically for
the requirement-4 (`flows[].plan`) surface the orchestrating prompt flagged.
Evidence: the static trace already captured in
`docs/issue-189/reports/execution-observation/survey.md` (the `b60843f` diff of
`_plan_from_body` against the issue #189 body text already read), plus a phase-2
read of `test_spawn.py`'s actual new-test bodies (`git show b60843f --
test_spawn.py`, not yet read) to see whether the observed role's own test
coverage exercises a fenced-illustration or trailing-text-header body. No
execution of `spawn.py`/`gates/flows.py` will be performed: this role's
directive prohibits re-running the observed role's code ("PROHIBITED, always:
never re-run the observed role's code ... never by re-executing the observed
task"). This is a deliberate deviation from the orchestrating prompt's
suggested repro command (`python3 spawn.py flows --json -C <repo>`) — noted
here as a conflict between the immediate task instruction and this role's
standing protocol, resolved in favor of the protocol, since the protocol is
this role's own governing directive and the static trace already available
covers the same factual ground without executing anything.

The remaining acceptance criteria not centered on requirement 4 (1.1-1.3,
2.1-2.4, 3.1-3.4, 5.1-5.5 — all `run.md` prose additions per both approved
proposals' own scoping) will be checked outcome-level by reading the actual
`run.md` diff (`git show b60843f -- on-the-record/commands/run.md`, not yet
read) against each criterion's text, since these are static prose-presence
checks, not runtime behavior, and so do not raise the same re-execution
question.

**Trajectory** — was the `implementation` role's phase-1→phase-2 path sound:
did it survey before proposing (its `survey.md`, already read — shows a
survey-first pattern with an explicit scout-skip record), get real human
approval before each phase (`APPROVE issue-189/product-discovery` at
2026-08-02T06:02:57Z, `APPROVE issue-189/implementation` at
2026-08-02T06:29:54Z — both already read from the issue's comments), and does
its own phase-2 record's claims hold up against its diff (partially
cross-checked already in the survey: the record's "144 to 147 pytest" and
`closed_checks` claims are stated in prose but the record does not itself
paste the raw command transcript — whether that is sufficient citation, or a
step-level gap, is a phase-2 judgment). Evidence: the two APPROVE timestamps
cross-referenced against the two PR open/merge timestamps (not yet
cross-referenced — reserved for phase 2), plus `survey.md` and
`implementation.md`, both already read in full.

**Step** — which specific artifact, if any, is deficient. Candidates already
surfaced (not judged) are: `_plan_from_body`'s fence-handling and
header-matching in `gates/flows.py` (`b60843f`), and `implementation.md`'s
substitution of a synthetic fixture for the manual-check line in
`implementation-plan.md`'s "How you'll know it worked." Evidence for each:
file:line citations into the `b60843f` diff and `test_spawn.py`'s actual
new-test bodies (to be read in phase 2), plus the issue body text already
captured this session. Any deficiency finding will carry the four-part
blameless shape (impact, timeline, root cause, action item) this role's
directive requires.

## Independent sweep, beyond the two orchestrator-flagged defects

Phase 2 will also check acceptance criteria 4.4 items 3-5 (call-count,
schema-doc consistency, no-new-file) against the `b60843f` diff already read,
and the candidates already surfaced in the survey's "Other candidates" section
(the 1000-issue `--limit` cap, `_PLAN_STEP_RE`'s whitespace tolerance) as
additional independent leads — plus a fresh read of `test_gates.py`'s two new
tests and the `flows-schema.md` diff, neither read this session yet.

## Method constraint carried into phase 2

Every verdict-bearing sentence in the phase-2 record will name its source
(commit SHA, file:line, or PR comment URL) immediately adjacent, per this
role's directive. No `src/` file will be cited as evidence of "what happened"
— only diffs, commits, and the observed role's own record. Where a file:line
citation into current `HEAD` is used, it is used only where already confirmed
identical to the `b60843f` diff state — confirmed this session via
`git log --oneline --follow -- gates/flows.py`, which shows `b60843f` as the
tip commit touching that file (current `HEAD` `41b2051` matches
`origin/main`).

## Gate check before phase 2 opens

As of this session, the issue's two comments are
`APPROVE issue-189/product-discovery` and `APPROVE issue-189/implementation`
only — no `APPROVE issue-189/execution-observation` comment exists, and no PR
review Approve exists on any PR for the `issue-189/execution-observation`
branch (none is open yet). Per role-handoff contract v3 s19, phase 2 does not
open until one of those two approval paths is satisfied for this role
specifically. This proposal, the accompanying survey, and the PR that carries
them are this session's phase-1 output; phase 2 (the actual verdict record at
`docs/issue-189/reports/execution-observation.md`) is deferred to a future
session after approval.
