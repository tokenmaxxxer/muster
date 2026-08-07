---
status: proposed
files:
  - gates/closure_sweep.py
  - test_gates.py
  - docs/issue-391/decisions/2026-08-07-mass-failure-threshold.md
---

## Request

Eight open PRs are red on `closes-gate` for one shared cause (the
`-f`/`-X GET` bug that #388 owns fixing). Nothing currently reads "N PRs
failing the same check with the same message" as one fact about the
checker; each failure is reported and the operator notified per-PR.
Build the detector: what counts as a mass-identical failure, at what
threshold, landing where, without inventing a mechanism this repo
already has for the same shape of problem (#374, #383).

## Constraints

- Must not silently absorb genuine, independently-bad PRs into "probably
  the gate" — a false-positive here is worse than no mechanism (stated
  explicitly in the issue's Acceptance section).
- Must reuse `closure_sweep.py`'s existing report-only, `--post`-gated,
  network-free-classifier shape rather than add a second sweep
  mechanism — #383 already extended this exact file for a structurally
  identical "data exists, nothing reads the aggregate" defect, and it is
  already invoked once per orchestrator cycle via `run.md`.
- Detection must not depend on #388 landing first — it has to work
  against the raw check output that exists today (the eight PRs are
  live right now).
- No code in this proposal fixes #388's underlying bug and no code
  auto-closes, auto-merges, or auto-edits anything (contract v3: GitHub
  actions stay human/orchestrator; `closure_sweep.py` already only
  reports).

## Rationale

**Chosen approach:** extend `gates/closure_sweep.py` with a pure
classifier `mass_check_failure(failures: list[dict]) -> list[dict]`
that takes `[{pr, check, message}, ...]` gathered from `gh pr checks
<pr> --json name,state,description` across open PRs, groups by
`(check_name, normalize(message))` where `normalize()` strips digit
runs only (PR numbers, issue numbers — the only thing that varies
between an identical checker-side failure hitting different PRs), and
flags a group as `MASS_CHECK_FAILURE` when it has **3 or more members**.
A network-gathering sweep function calls it and the existing `--post`
path emits one comment (one finding, not N).

**Alternative considered and rejected — a new standalone script.** A
fresh `gates/mass_failure_sweep.py` would keep the classifier/gatherer
split cleaner (closure_sweep.py already does two unrelated things:
issue/PR closing consistency, not check-output consistency). Rejected
because it would need its own invocation point, and #383 already
established that an un-invoked sweep is worse than no sweep — it
"reports clean" or, here, simply never runs. `run.md` already calls
`closure_sweep.py` every cycle; a second file needs a second wiring
decision this proposal has no mandate to make, and the two mechanisms
(closing-consistency, check-failure-clustering) are close enough in
shape — network-free classifier, board-wide sweep, report-only,
dedup-guarded `--post` — that one file with two classifiers is less
surface than two files with duplicated plumbing.

**Threshold: 3, not 2.** Two PRs sharing an identical normalized
failure message is not enough — a common, easy, independently-made
mistake (e.g. two authors both forgetting a required trailer) can
organically produce the same message text from two people who made two
real, unrelated mistakes. At 3+ concurrently-open PRs, the same
exact-after-digit-strip message is much less likely to be three
independent authors making the identical mistake and much more likely
to be one code path failing the same way for everyone who touches it.
This is argued, not measured — see the decision record for the
full false-positive analysis, including what this threshold does to a
genuine batch of eight independently-bad PRs (it does **not** collapse
them into one finding, because independent defects trigger different
code paths and produce different message text — see below).

## What will be done

- `gates/closure_sweep.py`: add `MASS_CHECK_FAILURE` constant,
  `_normalize_check_message(text) -> str` (strip digit runs), pure
  `mass_check_failure(failures: list[dict]) -> list[dict]` (group by
  `(check, normalized)`, emit one entry per group with `len >= 3`,
  carrying the PR list and the shared message), and a network-gathering
  function `_open_pr_check_failures(root)` (loops `gh pr list --state
  open --json number`, then `gh pr checks <pr> --json name,state,
  description` per PR, keeps only failing/non-success entries) that
  feeds it. Wire the result into `main()`'s existing report/exit-code
  path alongside the current closing-consistency violations, and into
  the existing `--post` comment (one comment covering both violation
  kinds, still one `_SWEEP_COMMENT_MARKER`-guarded post per digest so
  repeat runs don't re-notify).
- `test_gates.py`: unit tests for `_normalize_check_message` and
  `mass_check_failure` — no-groups-under-3, exactly-3 groups, 8
  independently-bad PRs with 8 distinct messages producing zero
  findings (the required negative case from Acceptance), digit-only
  variation collapsing to one group.
- `docs/issue-391/decisions/2026-08-07-mass-failure-threshold.md`:
  record the threshold=3 choice, the rejected threshold=2 alternative,
  and the worked false-positive example (eight independently-bad PRs,
  why they don't collapse) — this is the hard-to-reverse choice
  contract v3's doctrine ladder sends to `decisions/`.

## Out of scope

- Fixing the `-f`/`-X GET` bug itself (#388).
- Wiring `closure_sweep.py --post` into `.github/` as a required check
  (#383 already identified this gap for the closing-consistency half;
  out of this issue's write set — `run.md`'s per-cycle invocation is
  the existing schedule this proposal relies on, per the issue prompt).
- Suppressing or altering the per-PR `closes-gate` check itself — this
  proposal adds a second, aggregate-level report; it does not change
  what any individual PR's required check does or says.
- Any new mechanism for #374 (decision-queue aging) — related in shape,
  not in data, and already has its own issue.

## How you'll know it worked

- `python3 -m pytest test_gates.py -k mass_check_failure` passes,
  including the 8-distinct-messages-zero-findings case.
- Run `gates/closure_sweep.py --repo .` (or the new sweep function
  directly) against this repository's current open-PR state: the eight
  PRs named in #391 (#340, #343, #346, #350, #352, #353, #357, #389),
  if still open and still sharing the `-f`/`-X GET`-caused message at
  build time, are reported as one `MASS_CHECK_FAILURE` finding naming
  all eight PRs and the shared message — not eight separate lines.
- The negative case is exercised in the same run: no existing, unrelated
  failing check anywhere in the board collapses into a false
  `MASS_CHECK_FAILURE` (checked by the 8-distinct-messages unit test
  standing in for "genuine batch of eight independently-bad PRs").
