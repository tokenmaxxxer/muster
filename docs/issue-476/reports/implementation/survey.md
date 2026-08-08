# current-state survey — issue #476, step 3 (implementation)

## Scope

Step 3 of the approved execution plan: build H1
(`gates/reexecution_gate.py` + `gates/claim_scan.py`) and H2 (refusal
vocabulary extension), per
`docs/issue-476/decisions/2026-08-08-h1-h2-mechanism-adr.md`. This survey
covers what the write set actually looks like today, before drafting the
proposal.

## H1 — gate suite has no execution today

- `gates/*.py` (`acceptance_gate.py`, `pr_reference.py`,
  `landing_readiness.py`, `record_wellformed`/`record_enums` in
  `gates.py`) are all pure text/structure checks over an issue body, PR
  body, or record frontmatter — none of them spawn a subprocess or touch
  a git worktree. `gates/ci.py` is the CI entry point; it imports
  `flows`, `gates`, `pr_reference`, `spawn`, `spec_index` — no execution
  helper exists to reuse.
- No `.reexecution/` directory exists in the repo.
- `landing_readiness.classify()` (`gates/landing_readiness.py:30`) is a
  pure function `(pr_state, checks, has_record, has_approval, pr_files,
  blocking_causes) -> (kind, reason)`. `blocking_causes` is already the
  extension point the ADR's "aggregated by the existing
  `landing_readiness.py`" line calls for — a `reexecution_gate` fail can
  be surfaced as one more blocking cause, scoped by file prefix, with no
  change to `classify()`'s signature.
- No existing helper resolves "PR head commit SHA" or creates a worktree
  anywhere in this codebase (checked `gates/ci.py`, `gates/gates.py`,
  `spawn.py`) — H1's SHA-pinned worktree provisioning is wholly new code,
  not an extension of an existing helper.
- The after-proposal hunt's vacuous-command finding
  (`docs/reports/2026-08-08-hunt-architecture.md`) is the origin of the
  ADR's command-to-target traceability requirement (§2 of the Decision) —
  confirmed still unaddressed in code (no `claim_scan.py` exists yet).

## H2 — closed vocabulary lives in two different places, not one

The ADR's phrasing ("extend `run.md`/`acceptance_gate.py`") does not
match a single existing enforcement point once the actual code is read;
there are two independent enums, and neither is `acceptance_gate.py`:

1. **`roles/<role>.json` `record_fields.loop_state`** — e.g.
   `roles/implementation.json:20` declares `["scope-proposed",
   "scope-approved", "in-progress", "landed"]`; `roles/architecture.json`
   declares the same four. This is enforced at write time by
   `gates.record_enums()` (`gates/gates.py:302-341`), which rejects any
   `loop_state` value in a changed
   `docs/issue-<n>/reports/<role>.md` not present in that role's
   declared list. **This is the enum the ADR's "closed enum" language
   refers to** — the H2 decision text's own example fields
   (`refused`/`not-needed`/`cannot-verify` as `loop_state` values) only
   make sense against this enum, not against `run.md`'s prose.
2. **`run.md`'s `stage` field** (six fixed values: `proposal` /
   `approval` / `implementation` / `verification` / `merge` / `close`,
   `on-the-record/commands/run.md:114-116`) is a *reporting* convention
   for the orchestrator's own conversational status lines — it is prose
   in a command doc, not a machine-checked enum, and has no gate reading
   it. Extending it would add zero mechanized force; it is not a build
   target.
3. **`acceptance_gate.py`** checks an **issue's** `## Acceptance` section
   for an executable-artifact reference vs. an explicit
   `unverifiable: <reason>` line (`gates/acceptance_gate.py:39-59`) — it
   never reads a role record's frontmatter or field-presence at all. The
   ADR's "extend `acceptance_gate.py`'s field-presence check" does not
   describe code that exists; there is no field-presence check in
   `acceptance_gate.py` to extend. The record-frontmatter field-presence
   check that does exist is `gates.record_wellformed_in()`
   (`gates/gates.py:350-372`), which only checks that the frontmatter
   block parses (has open/close `---`), not that specific fields are
   present for a given `loop_state`.

