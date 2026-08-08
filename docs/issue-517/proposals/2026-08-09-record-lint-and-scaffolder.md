---
status: proposed
files:
  - gates/record_lint.py
  - gates/test_record_lint.py
  - on-the-record/hooks/record-scaffold.sh
  - on-the-record/hooks/test_record_scaffold.py
  - on-the-record/hooks/record-claim-guard.sh
  - gates/ci.py
  - docs/handbooks/record-authoring.md
---

## Request

Issue #517: authoring a role record currently costs one model turn per
gate refusal because record rules are scattered across several
independent checkers, each reporting only its own first failure — a
7-refusal loop was observed on issue-512 phase 2. Build (1) a
`record_lint` command that runs every record rule in one pass and
reports the complete violation list, shared by the existing hooks
instead of duplicated in them, and (2) a scaffolder that generates a
role/issue-appropriate record skeleton with every required section
present as a recognizable placeholder.

## Constraints

- Single source of truth: hooks call the same `record_lint`
  implementation used standalone; no duplicated rule logic between hook
  and lint.
- Must run against a full record file on disk, not only a diff fragment
  — several existing rules (`loop_state` presence, required headings)
  need the whole file, which today's write-time hook cannot see.
- Must work in plugin-installed sessions on arbitrary target repos,
  anchored to the target project root — not hardcoded to this repo's own
  checkout path.
- Placeholder text the scaffolder emits must itself fail `record_lint`
  until replaced (Acceptance's "placeholder-remaining violations"
  requirement), and a filled-in copy must pass clean.
- No CI or hook behavior change beyond routing through the shared
  implementation — existing hook test suites must still pass unmodified
  in intent (per Acceptance).

## Rationale

Two structural alternatives were visible from the survey and rejected:

- **Keep the checks scattered across `gates/gates.py` and
  `record-claim-guard.sh`'s inline mirror, and just document "run these
  several commands before writing"**: rejected because it does not
  satisfy requirement 1's "single command... single source of truth" —
  the Acceptance test asserts one `record_lint` invocation reports every
  violation, which several separate commands cannot produce, and it
  leaves the exact drift risk (hook mirror vs. `gates.py` original)
  requirement 1 names.
- **Rewrite the claim-shape checks from scratch inside `record_lint`
  instead of calling into `gates.py`'s existing check functions**:
  rejected because `gates.py` already owns more check functions than
  `record-claim-guard.sh` currently mirrors (`record_enums`,
  `record_refusal_reasoned`, `record_no_tool_residue_in`,
  `sibling_mention_check`, `reach_check` have no write-time mirror
  today); reimplementing would recreate a second copy of logic that
  already exists once, the opposite of "single source of truth."

Chosen approach: `record_lint` is a thin aggregator module
(`gates/record_lint.py`) that calls the existing `gates.py` check
functions (and the four checks currently inlined in
`record-claim-guard.sh`, lifted out to be called the same way) against a
full record file, unions their violation lists, and exposes both a CLI
entry point (`python3 -m gates.record_lint <path>`, following
`gates/claims.py`'s existing `python3 -m gates.claims .` pattern) and an
importable function `lint_record(path) -> list[str]`.
`record-claim-guard.sh` and `gates/ci.py` are rewired to call
`lint_record`/the CLI instead of their current independent checks, so
there is exactly one place each rule's logic lives.

## What will be done

- `gates/record_lint.py`: `lint_record(path: Path) -> list[str]`
  aggregating `gates.py`'s `record_enums`, `record_refusal_reasoned`,
  `record_wellformed`, `record_no_tool_residue`, `record_derived_counts`,
  `reach_check`, `sibling_mention_check`, plus the four checks
  `record-claim-guard.sh` currently inlines (unverifiable-reason,
  checked-claim reason, bare-count claims, orphaned path references),
  each adapted to run against one file's full text rather than a diff.
  A CLI entry (`python3 -m gates.record_lint <record-path>`) prints every
  violation and exits non-zero if any exist; run with no record files
  present it prints an explicit "no records" result and exits 0
  (Acceptance's empty-state requirement).
- `gates/test_record_lint.py`: a fixture record containing four distinct
  violations (missing `loop_state`, a broken code reference, a missing
  required heading, a bare count claim) asserted via one `record_lint`
  invocation reporting all four.
- `on-the-record/hooks/record-scaffold.sh`: a PreToolUse (or on-demand
  CLI) generator that, given a role and issue number, writes
  `docs/issue-<n>/reports/<role>.md` with every section/field
  `roles/<role>.json`'s `record_fields` declares, filled with
  recognizable placeholder tokens (e.g. `PLACEHOLDER: <field>`) that
  `record_lint` treats as violations until replaced.
- `on-the-record/hooks/test_record_scaffold.py`: asserts the scaffolder's
  raw output fails `record_lint` with only placeholder-remaining
  violations, and a placeholder-filled copy passes clean.
- `on-the-record/hooks/record-claim-guard.sh` and `gates/ci.py`: rewired
  to call `gates.record_lint`'s shared functions instead of their
  current independent/inline logic, so hooks and CI both run the one
  implementation (grep-verifiable: hook script calls into
  `gates.record_lint`, no duplicated rule regexes remain in the hook
  script).
- `docs/handbooks/record-authoring.md`: new handbook section instructing
  "run `record_lint` before writing the record" (issue requirement 3),
  and documenting the scaffolder invocation.

This is a phase-1 proposal only, per the standing survey-order and
role-handoff protocol; no code from this list is written until a human
approver's Approve lands.

## Out of scope

- Changing what any individual rule checks (enum values, heading names,
  claim-shape regexes) — this proposal only aggregates and shares
  existing/mirrored logic, it does not add or alter rules.
- Auto-fixing violations found by `record_lint` — it reports, it does not
  rewrite an author's record content beyond the initial scaffold.
- Extending the scaffolder or lint to any document type outside
  `docs/issue-<n>/reports/<role>.md` records (proposals, surveys, specs
  are not in scope).
- Migrating the per-role skeleton generator under
  `docs/issue-170/_assets/rulebook-skeleton` and
  `docs/issue-167/_assets/rulebook-skeleton` — that is a separate,
  unrelated subsystem this proposal does not touch.

## How you'll know it worked

- `pytest gates/test_record_lint.py` passes: a fixture record with four
  distinct violations yields all four from one `record_lint` invocation.
- `pytest on-the-record/hooks/test_record_scaffold.py` passes: raw
  scaffolder output fails `record_lint` only on placeholder-remaining
  violations; a filled-in copy passes clean.
- `grep` over `on-the-record/hooks/record-claim-guard.sh` and
  `gates/ci.py` shows both calling into `gates.record_lint` rather than
  carrying their own duplicated rule logic.
- Previously passing hook test suites
  (`on-the-record/hooks/test_record_claim_guard.py` and the `gates/`
  test suite) still pass after the rewire.
