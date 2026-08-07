# Survey — issue #391

## Current state

- `gates/ci.py` is the deterministic closes-gate CI entrypoint. Its
  failure strings for the phase-2 branch (`check()`, ~ci.py:350-375)
  embed the issue number and PR number, so two PRs blocked by the exact
  same underlying defect do not necessarily produce byte-identical text
  — the *shape* is identical, the digits differ. Any aggregate detector
  must normalize (strip digits / known variable tokens) before
  comparing, not do exact string equality.
- `_fetch_ref_file` (ci.py:167-186) is the concrete #388 bug: `gh api
  ... -f ref={branch}` without `-X GET` turns the call into a POST, so
  every lookup 404s and `_phase2_record_evidence` always returns
  `False`. That is out of this issue's scope (#388 owns it) — #391 is
  about the fact that nothing notices eight PRs failing the same way
  before #388 lands.
- No existing code reads GitHub check state across multiple open PRs
  at once. `spawn.py` computes `decision_queue` (per #374) from
  approval state, not check state — a different signal. `grep -rn
  "statusCheckRollup\|pr checks" spawn.py gates/*.py` found nothing;
  confirmed by searching for `checks` next to `def` in spawn.py
  (spawn.py:272,319,1512,1881,2808 — none of these read CI check
  results). So there is no "read failing checks for PR N" helper to
  extend; a new one is needed.
- `gates/closure_sweep.py` is the precedent for this issue's shape: it
  scans the whole board (not one PR), classifies purely with local
  functions (`classify()`, network-free, unit-tested), and *only
  reports* — never closes/edits anything (contract v3: GitHub actions
  stay human/orchestrator). It has a `--post` mode that would post one
  comment, gated by a `_SWEEP_COMMENT_MARKER` digest so re-runs don't
  spam (closure_sweep.py:23, :142-147). No `.github/` workflow wires
  it in; `grep -rn closure_sweep .github/` is empty (confirmed by
  #383, which measured the same gap for a different purpose).
- `on-the-record/commands/run.md` is the orchestrator's per-cycle
  driver script and already references `closure_sweep.py` (run.md:239,
  :307) as something invoked every pass, i.e. "runs on a schedule" in
  the sense that matters here: once per orchestrator cycle, not via
  GitHub Actions cron. This is the mechanism #383 already extended and
  the one #391's prompt points at — a new standalone script would
  duplicate this invocation point rather than reuse it.
- #374 (decision queue) and #383 (closure sweep) are both "the data
  already exists and nothing reads the aggregate" defects, structurally
  identical to #391's framing, but over different data (approval age;
  issue/PR open-closed pairing) than #391 needs (identical CI failure
  text across PRs). None of their code paths can be reused for reading
  check output — only the *pattern* (network-free `classify()`, a sweep
  function over the board, report-only, one dedup-guarded `--post`)
  transfers.

## Write set implied by the above

- `gates/closure_sweep.py` — add a network-free classifier for
  "N+ open PRs share one normalized failing-check message" and a sweep
  function that gathers `gh pr checks` output per open PR and calls it.
  Reuses the existing report-only / `--post` dedup shape instead of a
  new file.
- `test_gates.py` — unit tests for the new classifier (pure function,
  same test file the existing `classify()` is tested in).
- `docs/issue-391/decisions/` — the threshold choice and its
  false-positive tradeoff (a named alternative rejected), since this is
  a judgment call the issue explicitly asks to be argued, not assumed.

## Skip conditions checked

Scouting was not skipped: this issue has an open design decision (the
threshold). The scout sweep for this non-product, reliability-mechanism
deliverable was internal-only — `docs/decisions/` and `docs/issue-*/
reports/` were searched for prior art on failure-clustering or
dedup-threshold precedent in this repository (`grep -rln
"threshold|dedup|flapping|중복" docs/decisions`); none exists. This
session's environment has no web-search tool loaded, so the "best
comparable systems" sweep for this round is limited to the repository's
own precedent (#374, #383, `closure_sweep.py`) rather than external
alerting/dedup systems — stated as a limitation, not silently skipped.