**Consequence for the proposal**: H2's actual write set is
`roles/*.json` (add `refused`/`not-needed`/`cannot-verify` to each
role's `loop_state` enum) plus a new field-presence check in `gates.py`
(there is no existing per-field-required-by-loop_state check to extend —
one must be added, structurally next to `record_enums`/
`record_wellformed_in`, not inside `acceptance_gate.py`). This is a
deviation from the ADR's literal file list (`run.md`/`acceptance_gate.py`)
to the ADR's actual intent (a closed vocabulary + field-presence
enforcement at "equal structural cost" to what exists) — the ADR text
itself says exact function signatures are a step-3 decision it does not
fix (`## Hand-off`).

## Existing conventions to match

- Pure-function-first: every check exposes a network-free, pure
  function (`check_issue_body`, `classify`, `record_enums`) tested by a
  same-directory `test_*.py` with no `unittest`/`pytest` — see
  `gates/test_acceptance_gate.py`, `gates/test_landing_readiness.py`
  (plain `t_*` functions run via a `main()` that calls each and reports
  pass/fail — check the runner pattern before adding a new test file).
- Fail-closed on missing/unreadable state, never silent skip (repo-wide
  habit, cited directly in the ADR's Consequences section and in
  `record_enums`' docstring: "선언되지 않은 필드는 검사하지 않는다 ...
  role 정의를 못 읽으면 '검사할 게 없다'가 아니라 '검사할 수 없다':
  차단한다").
- Retroactivity rule (`run.md` "게이트 작성 시 지킬 것 (#362)",
  `gates/gates.py` module docstring): a gate judges an artifact against
  the rules in force when the artifact was written, never against rules
  added later. `reexecution_gate.py`/`claim_scan.py` are new required
  gates — existing merged records predate them and must not be
  retroactively judged.
- `gates/*.py` modules are invoked both as CLI scripts (`if __name__ ==
  "__main__"`) and as library imports from `gates.py`/`ci.py`
  (`sys.path.insert(0, str(Path(__file__).parent))` then `import
  <module>`) — new modules should follow the same dual shape.

## Write set implied

- `gates/claim_scan.py` (new) — claim-vocabulary regex + command-adjacency
  + command-to-target traceability, pure functions + CLI, + `gates/test_claim_scan.py`.
- `gates/reexecution_gate.py` (new) — SHA-pinned worktree provisioning,
  subprocess execution, `.reexecution/<issue>-<role>.json` verdict write,
  pure judgment function + CLI, + `gates/test_reexecution_gate.py`.
- `gates/landing_readiness.py` — wire a `reexecution_gate` fail into
  `blocking_causes` (scoped to the affected PR's files), or into
  `main()`'s call site; exact seam decided in the proposal's "What will
  be done".
- `gates/gates.py` — extend `roles/*.json`-driven enum checking with a
  loop_state-conditional field-presence check for refusal-shaped
  records, colocated with `record_enums`/`record_wellformed_in`.
- `roles/*.json` — add `refused`/`not-needed`/`cannot-verify` to each
  role's `record_fields.loop_state` list (at minimum
  `roles/implementation.json`, `roles/architecture.json` — the two
  roles this issue's own execution plan uses; extending every role file
  is a scope question for the proposal, not settled by this survey).
- `.reexecution/` — new gate-owned directory, gitignored (session-
  unwritable per the ADR — never staged by a role's own commits).

## Open questions the proposal must settle (not decided by this survey)

- Exact claim-vocabulary regex and command-to-target traceability
  heuristic (ADR hands this off explicitly as a "living risk").
- Subprocess timeout / resource-limit values.
- Which `roles/*.json` files get the H2 enum extension (all vs. the two
  this issue exercises).
- Exact `.reexecution/<issue>-<role>.json` schema fields.
