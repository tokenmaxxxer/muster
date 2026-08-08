# Current-state survey — issue #476, step 4 (execution-observation)

## Scope

Observed: role `implementation`, subject issue #476, PR #485
(`issue-476/implementation` → merged into `main` as merge commit
`8170dae`). Observed commits: `5d18d584` (phase-1 survey+proposal),
`e7b4443f` (H1/H2 build), `5257814f` (before-landing hunt record +
open finding). Observed record: `docs/issue-476/reports/implementation.md`
(`loop_state: landed`).

Read this session, in full, before any proposal text below: `gh issue
view 476` and its 4 comments (operator requirement, operator
iterative-decision-rule addition, and three `APPROVE issue-476/<role>`
comments for product-discovery/architecture/implementation — no
`APPROVE issue-476/execution-observation` comment exists yet);
`gh pr view 485 --json commits,files,body` (commit SHAs above, 17
changed files); `docs/issue-476/proposals/discovery.md` (pre-registered
H1/H2 hypotheses, metrics, thresholds, decision rules);
`docs/issue-476/decisions/2026-08-08-h1-h2-mechanism-adr.md`; the merged
`docs/issue-476/reports/implementation.md`; and the two mechanism
source files as delivered, `gates/claim_scan.py` and
`gates/reexecution_gate.py` (both read in full), plus the
`reexecution_blocking_cause` wiring point in `gates/landing_readiness.py`
(`landing_readiness.py:60`, called at `landing_readiness.py:137`).

## What the pre-registered package (discovery.md) asks step 4 to do

Three things, per this session's task: (a) mechanism conformance to the
ADR's failure signatures; (b) immediate adversarial-effectiveness
evidence — fabricated-positive records vs. honest null-result records,
sandboxed, against `reexecution_gate`; (c) state the 30-record
`fabrication_survival_rate` measurement-window procedure. The operator's
2026-08-08 issue comment additionally requires the decision rule to be
iterative: go / pivot / kill-and-redesign, not close-on-delivery.

## What exists now, as delivered (PR #485, read this session)

- `gates/claim_scan.py::scan_text()` — regex-matches claim vocabulary
  (`reproduced|verified|confirmed|passed|tests? pass(es|ed)?|repro(duces|duced)?`,
  case-insensitive, word-boundary); for each hit, requires adjacent
  evidence (fenced code block or a `Repro:`/`Verify:` line within
  `ADJACENCY_LINES = 5` lines); when `repo_targets` is supplied (CLI
  path only, via `git ls-files`), additionally requires the evidence's
  cited target string to appear in that set. Two independent hard-fail
  reasons: no adjacent evidence; evidence present but untraceable to a
  repo/diff target.
- `gates/reexecution_gate.py::run_reexecution()` — `git worktree add
  --detach <target_sha>` into a `tempfile.TemporaryDirectory()`, runs
  `shlex.split(command)` inside it under `timeout`, verdict is the
  subprocess exit code (`pass`/`fail`) or `error` on worktree-creation
  failure, timeout, or `OSError`/`ValueError` from the subprocess call
  itself — three distinct fail-closed branches, no silent-skip branch
  observed in the source. `write_verdict()` persists to
  `.reexecution/<issue>-<role>.json` unconditionally (all three verdict
  kinds get a file). No caller in this file or in
  `landing_readiness.py` grants the audited role session write access
  to that path — the write only happens inside `run_reexecution`'s own
  process.
- `gates/landing_readiness.py::reexecution_blocking_cause()` — reads
  the verdict file and returns a `blocking_causes` entry scoped to
  `docs/issue-<n>/reports/<role>.md` (not a `gates/`-prefix scope),
  called once from `main()` (`landing_readiness.py:137`).
- H2: `roles/implementation.json` / `roles/architecture.json` —
  `loop_state` enum gains `refused`/`not-needed`/`cannot-verify`,
  inserted before `landed` (implementation record's own "what did not
  work" section explains this ordering was forced by
  `_terminal_loop_state()` reading the last enum entry as terminal).
  `gates/gates.py` gains `record_refusal_reasoned()` requiring a
  `reason:` field on those states — not yet located precisely in this
  session (only the call site `landing_readiness.py` was read in
  depth); its exact line range is unread and is named here as an open
  gap for phase 2, not asserted.

## Gap the implementation record itself already flags (not re-derived here)

`docs/issue-476/reports/implementation.md`'s own "Open findings"
section: `gates/ci.py:_phase2_record_evidence()` and
`gates/closure_sweep.py`'s evidence check treat any non-empty
`loop_state` as closing-intent evidence, so a `refused`/`not-needed`/
`cannot-verify` record currently satisfies the "Closes #issue" CI
requirement it should not. This is the implementation role's own
citation (`docs/reports/2026-08-08-hunt-implementation.md`,
"before-landing" section), not a claim this survey re-derives — carried
forward here because it is in-scope for the H2 guardrail
(`refusal_rate`) this step must eventually measure.

## Scout: skipped

Skip condition: the spec leaves no external-field design decision open
— H1/H2's metrics, thresholds, decision rules, and measurement window
are already pre-registered verbatim in `docs/issue-476/proposals/discovery.md`;
this step's job is executing that pre-registered procedure against the
delivered mechanism, not choosing among competing external designs a
market/product scout could inform.

## What is NOT yet known from this session's reading alone

No sandbox exercise of `claim_scan.scan_text()` or
`reexecution_gate.run_reexecution()` against constructed
fabricated-positive / honest-null records has been run this session —
source-reading establishes what the code does on its face, not whether
it behaves as designed against adversarial input. That empirical step,
and any verdict language about mechanism conformance or measured
`fabrication_survival_rate`/`false_reject_rate`, is phase-2 work under
this role's own contract (role directive: "verdict language belongs to
phase 2") and is out of scope for this survey.
