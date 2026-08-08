---
status: proposed
files:
  - gates/claim_scan.py
  - gates/test_claim_scan.py
  - gates/reexecution_gate.py
  - gates/test_reexecution_gate.py
  - gates/landing_readiness.py
  - gates/test_landing_readiness.py
  - gates/gates.py
  - gates/test_gates.py
  - roles/implementation.json
  - roles/architecture.json
  - .gitignore
---

## Request

Build H1 (mechanized, gate-provisioned, SHA-pinned worktree
re-execution of a claim-language-triggered command, with a gate-owned
verdict artifact) and H2 (refusal-vocabulary extension at equal
structural cost to the existing positive-path check), per the merged
ADR `docs/issue-476/decisions/2026-08-08-h1-h2-mechanism-adr.md`.

## Constraints

- Ship on the deployed plugin surface only (`gates/`, `roles/*.json`) —
  no external CI service (ADR alternative #2, rejected).
- The audited role session must never provision or write its own
  verdict — trigger is claim-language pattern match in the diff, not a
  self-reported field; verdict file lives under `.reexecution/` and is
  never staged by a role's own commit (ADR §3, §5).
- SHA-pin the worktree to the PR head commit as reported by the
  triggering event, never re-read the branch ref at execution time (ADR
  §3, closes the force-push race).
- A claim with no adjacent runnable command, or a command with no
  traceable target in the diff/repo, is a hard fail at scan time, before
  execution (ADR §2 — closes the after-proposal hunt's vacuous-command
  finding).
- Fail closed, never silent-skip, when the execution environment cannot
  create a git worktree (ADR Consequences).
- Retroactivity rule: these are new required gates; existing merged
  records predate them and are never judged against them
  (`run.md` "게이트 작성 시 지킬 것 (#362)").
- New modules match the repo's established shape: pure judgment
  function + thin CLI wrapper, `gates/test_<module>.py` with plain
  `t_*` functions (no `unittest`/`pytest`), network-free where the
  logic itself doesn't require `gh`/`git`.

## Rationale

**H1 seam: extend `landing_readiness.blocking_causes`, not a new
aggregation path.** `landing_readiness.classify()`
(`gates/landing_readiness.py:30`) already accepts
`blocking_causes: [{"reason", "scope"}]` scoped by file-path prefix —
built for exactly this: a cause that should block only the PRs whose
files it actually covers (issue #398's over-generalization fix, per the
function's own docstring). The alternative — giving
`reexecution_gate.py` its own separate aggregation/reporting path
outside `landing_readiness.py` — was considered and rejected: it would
duplicate the READY/BLOCKED_ON_PR/BLOCKED_ON_SCOPE classification
`landing_readiness.py` already owns, and the ADR itself says
`reexecution_gate` failures should be treated "identically to any other
required-gate failure it already aggregates — no new merge ceremony"
(ADR §6). Reusing the existing parameter is the zero-new-ceremony path;
a parallel aggregator is a second source of truth for the same
decision.

**H2 target: `roles/*.json` + a new field-presence check next to
`record_enums`, not `run.md`/`acceptance_gate.py` literally.** The
survey (`docs/issue-476/reports/implementation/survey.md`) found the
ADR's literal file list does not correspond to code that exists:
`run.md`'s `stage` field is prose with no gate reading it, and
`acceptance_gate.py` checks an issue's `## Acceptance` section, never a
role record's frontmatter. The closed vocabulary the ADR's H2 decision
text actually describes (`loop_state` values `refused`/`not-needed`/
`cannot-verify`) matches `roles/<role>.json`'s `record_fields.loop_state`
enum, enforced today by `gates.record_enums()`
(`gates/gates.py:302-341`). The alternative of adding a brand-new
`refusal_gate.py` was already rejected in the ADR itself (alternative
#4: "would itself be a new gate satisfiable by performance"); this
proposal's file choice is a continuation of that same reasoning applied
to the mismatch the survey found — extend the code that already does
this job (`record_enums` for the enum, a new sibling function for
field-presence) rather than a name in the ADR that does not correspond
to an enforcement point. `roles/*.json` and `gates/gates.py`
(record-enum/field-presence machinery) are within the ADR's stated
deployment-surface constraint (`gates/`, and the role-vocabulary files
the ADR's own context section names as one of the two existing closed
vocabularies).

**H2 enum scope: `roles/implementation.json` + `roles/architecture.json`
only, not all role files.** This issue's own execution plan exercises
exactly these two roles (`implementation`, `architecture` — see this
issue's `## 실행 계획`). Extending every role file in `roles/*.json` was
considered and rejected as scope creep beyond what issue #476
pre-registered or what this ADR's write set covers — a role not in this
issue's plan gaining new `loop_state` values it never asked for is a
decision that role's own issue should make, not a side effect of this
build.

## What will be done

**H1**

1. `gates/claim_scan.py` — `scan_text(text: str) -> list[Finding]` (pure,
   network-free): regex-matches claim vocabulary (case-insensitive,
   word-boundary: `reproduced`, `verified`, `passed`, `confirmed`,
   `tests? pass`, `repro(duces)?`), and for each hit checks (a) a fenced
   code block or an explicit `Repro:`/`Verify:` line within N lines
   (N fixed as a constant, documented at the point of use), and (b) the
   cited command names a target string (test file path, function name,
   or module) that also appears in the same claim's surrounding text and
   in the diff/repo. Either check failing is a hard-fail finding —
   before any execution. CLI wrapper reads a file or PR diff via `gh pr
   diff` and prints findings / exit code.
2. `gates/reexecution_gate.py` — `run_reexecution(command: str, target_sha:
   str, repo: Path, timeout: int) -> Verdict` (pure aside from the
   subprocess/git calls, isolated behind this one function for
   testability): creates a `git worktree add` at `target_sha` under a
   temp path, runs the cited command inside it with a timeout, captures
   exit code, writes `.reexecution/<issue>-<role>.json` (command,
   exit code, timestamp, worktree SHA), removes the worktree. Fails
   closed (verdict `error`, gate blocks) if worktree creation itself
   fails — never silently skipped. CLI wrapper takes `--issue --role
   --sha --command`.
3. Wire `reexecution_gate`'s verdict into
   `landing_readiness.py`'s `blocking_causes` construction in `main()`:
   a `fail`/`error` verdict for a PR's issue+role becomes one
   `{"reason": "reexecution_gate: <detail>", "scope": {f"docs/issue-<n>/reports/<role>.md"}}`-shaped
   entry, scoped to that PR's own record path — never a fixed prefix
   like `gates/` (an after-proposal hunt on this proposal reproduced
   that a `gates/`-scoped cause silently fails to block the normal case:
   a role PR whose files never touch `gates/` at all, so `classify()`
   returns `READY` despite a failing verdict). Scoping to the record
   path the verdict is actually about ties the cause to files every
   audited PR necessarily touches (its own board record), closing that
   bypass. No change to `classify()`'s signature — it already accepts
   this shape.
4. `.gitignore` — add `.reexecution/` (gate-owned, session-unwritable;
   never a path a role's own commit stages).

**H2**

5. `roles/implementation.json`, `roles/architecture.json` —
   `record_fields.loop_state` gains `refused`, `not-needed`,
   `cannot-verify` alongside the existing four values.
6. `gates/gates.py` — a new pure function, colocated with
   `record_enums`/`record_wellformed_in`, that takes a role's declared
   `record_fields` plus a record's frontmatter and, when
   `loop_state` is one of the new refusal values, requires a `reason:`
   field to be present (same strictness as the positive-path
   `record_wellformed_in` check: presence, not content-quality). Wired
   into the same router/CI call sites `record_enums`/
   `record_wellformed` already are.
7. Tests: `gates/test_claim_scan.py`, `gates/test_reexecution_gate.py`
   (the worktree/subprocess paths get a fixture using a throwaway local
   git repo, not network), extensions to `gates/test_landing_readiness.py`
   and `gates/test_gates.py` for the new blocking-cause shape and the new
   field-presence function.

## Out of scope

- Extending the H2 enum to any `roles/*.json` file beyond
  `implementation.json`/`architecture.json`.
- Any change to `run.md`'s `stage` field or its prose — confirmed by the
  survey to be an unenforced reporting convention, not a build target.
- Any change to `acceptance_gate.py` — it checks issue bodies, not role
  records; not the right file for this vocabulary.
- Tuning the claim-vocabulary regex or the traceability heuristic beyond
  a first working version — both are named in the ADR as living risks
  expected to need iteration once exercised against real records; this
  build ships the mechanism, not a tuned-to-convergence detector.
- Timeout/resource-limit value-tuning as a performance question (ADR
  hands this to performance-engineering if it becomes one).
- Step 4 (execution-observation / conformance-review) — measuring the
  pre-registered metrics against threshold is a separate role/step.

## How you'll know it worked

- `python3 gates/test_claim_scan.py`, `gates/test_reexecution_gate.py`,
  `gates/test_gates.py`, `gates/test_landing_readiness.py` all run and
  pass (existing + new cases), shown in this session's own record.
- A hand-constructed record body containing a bare claim word with no
  adjacent command is rejected by `claim_scan.scan_text`; one with an
  adjacent command whose cited target does not appear in the diff/repo
  is also rejected (closes the after-proposal hunt's vacuous-command
  finding, concretely).
- A hand-constructed refusal-shaped record (`loop_state: refused`) with
  a `reason:` field passes the new field-presence check; the same
  record with `reason:` stripped fails it.
- `roles/implementation.json` and `roles/architecture.json` parse as
  valid JSON with the three new `loop_state` values present, and
  `gates.record_enums()` accepts a record using one of them.
